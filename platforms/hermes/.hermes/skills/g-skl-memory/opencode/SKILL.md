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

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
