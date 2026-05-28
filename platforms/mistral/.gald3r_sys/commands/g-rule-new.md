---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-rule-new - Scaffold a new gald3r rule with mandatory subsystem tagging

Creates a new `.gald3r_sys/rules/g-rl-<NN>-<slug>.md` using the canonical
rule template with the next sequential rule number, `alwaysApply:`, and
`subsystem_memberships:` pre-filled.

## Usage

```
@g-rule-new <slug> [group]
@g-rule-new "no-empty-agents"
@g-rule-new "no-empty-agents" AGENT_ORCHESTRATION
```

- `<slug>` — descriptive slug without number prefix (e.g. `no-empty-agents`)
  The rule number (NN) is assigned automatically as highest existing + 1
- `[group]` — optional subsystem group; prompted interactively if omitted

## Steps

Activates **g-skl-gald3r-component-new** with `type: rule`.

1. Scan `.gald3r_sys/rules/` to determine the next rule number
2. Collect slug, group, `alwaysApply` (true/false), and `description:` line
3. Write `.gald3r_sys/rules/g-rl-<NN>-<slug>.md` from the rule template
4. Verify `subsystem_memberships:` and `description:` are present
5. Offer to run `platform_parity_sync.ps1 -Sync` to propagate to all IDE `.cursor/rules/` targets
6. Offer to regenerate `PRODUCT_SYSTEMS.md`
7. Offer CHANGELOG entry (g-rl-26)

## After creation

The rule file must be synced to all IDE targets:
```powershell
pwsh custom_scripts\platform_parity_sync.ps1 -Sync
```

For `alwaysApply: true` rules, the IDE must restart (or rules must be reloaded) before
the rule takes effect in new conversations.

## Related

- Skill: `g-skl-gald3r-component-new` (implementation + template)
- Rule: `g-rl-38` (always-applied creation standards)
- Hook: `g-hk-component-tag-check` (git pre-commit enforcement)
