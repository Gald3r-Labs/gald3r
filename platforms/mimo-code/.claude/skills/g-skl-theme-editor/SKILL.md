---
name: g-skl-theme-editor
description: Create and edit gald3r HTML themes against docs/themes/theme-schema.json. Visual editor (live preview, per-token color pickers, import/export :root blocks) ships in example_desktop; this skill is the spec + a file-first fallback that works without the app. Invoked by g-theme-edit.
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
