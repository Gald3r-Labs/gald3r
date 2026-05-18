# g-template-export — Slim template export (gald3r_dev maintainers)

**gald3r_dev only** — not part of installable `G:/gald3r_ecosystem/gald3r_template_full`.

## Steps

1. From repo root, optionally sync parity: `.\scripts\platform_parity_sync.ps1 -Sync`
2. Dry-run: `.\scripts\export_slim_template_repo.ps1 -Destination '<PATH>'`
3. Apply: `.\scripts\export_slim_template_repo.ps1 -Destination '<PATH>' -Apply`
4. Read `<PATH>\MAINTAINER_EXPORT.md` for release + `git init` checklist.

## Flags

| Flag | Effect |
|------|--------|
| `-Apply` | Copy files (omit = list-only dry-run) |
| `-Force` | Skip parity gate (logs warning) |
| `-SkipParityCheck` | Do not run `platform_parity_check.ps1` |
| `-UseGald3rFullRootDocs` | Overlay repo-root README/CHANGELOG/LICENSE |

## Related

- `g-skl-git-commit` — conventional commits after export
- `scripts/platform_parity_check.ps1` — pre-export gate
