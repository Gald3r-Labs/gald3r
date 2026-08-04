---
name: g-skl-platform-goose
description: Authoritative reference for Goose (Block) AI agent customization in gald3r projects. Covers .goosehints + AGENTS.md instructions, ~/.config/goose/config.yaml MCP extensions, Recipes/Subrecipes as slash commands, native subagents, Agent Skills (SKILL.md, shared via ~/.claude/skills/), lifecycle hooks (hooks.json), and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/goose/
vault_docs_url: https://block.github.io/goose/docs
docs_url: https://block.github.io/goose/docs
docs_url_secondary:
  - https://goose-docs.ai/docs
  - https://goose-docs.ai/blog/2026/05/14/goose-hooks/
  - https://goose-docs.ai/docs/guides/subagents/
  - https://goose-docs.ai/docs/guides/context-engineering/using-skills/
  - https://block.github.io/goose/docs/guides/recipes/
  - https://block.github.io/goose/docs/getting-started/using-extensions/
last_doc_scan: 2026-06-02
capability_status:
  hooks: "✅ native lifecycle hooks (hooks.json in .agents/plugins/<name>/hooks/; 11 events SessionStart..AfterShellExecution; shell scripts; announced 2026-05-14)"
  rules: "✅ .goosehints static always-on (global + project; every line sent every request) + Memory Extension (dynamic MCP memory)"
  skills: "✅ Agent Skills (SKILL.md) auto-discovered from ~/.config/goose/skills/ OR ~/.claude/skills/ (shared with Claude)"
  commands: "✅ custom slash commands for Recipes (Desktop + CLI) + built-in /plan,/mode,/prompts,/builtin,/clear"
  agents: "✅ native subagents (auto-spawned, parallel up to 10) + Subrecipes (typed reusable recipe files)"
  mcp: "✅ native — extensions ARE MCP servers; extensions: in ~/.config/goose/config.yaml; 70+ extensions"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Provisioned by `gald3r platform install`.
Documentation: https://docs.gald3r.ai
