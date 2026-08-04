---
name: g-skl-platform-qwen
description: Authoritative reference for Qwen Code (Alibaba CLI coding agent, a Gemini CLI fork) customization in gald3r projects. Covers .qwen/settings.json hooks+MCP, QWEN.md context (NOT AGENTS.md by default), custom commands, subagents, Agent Skills (SKILL.md), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/qwen/
vault_docs_url: https://qwenlm.github.io/qwen-code-docs/
docs_url: https://qwenlm.github.io/qwen-code-docs/
docs_url_secondary:
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/sub-agents/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/
  - https://qwenlm.github.io/qwen-code-docs/en/core/memport/
  - https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native 14-event lifecycle hooks in .qwen/settings.json (command incl. python <path> / http; matcher, timeouts)"
  rules: "✅ hierarchical QWEN.md context/memory with @file.md imports (/memory show|refresh)"
  skills: "✅ Agent Skills (SKILL.md) in .qwen/skills/, model-invoked; GA 2026-02-09"
  commands: "✅ native slash commands .qwen/commands/ (Markdown+YAML; TOML back-compat; /dir:name)"
  agents: "✅ native subagents .qwen/agents/ (md + YAML; /agents, approvalMode, tools allowlist)"
  mcp: "✅ first-class mcpServers in .qwen/settings.json (stdio/SSE/HTTP, OAuth) + qwen mcp add + /mcp"
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
