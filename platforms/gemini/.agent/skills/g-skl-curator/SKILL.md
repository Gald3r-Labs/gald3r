---
name: g-skl-curator
description: >
  Autonomous skill library curator — grades every SKILL.md against a structured rubric
  (recency, clarity, scope overlap, token efficiency, last-invoked rate), proposes
  consolidations and archive-candidate tags for low-scoring or overlapping skills, and
  writes a structured audit log. Never deletes — only proposes. Safe for unattended
  scheduled runs.
type: skill
tags: [skill-management, audit, rubric, consolidation, scheduling]
safety: file-read + file-write only; no Shell, no web fetch, no destructive ops
triggers:
  - "@g-curator"
  - "curate skills"
  - "audit skill library"
  - "grade skills"
  - "skill rubric"
  - "consolidate skills"
  - "prune skills"
token_budget: high
subsystem_memberships: [AGENT_ORCHESTRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
