---
subsystem_memberships: [WORKSPACE_COORDINATION, AGENT_ORCHESTRATION]
---
# g-skl-territory
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Exposes `LEASE` / `RENEW` / `RELEASE` / `STATUS` over subsystem/path territories with TTLs, so
multiple coordinators can safely partition a project without file-based `[🔄]` locking or model
arbitration. Builds directly on the T631 atomic-claim primitive (SQLite `INSERT OR IGNORE` +
expiry takeover) and the T632 subsystem-partitioning policy — it does not re-implement either.

## When to use

- A coordinator scoped via `@g-go-go --subsystem <GROUP>` (T632) leasing its scope before it
  starts claiming tasks.
- A `--swarm` bucket leasing the subsystem(s)/paths it owns for the run.
- Any agent wanting a soft mutual-exclusion signal over a slice of the codebase.
- See the **When to Use** section of `SKILL.md` for the authoritative list.

## Backing implementation

- `gald3r/db.py`: `lease_territory`, `renew_territory`, `release_territory`,
  `territory_status`, `sweep_stale_territory_leases` — the `territory_leases` SQLite table.
- `gald3r/adapters/mcp.py`: `gald3r_territory_lease` / `_renew` / `_release` / `_status` MCP
  tools that wrap the above for any MCP-speaking IDE.
- Tests: `.gald3r_sys/engine/tests/test_db_territory_t1612.py`.

## Related skills

- `g-skl-workspace` — manifest-backed Workspace-Control status/validation (a different layer:
  cross-repo topology, not in-project subsystem leasing).
- `g-skl-wpac-claim` / `g-skl-wpac-adopt` — cross-**project** parent/child topology registration
  (unrelated key space; do not confuse with territory leasing, which is intra-project).
- See the gald3r skill index for the full list.
