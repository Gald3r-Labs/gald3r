---
name: g-skl-platform-antigravity
description: Authoritative reference for Google Antigravity (agent-first IDE + CLI + SDK) customization in gald3r projects. Covers AGENTS.md/GEMINI.md instruction files, .agents/ rules/skills/hooks + .antigravity/mcp.json, Workflows (slash commands), dynamic subagents, lifecycle hooks, Scheduled Tasks, and gald3r install verification. Post-2.0-relaunch (I/O 2026); skill path + hook payload pin via install test.
crawl_max_age_days: 7
vault_doc_path: research/platforms/antigravity/
vault_docs_url: https://antigravity.google/docs/home
docs_url: https://antigravity.google/docs/home
docs_url_secondary:
  - https://antigravity.google/docs/hooks
  - https://antigravity.google/docs/subagents
  - https://antigravity.google/docs/skills
  - https://antigravity.google/docs/rules-workflows
  - https://antigravity.google/docs/mcp
  - https://antigravity.google/docs/command
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in hooks.json (before/after_tool_call, before/after_model_call, on_loop_stop, on_error; stdin/stdout JSON; shell scripts)"
  rules: "✅ Markdown rules (Manual/Always On/Model Decision/Glob) in .agents/rules + GEMINI.md; reads AGENTS.md"
  skills: "✅ Agent Skills (Anthropic SKILL.md) in .agents/.antigravity/.agent skills dirs (path pin via install test)"
  commands: "✅ Workflows (saved-prompt slash commands) /workflow-name; ~/.gemini/antigravity/global_workflows/"
  agents: "✅ native dynamic subagents (Orchestrator-spawned); ⚠️ no file-based g-agnt-*.md discovery"
  mcp: "✅ native — .antigravity/mcp.json or ~/.gemini/antigravity/mcp_config.json + MCP Store GUI"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
