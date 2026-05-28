# g-skl-res-review
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Analyze external sources (GitHub repos, URLs) for adoptable patterns and improvements. Vault-aware — reads from {vault}/research/recon/ when a shared vault is configured, else falls back to local research/harvests/. Uses _recon_index.yaml for cross-project dedup. …

## When to use

- Invoke via `@g-skl-res-review` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
