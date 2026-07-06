---
name: g-skl-verify-ladder
description: >-
  Multi-level verification gates for autonomous task completion. Configurable
  levels from minimal (lint) to thorough (tests + acceptance + hallucination guard).
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

<!-- gald3r-thinned-shim -->
# g-skl-verify-ladder — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** adversarial verification ladder (evidence standards, two-stage gate).

## Preferred — fetch the centralized judgment
`gald3r prompt get role.verifier`   ·   MCP `gald3r_prompt_get id=role.verifier`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
