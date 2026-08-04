---
name: g-skl-platform-subq
description: Authoritative reference for SubQ (Subquadratic Inc.) and "SubQ Code" in gald3r projects. SubQ is a long-context LLM (OpenAI-compatible Chat Completions API); SubQ Code is a PLUGIN / long-context layer that plugs into Claude Code, Codex, and Cursor — it exposes NO native commands/rules/agents/skills/hooks/MCP of its own. gald3r installs target the HOST tool, not SubQ.
crawl_max_age_days: 30
vault_doc_path: research/platforms/subq/
vault_docs_url: https://subq.ai
docs_url: https://subq.ai
docs_url_secondary:
  - https://subq.ai/code
  - https://docs.subq.ai/overview/
  - https://subq.ai/introducing-subq
  - https://console.subq.ai/
  - https://playground.subq.ai/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "❌ none — SubQ Code is a plugin; no lifecycle hooks. Wire g-hk-*.py on the HOST (Claude Code/Codex/Cursor) or via git core.hooksPath"
  rules: "❌ none — no .mdc/rules/memory mechanism; persistent instructions live in the host's AGENTS.md/CLAUDE.md"
  skills: "❌ none — no SKILL.md / Agent-Skills discovery; gald3r skills load via the host, not SubQ"
  commands: "❌ none — no slash/custom-command system; commands come from the host tool"
  agents: "❌ none — SubQ Code is a layer invoked by an existing agent; not a multi-agent framework"
  mcp: "❌ none — developer surface is an OpenAI-compatible Chat Completions API (HTTP), NOT MCP"
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
