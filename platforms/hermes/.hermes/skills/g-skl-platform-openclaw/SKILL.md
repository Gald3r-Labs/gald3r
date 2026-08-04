---
name: g-skl-platform-openclaw
description: Authoritative reference for OpenClaw (self-hosted AI agent gateway — Discord/Telegram/Slack/WhatsApp) customization in gald3r projects. Covers the AGENTS.md + SOUL.md instruction-file convention, folder-per-skill SKILL.md (which double as slash commands), TypeScript HOOK.md hooks, sessions_spawn sub-agents, native MCP client+server, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/openclaw/
vault_docs_url: https://docs.openclaw.ai
docs_url: https://docs.openclaw.ai
docs_url_secondary:
  - https://docs.openclaw.ai/concepts/agent-workspace
  - https://docs.openclaw.ai/tools/slash-commands
  - https://docs.openclaw.ai/tools/skills
  - https://docs.openclaw.ai/tools/subagents
  - https://docs.openclaw.ai/automation/hooks
  - https://docs.openclaw.ai/cli/mcp
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native event-driven hooks (HOOK.md + handler.ts, openclaw.json) — TypeScript handlers, OpenClaw event taxonomy; gald3r .ps1 NOT drop-in (rewrite to handler.ts)"
  rules: "✅ AGENTS.md (operating rules) + SOUL.md (hard 'never do X') + MEMORY.md injected every session; prose-only, no .mdc typed rules"
  skills: "✅ Agent Skills (folder-per-skill SKILL.md) precedence-loaded; install to ~/.openclaw/workspace/skills/; skills double as slash commands"
  commands: "✅ user-invocable skills → /skill <name>; direct command registration; native Discord/Telegram registration (~v2026.2.23)"
  agents: "✅ per-persona agents via bindings + runtime sub-agents via sessions_spawn tool (maxSpawnDepth default 1; /subagents is inspect-only)"
  mcp: "✅ native client + server — mcp.servers in openclaw.json (openclaw mcp add/set/configure); stdio/HTTP-SSE/streamable-http; openclaw mcp serve"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
