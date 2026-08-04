---
name: g-skl-release
description: Own and manage all release data — RELEASES.md index and releases/ individual files. Operations: CREATE new release, ASSIGN tasks to a release, STATUS summary, PUBLISH ROADMAP.md, ACCELERATE target dates with cascading shift to subsequent planned releases, SYNC reconcile CHANGELOG entries against release records (C-023).
token_budget: low
subsystem_memberships: [RELEASE_AND_VERSIONING]
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
