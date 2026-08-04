---
name: g-skl-platform-windsurf
description: Authoritative reference for Windsurf (Cascade IDE, by Cognition / Windsurf) customization in gald3r projects. Covers .windsurf/ rules/workflows/skills/hooks + ~/.codeium/windsurf MCP, AGENTS.md/.windsurfrules instruction files, .claude/.agents skill reuse, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
vault_docs_url: https://docs.windsurf.com
docs_url: https://docs.windsurf.com
docs_url_secondary:
  - https://docs.windsurf.com/windsurf/cascade/skills
  - https://docs.windsurf.com/windsurf/cascade/hooks
  - https://docs.windsurf.com/windsurf/cascade/workflows
  - https://docs.windsurf.com/windsurf/cascade/memories
  - https://docs.windsurf.com/windsurf/cascade/mcp
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native Cascade Hooks (hooks.json; 12 events incl. pre_user_prompt/pre_write_code/post_setup_worktree; powershell key supported; pre-hooks block on exit 2)"
  rules: "✅ .windsurf/rules/*.md (always_on/model_decision/glob/manual, 12,000-char) + AGENTS.md + legacy .windsurfrules + global_rules.md"
  skills: "✅ Cascade Skills (SKILL.md) in .windsurf / .claude / .agents skills dirs; progressive disclosure"
  commands: "✅ Workflows (.windsurf/workflows/*.md, /[name] slash, manual-only, 12,000-char)"
  agents: "⚠️ Cascade modes + Plan Mode + planning agent + Wave 13 parallel agents (≤5); NO named sub-agent config file"
  mcp: "✅ native — ~/.codeium/windsurf/mcp_config.json + Marketplace; stdio + Streamable HTTP; 100-tool cap"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
