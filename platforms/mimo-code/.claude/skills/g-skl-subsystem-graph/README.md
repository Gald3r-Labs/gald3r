---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-skl-subsystem-graph
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Generate and update .gald3r/SUBSYSTEM_GRAPH.md from subsystem spec file dependencies. Auto-triggered when subsystems are created or updated with dependency changes. Also callable via @g-dependency-graph --subsystems or @g-subsystem-graph.

## When to use

- Invoke via `@g-skl-subsystem-graph` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
