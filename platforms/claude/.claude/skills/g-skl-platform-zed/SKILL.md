---
name: g-skl-platform-zed
description: Authoritative reference for Zed (agent panel + ACP host) customization in gald3r projects. Covers the .rules-first project-instructions precedence list, native AGENTS.md (project + personal ~/.config/zed/AGENTS.md), native Agent Skills (.agents/skills/, shared with Codex/Amp/Deep Code), native MCP (context_servers), External Agents hosted via the Agent Client Protocol (agent_servers), the absent hooks/commands surfaces, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/zed/
vault_docs_url: https://zed.dev/docs/ai/external-agents
docs_url: https://zed.dev/docs/ai/external-agents
docs_url_secondary:
  - https://zed.dev/docs/ai/agent-settings
  - https://zed.dev/docs/ai/instructions
  - https://zed.dev/docs/ai/skills
  - https://zed.dev/docs/ai/mcp
  - https://zed.dev/docs/ai/agent-panel
  - https://agents.md/
last_doc_scan: 2026-07-03
capability_status:
  hooks: "❌ no published event taxonomy/schema for hand-authored hooks (Tool Permissions/Agent Sandboxing are access-control, not an event bus)"
  rules: "✅ native AGENTS.md (project root + personal ~/.config/zed/AGENTS.md); .rules legacy filename outranks AGENTS.md if both exist"
  skills: "✅ native Agent Skills (SKILL.md) in .agents/skills/, name+description frontmatter, shared convention with Codex/Amp/Deep Code"
  commands: "❌ no dedicated user-authored slash-command file format; only built-in /compact documented — Skills fill the invocation role"
  agents: "❌ no project-scoped agent roster; Zed's own agent is Profile/UI-configured, third parties attach via ACP agent_servers"
  mcp: "✅ native MCP via context_servers in .zed/settings.json (local command/args/env or remote url/headers); forwarded to ACP External Agents too"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
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
