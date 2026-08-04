---
name: g-skl-platform-openhands
description: Authoritative reference for OpenHands (All Hands AI, formerly OpenDevin) AI agent customization in gald3r projects. Covers AGENTS.md context, .agents/skills + .agents/agents File-Based Agents, .openhands/hooks.json lifecycle hooks, config.toml MCP, Plugins bundle, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/openhands/
vault_docs_url: https://docs.openhands.dev
docs_url: https://docs.openhands.dev
docs_url_secondary:
  - https://docs.openhands.dev/sdk/guides/plugins
  - https://docs.openhands.dev/sdk/guides/skill.md
  - https://docs.openhands.dev/sdk/guides/agent-file-based.md
  - https://docs.openhands.dev/openhands/usage/customization/hooks
  - https://docs.openhands.dev/openhands/usage/settings/mcp-settings
  - https://docs.openhands.dev/overview/skills/repo.md
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in .openhands/hooks.json (PreToolUse/PostToolUse/UserPromptSubmit/Stop/SessionStart/SessionEnd; stdin JSON; deny decisions)"
  rules: "✅ AGENTS.md always-on (injected at conversation start) + General Skills; CLAUDE.md/GEMINI.md variants"
  skills: "✅ Agent Skills (extended AgentSkills SKILL.md) in .agents/skills (> deprecated .openhands/skills/microagents); .claude/skills accepted"
  commands: "✅ Plugin commands/*.md + Agent Skills as /skill-name (no standalone per-repo command file)"
  agents: "✅ File-Based Agents .agents/agents/*.md (md + YAML) + DelegateTool sub-agents; advanced via SDK register_agent()"
  mcp: "✅ native — config.toml [mcp] stdio/SSE/SHTTP + Settings UI + plugin .mcp.json"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
