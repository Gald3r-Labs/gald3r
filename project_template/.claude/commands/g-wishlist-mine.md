---
subsystem_memberships: [TASK_MANAGEMENT]
---
# g-wishlist-mine - Mine a human-prose wishlist/intent doc into tasks (READ-ONLY)

Reads a free-form, human-prose intent/wishlist document (the user's own words, no schema) and
mines READY, concrete wants into formal gald3r tasks — deduping against existing tasks, routing
vision to epics, and reporting unsure items as backlog candidates. The prose doc is **never
modified**. Activates **g-skl-wishlist-mine** → MINE operation.

## Usage

```
@g-wishlist-mine [doc-path] [--dry-run] [--target-repo <repo_id>] [--cascade]
```

- `doc-path` (optional) — path to the prose doc. Defaults: configured `wishlist_doc:`, else
  `.gald3r/DELIVERABLES.md`, else `.gald3r/WISHLIST.md`. Asks if none found.
- `--dry-run` — propose tasks without creating them (review the table first).
- `--target-repo <repo_id>` — WPAC controllers only: route mined tasks to a member repo
  (cascade via `@g-wpac-order`). Default `local`.
- `--cascade` (T465) — WPAC controllers only: auto-dispatch created tasks to their `target_repo:`
  via `@g-wpac-order` at the end of the run. Controller-tier-gated — a non-controller never cascades.

Server-backed (T465): `gald3r wishlist mine` (CLI) and the Throne `mineWishlist` bridge call the
world_tree route `POST /api/v1/planner/wishlist/mine` to run mining server-side (JWT-gated,
tenant-safe). The route returns the proposed/backlog split + an agent-session dispatch (the JUDGMENT
runs via `/agent/run`, never an inline LLM); the prose doc stays READ-ONLY (`doc_modified: false`).

## Steps

1. Activate the **g-skl-wishlist-mine** skill, MINE operation.
2. The skill resolves + confirms the doc path, reads it READ-ONLY, extracts READY/VISION/UNSURE
   wants, dedups against `.gald3r/TASKS.md`, creates READY tasks + epics via `g-skl-tasks`, and
   emits the created-tasks table + backlog-candidates list.

## After running

- Review the **Backlog Candidates** list and run `@g-task-add` for any you want to promote.
- The prose doc is left untouched — it is human-owned and read-only.

## Related

- Skill: `g-skl-wishlist-mine` (implementation), `g-skl-tasks` (task creation), `g-skl-wpac-order` (cascade)
- Task: T453
