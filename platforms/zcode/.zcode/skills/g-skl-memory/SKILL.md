---
name: g-skl-memory
description: >
  Capture structured insights, session summaries, and search cross-session agent memory
  via example_app MCP tools. Dual-mode: degrades to file-based g-skl-learn when
  backend is unavailable. Full semantic search requires Docker backend (adv tier).
version: 1.0.0
min_tier: adv
triggers:
  - "capture insight"
  - "remember this"
  - "store memory"
  - "search memory"
  - "what did we decide"
  - "cross-session memory"
  - "capture session"
  - "memory search"
  - g-memory
requires:
  - example_app MCP server (Docker backend) for full semantic search
  - memory_capture_insight MCP tool
  - memory_capture_session MCP tool
  - memory_search MCP tool
  - memory_search_combined MCP tool
fallback:
  - g-skl-learn (file-based insight capture when backend unavailable)
token_budget: very_high
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
