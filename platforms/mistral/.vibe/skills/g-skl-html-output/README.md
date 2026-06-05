---
subsystem_memberships: [UI_AND_OUTPUT]
---
# g-skl-html-output
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Render human-facing reports (status, review, backlog) as themed HTML using docs/templates/ + docs/themes/. Operations RENDER, CHOOSE_THEME, VALIDATE, EXPORT. Invoked by --html flag commands (T1318). Never used for coordination files (TASKS.md, BUGS.md, task specs) which are always markdown.

## When to use

- Invoke via `@g-skl-html-output` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
