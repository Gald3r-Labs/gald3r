---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
# g-skl-wpac-spawn
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Spawn a new gald3r project from the current project. Creates the new project folder in the same ecosystem root, installs gald3r (matching the current project's install type — symlinks or fresh template), seeds it with any passed description/features/code, runs gald3r-setup, and immediately links both projects via PCAC …

## When to use

- Invoke via `@g-skl-wpac-spawn` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
