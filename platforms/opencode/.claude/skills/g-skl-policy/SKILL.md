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

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
