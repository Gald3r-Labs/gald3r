---
name: g-skl-platform-cursor
description: Authoritative reference for Cursor IDE customization in gald3r projects. Covers .cursor/ folder layout, all supported primitives (rules/skills/agents/commands/hooks/MCP), AGENTS.md instruction file, .claude/.codex/.agents cross-tool reuse, parity tiers, and install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/cursor/
vault_docs_url: https://cursor.com/docs
docs_url: https://cursor.com/docs
docs_url_secondary:
  - https://cursor.com/docs/hooks
  - https://cursor.com/docs/subagents.md
  - https://cursor.com/help/customization/skills
  - https://cursor.com/changelog/1-6
  - https://cursor.com/docs/context/rules
  - https://cursor.com/docs/context/mcp
last_doc_scan: 2026-06-02
reference_implementation: true
capability_status:
  hooks: "✅ native lifecycle hooks in .cursor/hooks.json (sessionStart/stop/preToolUse/beforeShellExecution + large event surface; stdio JSON)"
  rules: "✅ .cursor/rules/*.mdc (alwaysApply/globs/description; 4 application types) + AGENTS.md + User/Team rules"
  skills: "✅ Agent Skills (SKILL.md) folder-per-skill in .cursor/skills + .agents/skills (auto-load)"
  commands: "✅ custom slash commands .cursor/commands/*.md (Cursor 1.6)"
  agents: "✅ native subagents .cursor/agents/ (md + YAML; parallel); also reads .claude/.codex agents"
  mcp: "✅ native — .cursor/mcp.json / ~/.cursor/mcp.json / Settings (stdio + SSE + HTTP; OAuth)"
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
