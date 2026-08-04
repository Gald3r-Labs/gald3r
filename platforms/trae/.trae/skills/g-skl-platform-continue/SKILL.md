---
name: g-skl-platform-continue
description: Authoritative reference for Continue.dev (open-source VS Code / JetBrains extension) customization in gald3r projects. Covers .continue/ rules/prompts/agents/skills/mcpServers, the corrected commands path (.continue/prompts, NOT .continue/commands), the absence of a native AGENTS.md read, the absent hook surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/continue/
vault_docs_url: https://docs.continue.dev
docs_url: https://docs.continue.dev
docs_url_secondary:
  - https://docs.continue.dev/customize/overview
  - https://docs.continue.dev/customize/deep-dives/prompts
  - https://docs.continue.dev/customize/deep-dives/rules
  - https://docs.continue.dev/customize/deep-dives/mcp
  - https://docs.continue.dev/customize/deep-dives/agents
last_doc_scan: 2026-07-18
capability_status:
  hooks: "❌ no lifecycle-hook/event-bus documentation found; do not fabricate a hook config surface"
  rules: "✅ native — .continue/rules/*.md, loaded automatically, lexicographic order; NOT AGENTS.md"
  skills: "⚠️ third-party marketplaces document .continue/skills/ / ~/.continue/skills/; Continue's own tracker has an OPEN 'plans to support skills?' issue (#9216) — native first-party support unconfirmed"
  commands: "✅ native — Prompt files .continue/prompts/*.md (invokable: true), invoked /<name>; CORRECTED from .continue/commands/ (T386)"
  agents: "✅ native — .continue/agents/*.md, Markdown + YAML frontmatter, one file per custom sub-agent"
  mcp: "✅ native — .continue/mcpServers/<name>-mcp.yaml, or a plain JSON file auto-recognized in the same folder, or inline mcpServers: in config.yaml"
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
