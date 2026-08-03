---
description: 'Update a task''s status, priority, dependencies, promotion/demotion, or release-hold fields.'
subsystem_memberships: [TASK_MANAGEMENT]
execution_tier: guarded_prompt
---
Update task status or fields. Activates **g-skl-tasks** → UPDATE STATUS operation.

```
@g-task-upd TASK-NNN status in-progress
@g-task-upd TASK-NNN priority high
@g-task-upd TASK-NNN add-dependency TASK-MMM
@g-task-upd --promote TASK-NNN          # waiting → pending (all spec prereqs confirmed met)
@g-task-upd --demote TASK-NNN --reason "Decision reversed — re-spec needed"

@g-task set-release-hold TASK-NNN manual "Holding for coordinated deploy"
@g-task set-release-hold TASK-NNN sync_required "API contract change" --sync-project gald3r_agent --sync-task T890
@g-task set-release-hold TASK-NNN none "Ready to ship"     # equivalent to clear
@g-task clear-release-hold TASK-NNN
```

The skill handles: file update, TASKS.md sync, Status History append, subsystem Activity Log update.

> **`--promote` (waiting → pending)**: moves a `[⌛] waiting` task to `[📋] pending`. Clears `waiting_since` TTL. Writes Status History row. Should only be called when `spec_task_reqs` are all `[✅]` and any `spec_reqs` have been manually verified.

> **`--demote` (any → waiting)**: moves a task back to `[⌛] waiting` with an optional reason. Used when a decision changes, a dependency is cancelled, or a spec must be re-done. Optionally adds new `spec_reqs` entries. Writes Status History row.

> **Unpause alignment check**: when a task transitions from `paused` (`[⏸️]`) → `pending` (`[📋]`), an Alignment Check runs automatically. It scans for stale skill/command/path/subsystem references, collects related work since the pause (git log, completed tasks, DECISIONS.md), and may prompt `(A) Update spec now  (B) Proceed anyway  (C) Cancel unpause` before writing the status change. Age-based escalation: <7d advisory, 7–30d prompt on stale findings, >30d always prompt. See `g-skl-tasks` SKILL.md → *Operation: ALIGNMENT CHECK* for full behavior and the well-known renames table.

> **Release staging (T419)**: `set-release-hold <id> <none|manual|sync_required> "<reason>"` and `clear-release-hold <id>` set/clear the `release_hold` frontmatter field that `g-ship` sweeps and `g-status` surfaces. `manual` and `sync_required` hold a task back from a release; `none` (or clear) lets `g-ship` include it. For `sync_required`, pass `--sync-project <id> --sync-task <id>` to record the sync partner in `sync_with:`. Engine-backed: `gald3r task set-release-hold|clear-release-hold` (CLI) / `gald3r_task_set_release_hold` / `gald3r_task_clear_release_hold` (MCP). See `g-skl-tasks` SKILL.full.md → *Release Staging — `release_hold` Field*.

> **Alias**: `@g-task-update` also works (deprecated; use `@g-task-upd` for new work).

Workspace-Control updates: `@g-task-upd TASK-NNN workspace-repos <gald3r_source>,<template_full>` and `@g-task-upd TASK-NNN workspace-touch-policy generated_output` must validate IDs/policies against `.gald3r/linking/workspace_manifest.yaml` when present. Unknown member IDs are invalid. Widening from current-repo-only to member repos, or to `generated_output`/`multi_repo`, requires Status History context or equivalent explicit instruction before writing the update.
