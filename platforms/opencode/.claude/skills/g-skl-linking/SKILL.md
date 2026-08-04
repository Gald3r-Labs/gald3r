---
name: g-skl-linking
description: >
  Unified linking file-mirror (D7 / T1610). Pulls the server-owned world_tree
  linking registry (parent/child/sibling edges + project_type/skills, keyed by
  project UUID — T1625) and writes the human-readable local mirror under
  .gald3r/linking/. Online the mirror reconciles against the registry; offline
  the local mirror is authoritative and reconciles on reconnect. Reconcile is
  non-destructive: conflicting edges open a review item, never overwrite.
token_budget: low
subsystem_memberships: [WORKSPACE_COORDINATION, PROJECT_IDENTITY_SETUP]
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
