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

## MCP-First Loop (guarded — opt-in until T493 passes)
When an `mcp_url` is configured (in `.gald3r/.identity` or `GALD3R_MCP_URL`), agents that
support it (e.g. `gald3r_agent`) **prefer the MCP task tools** (`gald3r_task_*` /
`get_next_task` → `get_task_context` → `claim_task` → `complete_task`) over reading the full
`TASKS.md` index. This cuts planning-loop tokens by routing each step through one tool call
instead of loading the whole index file.

- **MCP-first when available:** `mcp_url` set → use the MCP tools for the next-task loop.
- **File-first fallback:** no `mcp_url`, or MCP is unreachable / returns `UNAVAILABLE` → fall
  back to the file-first path (read `TASKS.md` + the task file). The fallback is always
  available and is the default; `.gald3r/` markdown remains the source of truth.
- **Guarded:** this MCP-first preference is **opt-in, not the default** — it stays **guarded
  behind the T493 gate** until that contract suite passes. MCP-as-default in skills/commands
  is not enabled; no core task skill ever *requires* `gald3r_agent` or `gald3r_valhalla`.

See `gald3r_agent/docs/gald3r-mcp-integration.md` for the adapter, configuration, and token-cost
details.

## Active agent run → inbox routing (T585)
During a multi-agent / autopilot run (marker `.gald3r/logs/ggo_run_state.json` `active: true`,
or env `GALD3R_AGENT_RUN=1`), the engine `create()` **auto-routes** a new task to `tasks/inbox/`
as an **id-less draft** (uuid-suffixed filename) instead of assigning an id directly. The
hot-inbox **intake** (run at each iteration boundary) is the *single ID-assigning authority* and
assigns ids atomically — so concurrent agents can never collide on the next id. Idle (no run) →
direct create, unchanged. **Hand-writing agents (manual fallback) MUST drop new-task drafts in
`tasks/inbox/` during a run — never write `tasks/open/` + regenerate the index directly.**

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`task-file`).
Everything needed ships in the install — nothing external.
