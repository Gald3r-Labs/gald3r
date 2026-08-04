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

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Run: `gald3r prompt get voice.marketing`
Documentation: https://docs.gald3r.ai
