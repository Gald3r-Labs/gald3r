# License Templates

Canonical LICENSE and NOTICE templates used by every workspace member repository in `g:\gald3r_ecosystem\`. The license posture for each repository is recorded in `.gald3r/linking/workspace_manifest.yaml` under the per-repository `license:` key, and validated by `.gald3r_sys/skills/g-skl-workspace/.gald3r_sys/skills/g-skl-workspace/scripts/validate_workspace_members_gald3r.ps1`.

## Templates

| File | Used by |
|------|---------|
| `LICENSE_FSL_TEMPLATE.txt` | Public repos (FSL-1.1-Apache) |
| `LICENSE_PROPRIETARY_TEMPLATE.txt` | Private repos (all-rights-reserved) |
| `NOTICE_FSL_TEMPLATE.txt` | Public repos (companion to FSL LICENSE) |
| `NOTICE_PROPRIETARY_TEMPLATE.txt` | Private repos (companion to proprietary LICENSE) |

## Per-repo posture

Authoritative source: `g:\gald3r_ecosystem\LICENSING_STRATEGY.md` and `.gald3r/CONSTRAINTS.md` C-020.

| Repo | License |
|------|---------|
| `gald3r` (hero, public) | FSL-1.1-Apache |
| `gald3r_throne` (public) | FSL-1.1-Apache |
| `gald3r_template_slim` (public) | FSL-1.1-Apache |
| `gald3r_template_full` (public) | FSL-1.1-Apache |
| `gald3r_template_adv` (public) | FSL-1.1-Apache |
| `gald3r_dev` (private) | Proprietary |
| `gald3r_agent` (private) | Proprietary |
| `gald3r_discord` (private) | Proprietary |
| `gald3r_forge` (private) | Proprietary |
| `gald3r_terminal` (private) | Proprietary |
| `gald3r_valhalla` (private) | Proprietary |
| `gald3r_vault` (private) | Proprietary |
| `gald3r_web` (private) | Proprietary |
| `gald3r_world_tree` (private) | Proprietary |

## Apply

Replace `{REPO_NAME}` in NOTICE templates with the repo display name. The LICENSE templates are byte-identical across repos (no placeholders).

```powershell
# Example: apply proprietary license to a private repo
Copy-Item scripts\license_templates\LICENSE_PROPRIETARY_TEMPLATE.txt <repo>\LICENSE
(Get-Content scripts\license_templates\NOTICE_PROPRIETARY_TEMPLATE.txt) `
    -replace '\{REPO_NAME\}','gald3r_<name>' `
    | Set-Content <repo>\NOTICE
```
