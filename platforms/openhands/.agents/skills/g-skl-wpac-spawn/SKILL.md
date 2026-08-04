---
name: g-skl-wpac-spawn
description: >
  Spawn a new gald3r project from the current project. Creates the new project folder
  in the same ecosystem root, installs gald3r (matching the current project's install
  type — symlinks or fresh template), seeds it with any passed description/features/code,
  runs gald3r-setup, and immediately links both projects via WPAC topology
  (--parent | --sibling | --child).
token_budget: medium
subsystem_memberships: [WORKSPACE_COORDINATION]
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
