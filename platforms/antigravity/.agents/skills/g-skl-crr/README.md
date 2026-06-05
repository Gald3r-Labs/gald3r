---
subsystem_memberships: [VAULT_AND_RESEARCH, AGENT_ORCHESTRATION]
---
# g-skl-crr
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Clean-Room Rewrite pipeline. Orchestrates 4 phases via independent background subagents — harvest a source repo, write all findings to IDEA_BOARD (mandatory), triage tasks, and produce a gald3r-native clean-room implementation spec.

## When to use

- Invoke via `@g-skl-crr` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
