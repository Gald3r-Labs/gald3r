---
name: g-skl-security-scan
description: SAST-style static analysis for hardcoded secrets, injection patterns, insecure deserialization, path traversal, and other critical vulnerabilities. Severity-ranked findings with line references and remediation guidance. Includes two-phase threat-model + diff-revalidation mode (T1167) for use as the post-implementation gate in g-go-review.
token_budget: medium
subsystem_memberships: [BUG_AND_QUALITY, SECURITY_AND_COMPLIANCE]
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
