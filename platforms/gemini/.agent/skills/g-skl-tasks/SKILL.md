---
name: g-skl-tasks
maturity: production
description: Own and manage all task data — TASKS.md index, tasks/ individual files, status transitions, sync validation, complexity scoring, and sprint planning. Single source of truth for everything task-related.
token_budget: low
subsystem_memberships: [TASK_MANAGEMENT]
---

<!-- gald3r-thinned-shim -->
# g-skl-tasks — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** task lifecycle over TASKS.md + tasks/<status>/.

## Preferred — invoke the engine
- **CLI:** `uv run --project .gald3r_sys/engine gald3r task …`  (or the installed `gald3r`)
- **MCP tools:** `gald3r_task_*`   ·   facade `Gald3r(...).tasks`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`task-file`).
Everything needed ships in the install — nothing external.
