---
name: g-skl-ideas
description: Own and manage IDEA_BOARD.md — capture ideas instantly, review the board, promote to tasks, and run proactive codebase scans for improvement opportunities.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP, VAULT_AND_RESEARCH]
---

<!-- gald3r-thinned-shim -->
# g-skl-ideas — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** idea board (IDEA_BOARD.md).

## Preferred — invoke the engine
- **MCP tools:** `gald3r_idea_*`   ·   facade `Gald3r(...).ideas`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`generic`).
Everything needed ships in the install — nothing external.
