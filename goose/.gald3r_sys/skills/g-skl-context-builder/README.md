# g-skl-context-builder
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Dynamic context assembly from live .gald3r/ state. Builds a token-budgeted agent context block including active tasks, constraints, subsystem specs, and session memory. Use at session start or when handing off between agents in g-go pipelines.

## When to use

- Invoke via `@g-skl-context-builder` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
