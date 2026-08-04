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
