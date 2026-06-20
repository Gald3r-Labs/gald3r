---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# @g-subsystem-audit

Audit subsystem and skill tagging compliance against the L1 group hierarchy defined in
`PRODUCT_SYSTEMS.md`. Surfaces ungrouped subsystems, unknown group values, and untagged skills.
Activates **g-skl-subsystems** → AUDIT operation.

## What This Does

1. Reads `PRODUCT_SYSTEMS.md` frontmatter `defined_groups:` for the authoritative group list
2. Scans all `.gald3r/subsystems/*.md` — checks `parent_system:` field
3. Scans all `SKILL.md` files — checks `subsystem_memberships:` field
4. Reports: ungrouped files, unknown group names (typos), empty groups, UNCATEGORIZED skills

## When This Fires Automatically

- `g-medic` L2-F2 triage: when subsystem count > 20 and no PRODUCT_SYSTEMS.md exists
- `g-medic` L2-F2 triage: when >25% of subsystem specs lack `parent_system:`
- Session start (g-rl-25): when subsystem count > 25 and PRODUCT_SYSTEMS.md is absent

## Steps

1. Activate `g-skl-subsystems` AUDIT operation (see SKILL.md for algorithm)
2. Read `PRODUCT_SYSTEMS.md` (from `.gald3r/PRODUCT_SYSTEMS.md`) for `defined_groups:` list.
   If missing, use default group list.
3. Scan `.gald3r/subsystems/*.md` for `parent_system:` compliance
4. Scan `skills/**/SKILL.md` for `subsystem_memberships:` compliance
5. Output structured report:
   - Compliant: N subsystems, M skills tagged
   - Ungrouped subsystems: [list]
   - Unknown group refs: [list] (likely typos -- fix before running @g-system-rebuild)
   - UNCATEGORIZED skills: [list] (need manual classification)
   - Empty groups: [list] (informational)
6. If unknown group refs > 0: stop and ask user to correct them
7. If ungrouped subsystems > 0: offer to run fix interactively (ask which group each belongs to)
8. After fixing, recommend: `@g-system-rebuild` to regenerate PRODUCT_SYSTEMS.md

## Related

- `@g-system-rebuild` — regenerate PRODUCT_SYSTEMS.md from tags
- `add_subsystem_tags.ps1` — bulk-tag SKILL.md files
- `aggregate_subsystems.ps1` — generates PRODUCT_SYSTEMS.md
- `g-skl-subsystems` AUDIT operation — the underlying implementation
- C-026 — constraint requiring `parent_system:` on all new subsystem specs
