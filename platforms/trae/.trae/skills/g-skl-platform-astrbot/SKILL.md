---
name: g-skl-platform-astrbot
description: Authoritative reference for AstrBot customization in gald3r projects. Covers curated (BUG-137, human-assessed, not yet live-crawled) support signals for Hooks/Rules/Skills/Commands/MCP, the still-unverified folder hierarchy and instruction file, and how to upgrade this spec from curated to verified.
crawl_max_age_days: 14
vault_doc_path: research/platforms/astrbot/
vault_docs_url: https://astrbot.app
docs_url: https://astrbot.app
docs_url_secondary: []
last_doc_scan: never
capability_status:
  hooks: "✅ curated (BUG-137) — human-assessed supported; native hook config file, event list, and payload format are unverified pending a live docs crawl"
  rules: "✅ curated (BUG-137) — human-assessed supported; platform_matrix_data.json records rules_ext: '—' (no established rules-file extension curated yet)"
  skills: "✅ curated (BUG-137) — human-assessed supported; SKILL.md discovery path and frontmatter shape are unverified"
  commands: "✅ curated (BUG-137) — human-assessed supported; slash-command syntax and workflow-file format are unverified"
  agents: "❓ untested — not a matrix-tracked column; no verified info"
  mcp: "✅ curated (BUG-137) — human-assessed supported, curated engine-integration tier MCP (L2); connection config and transport details are unverified"
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
