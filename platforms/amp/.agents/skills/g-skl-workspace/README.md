---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
# g-skl-workspace
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Workspace-Control Mode skill. Reads .gald3r/linking/workspace_manifest.yaml as the canonical registry and provides STATUS, VALIDATE, MEMBER LIST, SPAWN, ADOPT, EXPORT/SYNC dry-run planning, and member `.gald3r/` marker bootstrap/remediate/validate operations for manifest-declared repositories.

## When to use

- Invoke via `@g-skl-workspace` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
