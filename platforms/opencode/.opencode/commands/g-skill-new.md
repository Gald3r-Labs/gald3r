---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-skill-new - Scaffold a new skill in YOUR project

Creates a new skill for your own project. You choose where it lives - your AI platform folder
(e.g. `.cursor/skills/`, `.claude/skills/`) or somewhere in your repo's own contents. This never
writes to `.gald3r_sys/` (the gald3r framework payload is read-only to your project).

## Usage

```
@g-skill-new <name>
@g-skill-new "my-feature"
```

- `<name>` - slug for the skill (e.g. `my-feature`).

## Steps

Activates **g-skl-gald3r-component-new**.

1. Ask **where** to create it:
   - **(a) Platform folder** - your chosen IDE: `.cursor/skills/<name>/SKILL.md`,
     `.claude/skills/<name>/SKILL.md`, etc. (pick one or more installed platforms).
   - **(b) Repo contents** - a path inside your own project source you specify.
2. Collect a one-line description and trigger phrases.
3. Write `SKILL.md` from the template at the chosen location.
4. Offer a CHANGELOG entry if your project keeps one.

## Related

- Skill: `g-skl-gald3r-component-new` (implementation)
- Maintainer-only equivalent (edits gald3r itself): `@g-gald3r-skill-new`
