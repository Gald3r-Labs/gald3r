---
name: g-skl-muninn
description: >
  gald3r_muninn MCP — query the local codebase knowledge graph for impact
  analysis, caller chains, dependencies, and symbol search. Clean-room
  rewrite (T1147 epic, T1153-T1158) of the GitNexus integration; auto-loaded
  by the example_app MCP server from docker/gald3r/tools/plugins/muninn/.
  Wire into g-go-code Step b0 Impact Scan before any implementation.
version: "1.0"
platforms: [cursor, claude, gemini, codex, opencode]
mcp_server: example_app
mcp_entry: ".mcp.json → gald3r_muninn entry (auto-loaded into example_app)"
related_tasks: [T1147, T1153, T1154, T1155, T1156, T1157, T1158, T921]
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
