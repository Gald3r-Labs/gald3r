# g-skl-res-deep
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Analyze any external repository and produce a structured FEATURES.md harvest report. Writes to {vault}/research/recon/{slug}/ when a shared vault is configured, else falls back to local research/harvests/{slug}/. Performs cross-project dedup via _recon_index.yaml. Agents are reporters — humans are editors. …

## When to use

- Invoke via `@g-skl-res-deep` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
