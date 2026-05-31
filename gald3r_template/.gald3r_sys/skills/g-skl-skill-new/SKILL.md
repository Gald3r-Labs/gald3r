---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
skill_trust_level: core
---
# g-skl-skill-new - Create a new skill in your own project

Scaffolds a new skill **for your project** at a location you choose. This is the user-facing
counterpart to the maintainer-only `g-skl-gald3r-skill-new` (which edits the gald3r framework).

> This skill NEVER writes to `.gald3r_sys/`. The gald3r framework payload is not yours to modify -
> your custom skills live in your platform folders or your repo.

## Trigger Phrases
- `@g-skill-new <name>`
- "create a skill for my project", "add a new skill"

## Operations

1. **Ask where it should live** (required - do not assume):
   - **(a) Platform folder** of an installed AI tool, under its skills directory, e.g.
     `.cursor/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md`. Offer the platforms the
     project actually has.
   - **(b) Repo contents** - a path inside the user's own source tree that they specify.
2. Collect: **name** (slug), **one-line description**, **trigger phrases**.
3. Write `SKILL.md` at the chosen location from this template:

```markdown
---
description: <one-line description>
---
# <name> - <one-line description>

<2-3 sentences: what this skill does and when to use it.>

## Trigger Phrases
- <phrase 1>
- <phrase 2>

## Operations
### <Operation>
<step-by-step instructions>
```

4. If the project keeps a `CHANGELOG.md`, offer an entry.

## Related
- Command: `@g-skill-new`
- Maintainer-only (edits gald3r itself): `g-skl-gald3r-skill-new`
