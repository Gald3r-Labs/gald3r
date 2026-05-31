# g-skl-recon-docs
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Documentation URL ingestion with periodic revisit. Crawls URLs into research/platforms/, tracks staleness per _index.yaml, surfaces stale count at session start. Depends on g-skl-crawl (crawl4ai).

## When to use

- Invoke via `@g-skl-recon-docs` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
