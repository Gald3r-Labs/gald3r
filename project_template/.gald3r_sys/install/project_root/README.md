# Project root install bundle

Files here are merged into the **target project root** by `setup_gald3r_project.ps1` (step 3/5).

| File | Merge strategy |
|------|----------------|
| `GUARDRAILS.md` | add-if-missing |
| `WORKFLOW.md` | add-if-missing |
| `GALD3R-MIGRATION.md` | add-if-missing |
| `GALD3R-PROMPT.md` | add-if-missing |

**Canonical edit location:** `<gald3r_source>/project_template/.gald3r_sys/install/project_root/`

After edits, run:

```powershell
<ECOSYSTEM_ROOT>/<gald3r_source>/custom_scripts/platform_parity_sync.ps1 -SyncGaldSys -Sync
```

That sync propagates `.gald3r_sys/` (including this folder) and the `project_template/` payload to `<template_adv>`, `<template_full>`, `<template_slim>`, and `gald3r`.

`.gitignore`, `scripts/`, `temp_docs/`, and `temp_scripts/` remain at the `project_template/` payload root (not in this folder).
