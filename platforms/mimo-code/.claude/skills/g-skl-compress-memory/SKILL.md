---
name: g-skl-compress-memory
description: Compress the NON-gald3r sections of AGENTS.md/CLAUDE.md (and *memory*.md) to cut token overhead, while strictly preserving the install-managed gald3r SECTION ranges, code blocks, and URLs. Dry-run by default; apply only after confirmation.
token_budget: low
skill_trust_level: core
allowed-tools: [Read, Edit, Bash]
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
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
