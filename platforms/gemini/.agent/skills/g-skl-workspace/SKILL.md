---
name: g-skl-workspace
description: Workspace-Control Mode skill. Reads .gald3r/linking/workspace_manifest.yaml as the canonical registry and provides STATUS, VALIDATE, MEMBER LIST, SPAWN, ADOPT, EXPORT/SYNC dry-run planning, and member `.gald3r/` marker bootstrap/remediate/validate operations for manifest-declared repositories.
operations: [STATUS, VALIDATE, MEMBER_LIST, INIT_PLAN, INIT_APPLY, MEMBER_ADD_PLAN, MEMBER_ADD_APPLY, MEMBER_REMOVE_PLAN, MEMBER_REMOVE_APPLY, SPAWN_PLAN, SPAWN_APPLY, EXPORT_PLAN, SYNC_PLAN, PARSE_MANIFEST, ENFORCE_SCOPE, ADOPT_DISCOVER, ADOPT_DRY_RUN, ADOPT_APPLY, MEMBER_MARKER_BOOTSTRAP, MEMBER_MARKER_REMEDIATE, MEMBER_MARKER_VALIDATE, PROMOTE_PLAN, PROMOTE_APPLY]
min_tier: slim
token_budget: medium
subsystem_memberships: [WORKSPACE_COORDINATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
