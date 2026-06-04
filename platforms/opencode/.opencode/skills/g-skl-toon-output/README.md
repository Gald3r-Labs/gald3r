# g-skl-toon-output
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Emit gald3r output as TOON (Token-Oriented Object Notation) — a compact, lossless, LLM-friendly format that states record keys once (tabular arrays) to cut tokens vs markdown/JSON. Operations ENCODE, DECODE, VALIDATE, EXPORT. Invoked by --toon flag commands (T1382). Coordination state files stay markdown.

## When to use

- Invoke via `@g-skl-toon-output` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
