---
description: 'Scaffold a new slash command file into a chosen platform folder or repo path with prompted metadata.'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
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

1. Ask **where** to create it:
   - **(a) Platform folder** - e.g. `.cursor/commands/<verb-noun>.md`, `.claude/commands/<verb-noun>.md`.
   - **(b) Repo contents** - a path you specify inside your project.
2. Collect a one-line description and the steps the command should perform. Confirm whether the
   command takes arguments.
3. Write the command file from the template at the chosen location. The YAML frontmatter MUST
   include (T441):
   - `description:` - imperative mood, specific to this command (no generic collision-prone
     wording per g-rl-42), <=110 characters.
   - `argument-hint:` - present whenever the command takes arguments; a short pattern showing the
     accepted forms (e.g. `'<name>'`, `'<description> | status | clear'`). Omit only when the
     command takes no arguments at all.
4. Offer a CHANGELOG entry if your project keeps one.
