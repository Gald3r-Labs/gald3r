---
name: g-skl-marketing
description: >
  AI-powered marketing system for gald3r projects. Deploys specialized
  growth agents across SEO, GEO (AI search visibility), content, community,
  and launch channels. Designed for indie founders, solopreneurs, and small
  teams where distribution is the bottleneck — not building.
triggers:
  - "@g-marketing"
  - "@g-marketing-audit"
  - "@g-marketing-launch"
  - "@g-marketing-content"
  - "@g-marketing-geo"
  - "@g-marketing-reddit"
  - "@g-marketing-hn"
  - "@g-marketing-social"
  - "@g-marketing-status"
  - "marketing"
  - "distribution"
  - "launch"
  - "SEO"
  - "GEO"
  - "growth"
token_budget: low
subsystem_memberships: [AGENT_ORCHESTRATION]
---

<!-- gald3r-thinned-shim -->
# g-skl-marketing — thinned shim (prompt-layer)

> **Judgment served by the bundled prompt layer** (one canonical copy in `.gald3r_sys/engine`). Full
> original text retained in **`SKILL.full.md`** for installs without the engine.

**What it does:** distribution-first marketing voice.

## Preferred — fetch the centralized judgment
`uv run --project .gald3r_sys/engine gald3r prompt get voice.marketing`   ·   MCP `gald3r_prompt_get id=voice.marketing`

## Manual fallback (engine not provisioned)
Follow **`SKILL.full.md`** in this directory, plus any `rules.md` / `reference/` / `examples/`.
