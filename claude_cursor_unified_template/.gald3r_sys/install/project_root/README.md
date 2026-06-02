# Project root install bundle

Files here are merged into the **target project root** by `setup_gald3r_project.ps1` (step 3/5).

| File | Merge strategy |
|------|----------------|
| `GUARDRAILS.md` | add-if-missing |
| `WORKFLOW.md` | add-if-missing |
| `GALD3R-MIGRATION.md` | add-if-missing |
| `GALD3R-PROMPT.md` | add-if-missing |

**Canonical edit location:** `gald3r_templates/claude_cursor_unified_template/.gald3r_sys/install/project_root/`

After edits, run:

```powershell
G:/gald3r_ecosystem/gald3r_templates/custom_scripts/platform_parity_sync.ps1 -SyncGaldSys -Sync
```

That sync propagates `.gald3r_sys/` (including this folder) and the `claude_cursor_unified_template/` payload to `gald3r_template_adv`, `gald3r_template_full`, `gald3r_template_slim`, and `gald3r`.

`.gitignore`, `scripts/`, `temp_docs/`, and `temp_scripts/` remain at the `claude_cursor_unified_template/` payload root (not in this folder).
