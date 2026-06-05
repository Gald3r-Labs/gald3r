---
subsystem_memberships: [SECURITY_AND_COMPLIANCE, BUG_AND_QUALITY]
---
# g-skl-dependency-audit
**Skill file**: `SKILL.md`

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this page is for developers browsing the skill library.

## What it does

Scan package files for outdated or vulnerable dependencies. Generates a severity-ranked report with CVE references and upgrade commands. Supports Python (requirements.txt/pyproject.toml), JavaScript/Node (package.json/package-lock.json), and Rust (Cargo.toml/Cargo.lock).

## When to use

- Invoke via `@g-skl-dependency-audit` (or when the agent determines this skill is relevant)
- See the **When to Use** / trigger section of `SKILL.md` for the authoritative list

## Related skills

- See `SKILL.md` and the gald3r skill index for related skills
