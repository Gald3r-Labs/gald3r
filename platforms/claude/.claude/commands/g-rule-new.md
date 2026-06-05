---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-rule-new - Scaffold a new rule in YOUR project

Creates a new rule for your own project. You choose where it lives - your AI platform folder
(e.g. `.cursor/rules/`, `.claude/` rules, `AGENTS.md`) or somewhere in your repo's contents.
Never writes to `.gald3r_sys/`.

## Usage

```
@g-rule-new <slug>
@g-rule-new "no-console-logs"
```

- `<slug>` - kebab-case slug for the rule.

## Steps

Activates **g-skl-gald3r-component-new**.

1. Ask **where** to create it:
   - **(a) Platform folder** - e.g. `.cursor/rules/<slug>.mdc` (Cursor), a rules entry for Claude, etc.
   - **(b) Repo contents** - a path you specify inside your project.
2. Collect the rule description and whether it always applies or is scoped to file globs.
3. Write the rule file from the template at the chosen location.
4. Offer a CHANGELOG entry if your project keeps one.

## Related

- Skill: `g-skl-gald3r-component-new` (implementation)
- Maintainer-only equivalent (edits gald3r itself): `@g-gald3r-rule-new`
