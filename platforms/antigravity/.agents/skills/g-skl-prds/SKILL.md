---
name: g-skl-prds
description: Own and manage all PRD data — PRDS.md index, prds/ individual files, governance lifecycle (draft→review→approved→in-implementation→released→archived), revision chain, and freeze enforcement. Parallel artifact to Features for compliance, audit, and external sign-off.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

<!-- gald3r-thinned-shim -->
# g-skl-prds — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** PRD lifecycle over PRDS.md + prds/ (frozen on release).

## Preferred — invoke the engine
- **MCP tools:** `gald3r_prd_*`   ·   facade `Gald3r(...).prds`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`prd-file`).
Everything needed ships in the install — nothing external.
