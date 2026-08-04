---
name: g-skl-graphify
description: >
  Build and query a code graph representation of the codebase for 71x fewer tokens
  on architecture questions. Wire into g-go-code context-prep phase: query the graph
  before editing files instead of grepping linearly. Use when answering "what calls X?",
  "what does X depend on?", "what breaks if I change Y?", or any architecture question.
version: "1.0"
platforms: [cursor, claude, gemini, codex, opencode]
requires: [graphify-cli OR gitNexus]
token_budget: medium
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
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
