---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-pers-pick — Switch to a personality pack

Switch the active personality pack. Removes the currently active pack (if any),
installs the chosen pack, and updates `.gald3r/.identity`.

## Usage

```
g-pers-pick <pack-name>   Install <pack-name> as the active personality
g-pers-pick none          Uninstall current personality pack (no active personality)
```

## Steps

1. Read current pack from `.gald3r/.identity` `personality=` key
2. If current pack exists (and is not `none`):
   - Run `.gald3r_sys/personality_packs/<current>/install.ps1 -Uninstall -ProjectRoot .`
3. If `<pack-name>` is `none`:
   - Remove `personality=` line from `.identity`
   - Print: "Personality pack removed. No active personality."
   - Remind user to restart IDE session
   - Exit
4. Validate `<pack-name>` exists in `.gald3r_sys/personality_packs/`
5. Run `.gald3r_sys/personality_packs/<pack-name>/install.ps1 -ProjectRoot .`
6. Write `personality=<pack-name>` to `.gald3r/.identity`
7. Confirm and remind user to restart IDE session

## Notes
- All personality packs are fully swappable — including `gald3r_personality`
- `fandom-skills` is skills-only; it does not conflict with a personality pack. Use `g-skill-pack-add` for it
- `.codex`, `.opencode` and other rule-free platforms only get skill files if the pack includes them
- Restart your IDE session after switching for the new personality to load into context
