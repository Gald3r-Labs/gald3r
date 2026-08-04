---
name: g-skl-platform-kiro
description: Authoritative reference for Kiro (Amazon's agentic IDE + Kiro CLI, the Q Developer CLI rebrand) customization in gald3r projects. Covers .kiro/ steering/prompts/agents/skills + settings/mcp.json, Agent Hooks (IDE file-event + CLI lifecycle), AGENTS.md instruction file, spec-driven workflow, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro/
vault_docs_url: https://kiro.dev/docs
docs_url: https://kiro.dev/docs
docs_url_secondary:
  - https://kiro.dev/docs/hooks/
  - https://kiro.dev/docs/chat/subagents/
  - https://kiro.dev/docs/skills/
  - https://kiro.dev/docs/chat/slash-commands/
  - https://kiro.dev/docs/steering/
  - https://kiro.dev/docs/mcp/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native Agent Hooks — IDE file-event triggers + CLI lifecycle (agentSpawn/userPromptSubmit/preToolUse/postToolUse/Stop)"
  rules: "✅ Steering .kiro/steering/*.md (Always/Conditional/Manual/Auto inclusion modes) + reads AGENTS.md"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .kiro/skills/ — same standard gald3r uses (Kiro 0.9)"
  commands: "✅ slash commands + local prompts .kiro/prompts/ (@name); skills/subagents auto-register"
  agents: "✅ native subagents .kiro/agents/ (IDE md+YAML; CLI JSON; parallel, own context window)"
  mcp: "✅ native — .kiro/settings/mcp.json (+ ~/.kiro, workspace precedence); subagent wildcard scoping"
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
