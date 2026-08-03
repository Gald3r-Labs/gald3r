---
description: 'Archive completed/failed/cancelled tasks into .gald3r/archive/ buckets via `gald3r task archive` (T497).'
subsystem_memberships: [TASK_MANAGEMENT]
execution_tier: orchestration
---
Archive terminal task history into `.gald3r/archive/` while keeping `TASKS.md` as an active working index.

```
@g-task-archive
@g-task-archive --apply
@g-task-archive --include-recent
@g-task-archive --apply --include-recent --recent-window-days 7
```

## What This Command Does

Runs the compiled **`gald3r task archive`** verb (T497 -- backs g-rl-33's Active Index
Archive Gate, which previously had no deterministic implementation).

The verb moves completed/failed/cancelled task history out of the active index and into
count-based archive buckets:

- Index files: `.gald3r/archive/archive_tasks_0000_0999.md`, `.gald3r/archive/archive_tasks_1000_1999.md`, ...
- Task files: `.gald3r/archive/tasks/tasks_0000_0999/`, `.gald3r/archive/tasks/tasks_1000_1999/`, ...

Buckets hold at most 1000 archive entries/files and are assigned by archive entry ordinal, not
by original task ID. Each archived file's frontmatter gains an `archive:` provenance block
(slot, index path, archived-at date, source project, original task id).

## Flags

| Flag | Effect |
|---|---|
| (none) | Dry-run preview -- classifies every candidate, writes nothing. |
| `--apply` | Actually move files, update the DB, and rewrite `TASKS.md`. |
| `--include-recent` | Also archive terminal tasks completed within the recency window (default: excluded). |
| `--recent-window-days N` | Override the default 14-day recency window. |
| `--json` | Machine-readable report (candidates, exclusions, held-back-as-recent). |

## Safety

- Dry-run is the default -- `--apply` is required to write anything.
- A task still listed as a `dependencies:` target of any other on-disk task is excluded from
  archival (reported under "Excluded"), regardless of that referencing task's own status --
  archiving it would leave the referencing task's dependency dangling.
- Recently completed tasks stay active unless `--include-recent` is supplied.
- Never deletes history: files move, they are not removed. The task/bug row in `gald3r.db` is
  relocated out of the live `tasks` table (so `gald3r db verify` never reports an `orphan_row`)
  -- `status_history` rows are preserved as permanent audit trail.
- Apply leaves an `## Archive Pointers` section in `TASKS.md` linking every archive index file.
- As with any `--apply` destructive verb, only run it when the active task explicitly
  authorizes archival work -- the CLI itself has no session/task-authorization concept, so this
  is an agent-level discipline, not something the verb enforces.
