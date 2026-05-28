---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-skill-pack-list — List available skill packs and install status

Show all available skill packs from `.gald3r_sys/skill_packs/` along with which packs
and individual skills are currently installed in this project.

## Steps

1. Read `.gald3r/.identity` for `installed_skill_packs:` block
2. Scan `.gald3r_sys/skill_packs/` for all pack directories with a `PACK.md`
3. For each pack, read `name`, `version`, `tier`, skill list from PACK.md
4. Compare against installed state to determine: installed / available / update-available
5. Display:

```
Available Skill Packs
=====================

  PACK              TIER    VERSION   INSTALLED    SKILLS
  3d-graphics       adv     1.0.0     —            skl-3d-performance, skl-algorithmic-art, ...
  ai-media          adv     1.2.0     1.2.0 ✅     skl-higgsfield, skl-seedance
  cloud-providers   full    1.0.0     0.9.0 ⬆     (update available)
  community         slim    1.0.0     1.0.0 ✅     skl-discord, skl-slack, skl-telegram
  ...

Installed packs: 3  |  Available: 7
Use: g-skill-pack-add <pack> [--skill <name>]  to install
```

6. For installed packs, show individual skill status including `_evolved` badges

