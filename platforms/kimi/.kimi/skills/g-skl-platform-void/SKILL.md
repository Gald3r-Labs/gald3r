---
name: g-skl-platform-void
description: Authoritative reference for Void (VS Code fork) customization in gald3r projects. Covers curated (BUG-137, human-assessed, not yet live-crawled) capability signals — Hooks/Skills/Commands curated not-supported, Rules via the legacy .cursorrules file, and MCP curated supported — plus the still-unverified folder hierarchy and instruction file.
crawl_max_age_days: 14
vault_doc_path: research/platforms/void/
vault_docs_url: https://voideditor.com
docs_url: https://voideditor.com
docs_url_secondary: []
last_doc_scan: never
capability_status:
  hooks: "❌ curated (BUG-137) — human-assessed not supported; no native lifecycle-hook system assessed as present"
  rules: "✅ curated (BUG-137) — human-assessed supported via the legacy .cursorrules file (rules_ext: '.cursorrules'); loading behavior unverified"
  skills: "❌ curated (BUG-137) — human-assessed not supported; do not assume any g-skl-*/SKILL.md discovery path exists"
  commands: "❌ curated (BUG-137) — human-assessed not supported; no slash-command or workflow-file primitive assessed as present"
  agents: "❓ untested — not a matrix-tracked column; no verified info"
  mcp: "✅ curated (BUG-137) — human-assessed supported, curated engine-integration tier MCP (L2); connection config unverified"
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
