---
name: g-gald3r-export
description: >
  Export gald3r_template_full/ to a clonable slim gald3r template repo.
  MAINTAINER-ONLY — gald3r_dev root IDE trees only; never propagated to gald3r_template_full/.
---

# g-gald3r-export

> **MAINTAINER TOOL** — This skill exists only under gald3r_dev root IDE configs (`.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`). It is **never** copied into `gald3r_template_full/` nor propagated to consumer installs.

**Activate for**: "export template", "release gald3r", "make clonable", "export slim repo", "publish gald3r template"

---

## Overview

`g-gald3r-export` produces a **standalone, clonable folder** from `gald3r_template_full/` contents — ready for `git init`, commit, and release. It is the guarded publish path for shipping the gald3r framework to consumers.

**Script**: `scripts/export_slim_template_repo.ps1`

---

## Operation: EXPORT

### Pre-flight (mandatory unless `--force`)

1. **Run parity check** — invoke `scripts/platform_parity_check.ps1`
   - If any gaps → **abort** and print: "Parity gaps detected. Fix with: `.\scripts\platform_parity_sync.ps1 -Sync`   OR re-run with -Force"
   - If clean → proceed

2. **Confirm destination** — show `--dest` path and warn if it already exists (non-destructive; robocopy merges by default)

### Export

```powershell
# Dry-run (default — no files written)
.\scripts\export_slim_template_repo.ps1 -Destination <path>

# Apply (actually copies)
.\scripts\export_slim_template_repo.ps1 -Destination <path> -Apply

# With root docs overlay (README.md, CHANGELOG.md, LICENSE from gald3r_dev root)
.\scripts\export_slim_template_repo.ps1 -Destination <path> -Apply -UseGald3rFullRootDocs

# Skip parity check (not recommended for release)
.\scripts\export_slim_template_repo.ps1 -Destination <path> -Apply -Force
```

### Output

- `<dest>/` — full `gald3r_template_full/` tree (all IDE dirs, `.gald3r/`, docs)
- `<dest>/MAINTAINER_EXPORT.md` — release checklist, suggested git commands, parity note

### Release Checklist (generated in MAINTAINER_EXPORT.md)

1. Open `CHANGELOG.md` — move `[Unreleased]` items under a new version heading
2. Update version badges in `README.md` if present
3. `git init` → `git add .` → `git commit -m "chore: import gald3r template snapshot"`
4. Tag: `git tag -a v{version} -m "Template release"`
5. Use `@g-skl-git-commit` for conventional commit style on future changes

---

## Safety Guarantees

| Rule | Detail |
|------|--------|
| Default is dry-run | No files copied without `-Apply` |
| Never deletes gald3r_template_full | Source directory is read-only from this tool's perspective |
| Never writes to gald3r_dev root | Only writes to explicit `--dest` (outside gald3r_dev unless intentional) |
| Parity gate is default-on | Ensures consumers get consistent cross-IDE templates |
| gald3r_dev-only paths excluded | `docker/`, `skill_packs/`, monorepo scripts are never mirrored |

---

## Scope Boundary

This skill is intentionally **asymmetric** (C-009 exception):
- Lives in **root** IDE trees only
- **Never** in `gald3r_template_full/` — this would create a circular self-reference
- The "10-target parity" rule does **not** apply to this skill
