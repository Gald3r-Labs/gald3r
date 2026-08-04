---
name: g-skl-swot-review
description: >-
  Automated SWOT analysis for the current project phase. Reviews progress,
  architectural compliance, code quality, goal alignment, and technical debt.
  Runs weekly via heartbeat or on-demand.
token_budget: low
subsystem_memberships: [BUG_AND_QUALITY]
---

## HELP CONTRACT (T442 — cross-platform, non-substitutable)

If the invoking command's arguments are EXACTLY `-h`, `--help`, or `help` (one
token, nothing else): do NOT run any operation of this skill. Respond ONLY with a
compact usage card — the command's name, its one-line purpose, each documented
argument/option on its own line (or "none"), and the path to its command file —
then STOP. Read-only: no `.gald3r/` writes, no state changes, no task/bug
creation. This block lives in the SKILL (not a rule) because skills are the
execution layer on every supported platform; rules are optional context on most.

Run: `gald3r prompt get rubric.swot`
Documentation: https://docs.gald3r.ai
