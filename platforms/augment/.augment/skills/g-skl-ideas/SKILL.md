---
name: g-skl-ideas
description: Own and manage IDEA_BOARD.md — capture ideas instantly, review the board, promote to tasks, and run proactive codebase scans for improvement opportunities.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP, VAULT_AND_RESEARCH]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Run: `gald3r validate`
Documentation: https://docs.gald3r.ai
