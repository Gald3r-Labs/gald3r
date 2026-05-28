# g-skl-graphify
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Build and query a code graph representation of the codebase for 71x fewer tokens on architecture questions. Wire into g-go-code context-prep phase: query the graph before editing files instead of grepping linearly. …

## When to use

- Invoke via `@g-skl-graphify` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
