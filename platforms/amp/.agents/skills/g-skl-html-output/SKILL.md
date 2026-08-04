---
name: g-skl-html-output
description: Render human-facing reports (status, review, backlog) as themed HTML using docs/templates/ + docs/themes/. Operations RENDER, CHOOSE_THEME, VALIDATE, EXPORT. Invoked by --html flag commands (T1318). Never used for coordination files (TASKS.md, BUGS.md, task specs) which are always markdown.
token_budget: low
subsystem_memberships: [UI_AND_OUTPUT]
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
