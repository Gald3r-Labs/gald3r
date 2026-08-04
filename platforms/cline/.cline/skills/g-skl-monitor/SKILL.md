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
