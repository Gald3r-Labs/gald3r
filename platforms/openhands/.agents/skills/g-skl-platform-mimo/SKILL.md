---
name: g-skl-platform-mimo
description: Authoritative reference for Xiaomi MiMo-Code (terminal-native AI coding agent, a fork of OpenCode with persistent cross-session memory) customization in gald3r projects. Covers AGENTS.md + CLAUDE.md dual instruction files, MEMORY.md persistent memory, .mimocode/agents custom agents, MCP in mimocode.json, Compose-mode/Distill skills equivalents, and the partial/inherited hook surface pending verification.
crawl_max_age_days: 7
vault_doc_path: research/platforms/mimo/
vault_docs_url: https://mimo.xiaomi.com/mimocode
docs_url: https://mimo.xiaomi.com/mimocode
docs_url_secondary:
  - https://github.com/XiaomiMiMo/MiMo-Code
  - https://mimo.xiaomi.com/mimocode/agents
  - https://mimo.xiaomi.com/mimocode/start
last_doc_scan: 2026-06-13
capability_status:
  hooks: "⚠️ inherited from OpenCode; session hooks exist but lifecycle events need verification — target .mimocode/hooks.json once confirmed"
  rules: "✅ native — AGENTS.md at project root read natively; also reads CLAUDE.md"
  skills: "⚠️ via Compose mode workflows (equivalent, not SKILL.md-native); /distill auto-generates reusable skills into .mimocode/agents/{name}.md"
  commands: "✅ native — /goal, /dream, /distill, /voice, plus custom slash commands via Compose workflows in mimocode.json"
  agents: "✅ native — .mimocode/agents/*.md (project) or ~/.config/mimocode/agents/ (global)"
  mcp: "✅ native — mcp section in mimocode.json; inherits the full OpenCode MCP layer"
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
