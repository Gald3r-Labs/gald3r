---
name: g-skl-oracle
description: >
  Execute Oracle Database queries and operations via example_app MCP tools.
  Requires Docker backend (adv tier). Supports read-only queries (oracle_query)
  and full write operations (oracle_execute) including DDL and PL/SQL blocks.
version: 1.0.0
min_tier: adv
# Conditional skill activation (T1250): this skill only makes sense when the
# Oracle MCP tools are active — it directly calls them. Optional + inert until
# the T1394 catalog-generation filter ships; omitting it = always-show.
requires_toolsets: [oracle_query, oracle_execute]
triggers:
  - "oracle query"
  - "oracle execute"
  - "run oracle"
  - "query the database"
  - "oracle sql"
  - "select from oracle"
  - "insert into oracle"
  - g-oracle
requires:
  - example_app MCP server (Docker backend)
  - oracle_query MCP tool
  - oracle_execute MCP tool
token_budget: medium
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
