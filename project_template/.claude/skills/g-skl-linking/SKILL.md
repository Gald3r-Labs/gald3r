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

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

> **Realtime coordination overhaul (D7):** server-owned linking registry, file-mirrored locally. KEEPS the parent/child/sibling model WPAC's `link_topology.md` modeled; changes only the TRANSPORT.

# g-skl-linking

**Activate for**: "link this project", "pull the linking registry", "re-link to the ecosystem",
"linking mirror", "project topology sync", `@g-linking-pull`, `@g-linking-status`

## When to Use

- After `gald3r login` on a registered project, to pull/refresh the local link mirror
- **(T255) No longer required after a successful `@g-wpac-claim` / `@g-wpac-adopt` /
  `@g-wpac-spawn` edge registration** — `gald3r workspace outbox send --verb link` now
  auto-chains a `pull` the moment the POST returns `ok`, so the local mirror already
  reflects the new edge. A manual pull is still the right move when the edge was
  registered by ANOTHER project/session (this project's mirror wasn't the one that
  sent `link`), or after any `offline`/`error`/`auth_required`/`upgrade_required`
  outcome once connectivity/entitlement is restored
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
| `ok` | Mirror updated: `link_topology.md` (server emission verbatim) + `link_registry.json` (structured snapshot). **T328**: `.gald3r/.identity`'s `wpac_role=` and `.gald3r/linking/workspace_manifest.yaml`'s `wpac_relationship:` block are synced from the SAME emission in the SAME call (see `identity_reconcile` in the result) — the two other identity surfaces no longer drift behind the topology mirror (BUG-236). |
| `conflict` | Either (a) the local `link_topology.md` was hand-edited since the last pull AND differs from the registry, or (b) **T328/BUG-237**: the emission's own `project_id` disagrees with the project that queried it (a mismatched/conflated registry answer — e.g. gald3r_throne vs gald3r_throne_dev). Either way a review item opens under `.gald3r/linking/review/` carrying both versions; **nothing overwritten** — case (b) refuses ALL THREE surfaces (topology, identity, manifest), never just the newer two. Resolve (a) by registering the local-only edges server-side (`@g-wpac-claim`/`@g-wpac-adopt` or `gald3r workspace outbox send --verb link`) or accepting the server version, then re-pull; resolve (b) by fixing the registry-side project_id association before re-pulling. |
| `offline` | world_tree unreachable — local mirror stays authoritative; re-run on reconnect (probe is fail-soft, one cached health check). |
| `unregistered` | No `project_id` UUID in `.gald3r/.identity` — run `@g-setup` / register the project first. |
| `auth_required` | Run `gald3r login` (session token reuse — T605; this skill never writes credentials). |
| `upgrade_required` | Print the shim's upgrade line. Server sync is paid-Team; the basic local file mirror stays free and untouched. |
| `error` | Server-side error — local mirror untouched; log status + detail. |

`project_id=` in `.gald3r/.identity` is NEVER written by the T328 reconcile path (`.identity` remains the read-only local ground truth this skill has always treated it as) — only `wpac_role=` syncs.

### STATUS — mirror diagnostics

```
gald3r workspace status [--json]
```

Reports: project UUID presence, mirror/registry file presence, last pull time, open review
items, connectivity, and (**T328**) a `drift` block — a read-only, always-on comparison of
`.identity` / `workspace_manifest.yaml` / `link_topology.md` `wpac_role` (and a `project_id`
conflation check, BUG-237) surfaced even when a drift slipped through outside `pull` (offline
hand-edits, a pre-T328 mirror, a restored backup). Always exit 0 (verdicts are data).

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
   "relation": "parent"}'`); siblings via `relation: "sibling"`. **(T255)** a successful
   `link` send already refreshes `.gald3r/linking/link_topology.md` + `link_registry.json`
   for you at this point — step 4 below is for the "wasn't the sender" / reconnect cases.
4. `gald3r workspace pull` — reconcile the local mirror against the FULL registry (covers
   edges another project/session registered, or anything queued while offline)
5. Offline edits later? They stay authoritative until reconnect; conflicts open review
   items, never silent overwrites

## Tier rules (T633/T641)

Basic mirror (local files, offline authority, review items) — **free**. Server sync
(pull/reconcile against the registry, edge registration) — **paid Team** (the server
re-enforces with 402 on every gated route; the entitlement hint is client-side only).

## Relationship to other skills

| Skill | Relationship |
|---|---|
| `g-skl-wpac-claim` / `g-skl-wpac-adopt` / `g-skl-wpac-spawn` | WRITE edges (registry POST via `gald3r workspace outbox send --verb link`, file topology as fallback). T255: a successful `link` POST auto-chains a call into this skill's own `pull` so the two never silently diverge — see `cli/commands/workspace.py::_handle_workspace_outbox_send`. This skill READS + mirrors; it never POSTs an edge itself. |
| `g-skl-workspace` | Owns the shared connectivity verbs (`gald3r workspace probe|entitlement|token-status`) + transport (`gald3r workspace outbox`) this skill builds on |
| `g-skl-wpac-sync` | Peer contract sync (content); this skill handles the link GRAPH only |

**T255 canonical story**: exactly one writer per state — `wpac_transport`'s `link` verb
writes the SERVER edge; this skill's `pull`/`status` (`linking_mirror.py`) writes the
LOCAL mirror. They are chained (not merged, not duplicated): `link` triggers a `pull` on
`ok`. Neither path is deprecated.

Tests: in the engine suite (`tests/test_coordination_gald3r workspace`).
