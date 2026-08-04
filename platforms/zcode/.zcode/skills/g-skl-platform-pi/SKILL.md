---
name: g-skl-platform-pi
description: Authoritative reference for Pi (badlogic/pi-mono terminal coding-agent harness) customization in gald3r projects. Covers hierarchical AGENTS.md/CLAUDE.md instructions, native Agent Skills (SKILL.md), native prompt-template slash commands, TypeScript-extension lifecycle hooks (pi.on events), the absent MCP surface, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/pi/
vault_docs_url: https://pi.dev/docs/latest/usage
docs_url: https://pi.dev/docs/latest/usage
docs_url_secondary:
  - https://pi.dev/docs/latest/skills
  - https://pi.dev/docs/latest/prompt-templates
  - https://pi.dev/docs/latest/extensions
  - https://pi.dev/docs/latest/settings
  - https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md
last_doc_scan: 2026-07-03
capability_status:
  hooks: "✅ native TypeScript extension event handlers (pi.on(event, handler)); no JSON config"
  rules: "✅ hierarchical AGENTS.md/CLAUDE.md concat (global ~/.pi/agent/AGENTS.md + walk-up); flat body, no glob scoping"
  skills: "✅ native Agent Skills (SKILL.md) in .pi/skills/ + .agents/skills/, name+description frontmatter, /skill:name invocation"
  commands: "✅ native prompt templates .pi/prompts/<name>.md (or global ~/.pi/agent/prompts/), /name invocation"
  agents: "❌ no project-level agents/*.md roster convention; only imperative extension session-spawning"
  mcp: "❌ explicitly unsupported by design — \"No MCP\" per the coding-agent README"
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
