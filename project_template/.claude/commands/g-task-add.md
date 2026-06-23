---
subsystem_memberships: [TASK_MANAGEMENT]
---
Create a new task. Activates **g-skl-tasks** → CREATE TASK operation.

```
@g-task-add "Task title and brief description"
```

The skill handles: ID assignment, complexity scoring, file creation, TASKS.md entry — all atomically.

> **Active agent run → inbox routing (T585):** during a `g-go-go` / `g-go-code` / swarm run (marker `.gald3r/logs/ggo_run_state.json` `active: true`, or env `GALD3R_AGENT_RUN=1`), the skill/engine writes the new task to `tasks/inbox/` as an **id-less draft** instead of assigning an id directly — the hot-inbox intake assigns the real id atomically at the next iteration boundary, so concurrent agents never collide on the next id. Display: *"Agent run detected — task queued to inbox for safe ID assignment."* No active run → direct create, unchanged.

> **Alias**: `@g-task-new` also works (deprecated; use `@g-task-add` for new work).

Workspace-Control optional flags/fields: when a task may inspect or modify workspace members, include `workspace_repos` and `workspace_touch_policy`. Validate repo IDs and touch policies against `.gald3r/linking/workspace_manifest.yaml` when present; unknown IDs are invalid. Omit both fields for current-repo-only work. Member repo writes require explicit member IDs, compatible policy, task authorization, and manifest write permission.
