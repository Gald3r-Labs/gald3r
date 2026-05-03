# @g-gald3r-export — Export gald3r template to clonable repo

> **MAINTAINER TOOL** — gald3r_dev root only. Never propagated to gald3r_template_full/ or consumer installs.

Export `gald3r_template_full/` to a clean, clonable destination folder, guarded by a parity check.

---

## Usage

```
@g-gald3r-export                          # Guided walkthrough
@g-gald3r-export dest=G:\gald3r            # Dry-run to destination
@g-gald3r-export dest=G:\gald3r apply      # Real export
@g-gald3r-export dest=G:\gald3r apply docs # Export + overlay root README/CHANGELOG/LICENSE
@g-gald3r-export dest=G:\gald3r force      # Skip parity gate (adds warning note)
```

---

## Execution Protocol

### Step 1 — Parity Gate

Unless `force` argument is given:

```powershell
.\scripts\platform_parity_check.ps1
```

- Exit 0 → continue  
- Exit non-zero → **abort**; print:
  > "Parity gaps detected. Fix first:  
  > `.\scripts\platform_parity_sync.ps1 -Sync`  
  > Then re-run, or use `force` to override."

### Step 2 — Confirm Destination

Print the resolved destination path. If it already exists, note: "Destination exists — files will be merged/overwritten (non-destructive)."

Without `apply`: run in **dry-run mode** (lists files, writes nothing).

### Step 3 — Export

Invoke `export_slim_template_repo.ps1`:

```powershell
# Dry-run
.\scripts\export_slim_template_repo.ps1 -Destination <dest>

# Apply
.\scripts\export_slim_template_repo.ps1 -Destination <dest> -Apply

# Apply + root docs overlay
.\scripts\export_slim_template_repo.ps1 -Destination <dest> -Apply -UseGald3rFullRootDocs

# Force (skip parity)
.\scripts\export_slim_template_repo.ps1 -Destination <dest> -Apply -Force
```

### Step 4 — Release Checklist

After successful export, print or confirm the checklist from `MAINTAINER_EXPORT.md`:

1. `CHANGELOG.md` — move `[Unreleased]` to a versioned heading
2. `README.md` — review version badges / intro section
3. `git init` (if new repo):
   ```bash
   cd <dest>
   git init
   git add .
   git commit -m "chore: import gald3r template snapshot $(date +%Y-%m-%d)"
   ```
4. Tag: `git tag -a v{version} -m "Template release {version}"`
5. Push: `git remote add origin <url> && git push -u origin main`

### Step 5 — Summary

Print:
- Files copied (count)
- Destination path
- Whether root docs were overlaid
- Whether parity was clean or forced
- Suggested next command: `cd <dest> && git init`
