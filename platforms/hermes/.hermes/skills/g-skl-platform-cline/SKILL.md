---
name: g-skl-platform-cline
description: Authoritative reference for Cline (VS Code / JetBrains extension + CLI + SDK) customization in gald3r projects. Covers .clinerules rules + workflows-as-slash-commands, .cline/skills SKILL.md, lifecycle hooks (macOS/Linux only), SDK subagents/teams, MCP marketplace, AGENTS.md (not CLAUDE.md), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/cline/
vault_docs_url: https://docs.cline.bot
docs_url: https://docs.cline.bot
docs_url_secondary:
  - https://docs.cline.bot/features/slash-commands/workflows
  - https://docs.cline.bot/customization/cline-rules
  - https://docs.cline.bot/sdk/guides/multi-agent-teams
  - https://docs.cline.bot/features/skills
  - https://cline.bot/blog/cline-v3-36-hooks
  - https://docs.cline.bot/mcp/mcp-overview
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks (PreToolUse/PostToolUse/UserPromptSubmit/TaskStart/TaskResume/TaskCancel) — executable scripts, JSON stdin/stdout — BUT macOS/Linux only (no Windows yet)"
  rules: "✅ .clinerules file or folder (all .md/.txt combined); toggleable per-file (v3.13); YAML frontmatter path-scoping; reads AGENTS.md (NOT CLAUDE.md)"
  skills: "✅ Agent Skills SKILL.md (3-tier progressive disclosure) in .cline/skills/ or ~/.cline/skills/; use_skill tool"
  commands: "✅ Workflows = custom slash commands in .clinerules/workflows/*.md (/<filename>) + built-ins"
  agents: "✅ native subagents + multi-agent teams via the Cline SDK / CLI runtime (own model/tools/prompt, shared task board) — not the bare IDE chat"
  mcp: "✅ native — STDIO + Remote HTTP/SSE; MCP Marketplace; cline_mcp_settings.json (IDE) / ~/.cline/mcp.json (CLI)"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
