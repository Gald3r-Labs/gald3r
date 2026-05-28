Archive terminal task history into `.gald3r/archive/` while keeping `TASKS.md` as an active working index.

```
@g-task-archive --dry-run
@g-task-archive --apply
@g-task-archive --dry-run --include-recent
```

## What This Command Does

Delegates to **g-skl-tasks** -> ARCHIVE TASKS.

The command moves completed/failed/cancelled task history out of the active index and into count-based archive buckets:

- Index files: `.gald3r/archive/archive_tasks_0000_0999.md`, `.gald3r/archive/archive_tasks_1000_1999.md`, ...
- Task files: `.gald3r/archive/tasks/tasks_0000_0999/`, `.gald3r/archive/tasks/tasks_1000_1999/`, ...

Buckets hold at most 1000 archive entries/files and are assigned by archive entry ordinal, not by original task ID.

## Safety

- Dry-run is the default.
- Apply requires an active task that explicitly authorizes archival work.
- Active, blocked, paused, in-progress, awaiting-verification, and requires-user-attention tasks must stay in `TASKS.md`.
- Recently completed tasks stay active unless `--include-recent` is supplied.
- Archive apply must leave an Archive Pointers section in `TASKS.md`.
