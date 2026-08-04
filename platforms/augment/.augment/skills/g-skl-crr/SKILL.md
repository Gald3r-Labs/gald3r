---
name: g-skl-crr
description: Clean-Room Rewrite pipeline. Orchestrates 4 phases via independent background subagents — capture a source repo as a whole-system, consumer-neutral functional spec centralized in the shared vault (research/CRR_FunctionalSpecs/), write all findings to IDEA_BOARD (mandatory), triage tasks, and produce a gald3r-native clean-room implementation spec.
triggers:
  - "@g-crr"
  - "clean room rewrite"
  - "clean-room rewrite"
  - "crr"
  - "harvest and spec"
token_budget: high
subsystem_memberships: [VAULT_AND_RESEARCH, AGENT_ORCHESTRATION]
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
