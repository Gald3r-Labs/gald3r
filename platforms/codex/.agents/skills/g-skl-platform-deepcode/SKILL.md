---
name: g-skl-platform-deepcode
description: Authoritative reference for Deep Code CLI (lessweb/deepcode-cli, a third-party community terminal AI coding assistant for the deepseek-v4 model family) customization in gald3r projects. Covers AGENTS.md, .agents/skills + .deepcode/skills Agent Skills, MCP inside .deepcode/settings.json, the fixed built-in slash-command set (no user commands), the absent hook/subagent surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/deepcode/
vault_docs_url: https://github.com/lessweb/deepcode-cli
docs_url: https://github.com/lessweb/deepcode-cli
docs_url_secondary:
  - https://raw.githubusercontent.com/lessweb/deepcode-cli/main/docs/mcp.md
  - https://raw.githubusercontent.com/lessweb/deepcode-cli/main/docs/configuration.md
  - https://api-docs.deepseek.com/quick_start/agent_integrations/deepcode
last_doc_scan: 2026-07-18
capability_status:
  hooks: "❌ no lifecycle-hook framework; only a post-turn-only notify shell script in settings.json (cannot block tool calls)"
  rules: "✅ native — AGENTS.md, scaffolded via /init, the single instruction/rules surface (no .deepcode/rules/, no memory dir)"
  skills: "✅ native — Agent Skills (SKILL.md) discovered from .deepcode/skills/ (native) and .agents/skills/ (interop); gald3r targets .agents/skills/"
  commands: "⚠️ fixed built-in slash set only (/new /resume /continue /model /raw /init /skills /mcp /undo /exit); no user-defined command directory"
  agents: "❌ single AI assistant; no sub-agents, agent roles, or distinct agent modes documented"
  mcp: "✅ native — mcpServers object inside settings.json (no standalone .mcp.json); inspect via /mcp"
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
