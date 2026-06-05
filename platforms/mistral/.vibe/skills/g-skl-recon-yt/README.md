---
subsystem_memberships: [VAULT_AND_RESEARCH]
---
# g-skl-recon-yt
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

YouTube transcript ingestion into the vault. Uses yt-dlp to fetch transcripts locally — no Docker, no MCP, no screen captures. Stores in research/videos/ with analysis_depth=transcript_only for future vision upgrade.

## When to use

- Invoke via `@g-skl-recon-yt` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
