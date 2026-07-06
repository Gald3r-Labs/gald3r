---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
skill_trust_level: core
---
# g-skl-command-new - Create a new command in your own project

Scaffolds a new command **for your project** at a location you choose. User-facing counterpart to
the maintainer-only `g-skl-gald3r-command-new`. NEVER writes to `.gald3r_sys/`.

## Trigger Phrases
- `@g-command-new <verb-noun>`
- "create a command for my project", "add a slash command"

## Operations

1. **Ask where it should live** (required):
   - **(a) Platform folder** - e.g. `.cursor/commands/<verb-noun>.md`,
     `.claude/commands/<verb-noun>.md`. Offer installed platforms.
   - **(b) Repo contents** - a path the user specifies.
2. Collect: **verb-noun** name, **one-line description**, **steps** the command performs.
3. Write the command at the chosen location from this template:

```markdown
---
description: <one-line description>
---
# <verb-noun> - <one-line description>

<2-3 sentence description.>

## Usage
\`\`\`
@<verb-noun> <required-arg> [optional-arg]
\`\`\`

## Steps
1. <step 1>
2. <step 2>
```

4. Offer a CHANGELOG entry if the project keeps one.

## Related
- Command: `@g-command-new`
- Maintainer-only (edits gald3r itself): `g-skl-gald3r-command-new`
