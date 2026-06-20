---
name: g-skl-bugs
description: Own and manage all bug data — BUGS.md index, bugs/ individual files, bug fixes, quality metrics. Single source of truth for everything bug and quality related.
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-skl-bugs — thinned shim (engine-backed)

> **Handled by the bundled gald3r engine** (`.gald3r_sys/engine`, pure Mode-A, no LLM). Full original
> procedure retained in **`SKILL.full.md`** so an install without the engine still works.

**What it does:** bug lifecycle over BUGS.md + bugs/<status>/.

## Preferred — invoke the engine
- **CLI:** `uv run --project .gald3r_sys/engine gald3r bug …`  (or the installed `gald3r`)
- **MCP tools:** `gald3r_bug_*`   ·   facade `Gald3r(...).bugs`

The engine owns ID allocation, file placement, status→folder moves, index regeneration, and
validation. `.gald3r/` markdown stays the data source of truth.

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** (full procedure) + the schema in `.gald3r_sys/schemas/` (`bug-file`).
Everything needed ships in the install — nothing external.
