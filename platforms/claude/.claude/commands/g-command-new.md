---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-command-new - Scaffold a new gald3r command with mandatory subsystem tagging

Creates a new `.gald3r_sys/commands/g-<verb>-<noun>.md` using the canonical
command template with `subsystem_memberships:` pre-filled.

## Usage

```
@g-command-new <verb-noun> [group]
@g-command-new "feat-promote"
@g-command-new "feat-promote" RELEASE_AND_VERSIONING
```

- `<verb-noun>` — slug without the `g-` prefix (e.g. `feat-promote` creates `g-feat-promote.md`)
- `[group]` — optional subsystem group; prompted interactively if omitted

## Steps

Activates **g-skl-gald3r-component-new** with `type: command`.

1. Collect verb-noun slug, group, and one-line description
2. Write `.gald3r_sys/commands/g-<verb>-<noun>.md` from the command template
3. Verify `subsystem_memberships:` is present
4. Offer to run `platform_parity_sync.ps1 -Sync`
5. Offer to regenerate `PRODUCT_SYSTEMS.md`
6. Offer CHANGELOG entry (g-rl-26)

## Related

- Skill: `g-skl-gald3r-component-new` (implementation + template)
- Rule: `g-rl-38` (always-applied creation standards)
- Hook: `g-hk-component-tag-check` (git pre-commit enforcement)
