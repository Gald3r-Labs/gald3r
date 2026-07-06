---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-skill-pack-add — Install a skill pack or individual skill

Install all skills from a pack, or a single named skill from a pack.

## Usage

```
g-skill-pack-add <pack-name>                  Install all skills in the pack
g-skill-pack-add <pack-name> <skill-name>     Install one skill from the pack
```

## Steps

1. Validate `<pack-name>` exists in `.gald3r_sys/skill_packs/`
2. If `<skill-name>` given, validate it exists in `<pack-name>/source/skills/`
3. Detect active platforms via helper: check which IDE folders exist in project root
3b. **Trust-level provenance warning (C-032 — non-blocking)**: read each skill's `skill_trust_level:` frontmatter. For every skill whose value is `community` or unset, surface a warning **before** install proceeds:
   ```
   ⚠️  Skill '<skill-name>' — trust level: <community | unset>
       Source: <pack-name>
       Its `allowed-tools:` boundary still applies, but this skill is not gald3r-core.
       Inspect the skill body before its first invocation.
   ```
   This is advisory only — installation continues after the warning. `core` and `local` skills install without a warning. (Canonical wording: `skl-skill-create/SKILL.md` → `### skill_trust_level:` declaration.)
4. Run install:
   ```powershell
   .gald3r_sys/skill_packs/<pack-name>/install.py --project-root . [--skill <skill-name>]
   ```
5. Update `.gald3r/.identity` `installed_skill_packs:` block:
   - If pack not listed: add entry with `pack`, `version`, `skills`, `installed_date`
   - If pack listed: add/update the skill entry; update `version` if installing whole pack
6. Confirm what was installed and to which platforms
7. Remind user to restart IDE session

## Notes
- Adding a skill from a pack that is not yet listed creates a partial install entry
- Version is read from pack's `PACK.md` `version:` frontmatter
- `_evolved` variants are preserved — `add` will not overwrite a skill folder with `_evolved` suffix

