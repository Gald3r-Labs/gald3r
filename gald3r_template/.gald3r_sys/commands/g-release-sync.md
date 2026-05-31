---
name: g-release-sync
description: Reconcile CHANGELOG version headers with .gald3r/releases/ files (C-023). Backfill missing release records.
subsystem_memberships: [RELEASE_AND_VERSIONING]
---

# @g-release-sync

Activate `g-skl-release` SYNC operation (C-023).

## Usage

```
@g-release-sync
@g-release-sync --apply
```

## What it does

1. Reads `CHANGELOG.md` version headers (`## [X.Y.Z]`)
2. Compares against `.gald3r/releases/release*_v*.md` files
3. Reports gaps (dry-run) or creates missing release files (`--apply`)

## Script

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-release/scripts/backfill_release_files.ps1 -ProjectRoot .
# Apply:
powershell -NoProfile -ExecutionPolicy Bypass -File .gald3r_sys/skills/g-skl-release/scripts/backfill_release_files.ps1 -ProjectRoot . -Apply
```

## See also

- `@g-ship` -- semver bump + tag
- `@g-release-cut` -- cut local release tag
- `action_scripts/pre_release_audit.ps1` -- multi-repo pre-flight before public ship
