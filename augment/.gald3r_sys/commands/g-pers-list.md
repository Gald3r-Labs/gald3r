---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-pers-list — List available personality packs

List all available personality packs from `.gald3r_sys/personality_packs/` and show
which pack is currently active.

## Steps

1. Read `.gald3r/.identity` for `personality=` key (current active pack)
2. Scan `.gald3r_sys/personality_packs/` for all `PACK.md` files
3. For each pack, read `name`, `display_name`, `default`, `description` from frontmatter
4. Display table:

```
Available Personality Packs
===========================

  PACK                    DEFAULT   STATUS         DESCRIPTION
  gald3r_personality      yes       🟢 active       Norse pantheon co-developers
  personality-rules       —         — available     BSG, Firefly, Hackers, SV, Star Trek, Star Wars
  fandom-skills           —         — available     7 megafan knowledge skills
  shoresy                 —         — available     Shoresy from Letterkenny

Active pack: gald3r_personality
Use: g-pers-pick <pack-name>   to switch personality
Use: g-pers-pick none          to clear to no personality pack
```

5. If `personality=` key is absent from `.identity`, show `gald3r_personality` as active (installed by g-setup)
6. If no pack is installed at all, say so and suggest `g-pers-pick gald3r_personality`

## Notes
- `gald3r_personality` is the default installed by `g-setup` but is fully replaceable
- Only one personality pack is active at a time — they are swapped, not stacked
- `fandom-skills` is a skills-only pack (no rule file) and can be installed alongside any personality
- If `.gald3r_sys/personality_packs/` is missing, inform user and exit gracefully
