---
name: g-skl-platform-kiro-cli
description: Authoritative reference for Kiro CLI (Amazon's terminal agent, the Q Developer CLI rebrand) customization in gald3r projects. Covers .kiro/steering/ + AGENTS.md, Agent Skills (SKILL.md), JSON custom agents + subagents, lifecycle hooks, slash commands, MCP, and gald3r install verification. Distinct from Kiro IDE (g-skl-platform-kiro).
crawl_max_age_days: 7
vault_doc_path: research/platforms/kiro-cli/
vault_docs_url: https://kiro.dev/docs/cli
docs_url: https://kiro.dev/docs/cli
docs_url_secondary:
  - https://kiro.dev/docs/cli/skills/
  - https://kiro.dev/docs/cli/steering/
  - https://kiro.dev/docs/cli/custom-agents/configuration-reference/
  - https://kiro.dev/docs/cli/hooks/
  - https://kiro.dev/docs/cli/mcp/
  - https://kiro.dev/docs/cli/reference/slash-commands/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in agent JSON config (agentSpawn/userPromptSubmit/preToolUse/postToolUse/stop; STDIN-JSON; exit 2 blocks PreToolUse)"
  rules: "✅ steering files .kiro/steering/*.md (product/tech/structure auto-loaded) + reads AGENTS.md"
  skills: "✅ Agent Skills (SKILL.md) auto-loaded from .kiro/skills/ + ~/.kiro/skills/; also /skill-name"
  commands: "✅ Skills-as-slash-commands (/skill-name) + /prompts create; no standalone command-file format"
  agents: "✅ native JSON custom agents (filename=name) + subagents (isolated context, up to 4)"
  mcp: "✅ native — mcpServers JSON at .kiro/settings/mcp.json + ~/.kiro/settings/mcp.json"
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
