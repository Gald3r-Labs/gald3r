---
name: g-skl-subsystems
description: Own and manage SUBSYSTEMS.md (registry + mermaid graph) and subsystems/ spec files. Tracks what subsystems exist, their boundaries, dependencies, and activity logs.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

<!-- gald3r-thinned-shim -->
# g-skl-subsystems — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** subsystem registry (SUBSYSTEMS.md + subsystems/).

## Preferred — invoke the engine
- **MCP tools:** `gald3r_subsystem_*`   ·   facade `Gald3r(...).subsystems`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`subsystem-file`).
Everything needed ships in the install — nothing external.
