---
name: g-skl-platform-codex
description: Authoritative reference for OpenAI Codex (codex CLI / IDE / app) customization in gald3r projects. Covers config.toml, AGENTS.md instruction file, .agents/skills Agent Skills, .codex/agents TOML subagents, 10-event hooks (hooks.json / [hooks]), [mcp_servers.*] MCP, execpolicy/Memories rules, plugins/apps, and gald3r install verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/openai/
vault_docs_url: https://developers.openai.com/codex
docs_url: https://developers.openai.com/codex
docs_url_secondary:
  - https://developers.openai.com/codex/guides/agents-md
  - https://developers.openai.com/codex/hooks
  - https://developers.openai.com/codex/subagents
  - https://developers.openai.com/codex/skills
  - https://developers.openai.com/codex/cli/slash-commands
  - https://developers.openai.com/codex/mcp
  - https://developers.openai.com/codex/plugins
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks via hooks.json / [hooks] in config.toml (10 events: SessionStart…Stop; g-hk-*.py via python <path> command handlers)"
  rules: "✅ AGENTS.md instruction hierarchy + Memories (~/.codex/memories/) + execpolicy hard allow/block"
  skills: "✅ Agent Skills (open SKILL.md standard) in .agents/skills + $HOME/.agents/skills"
  commands: "✅ ~40 built-in slash commands; user-defined via skills (Custom Prompts deprecated)"
  agents: "✅ native subagents .codex/agents/*.toml (parallel; explicit-spawn only; /agent)"
  mcp: "✅ native — [mcp_servers.<name>] in config.toml (stdio + HTTP); codex mcp add; /mcp"
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
