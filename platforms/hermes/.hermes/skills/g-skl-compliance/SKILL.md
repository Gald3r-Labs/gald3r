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

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
