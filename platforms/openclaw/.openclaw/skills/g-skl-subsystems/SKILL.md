---
name: g-skl-subsystems
description: Own and manage SUBSYSTEMS.md (registry + mermaid graph) and subsystems/ spec files. Tracks what subsystems exist, their boundaries, dependencies, and activity logs.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

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
Follow **`SKILL.full.md`** (full procedure); the engine validates via its embedded schemas (`gald3r validate`; `subsystem-file`).
Everything needed ships in the install — nothing external.
