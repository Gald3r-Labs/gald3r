---
name: g-skl-features
description: Own and manage all feature data — FEATURES.md index, features/ individual files, staging lifecycle (staging→specced→committed→shipped), harvest source collection, and feature promotion. Single source of truth for everything feature-related.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

<!-- gald3r-thinned-shim -->
# g-skl-features — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** feature staging over FEATURES.md + features/.

## Preferred — invoke the engine
- **MCP tools:** `gald3r_feature_*`   ·   facade `Gald3r(...).features`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`feature-file`).
Everything needed ships in the install — nothing external.
