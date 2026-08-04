---
name: g-skl-wpac-send-to
description: >
  Send files, features, specs, ideas, or code from the current project to any
  related project in the topology (parent, sibling, or child). Handles file copying,
  INBOX notification, vault provenance logging, and optional source cleanup.
  Lighter-weight than g-skl-wpac-move (which requires topology pre-registration);
  this skill also works when the destination is a recently-spawned project.
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
