---
name: g-skl-constraints
description: Own and manage .gald3r/CONSTRAINTS.md — add, update, deprecate, check, and surface project constraints at session start.
token_budget: low
skill_trust_level: core
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

<!-- gald3r-thinned-shim -->
# g-skl-constraints — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** constraint registry (CONSTRAINTS.md).

## Preferred — invoke the engine
- **MCP tools:** `gald3r_constraint_*`   ·   facade `Gald3r(...).constraints`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`generic`).
Everything needed ships in the install — nothing external.
