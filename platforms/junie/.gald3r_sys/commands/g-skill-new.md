---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-skill-new - Scaffold a new gald3r skill with mandatory subsystem tagging

Creates a new `g-skl-<name>/SKILL.md` in `.gald3r_sys/skills/` using the canonical
skill template with `subsystem_memberships:` pre-filled.

## Usage

```
@g-skill-new <name> [group]
@g-skill-new "my-feature-name"
@g-skill-new "my-feature-name" TASK_MANAGEMENT
```

- `<name>` — slug without the `g-skl-` prefix (e.g. `my-feature` creates `g-skl-my-feature/`)
- `[group]` — optional subsystem group; prompted interactively if omitted

## Steps

Activates **g-skl-gald3r-component-new** with `type: skill`.

1. Collect name, group, and one-line description (interactive if not supplied)
2. Write `.gald3r_sys/skills/g-skl-<name>/SKILL.md` from the skill template
3. Verify `subsystem_memberships:` is present
4. Offer to run `platform_parity_sync.ps1 -Sync`
5. Offer to regenerate `PRODUCT_SYSTEMS.md`
6. Offer CHANGELOG entry (g-rl-26)

## Related

- Skill: `g-skl-gald3r-component-new` (implementation + template)
- Rule: `g-rl-38` (always-applied creation standards)
- Hook: `g-hk-component-tag-check` (git pre-commit enforcement)
