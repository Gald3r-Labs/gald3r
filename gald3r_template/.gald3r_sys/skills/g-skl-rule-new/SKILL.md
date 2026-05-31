---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
skill_trust_level: core
---
# g-skl-rule-new - Create a new rule in your own project

Scaffolds a new rule **for your project** at a location you choose. User-facing counterpart to the
maintainer-only `g-skl-gald3r-rule-new`. NEVER writes to `.gald3r_sys/`.

## Trigger Phrases
- `@g-rule-new <slug>`
- "create a rule for my project", "add a coding standard"

## Operations

1. **Ask where it should live** (required):
   - **(a) Platform folder** - e.g. `.cursor/rules/<slug>.mdc` (Cursor), a Claude rules entry, or
     your project's `AGENTS.md`. Offer installed platforms.
   - **(b) Repo contents** - a path the user specifies.
2. Collect: **slug**, **description**, **scope** (always-applied vs file-glob scoped).
3. Write the rule at the chosen location. Cursor `.mdc` template:

```markdown
---
description: <short description>
globs:
alwaysApply: true
---
# <Rule Title>

<When this rule fires and what it enforces.>

## Requirements
- <mandatory behavior>

## Enforcement Table
| Rationalization | Reality |
|---|---|
| "<excuse>" | "<correct behavior>" |
```

4. Keep always-applied rules tight - they inject into every AI context.
5. Offer a CHANGELOG entry if the project keeps one.

## Related
- Command: `@g-rule-new`
- Maintainer-only (edits gald3r itself): `g-skl-gald3r-rule-new`
