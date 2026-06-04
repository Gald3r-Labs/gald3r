# g-skl-theme-editor
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Create and edit gald3r HTML themes against docs/themes/theme-schema.json. Visual editor (live preview, per-token color pickers, import/export :root blocks) ships in gald3r_throne; this skill is the spec + a file-first fallback that works without the app. Invoked by g-theme-edit.

## When to use

- Invoke via `@g-skl-theme-editor` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
