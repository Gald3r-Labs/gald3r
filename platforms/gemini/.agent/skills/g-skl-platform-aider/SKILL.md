---
name: g-skl-platform-aider
description: Authoritative reference for Aider (terminal AI pair-programmer) customization in gald3r projects. Covers .aider.conf.yml, CONVENTIONS.md (native rules), built-in slash commands, architect/editor chat modes, auto-lint/test triggers, model roles, and gald3r install verification.
crawl_max_age_days: 14
vault_doc_path: research/platforms/aider/
vault_docs_url: https://aider.chat/docs
docs_url: https://aider.chat/docs
docs_url_secondary:
  - https://aider.chat/docs/usage/conventions.html
  - https://aider.chat/docs/usage/commands.html
  - https://aider.chat/docs/usage/modes.html
  - https://aider.chat/docs/usage/lint-test.html
  - https://aider.chat/docs/config/options.html
  - https://github.com/Aider-AI/aider/issues/4506
last_doc_scan: 2026-06-02
capability_status:
  hooks: "⚠️ partial — auto-lint/auto-test post-edit trigger (--auto-lint/--lint-cmd, --auto-test/--test-cmd) + git auto-commit; NO general event hooks (FR #2045)"
  rules: "✅ native — CONVENTIONS.md pinned read-only via --read / .aider.conf.yml read: (arbitrary filename; no rules folder)"
  skills: "❌ not native — no SKILL.md discovery/activation; community aider-skills PyPI injects externally"
  commands: "⚠️ partial — 40+ built-in slash commands (/add /architect /run /load …); NO user-defined custom commands"
  agents: "⚠️ partial — fixed chat modes (code/architect/ask/help); architect = architect-model + --editor-model; NO sub-agent files"
  mcp: "❌ not native — core CLI has none (FR #4506 open); only AiderDesk / mcpm-aider bridges"
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

Run: `gald3r platform install aider`
Documentation: https://docs.gald3r.ai
