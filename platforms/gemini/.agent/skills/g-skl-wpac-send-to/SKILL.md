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

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
