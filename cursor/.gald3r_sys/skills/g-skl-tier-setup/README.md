# g-skl-tier-setup
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Configurable product-tier onboarding skill. SETUP creates release_profiles/, scaffolds template_{tier}/ directories, and writes .gald3r/.identity tier metadata. ENABLE annotates existing SUBSYSTEMS.md with min_tier:, infers defaults from subsystem content, and calls platform_parity_sync -TierSync. …

## When to use

- Invoke via `@g-skl-tier-setup` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
