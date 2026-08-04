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

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
