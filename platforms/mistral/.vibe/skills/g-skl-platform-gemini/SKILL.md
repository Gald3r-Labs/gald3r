---
name: g-skl-platform-gemini
description: Authoritative reference for Gemini CLI (Google) customization in gald3r projects. Covers .gemini/ native config — settings.json hooks + MCP, TOML commands, markdown subagents, SKILL.md Agent Skills — GEMINI.md hierarchical memory (AGENTS.md-capable via context.fileName), and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/gemini/
vault_docs_url: https://github.com/google-gemini/gemini-cli
docs_url: https://github.com/google-gemini/gemini-cli
docs_url_secondary:
  - https://geminicli.com/docs/
  - https://geminicli.com/docs/hooks/
  - https://geminicli.com/docs/core/subagents/
  - https://geminicli.com/docs/cli/skills/
  - https://geminicli.com/docs/cli/custom-commands/
  - https://geminicli.com/docs/cli/gemini-md/
  - https://geminicli.com/docs/tools/mcp-server/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in .gemini/settings.json (11 events SessionStart…Notification; synchronous; added ~Jan 2026, default v0.26.0+)"
  rules: "✅ hierarchical GEMINI.md memory (@file.md imports; /memory add|show|refresh); context.fileName makes AGENTS.md a native context file"
  skills: "✅ Agent Skills (SKILL.md) in .gemini/skills/ or .agents/skills/; activate_skill; /skills list|link|enable|disable|reload"
  commands: "✅ native TOML slash commands .gemini/commands/*.toml (/name, /dir:name; prompt key + {{args}} + shell)"
  agents: "✅ native subagents .gemini/agents/*.md (md + YAML; @name; parallel; added ~Apr 2026)"
  mcp: "✅ native — mcpServers in .gemini/settings.json (@-prefixed tools; per-subagent scoping; /mcp)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
