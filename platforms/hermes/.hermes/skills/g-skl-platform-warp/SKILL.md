---
name: g-skl-platform-warp
description: Authoritative reference for Warp (AI terminal + Oz agent platform) customization in gald3r projects. Covers AGENTS.md/WARP.md project rules, Agent Skills (SKILL.md) cross-vendor discovery, Agent Profiles + Oz subagent orchestration, Warp Drive Workflows + MCP, the absent hook surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/warp/
vault_docs_url: https://docs.warp.dev
docs_url: https://docs.warp.dev
docs_url_secondary:
  - https://docs.warp.dev/agent-platform/capabilities/rules/
  - https://docs.warp.dev/agent-platform/capabilities/skills/
  - https://docs.warp.dev/agent-platform/capabilities/agent-profiles-permissions/
  - https://docs.warp.dev/agent-platform/capabilities/slash-commands
  - https://docs.warp.dev/agent-platform/capabilities/mcp/
  - https://github.com/warpdotdev/warp/issues/7834
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ no lifecycle-hook system; agent lifecycle hooks are open RFCs (warpdotdev/warp #7834, #6857). Oz Cloud Triggers fire agent runs, not local .ps1 hooks"
  rules: "✅ native Global + Project Rules (AGENTS.md/WARP.md, ALL-CAPS, WARP.md wins if both) + Agent Memory (cross-harness); single-file md, no .mdc/glob"
  skills: "✅ native Agent Skills (SKILL.md); discovers .agents/.warp/.claude/.cursor/… skills dirs (cross-vendor) — .claude/skills/ reusable"
  commands: "⚠️ built-in slash commands + cloud Warp Drive Workflows; NO user-defined custom slash commands (open RFC #6857); not installed from repo commands/"
  agents: "✅ Agent Profiles & permissions + Oz subagent orchestration (multi-harness: Warp Agent / Claude Code / Codex)"
  mcp: "✅ native — Settings > Agents > MCP servers (CLI + HTTP/SSE), per-profile access, shared local + Oz"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
