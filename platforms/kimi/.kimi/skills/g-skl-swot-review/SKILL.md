---
name: g-skl-swot-review
description: >-
  Automated SWOT analysis for the current project phase. Reviews progress,
  architectural compliance, code quality, goal alignment, and technical debt.
  Runs weekly via heartbeat or on-demand.
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-skl-swot-review — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** structured SWOT analysis of the current project phase.

## Preferred — fetch the centralized judgment
`uv run --project .gald3r_sys/engine gald3r prompt get rubric.swot`   ·   MCP `gald3r_prompt_get id=rubric.swot`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
