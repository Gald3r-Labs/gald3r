---
name: g-agnt-test
description: Test plan manager for gald3r projects — creates and maintains fast (L1), comprehensive (L2), and regression (L3) test plans. Activates on code review, verification gates, pre-release checks, and @g-test commands. Enforces C-013 (test plan maintenance), C-014 (fast test gate), and C-015 (comprehensive/regression before release).
model: inherit
tools: Read, Write, Edit, Bash, Glob, Grep
subsystem_memberships: [BUG_AND_QUALITY]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
