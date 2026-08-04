---
name: g-skl-policy
tier: full
local_only: false
description: Policy-as-code guardrail — loads an org policy bundle (file offline, world_tree online) and exposes a CHECK op used by the pre-tool-call and pre-commit hooks to deterministically block/allow. Team/Org tier only; free/retail installs run an empty/default bundle.
triggers:
  - "@g-policy-check"
  - "@g-policy-status"
  - "org policy"
  - "policy bundle"
  - "policy guardrail"
operations:
  - CHECK
  - STATUS
token_budget: low
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
