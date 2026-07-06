---
name: g-skl-review
description: Code review for security, quality, performance, reusability; structured report with severity and actions.
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-skl-review — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** code/work review.

## Preferred — fetch the centralized judgment
`gald3r prompt get role.code_reviewer`   ·   MCP `gald3r_prompt_get id=role.code_reviewer`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
