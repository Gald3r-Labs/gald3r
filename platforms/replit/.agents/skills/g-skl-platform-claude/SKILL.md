---
name: g-skl-platform-claude
description: Authoritative reference for Claude Code (Anthropic) customization in gald3r projects. Covers .claude/ commands/agents/skills/hooks/rules + settings.json hooks/MCP, CLAUDE.md (imports @AGENTS.md, NOT AGENTS.md-native), plugins/Agent SDK/Routines/Channels, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/claude-code/
vault_docs_url: https://code.claude.com/docs/en/overview
docs_url: https://code.claude.com/docs/en/overview
docs_url_secondary:
  - https://code.claude.com/docs/en/hooks
  - https://code.claude.com/docs/en/sub-agents
  - https://code.claude.com/docs/en/skills
  - https://code.claude.com/docs/en/memory
  - https://code.claude.com/docs/en/mcp
  - https://code.claude.com/docs/en/plugins
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks in settings.json '\"hooks\"' (PascalCase: SessionStart/PreToolUse/PostToolUse/Stop/…; PreToolUse blocks; python <path> invocation) — NOT lowercase hooks.json"
  rules: "✅ CLAUDE.md persistent instructions + .claude/rules/*.md (paths: glob) + auto memory MEMORY.md — advisory, use PreToolUse hook for hard enforcement"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .claude/skills/<name>/SKILL.md — progressive disclosure"
  commands: "✅ native slash commands .claude/commands/*.md (legacy) OR .claude/skills/<name>/SKILL.md → /<name> (merged into Skills)"
  agents: "✅ native subagents .claude/agents/*.md (md + YAML; built-in Explore/Plan/general-purpose; ~7 parallel)"
  mcp: "✅ native — .mcp.json + settings.json mcpServers + claude mcp add (stdio/http/sse/ws)"
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
