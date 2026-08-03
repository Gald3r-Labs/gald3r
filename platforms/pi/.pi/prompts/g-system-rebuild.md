---
description: 'Regenerate PRODUCT_SYSTEMS.md by scanning SKILL.md subsystem_memberships and parent_system tags.'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
---
# @g-system-rebuild

Regenerate `.gald3r/PRODUCT_SYSTEMS.md` by scanning all repos in the workspace for distributed
`subsystem_memberships:` tags (in SKILL.md files) and `parent_system:` tags (in subsystem specs).
Activates **g-skl-subsystems**.

## What This Does

1. Reads the authoritative L1 group list from `PRODUCT_SYSTEMS.md` frontmatter (`defined_groups:`)
2. Scans every `SKILL.md` file for `subsystem_memberships:` — maps each skill to its L1 group(s)
3. Scans every `.gald3r/subsystems/*.md` for `parent_system:` — maps each subsystem to its group
4. Detects: ungrouped files, unknown group names (typos), empty groups
5. Writes a new `PRODUCT_SYSTEMS.md` preserving `defined_groups:` in frontmatter (so T1458
   enforcement can read the group list without opening the full file)

## When to Use

- After adding any new subsystem or skill
- After the T1457 tagging pass
- When SUBSYSTEMS.md count exceeds 20 and sprawl is suspected
- When `@g-subsystem-audit` reports drift

## Steps

1. Run dry-run first to check for unknown group warnings:
   ```bash
   gald3r subsystem aggregate --root .
   ```
2. If no unknown groups → apply:
   ```bash
   gald3r subsystem aggregate --root . --apply
   ```
3. Report: "PRODUCT_SYSTEMS.md regenerated — N groups populated, M ungrouped."
4. If unknown group warnings: stop and ask user to correct the tags before applying (or pass
   `--force` to write anyway once the reference is confirmed intentional).

## Related

- `@g-subsystem-audit` — detailed audit of tagging compliance (T1458)
- `gald3r subsystem aggregate` — the real implementation of this regeneration (BUG-196; replaces
  the never-authored/lost `aggregate_subsystems.ps1`, T1459)
- `add_subsystem_tags.ps1` — bulk tagger for initial pass (T1457)
- `PRODUCT_SYSTEMS.md` — the output (read by `@g-subsystem-audit` and `g-skl-subsystems` CREATE)
