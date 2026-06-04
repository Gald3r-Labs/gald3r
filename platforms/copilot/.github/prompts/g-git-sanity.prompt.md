# @g-git-sanity — Pre-commit sanity check

Run a quick sanity check on staged changes before committing. Covers secrets detection, large files, gald3r sync drift, and Workspace-Control repo boundaries.

---

## Usage

```
@g-git-sanity          # Check all staged changes
@g-git-sanity secrets  # Secrets check only
@g-git-sanity size     # Large file check only
@g-git-sanity sync     # gald3r task sync check only
```

---

## Execution Protocol

### 1. Secrets Check (BLOCK)

```powershell
git diff --cached | Select-String -Pattern "sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9._-]{20,}|AKIA[A-Z0-9]{16}|password\s*=\s*\S+|api_key\s*=\s*\S+|secret\s*=\s*\S+"
```

If any match: **BLOCK** — print matching line(s) and halt. Do not proceed.

Also check staged filenames:
- `.env` or `.env.*` with actual content staged → BLOCK

### 2. Large File Check (WARN)

```powershell
git diff --cached --name-only | Where-Object { (Test-Path $_) -and ((Get-Item $_).Length -gt 5MB) }
```

If any file > 5 MB: **WARN** — list the file(s) and suggest adding to `.gitignore` or using Git LFS.

### 3. gald3r Sync Drift (WARN)

Check if `.gald3r/` is present and has pending drift:

```powershell
# TASKS.md staged but no tasks/ files staged?
$tasksMdStaged = (git diff --cached --name-only) -match "TASKS\.md"
$taskFilesStaged = (git diff --cached --name-only) -match "\.gald3r/tasks/"
```

If `TASKS.md` staged but no tasks/ files (or vice versa): **WARN** — suggest running `@g-task-sync-check`.

### 4. Workspace-Control Boundary Check (BLOCK)

If `.gald3r/linking/workspace_manifest.yaml` exists, compare staged paths from `git diff --cached --name-only` to the active task or bug routing metadata:

- Omitted `workspace_repos` means current repository only.
- Any staged path in a manifest repository not listed by the active task/bug is **BLOCK**.
- Any `workspace_repos` value not found in manifest `repositories[].id` is **BLOCK**.
- `docs_only` may stage documentation and `.gald3r/` metadata only; source changes are **BLOCK**.
- Controlled member repo writes require explicit `workspace_repos`, compatible `workspace_touch_policy`, authorization text, reviewed member git status/branch/remotes/worktree context, and manifest write permission.
- Commit readiness is per repository; do not stage a single cross-repo commit from the control project unless a later release orchestration task explicitly authorizes it.

If no active task or bug can be identified, print current-repo-only status and require the operator to run the relevant `g-task-upd` / `g-bug-upd` routing update before staging member repo changes.

### 5. Worktree Isolation Check (WARN/BLOCK)

If the active task has `worktree_path` metadata:

- Confirm `worktree_path` exists and is outside the active repository checkout.
- Confirm `worktree_branch` matches the current branch when running inside that worktree.
- Confirm `.gald3r-worktree.json` exists in the worktree root before cleanup or removal.
- Warn when the current checkout is dirty and no worktree metadata exists; coding/review workflows should create a worktree through the Gald3r worktree helper unless the task explicitly owns direct-root work.
- Block cleanup or removal of any directory that lacks gald3r ownership metadata.

### 6. Report

Print summary:

```
Pre-commit sanity check
=======================
Secrets:    PASS / BLOCK (N patterns matched)
Large files: PASS / WARN (N files > 5 MB)
gald3r sync: PASS / WARN (drift detected)
workspace:  PASS / BLOCK (repo boundary status)
worktree:   PASS / WARN / BLOCK (isolation status)
```

- Any BLOCK → exit with instruction to fix and re-run
- Only WARNs → print warnings and ask "Proceed anyway? (y/N)"

---

## Hook Integration

This check is also available as an automatic `pre-commit` hook:

```powershell
# Enable hook-based automation
git config core.hooksPath .cursor/hooks

# Disable
git config --unset core.hooksPath
```

Hook file: `.cursor/hooks/g-hk-pre-commit.ps1`

> Hook is soft-fail for WARNs (exit 0) and hard-fail for BLOCKs (exit 1).
