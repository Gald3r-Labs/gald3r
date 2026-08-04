---
name: g-skl-platform-hermes
description: Authoritative reference for Hermes Agent (Nous Research — self-improving CLI + Telegram/Discord/Slack gateway) customization in gald3r projects. Covers ~/.hermes/ config (config.yaml/.env), AGENTS.md-native instruction loading (auto-injected with SOUL.md/CLAUDE.md/.cursorrules), agentskills.io SKILL.md skills (the gald3r distribution opportunity), delegate_task subagents, MCP (mcp_servers), the native config.yaml hooks: surface (17+ events, pre_tool_call blocking), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/hermes/
vault_docs_url: https://hermes-agent.nousresearch.com/docs
docs_url: https://hermes-agent.nousresearch.com/docs
docs_url_secondary:
  - https://hermes-agent.nousresearch.com/docs/user-guide/configuration
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
  - https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
  - https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md
  - https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
  - https://github.com/NousResearch/hermes-agent
last_doc_scan: 2026-06-20
capability_status:
  hooks: "✅ native — config.yaml hooks: shell-hook block (JSON-stdin, 17+ events incl. on_session_start/pre_tool_call); pre_tool_call blocks via {action:block}; non-blocking on hook error (verify firing)"
  rules: "✅ AGENTS.md + SOUL.md auto-injected into system prompt + ~/.hermes/memories/MEMORY.md + USER.md — advisory, hardenable via a pre_tool_call hook"
  skills: "✅ agentskills.io SKILL.md folder-per-skill in ~/.hermes/skills/<cat>/<name>/ — gald3r g-skl-* directly portable (only name+description required); distribute via taps"
  commands: "⚠️ partial — built-in slash commands + every skill is /skill-name; NO user command-file primitive"
  agents: "✅ native subagents via delegate_task (goal or batch tasks:[...]; delegation.max_concurrent_children/max_spawn_depth); no declared agent file → deliver g-agnt-* as Skills"
  mcp: "✅ native — mcp_servers: in ~/.hermes/config.yaml (stdio command/args/env OR HTTP url/headers; .[mcp] extra)"
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
