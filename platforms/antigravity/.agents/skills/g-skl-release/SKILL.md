---
name: g-skl-release
description: Own and manage all release data — RELEASES.md index and releases/ individual files. Operations: CREATE new release, ASSIGN tasks to a release, STATUS summary, PUBLISH ROADMAP.md, ACCELERATE target dates with cascading shift to subsequent planned releases, SYNC reconcile CHANGELOG entries against release records (C-023).
token_budget: low
subsystem_memberships: [RELEASE_AND_VERSIONING]
---

<!-- gald3r-thinned-shim -->
# g-skl-release — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** release records (RELEASES.md + releases/).

## Preferred — invoke the engine
- **CLI:** `uv run --project .gald3r_sys/engine gald3r release …`  (or the installed `gald3r`)
- **MCP tools:** `gald3r_release_*`   ·   facade `Gald3r(...).release`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`generic`).
Everything needed ships in the install — nothing external.
