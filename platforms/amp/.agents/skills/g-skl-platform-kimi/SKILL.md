---
name: g-skl-platform-kimi
description: Authoritative reference for Kimi Code CLI (Moonshot AI, MoonshotAI/kimi-code, renamed from kimi-cli) customization in gald3r projects. Covers AGENTS.md, .kimi-code/skills + .agents/skills Agent Skills, YAML sub-agent specs, config.toml [[hooks]] lifecycle hooks, native MCP, and the post-rebrand config-directory rename (.kimi/ -> .kimi-code/).
crawl_max_age_days: 14
vault_doc_path: research/platforms/kimi/
vault_docs_url: https://www.kimi.com/code/docs/en
docs_url: https://www.kimi.com/code/docs/en
docs_url_secondary:
  - https://moonshotai.github.io/kimi-code/en/
  - https://moonshotai.github.io/kimi-code/en/customization/skills.html
  - https://moonshotai.github.io/kimi-code/en/customization/agents.html
  - https://moonshotai.github.io/kimi-code/en/customization/hooks.html
last_doc_scan: 2026-07-03
capability_status:
  hooks: "✅ native — $KIMI_CODE_HOME/config.toml (default ~/.kimi-code/config.toml) [[hooks]] array; JSON stdin, exit 0 allow / 2 block"
  rules: "✅ native — AGENTS.md, injected via the KIMI_AGENTS_MD system-prompt variable, generated/refreshed by /init"
  skills: "✅ native — SKILL.md (YAML frontmatter + Markdown) in .kimi-code/skills/ (native) and .agents/skills/ (cross-tool); invoked /skill:<name>"
  commands: "✅ native — expressed via Skills (/skill:<name>) and Flow skills (/flow:<name>), plus Custom Plugins (Beta); no standalone slash-command authoring file"
  agents: "✅ native — built-in coder/explore/plan subagents; custom YAML agent specs via --agent-file"
  mcp: "✅ native — kimi mcp sub-command group + /mcp-config"
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
