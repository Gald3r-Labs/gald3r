# g-skl-api-doc-gen
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Auto-generate OpenAPI 3.1 specs from FastAPI/Express/Flask routes; fill docstring gaps for undocumented functions; update README API tables. Covers Python FastAPI, Express.js, and Flask. Also generates MCP tool descriptions for FastMCP plugins.

## When to use

- Invoke via `@g-skl-api-doc-gen` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
