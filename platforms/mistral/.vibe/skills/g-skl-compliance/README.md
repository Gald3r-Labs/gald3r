---
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---
# g-skl-compliance
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

SCA/license compliance scanning — wraps ORT, FOSSA, Snyk, and PMD CPD behind a unified gald3r interface with SCAN/REPORT/GATE/STATUS operations. Produces structured compliance reports with pass/warn/fail verdicts.

## When to use

- Invoke via `@g-skl-compliance` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
