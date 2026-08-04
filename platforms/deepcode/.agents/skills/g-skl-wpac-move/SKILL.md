---
name: g-skl-wpac-move
description: >
  Transfer files or folders from this project to another project in the topology
  (parent, child, or sibling) with provenance tracking, safety gates, and
  vault log entries in both projects. Use when migrating subsystems between
  repos, promoting assets to the canonical template, or extracting code that
  grew in one project but belongs in another.
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
