---
name: g-skl-dependency-audit
description: Scan package files for outdated or vulnerable dependencies. Generates a severity-ranked report with CVE references and upgrade commands. Supports Python (requirements.txt/pyproject.toml), JavaScript/Node (package.json/package-lock.json), and Rust (Cargo.toml/Cargo.lock).
token_budget: medium
subsystem_memberships: [SECURITY_AND_COMPLIANCE, BUG_AND_QUALITY]
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
