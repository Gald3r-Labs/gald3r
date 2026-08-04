---
name: g-skl-platform-opencode
description: Authoritative reference for OpenCode (sst/opencode) customization in gald3r projects. Covers .opencode/ folder layout, opencode.json config, native skills discovery (.opencode/skills/ + .claude/skills/ + .agents/skills/), AGENTS.md/CLAUDE.md instructions, JS/TS plugin hooks, MCP, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/opencode/
vault_docs_url: https://opencode.ai/docs
docs_url: https://opencode.ai/docs
docs_url_secondary:
  - https://opencode.ai/docs/plugins/
  - https://opencode.ai/docs/agents/
  - https://opencode.ai/docs/skills/
  - https://opencode.ai/docs/commands/
  - https://opencode.ai/docs/rules/
  - https://opencode.ai/docs/mcp-servers/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks via JS/TS plugins in .opencode/plugins/ (20 events incl. tool.execute.before/after, session.created, file.edited); gald3r .ps1 need a JS/TS shim; no first-class git pre-commit event"
  rules: "✅ AGENTS.md primary (CLAUDE.md fallback; AGENTS.md wins if both local) + opencode.json instructions array; no .mdc glob-scoped rule engine"
  skills: "✅ Agent Skills (SKILL.md) loaded on-demand via native skill tool; discovered in .opencode/skills / .claude/skills / .agents/skills"
  commands: "✅ custom commands .opencode/commands/*.md ($ARGUMENTS/$1 + !bash; frontmatter description/agent/model/subtask)"
  agents: "✅ native primary agents (Build/Plan) + subagents (General/Explore/Scout) in .opencode/agents/ or opencode.json; @mention + Task tool"
  mcp: "✅ native — mcp field in opencode.json (local + remote), {env:}/{file:} substitution"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
