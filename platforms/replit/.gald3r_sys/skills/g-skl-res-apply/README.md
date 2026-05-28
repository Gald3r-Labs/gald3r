# g-skl-res-apply
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Convert a reverse-spec FEATURES.md (produced by g-skl-res-deep) into gald3r artifacts: project goals, PRDs, subsystem specs (merge or create), and tasks. Vault-aware — reads from {vault}/research/recon/{slug}/FEATURES.md when a shared vault is configured, else falls back to local research/harvests/{slug}/FEATURES.md. …

## When to use

- Invoke via `@g-skl-res-apply` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
