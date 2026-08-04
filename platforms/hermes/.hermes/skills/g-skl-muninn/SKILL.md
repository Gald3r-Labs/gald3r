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

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
