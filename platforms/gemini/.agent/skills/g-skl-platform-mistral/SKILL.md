---
name: g-skl-platform-mistral
description: Authoritative reference for Mistral Vibe CLI (mistral-vibe) coding agent customization in gald3r projects. Covers the .vibe/ config tree (TOML), AGENTS.md instructions, native Agent-Skills SKILL.md, native custom agents + subagents, MCP servers, experimental hooks, and honest capability boundaries.
crawl_max_age_days: 14
vault_doc_path: research/platforms/mistral/
vault_docs_url: https://docs.mistral.ai/mistral-vibe/terminal
docs_url: https://docs.mistral.ai/mistral-vibe/terminal
docs_url_secondary:
  - https://docs.mistral.ai/vibe/code/cli/configuration
  - https://docs.mistral.ai/vibe/code/cli/skills
  - https://docs.mistral.ai/vibe/code/cli/agents
  - https://docs.mistral.ai/vibe/code/cli/mcp-servers
  - https://github.com/mistralai/mistral-vibe
last_doc_scan: 2026-06-02
capability_status:
  hooks: "⚠️ experimental post-agent-turn lifecycle only (v2.9.0); no schema/file location; no pre-tool/session-start/pre-commit — cannot wire gald3r hooks"
  rules: "⚠️ AGENTS.md layered injection (+ optional custom system prompt via prompts/<id>.md); no scoped .mdc/glob rule system"
  skills: "✅ native Agent Skills (agentskills.io SKILL.md) in ~/.vibe/skills, ./.vibe/skills, ./.agents/skills + skill_paths"
  commands: "⚠️ slash commands only via skills (user-invocable: true → /skill-name); no command-file directory"
  agents: "✅ native custom agents + subagents (.vibe/agents/*.toml; vibe --agent; agent_type=subagent)"
  mcp: "✅ native — config.toml [[mcp_servers]] (http/streamable-http/stdio); no OAuth yet"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
