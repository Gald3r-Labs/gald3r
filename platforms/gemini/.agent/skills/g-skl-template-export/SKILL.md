---
name: g-skl-template-export
description: gald3r_dev maintainer-only — verify 10-target parity then export G:/gald3r_ecosystem/gald3r_template_full to a clonable slim repo folder (PowerShell).
token_budget: medium
subsystem_memberships: [RELEASE_AND_VERSIONING]
---

# g-skl-template-export

**Audience**: **gald3r_dev source repo maintainers only.** This skill is **not** shipped inside installable `G:/gald3r_ecosystem/gald3r_template_full` (C-009 exception).

## When to use

- Cut a **slim consumer template** (e.g. `G:\gald3r`) from the external `G:/gald3r_ecosystem/gald3r_template_full` repo.
- Before a **public template release**, after `platform_parity_sync.ps1 -Sync` (or accept `-Force`).

## Workflow

1. **Optional**: `.\custom_scripts\platform_parity_sync.ps1 -Sync` so root + `G:/gald3r_ecosystem/gald3r_template_full` match.
2. **Dry-run** (default — no files written):
   ```powershell
   .\custom_scripts\export_slim_template_repo.ps1 -Destination 'G:\gald3r'
   ```
3. **Apply** copy + write `MAINTAINER_EXPORT.md`:
   ```powershell
   .\custom_scripts\export_slim_template_repo.ps1 -Destination 'G:\gald3r' -Apply
   ```
4. **Parity gate**: script runs `platform_parity_sync.ps1` (report-only — omit `-Sync`) unless `-SkipParityCheck` or `-Force`.
5. **Overlay monorepo docs** (optional): `-UseGald3rFullRootDocs` copies root `README.md`, `CHANGELOG.md`, `LICENSE` onto the destination after mirror.

## Safety

- Never deletes `G:/gald3r_ecosystem/gald3r_template_full`.
- Does not write unless `-Destination` is explicit and `-Apply` is set.
- Excludes `.git`, `node_modules`, `__pycache__`, `.venv` from mirror.

## Release notes

Open `MAINTAINER_EXPORT.md` in the destination for checklist: CHANGELOG version heading, `git init`, tag, `@g-git-commit`.

## Command

`@g-template-export` (Cursor) / `/g-template-export` (Claude) — same instructions.
