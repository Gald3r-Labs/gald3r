# scripts/ — User-facing gald3r tools

These scripts are shipped with gald3r and can be run in any gald3r-managed project.

> **D015 canonical-scripts pattern**: Framework scripts that are owned by a specific skill
> live inside that skill at `.gald3r_sys/skills/<skill>/scripts/`. This folder holds only
> scripts that are user-facing or shared across many skills.
>
> **Maintainer tooling** (gald3r_dev-only, not installed) lives in `custom_scripts/`.

---

## User-facing scripts (available in every installed gald3r project)

| Script | Purpose |
|---|---|
| `gald3r_clean_commit.bat` | Windows batch wrapper for clean git commits |
| `gald3r_worktree.ps1` | Agent-owned isolated git checkout helper (T170) |
| `mission-overnight.ps1` | Unattended g-mission runner for AFK / overnight sessions |

## Validation (also in `g-skl-setup/scripts/`)
```powershell
.\scripts\gald3r_validate.ps1   # verify gald3r installation
```
The canonical copy is now at `.gald3r_sys/skills/g-skl-setup/scripts/gald3r_validate.ps1`.
The root `scripts/` copy is kept for discoverability.

## tests/
Development tests for the scripts themselves. Not shipped.

---

## Where to find other scripts

| You're looking for... | Find it at |
|---|---|
| Workspace-Control guard helpers | `.gald3r_sys/skills/g-skl-workspace/scripts/` |
| Git commit/push gate | `.gald3r_sys/skills/g-skl-git-commit/scripts/` |
| Release & semver | `.gald3r_sys/skills/g-skl-release/scripts/` |
| Medic / doctor | `.gald3r_sys/skills/g-skl-medic/scripts/` |
| Muninn graph impact | `.gald3r_sys/skills/g-skl-muninn/scripts/` |
| Subsystem hierarchy | `.gald3r_sys/skills/g-skl-subsystems/scripts/` |
| Feature hierarchy | `.gald3r_sys/skills/g-skl-features/scripts/` |
| Copilot instruction gen | `.gald3r_sys/skills/g-skl-platform-copilot/scripts/` |
| Hook shared utilities | `.gald3r_sys/scripts/` |
| License templates | `.gald3r_sys/licenses/` |
| Maintainer tools | `custom_scripts/` |
