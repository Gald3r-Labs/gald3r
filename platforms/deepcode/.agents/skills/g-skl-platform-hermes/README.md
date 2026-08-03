---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-skl-platform-hermes
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Authoritative reference for Hermes Agent (Nous Research) customization in gald3r projects. Covers `~/.hermes/` config (`config.yaml`/`.env`), the `AGENTS.md`-native auto-injected instruction surface, agentskills.io `SKILL.md` skills (the gald3r distribution opportunity, via taps), `delegate_task` subagents, MCP (`mcp_servers:`), the native `config.yaml` `hooks:` surface (17+ lifecycle events with `pre_tool_call` blocking), and install verification.

## When to use

- Invoke via `@g-skl-platform-hermes` (or when the agent determines this skill is relevant)
- See the **Activate for** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
