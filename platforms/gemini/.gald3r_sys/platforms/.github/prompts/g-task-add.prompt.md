Create a new task. Activates **g-skl-tasks** → CREATE TASK operation.

```
@g-task-add "Task title and brief description"
```

The skill handles: ID assignment, complexity scoring, file creation, TASKS.md entry — all atomically.

> **Alias**: `@g-task-new` also works (deprecated; use `@g-task-add` for new work).

Workspace-Control optional flags/fields: when a task may inspect or modify workspace members, include `workspace_repos` and `workspace_touch_policy`. Validate repo IDs and touch policies against `.gald3r/linking/workspace_manifest.yaml` when present; unknown IDs are invalid. Omit both fields for current-repo-only work. Member repo writes require explicit member IDs, compatible policy, task authorization, and manifest write permission.
