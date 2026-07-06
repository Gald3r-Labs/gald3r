---
name: g-skl-code-review
description: Code review — security, quality, performance, reusability. Structured report with severity ratings and action items. Scales from quick scan to comprehensive architecture review.
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-skl-code-review — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** comprehensive code review — security, quality, performance, reusability.

## Preferred — fetch the centralized judgment
`gald3r prompt get role.code_reviewer`   ·   MCP `gald3r_prompt_get id=role.code_reviewer`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
