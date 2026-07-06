---
name: g-skl-territory
description: Lease, renew, release, and check status of subsystem/path territories with TTLs — the coordination primitive multiple coordinators use to safely partition a project without stepping on each other's work.
token_budget: low
subsystem_memberships: [WORKSPACE_COORDINATION, AGENT_ORCHESTRATION]
---

> **Territory leasing (T1612 / D15):** builds on the T631 atomic-claim primitive and the T632
> subsystem-partitioning policy rather than re-implementing either. This skill is this repo's
> owned implementation of `LEASE` / `RENEW` / `RELEASE` / `STATUS` over territories.
# g-skl-territory

## When to Use

Use this skill whenever a coordinator (or a swarm of coordinators) needs to claim ownership of
a **territory** — a subsystem name (e.g. `WORKSPACE_COORDINATION`) or a path prefix — for a
bounded period, so that other coordinators know to steer clear without any file-based
`[🔄]` locking or model arbitration.

Typical callers:
- `@g-go-go --subsystem <GROUP>` (T632 partitioning) leasing its scope before it starts claiming
  tasks in that scope.
- A `--swarm` bucket leasing the subsystem(s) it owns for the run.
- Any agent that wants a soft mutual-exclusion signal over a slice of the codebase without
  touching the task-claim table directly.

## Operations

All four operations are backed by MCP tools exposed on the project server (`adapters/mcp.py`),
which call straight into `gald3r/db.py`'s `lease_territory` / `renew_territory` /
`release_territory` / `territory_status`. There is no CLI wrapper needed — call the tools
directly.

### LEASE

```
gald3r_territory_lease(territory, owner, ttl_min=120, worktree_path="", worktree_branch="", worktree_owner="")
```

Atomically leases `territory` to `owner` for `ttl_min` minutes. Implemented as the SAME
`INSERT OR IGNORE` + expiry-takeover pattern as `db.claim_task` (T631) — just keyed on
`territory` instead of `task_uuid`. Contention is resolved by CODE: exactly one caller gets
`GRANTED`; every other caller gets the deterministic **loser result**:

```json
{"status": "HELD", "territory": "...", "owner": "<held-by>", "expires_at": "...",
 "reason": "held by <held-by> until <expires_at>"}
```

No model arbitration ever decides who wins (g-rl-38) — the SQLite write-lock does. Pass
`worktree_path`/`worktree_branch`/`worktree_owner` when the caller is running from a worktree
(g-rl-02 metadata standard) so `STATUS` can attribute the lease to a concrete checkout.

A lease already held by the SAME `owner` is idempotently re-granted and refreshed (calling
`LEASE` again is a safe way to keep a lease alive instead of a separate `RENEW` call, though
`RENEW` is cheaper since it skips the insert branch).

An **expired** lease (TTL elapsed, no renew) is reclaimable by anyone — the next `LEASE` call
takes it over atomically.

### RENEW

```
gald3r_territory_renew(territory, owner, ttl_min=120)
```

Extends a lease **you already hold**. Unlike `LEASE`, `RENEW` does NOT take over an expired
lease from someone else — it only succeeds when `owner` is the current holder of a still-live
lease. Returns `{"status": "RENEWED", ...}` on success, `{"status": "HELD", ...}` if someone
else holds it, or `{"status": "NOT_FOUND", ...}` if the territory was never leased.

### RELEASE

```
gald3r_territory_release(territory, owner)
```

Releases a lease you hold — call this on clean completion or failure so the territory is
immediately available rather than waiting out the TTL. Returns `{"released": true|false}`;
`false` means you didn't hold it (already released, expired-and-swept, or never yours — a
safe no-op, never an error).

### STATUS

```
gald3r_territory_status(territory=None)
```

Lists active (non-expired) leases. Pass `territory` to check a single one; omit it to see every
live lease project-wide. Each row includes `owner`, `leased_at`, `expires_at`, and the worktree
metadata (`worktree_path`/`worktree_branch`/`worktree_owner`) recorded at lease time.

## Crash-Safety

A lease whose TTL has elapsed with no renew is stale and reclaimable — the same TTL + sweep
model T642 defined for the Redis swarm-lock backend. `LEASE` takes over an expired row inline
(lazy reclaim on next contention); `db.sweep_stale_territory_leases(conn)` proactively clears
stale rows (e.g. at coordinator startup) so `STATUS` doesn't show ghosts. Unlike task claims,
territory leases have no owning `coordinator_session` row to cross-check heartbeat against —
TTL elapsed is itself the sole reclaim signal.

## Online / Offline Behavior

- **Offline / free tier (default, all tiers):** a lease is a local, atomic SQLite
  `INSERT OR IGNORE` with a `lease_expires_at` in `.gald3r/gald3r.db` — exactly the mechanism
  above. This is the single-coordinator local lease and needs nothing else.
- **Online (world_tree connected):** the lease additionally pre-checks + pushes to `world_tree`,
  following the same pattern T640 defines for `task_claims` — online pre-check, write local,
  push `ON CONFLICT`. **world_tree T640 (task_claims PG mirror) is open**, so the online half of
  territory leasing is partial until it lands; the local SQLite half above is fully functional
  today and is what every offline/free/Pro caller uses.
- **Multi-machine leasing** (more than one physical machine leasing territories against the same
  project) is gated behind the Redis add-on entitlement (`can_use_redis_coordination`,
  T642/T641) — the same boundary the swarm-lock interface uses. Unentitled callers fall back to
  the SQLite path above with no functional loss on a single machine.

## Relationship to Existing Primitives

| Primitive | Owns | This skill |
|---|---|---|
| T631 `task_claims` | Exactly-one-claimer per **task UUID** | Reused pattern (INSERT OR IGNORE + expiry takeover), NOT re-implemented |
| T632 partitioning | Subsystem **scope** policy + collision detection for coordinators | Complementary — a coordinator can lease the same subsystem name it partitions on |
| T642 swarm locks | Exactly-one-bucket per **file path** (SQLite default, Redis team backend) | Same TTL + sweep crash-safety model, applied to territories instead of paths |

Territory leasing is a **new key space** (`territory_leases`, keyed on `territory`) — it does
not touch `task_claims` or `swarm_locks` rows, so leasing a territory has zero effect on
existing task-claim or file-lock behavior.

## Example

```
# Coordinator A partitions onto WORKSPACE_COORDINATION and leases it for 2 hours
gald3r_territory_lease("WORKSPACE_COORDINATION", "coord-A", ttl_min=120,
                       worktree_path="G:/gald3r_labs/wt/templates-grind1612",
                       worktree_branch="grind/t1612", worktree_owner="coord-A")
# -> {"status": "GRANTED", "territory": "WORKSPACE_COORDINATION", "owner": "coord-A", "expires_at": "..."}

# Coordinator B tries the same territory -> deterministic loser result, no arbitration
gald3r_territory_lease("WORKSPACE_COORDINATION", "coord-B")
# -> {"status": "HELD", "owner": "coord-A", "expires_at": "...", "reason": "held by coord-A until ..."}

# Coordinator A keeps working -> renews before the TTL runs out
gald3r_territory_renew("WORKSPACE_COORDINATION", "coord-A", ttl_min=120)

# Coordinator A finishes -> releases immediately instead of waiting out the TTL
gald3r_territory_release("WORKSPACE_COORDINATION", "coord-A")

# Anyone can check who holds what right now
gald3r_territory_status()
```
