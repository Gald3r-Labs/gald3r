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
