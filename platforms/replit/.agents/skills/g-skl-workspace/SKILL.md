---
name: g-skl-workspace
description: Workspace-Control Mode skill. Reads .gald3r/linking/workspace_manifest.yaml as the canonical registry and provides STATUS, VALIDATE, MEMBER LIST, SPAWN, ADOPT, EXPORT/SYNC dry-run planning, and member `.gald3r/` marker bootstrap/remediate/validate operations for manifest-declared repositories.
operations: [STATUS, VALIDATE, MEMBER_LIST, INIT_PLAN, INIT_APPLY, MEMBER_ADD_PLAN, MEMBER_ADD_APPLY, MEMBER_REMOVE_PLAN, MEMBER_REMOVE_APPLY, SPAWN_PLAN, SPAWN_APPLY, EXPORT_PLAN, SYNC_PLAN, PARSE_MANIFEST, ENFORCE_SCOPE, ADOPT_DISCOVER, ADOPT_DRY_RUN, ADOPT_APPLY, MEMBER_MARKER_BOOTSTRAP, MEMBER_MARKER_REMEDIATE, MEMBER_MARKER_VALIDATE, PROMOTE_PLAN, PROMOTE_APPLY]
min_tier: slim
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
