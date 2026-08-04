---
name: g-agnt-pcac-coordinator
description: >
  Cross-project coordination agent. Use when orchestrating parent/child/sibling
  project relationships — reading topology, triaging INBOX items, broadcasting
  tasks to children, sending requests to parent, syncing with siblings, or
  moving files/folders between projects. Activate on: "coordinate projects",
  "check inbox", "broadcast to children", "send to parent", "sync with siblings",
  "multi-project status", "move to another project", "cross-project".
model: inherit
tools: Read, Write, Edit, Glob, Grep, Bash
subsystem_memberships: [WORKSPACE_COORDINATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
