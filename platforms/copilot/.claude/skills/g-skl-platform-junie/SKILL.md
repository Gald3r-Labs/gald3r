---
name: g-skl-platform-junie
description: Authoritative reference for JetBrains Junie (IDE plugin + Junie CLI) customization in gald3r projects. Covers .junie/ commands/agents/skills + AGENTS.md guidelines + mcp.json + EAP SessionStart hooks, the extension bundle, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/junie/
vault_docs_url: https://junie.jetbrains.com/docs
docs_url: https://junie.jetbrains.com/docs
docs_url_secondary:
  - https://junie.jetbrains.com/docs/custom-slash-commands.html
  - https://junie.jetbrains.com/docs/guidelines-and-memory.html
  - https://junie.jetbrains.com/docs/junie-cli-subagents.html
  - https://junie.jetbrains.com/docs/agent-skills.html
  - https://junie.jetbrains.com/docs/junie-cli-hooks.html
  - https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
last_doc_scan: 2026-06-02
capability_status:
  hooks: "⚠️ EAP SessionStart-only hooks in config.json (personal ~/.junie/config.json; project hooks ignored); no PreToolUse/PostToolUse/pre-commit; JUNIE-1961 tracks more"
  rules: "✅ guidelines/memory via AGENTS.md (project > global ~/.junie/AGENTS.md; legacy .junie/guidelines.md still read); injected into every task"
  skills: "✅ Agent Skills (agentskills.io SKILL.md) in .junie/skills/ user+project; progressive disclosure; JetBrains IDEs + CLI"
  commands: "✅ custom slash commands .junie/commands/*.md (/name, $arg named args) — CLI"
  agents: "✅ native subagents .junie/agents/ (md + YAML; auto-delegated by name/description) — CLI"
  mcp: "✅ native — .junie/mcp/mcp.json (shared CLI + IDE), local + remote servers"
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
