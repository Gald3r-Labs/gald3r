---
name: g-skl-monitor
description: >
  Manage scheduled content monitors for YouTube playlists, docs sites, GitHub repos,
  and URLs via example_app MCP tools. Requires Docker backend (adv tier).
  Monitors trigger automatic re-ingestion when new content is detected.
version: 1.0.0
min_tier: adv
triggers:
  - "add monitor"
  - "content monitor"
  - "watch playlist"
  - "monitor docs"
  - "monitor repo"
  - "monitor url"
  - "check monitors"
  - "list monitors"
  - "remove monitor"
  - g-monitor
requires:
  - example_app MCP server (Docker backend)
  - monitor_add MCP tool
  - monitor_list MCP tool
  - monitor_check MCP tool
  - monitor_remove MCP tool
token_budget: medium
subsystem_memberships: [VAULT_AND_RESEARCH]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
