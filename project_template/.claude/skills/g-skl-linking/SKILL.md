---
name: g-skl-linking
description: >
  Unified linking file-mirror (D7 / T1610). Pulls the server-owned world_tree
  linking registry (parent/child/sibling edges + project_type/skills, keyed by
  project UUID — T1625) and writes the human-readable local mirror under
  .gald3r/linking/. Online the mirror reconciles against the registry; offline
  the local mirror is authoritative and reconciles on reconnect. Reconcile is
  non-destructive: conflicting edges open a review item, never overwrite.
token_budget: low
subsystem_memberships: [WORKSPACE_COORDINATION, PROJECT_IDENTITY_SETUP]
---

> **Realtime coordination overhaul (D7):** server-owned linking registry, file-mirrored locally. KEEPS the parent/child/sibling model WPAC's `link_topology.md` modeled; changes only the TRANSPORT.

# g-skl-linking

**Activate for**: "link this project", "pull the linking registry", "re-link to the ecosystem",
"linking mirror", "project topology sync", `@g-linking-pull`, `@g-linking-status`

## When to Use

- After `gald3r login` on a registered project, to pull/refresh the local link mirror
- After `@g-wpac-claim` / `@g-wpac-adopt` / `@g-wpac-spawn` registered an edge (they POST via
  `gald3r workspace outbox send --verb link`), to materialize the updated graph locally
- To re-link a standalone/extracted repo to its ecosystem (this repo's own TT-05 path)
- At session start when `.gald3r/linking/review/` carries unresolved conflict items

## Model vs transport

The MODEL is unchanged from WPAC: `parent`, `children[]`, `siblings[]`, plus `project_type`
and curated `skills[]` — now keyed by **project UUID** (`.gald3r/.identity` `project_id=`).
Only the TRANSPORT changed: `world_tree` owns the authoritative registry (T1625);
`.gald3r/linking/` holds the local mirror.

| State | Authority |
|---|---|
| Online + entitled | Server registry; the local mirror reconciles against it |
| Offline / unentitled / unauthenticated | LOCAL mirror is authoritative; reconciles on reconnect |

## Server endpoints (T1625 — live world_tree mounts)

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/projects/{id}/links` | Grouped parents/children/siblings + project_type/skills |
| `GET /api/v1/projects/{id}/links/mirror` | Deterministic `link_topology.md` emission (byte-stable) |
| `GET /api/v1/projects/topology` | Tenant-wide node/edge graph (Throne Ecosystem Topology feed) |
| `POST /api/v1/projects/{id}/links` | Register an edge — used by wpac claim/adopt/spawn via `gald3r workspace outbox send --verb link` |
| `PUT /api/v1/projects/{id}/profile` | Set project_type + curated skills |

All are Bearer-authed and paid-Team gated server-side (`require_paid_coordination`); the
T1609 shim (absorbed into `gald3r workspace probe|entitlement|token-status`) supplies probe/token/402 handling —
this skill never re-implements them.

## Operations

### PULL — reconcile the local mirror

```
gald3r workspace pull [--json]
```

Code decides the path, never the model (g-rl-38). Outcomes:

| Outcome | Meaning / action |
|---|---|
| `ok` | Mirror updated: `link_topology.md` (server emission verbatim) + `link_registry.json` (structured snapshot). |
| `conflict` | The local `link_topology.md` was hand-edited since the last pull AND differs from the registry — a review item opened under `.gald3r/linking/review/` carrying BOTH versions; **nothing overwritten** (non-destructive reconcile). Resolve by registering the local-only edges server-side (`@g-wpac-claim`/`@g-wpac-adopt` or `gald3r workspace outbox send --verb link`) or accepting the server version, then re-pull. |
| `offline` | world_tree unreachable — local mirror stays authoritative; re-run on reconnect (probe is fail-soft, one cached health check). |
| `unregistered` | No `project_id` UUID in `.gald3r/.identity` — run `@g-setup` / register the project first. |
| `auth_required` | Run `gald3r login` (session token reuse — T605; this skill never writes credentials). |
| `upgrade_required` | Print the shim's upgrade line. Server sync is paid-Team; the basic local file mirror stays free and untouched. |
| `error` | Server-side error — local mirror untouched; log status + detail. |

### STATUS — mirror diagnostics

```
gald3r workspace status [--json]
```

Reports: project UUID presence, mirror/registry file presence, last pull time, open review
items, connectivity. Always exit 0 (verdicts are data).

## Local mirror layout

```
.gald3r/linking/
  link_topology.md          human-readable graph (server emission, byte-stable)
  link_registry.json        parents/children/siblings + profile, structured
  .link_mirror_state.json   hash of last server emission written (conflict detection)
  review/                   non-destructive reconcile review items
```

## Re-linking a standalone repo (end-to-end)

1. `gald3r login` (agent/Throne session — reused read-only by the shim)
2. Ensure the project is registered server-side (its `project_id` UUID exists in the registry)
3. Register edges: `@g-wpac-claim <parent_path>` (or `gald3r workspace outbox send --verb link
   --project-uuid <this_uuid> --payload '{"target_project_id": "<parent_uuid>",
   "relation": "parent"}'`); siblings via `relation: "sibling"`
4. `gald3r workspace pull` — the local `.gald3r/linking/link_topology.md` +
   `link_registry.json` materialize from the registry
5. Offline edits later? They stay authoritative until reconnect; conflicts open review
   items, never silent overwrites

## Tier rules (T633/T641)

Basic mirror (local files, offline authority, review items) — **free**. Server sync
(pull/reconcile against the registry, edge registration) — **paid Team** (the server
re-enforces with 402 on every gated route; the entitlement hint is client-side only).

## Relationship to other skills

| Skill | Relationship |
|---|---|
| `g-skl-wpac-claim` / `g-skl-wpac-adopt` / `g-skl-wpac-spawn` | WRITE edges (registry POST via `gald3r workspace outbox send --verb link`, file topology as fallback); this skill READS + mirrors |
| `g-skl-workspace` | Owns the shared connectivity verbs (`gald3r workspace probe|entitlement|token-status`) + transport (`gald3r workspace outbox`) this skill builds on |
| `g-skl-wpac-sync` | Peer contract sync (content); this skill handles the link GRAPH only |

Tests: in the engine suite (`tests/test_coordination_gald3r workspace`).
