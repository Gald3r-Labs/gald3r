---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-command-new - Scaffold a new command in YOUR project

Creates a new command for your own project. You choose where it lives - your AI platform folder
(e.g. `.cursor/commands/`, `.claude/commands/`) or somewhere in your repo's contents. Never writes
to `.gald3r_sys/`.

## Usage

```
@g-command-new <verb-noun>
@g-command-new "deploy-staging"
```

- `<verb-noun>` - kebab-case command name (verb before noun).

## Steps

Activates **g-skl-gald3r-component-new**.

1. Ask **where** to create it:
   - **(a) Platform folder** - e.g. `.cursor/commands/<verb-noun>.md`, `.claude/commands/<verb-noun>.md`.
   - **(b) Repo contents** - a path you specify inside your project.
2. Collect a one-line description and the steps the command should perform.
3. Write the command file from the template at the chosen location.
4. Offer a CHANGELOG entry if your project keeps one.

## Related

- Skill: `g-skl-gald3r-component-new` (implementation)
- Maintainer-only equivalent (edits gald3r itself): `@g-gald3r-command-new`
