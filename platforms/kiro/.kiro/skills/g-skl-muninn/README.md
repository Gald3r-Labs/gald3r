---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-skl-muninn
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

gald3r_muninn MCP — query the local codebase knowledge graph for impact analysis, caller chains, dependencies, and symbol search. Clean-room rewrite (T1147 epic, T1153-T1158) of the GitNexus integration; auto-loaded by the example_app MCP server from docker/gald3r/tools/plugins/muninn/. …

## When to use

- Invoke via `@g-skl-muninn` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
