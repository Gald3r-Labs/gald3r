# g-skl-oracle
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Execute Oracle Database queries and operations via gald3r_valhalla MCP tools. Requires Docker backend (adv tier). Supports read-only queries (oracle_query) and full write operations (oracle_execute) including DDL and PL/SQL blocks.

## When to use

- Invoke via `@g-skl-oracle` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
