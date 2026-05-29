Update task status or fields. Activates **g-skl-tasks** → UPDATE STATUS operation.

```
@g-task-upd TASK-NNN status in-progress
@g-task-upd TASK-NNN priority high
@g-task-upd TASK-NNN add-dependency TASK-MMM
```

The skill handles: file update, TASKS.md sync, Status History append, subsystem Activity Log update.

> **Unpause alignment check**: when a task transitions from `paused` (`[⏸️]`) → `pending` (`[📋]`), an Alignment Check runs automatically. It scans for stale skill/command/path/subsystem references, collects related work since the pause (git log, completed tasks, DECISIONS.md), and may prompt `(A) Update spec now  (B) Proceed anyway  (C) Cancel unpause` before writing the status change. Age-based escalation: <7d advisory, 7–30d prompt on stale findings, >30d always prompt. See `g-skl-tasks` SKILL.md → *Operation: ALIGNMENT CHECK* for full behavior and the well-known renames table.

> **Alias**: `@g-task-update` also works (deprecated; use `@g-task-upd` for new work).

Workspace-Control updates: `@g-task-upd TASK-NNN workspace-repos gald3r_dev,gald3r_template_full` and `@g-task-upd TASK-NNN workspace-touch-policy generated_output` must validate IDs/policies against `.gald3r/linking/workspace_manifest.yaml` when present. Unknown member IDs are invalid. Widening from current-repo-only to member repos, or to `generated_output`/`multi_repo`, requires Status History context or equivalent explicit instruction before writing the update.
