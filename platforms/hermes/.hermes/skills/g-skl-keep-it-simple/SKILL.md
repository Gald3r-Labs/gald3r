---
name: g-skl-keep-it-simple
description: User-invoked terse mode toggle. Suppresses the active personality pack, response structure scaffolding, and footer metadata so the agent returns bare signal only. Intended for debugging, rapid lookups, and high-volume Q&A sessions where the standard ceremony adds noise. Deactivates at session boundary or on explicit toggle-off.
triggers:
  - "@g-skl-keep-it-simple"
  - "/g-keep-it-simple"
  - "terse mode"
  - "keep it simple"
  - "quiet mode"
token_budget: low
skill_trust_level: core
subsystem_memberships: [AGENT_ORCHESTRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
