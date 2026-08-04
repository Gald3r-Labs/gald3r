---
name: g-skl-json-output
description: Emit gald3r command output (status, review, backlog) as structured JSON for scripting, CI gates, dashboards, and agent-to-agent handoff. Operations SERIALIZE, SCHEMA, VALIDATE, EXPORT. Invoked by --json flag commands (T1381). Mirrors g-skl-html-output. Coordination state files stay markdown.
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
