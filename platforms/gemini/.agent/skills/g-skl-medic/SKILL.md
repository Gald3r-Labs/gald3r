---
name: g-skl-medic
maturity: beta
version: 2.0.0
description: >
  Tiered .gald3r/ health and intervention system. L1=triage (structural), L2=diagnosis
  (plan coherence), L3=surgery (cross-subsystem interface audit), L4=ecosystem
  (linked project negotiation). Replaces g-skl-medic.
triggers:
  - "@g-medic"
  - "fix gald3r"
  - "health check"
  - "upgrade gald3r"
  - "project is out of sync"
  - "placeholders"
  - broken TASKS.md
  - missing files
  - version mismatch
  - "medic"
token_budget: high
subsystem_memberships: [PROJECT_IDENTITY_SETUP, AGENT_ORCHESTRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
