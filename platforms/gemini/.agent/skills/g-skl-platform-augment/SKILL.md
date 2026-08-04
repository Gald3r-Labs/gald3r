---
name: g-skl-platform-augment
description: Authoritative reference for Augment Code (Auggie CLI + VS Code + JetBrains) customization in gald3r projects. Covers .augment/ commands/agents/skills/hooks/rules + settings.json MCP, CLAUDE.md/AGENTS.md and .claude/.agents reuse, plugins/marketplace, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/augment/
vault_docs_url: https://docs.augmentcode.com
docs_url: https://docs.augmentcode.com
docs_url_secondary:
  - https://docs.augmentcode.com/cli/hooks
  - https://docs.augmentcode.com/cli/subagents
  - https://docs.augmentcode.com/cli/skills
  - https://docs.augmentcode.com/cli/custom-commands
  - https://docs.augmentcode.com/cli/rules
  - https://docs.augmentcode.com/cli/plugins
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in .augment/settings.json (PreToolUse/PostToolUse/Stop/SessionStart/SessionEnd; .ps1 supported)"
  rules: "✅ .augment/rules/*.md (always_apply/agent_requested/manual) + .augment-guidelines + reads CLAUDE.md/AGENTS.md"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .augment / .claude / .agents skills dirs"
  commands: "✅ custom slash commands .augment/commands/*.md (also .claude/.agents)"
  agents: "✅ native subagents .augment/agents/ (md + YAML; parallel)"
  mcp: "✅ native — ~/.augment/settings.json + auggie mcp add/list/remove"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
