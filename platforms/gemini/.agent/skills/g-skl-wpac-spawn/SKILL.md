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

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
