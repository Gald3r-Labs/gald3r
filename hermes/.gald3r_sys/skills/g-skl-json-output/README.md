# g-skl-json-output
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Emit gald3r command output (status, review, backlog) as structured JSON for scripting, CI gates, dashboards, and agent-to-agent handoff. Operations SERIALIZE, SCHEMA, VALIDATE, EXPORT. Invoked by --json flag commands (T1381). Mirrors g-skl-html-output. Coordination state files stay markdown.

## When to use

- Invoke via `@g-skl-json-output` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
