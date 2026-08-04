---
name: g-skl-tasks
maturity: production
description: Own and manage all task data — TASKS.md index, tasks/ individual files, status transitions, sync validation, complexity scoring, and sprint planning. Single source of truth for everything task-related.
token_budget: low
subsystem_memberships: [TASK_MANAGEMENT]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Run: `gald3r task add`
Documentation: https://docs.gald3r.ai
