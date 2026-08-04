---
name: g-skl-platform-replit
description: Authoritative reference for Replit Agent (cloud IDE) customization in gald3r projects. Covers replit.md Agent instructions, Agent Skills in /.agents/skills, Plan/Build modes + effort tiers, MCP (client + hosted server), and cloud-IDE constraints (no hooks, no commands).
crawl_max_age_days: 14
vault_doc_path: research/platforms/replit/
vault_docs_url: https://docs.replit.com/replitai/replit-dot-md
docs_url: https://docs.replit.com/replitai/replit-dot-md
docs_url_secondary:
  - https://docs.replit.com/replitai/skills
  - https://docs.replit.com/replitai/agent
  - https://docs.replit.com/learn/model-context-protocol
  - https://docs.replit.com/references/agent/task-lifecycle
  - https://blog.replit.com/introducing-workflows
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ no native lifecycle hooks; task lifecycle is observational; no hook surface for g-hk-*.py to wire into"
  rules: "✅ replit.md single instruction/memory blob (auto-read, self-updated); no .mdc / no glob scoping"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in /.agents/skills — lazy-loaded, Project/User/Enterprise scopes"
  commands: "❌ no user-authored slash-command registry; Workflows are shell-command runners, not agent commands"
  agents: "⚠️ native Plan/Build modes + effort tiers; no user-definable custom-agent file format"
  mcp: "✅ native — Agent is an MCP client (cloud UI); Replit also ships a hosted MCP server"
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
