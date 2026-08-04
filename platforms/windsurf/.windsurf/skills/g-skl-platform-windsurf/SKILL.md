---
name: g-skl-platform-windsurf
description: Authoritative reference for Devin Desktop (formerly Windsurf — Cognition renamed the product 2026-06-02 after acquiring it; Cascade IDE) customization in gald3r projects. Covers .windsurf/ rules/workflows/skills/hooks + ~/.codeium/windsurf MCP, AGENTS.md/.windsurfrules instruction files, .claude/.agents skill reuse, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/windsurf/
vault_docs_url: https://docs.devin.ai/desktop/getting-started
docs_url: https://docs.devin.ai/desktop/getting-started
docs_url_secondary:
  - https://docs.devin.ai/desktop/cascade/skills
  - https://docs.devin.ai/desktop/cascade/hooks
  - https://docs.devin.ai/desktop/cascade/workflows
  - https://docs.devin.ai/desktop/cascade/memories
  - https://docs.devin.ai/desktop/cascade/mcp
  - https://docs.devin.ai/desktop/devin-desktop-faq
last_doc_scan: 2026-07-18
capability_status:
  hooks: "✅ native Cascade Hooks (hooks.json; 12 events incl. pre_user_prompt/pre_write_code/post_setup_worktree; powershell key supported; pre-hooks block on exit 2)"
  rules: "✅ .windsurf/rules/*.md (always_on/model_decision/glob/manual, 12,000-char) + AGENTS.md + legacy .windsurfrules + global_rules.md"
  skills: "✅ Cascade Skills (SKILL.md) in .windsurf / .claude / .agents skills dirs; progressive disclosure"
  commands: "✅ Workflows (.windsurf/workflows/*.md, /[name] slash, manual-only, 12,000-char)"
  agents: "⚠️ Cascade modes + Plan Mode + planning agent + Wave 13 parallel agents (≤5); NO named sub-agent config file"
  mcp: "✅ native — ~/.codeium/windsurf/mcp_config.json (Devin Desktop path unchanged post-rename, re-verified 2026-07-18) + Marketplace; stdio + Streamable HTTP; 100-tool cap"
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
