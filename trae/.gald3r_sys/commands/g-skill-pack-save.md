---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-skill-pack-save — Save an evolved skill back to the skill pack registry

When you have customized a skill and want to preserve that customization in the pack
registry (so it survives `g-skill-pack-add` updates), save it with this command.

## Usage

```
g-skill-pack-save <skill-name>                     Find skill, save to its pack
g-skill-pack-save <skill-name> --pack <pack-name>  Specify pack explicitly
```

## Steps

1. Search all active IDE folders for `<skill-name>/SKILL.md` (check `.cursor/skills/`, `.claude/skills/`, etc.)
2. Determine which pack owns this skill (read `installed_skill_packs:` from `.identity`)
   - If `--pack` given, use that
   - If not found, ask user which pack it belongs to
3. Copy the skill folder to:
   `.gald3r_sys/skill_packs/<pack-name>/source/skills/<skill-name>_evolved/`
4. Mark in the pack's source index that an evolved version exists:
   - Update `PACK.md` with a note: `evolved: true` for that skill entry
5. Update `.gald3r/.identity` installed_skill_packs entry: add `evolved: true` for the skill
6. Confirm: "Skill saved as <skill-name>_evolved in <pack-name>. Future g-skill-pack-add will install the evolved version."

## Notes
- The `_evolved` suffix signals to installers and `g-skill-pack-del` that this is user-customized
- The original non-evolved version is preserved alongside the evolved one in the registry
- `g-skill-pack-add --update` will show a diff before overwriting an evolved skill
- Evolved skills are not overwritten by gald3r updates (version bump does not touch `_evolved` folders)

