---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-skill-pack-del — Remove a skill pack or individual skill

Remove all skills from a pack, or a single named skill, from all active IDE folders.

## Usage

```
g-skill-pack-del <pack-name>                  Remove all skills in the pack
g-skill-pack-del <pack-name> <skill-name>     Remove one skill from the pack
g-skill-pack-del <pack-name> --force          Remove including _evolved variants
```

## Steps

1. Validate `<pack-name>` exists in `.gald3r_sys/skill_packs/`
2. Run uninstall:
   ```powershell
   .gald3r_sys/skill_packs/<pack-name>/install.ps1 -Uninstall -ProjectRoot . [-Skill <skill-name>]
   ```
3. The installer skips `_evolved` skill folders by default (warns with: "⚠ Skipping <name>_evolved — use --force to remove")
4. Update `.gald3r/.identity` `installed_skill_packs:` block — remove skill or whole pack entry
5. Confirm what was removed

## Notes
- `_evolved` skills (user-customized) are protected from accidental deletion
- Use `--force` only when you explicitly want to remove a customized skill
- gald3r core skills (in `.gald3r_sys/skills/`) are never touched by this command

