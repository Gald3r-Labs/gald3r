---
name: g-skl-plan
description: Own and manage PLAN.md (master strategy) and features/ (individual Feature files) — create plans, stage features, validate scope, and keep the deliverable index current.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

<!-- gald3r-thinned-shim -->
# g-skl-plan — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** planning & feature-staging judgment.

## Preferred — fetch the centralized judgment
`gald3r prompt get playbook.plan`   ·   MCP `gald3r_prompt_get id=playbook.plan`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
