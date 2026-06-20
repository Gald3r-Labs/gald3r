---
name: g-skl-qa
description: Track bugs, QA, and fixes in .gald3r/. For bug reports, issues, quality, fixes, QA workflows.
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-skl-qa — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** bug tracking + quality gates (zero-tolerance error logging).

## Preferred — fetch the centralized judgment
`uv run --project .gald3r_sys/engine gald3r prompt get role.qa_engineer`   ·   MCP `gald3r_prompt_get id=role.qa_engineer`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
