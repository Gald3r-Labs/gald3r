---
name: g-skl-crr
description: Clean-Room Rewrite pipeline. Orchestrates 4 phases via independent background subagents — harvest a source repo, write all findings to IDEA_BOARD (mandatory), triage tasks, and produce a gald3r-native clean-room implementation spec.
triggers:
  - "@g-crr"
  - "clean room rewrite"
  - "clean-room rewrite"
  - "crr"
  - "harvest and spec"
token_budget: high
subsystem_memberships: [VAULT_AND_RESEARCH, AGENT_ORCHESTRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
