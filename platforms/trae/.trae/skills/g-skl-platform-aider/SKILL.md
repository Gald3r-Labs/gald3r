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
  - https://aider.chat/docs/config/aider_conf.html
  - https://github.com/Aider-AI/aider/issues/4506
  - https://github.com/Aider-AI/aider/issues/4363
last_doc_scan: 2026-07-18
capability_status:
  hooks: "⚠️ partial — auto-lint/auto-test post-edit trigger (--auto-lint/--lint-cmd, --auto-test/--test-cmd) + git auto-commit; NO general event hooks (FR #2045)"
  rules: "✅ native — CONVENTIONS.md pinned read-only via --read / .aider.conf.yml read: (arbitrary filename; no rules folder); gald3r's own `gald3r platform install aider` now writes BOTH files automatically (T407)"
  skills: "❌ not native — no SKILL.md discovery/activation; community aider-skills PyPI injects externally"
  commands: "⚠️ partial — 40+ built-in slash commands (/add /architect /run /load …); NO user-defined custom commands"
  agents: "⚠️ partial — fixed chat modes (code/architect/ask/help); architect = architect-model + --editor-model; NO sub-agent files"
  mcp: "❌ not native — core CLI has none (FR #4506 open); only AiderDesk / mcpm-aider bridges"
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

Run: `gald3r platform install aider`
Documentation: https://docs.gald3r.ai
