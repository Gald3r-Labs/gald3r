---
name: g-skl-platform-zcode
description: Authoritative reference for ZCode (Z.ai / Zhipu, GLM-5.2 Agentic Development Environment) customization in gald3r projects. Covers the two-scope AGENTS.md convention (global-then-workspace, no imports/hierarchy), native Agent Skills (SKILL.md), native slash commands, Beta global-only subagents, native MCP, the absent hooks surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/zcode/
vault_docs_url: https://zcode.z.ai/en/docs/welcome
docs_url: https://zcode.z.ai/en/docs/agents
docs_url_secondary:
  - https://zcode.z.ai/en/docs/mcp-services
  - https://zcode.z.ai/en/docs/subagents
  - https://zcode.z.ai/en/docs/skill
  - https://zcode.z.ai/en/docs/commands
  - https://zcode.z.ai/en/docs/plugin
last_doc_scan: 2026-07-03
capability_status:
  hooks: "❌ no published event taxonomy/schema for hand-authored hooks (plugin-bundled hooks only, undocumented)"
  rules: "✅ two-scope AGENTS.md (global ~/.zcode/AGENTS.md appended by workspace AGENTS.md); flat, no imports"
  skills: "✅ native Agent Skills (SKILL.md) in .zcode/skills/, name+description frontmatter, $name invocation"
  commands: "✅ native slash commands .zcode/commands or workspace dir (.md prompt files), /name invocation"
  agents: "⚠️ Beta subagents ~/.zcode/agents/*.md — global/user-level ONLY, no project-level roster yet"
  mcp: "✅ native MCP via Settings UI (Form/Full-config JSON), stdio/HTTP/SSE, import from Claude Code/Codex/OpenCode"
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
