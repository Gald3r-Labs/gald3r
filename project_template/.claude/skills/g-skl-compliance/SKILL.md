---
name: g-skl-compliance
tier: full
local_only: false
description: SCA/license compliance scanning — wraps ORT, FOSSA, Snyk, and PMD CPD behind a unified gald3r interface with SCAN/REPORT/GATE/STATUS operations. Produces structured compliance reports with pass/warn/fail verdicts.
triggers:
  - "@g-compliance-scan"
  - "@g-compliance-gate"
  - "@g-compliance-report"
  - "compliance scan"
  - "license check"
  - "dependency audit"
  - "SCA scan"
  - "is our code clean"
operations:
  - SCAN
  - REPORT
  - GATE
  - STATUS
token_budget: medium
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
