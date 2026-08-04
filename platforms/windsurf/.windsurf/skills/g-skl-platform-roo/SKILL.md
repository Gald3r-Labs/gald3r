---
name: g-skl-platform-roo
description: Authoritative reference for Roo Code (VS Code extension; formerly Roo Cline) customization in gald3r projects. Covers .roo/rules/, custom modes (.roomodes), slash commands, Agent Skills (.roo/skills + .agents/skills), MCP, AGENTS.md, and gald3r install verification. NOTE — Roo Code was discontinued 2026-05-15.
crawl_max_age_days: 14
vault_doc_path: research/platforms/roo/
vault_docs_url: https://docs.roocode.com
docs_url: https://docs.roocode.com
docs_url_secondary:
  - https://docs.roocode.com/features/slash-commands
  - https://docs.roocode.com/features/custom-instructions
  - https://docs.roocode.com/features/custom-modes
  - https://docs.roocode.com/features/skills
  - https://docs.roocode.com/features/mcp/using-mcp-in-roo
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ none — Roo has no native lifecycle hook system; gald3r g-hk-*.py run manually / via git core.hooksPath / VS Code tasks"
  rules: "✅ .roo/rules/ + .roo/rules-{slug}/ (recursive, alphabetical) + legacy .roorules/.clinerules fallback; workspace wins over global"
  skills: "✅ Agent Skills (SKILL.md) in .roo/skills/ + .roo/skills-{mode}/ + .agents/skills/ — auto-discovered, progressive disclosure"
  commands: "✅ slash commands .roo/commands/*.md (filename=command; run_slash_command tool; optional mode frontmatter)"
  agents: "✅ modes are the agent analog — built-in + custom modes in .roomodes (slug/roleDefinition/groups/whenToUse; Orchestrator/boomerang)"
  mcp: "✅ native — project .roo/mcp.json (precedence over global) + use_mcp_tool/access_mcp_resource; STDIO + SSE/HTTP"
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
