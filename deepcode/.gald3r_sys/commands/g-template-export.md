---
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
# g-template-export — Slim template export (gald3r_dev maintainers)

**gald3r_dev only** — not part of installable `G:/gald3r_ecosystem/gald3r_template_full`.

## Steps

1. From repo root, optionally sync parity: `.\custom_scripts\platform_parity_sync.ps1 -Sync`
2. Dry-run: `.\custom_scripts\export_slim_template_repo.ps1 -Destination '<PATH>'`
3. Apply: `.\custom_scripts\export_slim_template_repo.ps1 -Destination '<PATH>' -Apply`
4. Read `<PATH>\MAINTAINER_EXPORT.md` for release + `git init` checklist.

## Flags

| Flag | Effect |
|------|--------|
| `-Apply` | Copy files (omit = list-only dry-run) |
| `-Force` | Skip parity gate (logs warning) |
| `-SkipParityCheck` | Do not run `platform_parity_sync.ps1` (report-only parity gate) |
| `-UseGald3rFullRootDocs` | Overlay repo-root README/CHANGELOG/LICENSE |

## Related

- `g-skl-git-commit` — conventional commits after export
- `custom_scripts/platform_parity_sync.ps1` (report-only — omit `-Sync`) — pre-export parity gate
