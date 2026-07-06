---
name: g-skl-git-commit
description: Create well-structured git commits following gald3r conventions, with proper type prefixes, task references, and clean trailers (no AI co-author footers per C-021).
token_budget: medium
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
# gald3r-git-commit

## When to Use
After completing a task, after any significant change, or @g-git-commit.

## Commit Message Format
```
{type}({subsystem}): {brief description}

{optional body — what changed and why}

Task: #{task_id}
Phase: {N}
```

## Commit Type Mapping
| Task Type | Commit Prefix |
|---|---|
| feature / task | `feat` |
| bug_fix | `fix` |
| refactor | `refactor` |
| documentation | `docs` |
| test | `test` |
| chore / config | `chore` |
| phase completion | `phase` |

## Steps

1. **Check what changed**:
   ```bash
   git status
   git diff --stat
   ```

2. **Stage relevant files**:
   ```bash
   git add .gald3r/tasks/taskNNN_*.md
   git add .gald3r/TASKS.md
   git add {changed source files}
   ```

3. **Compose message** using format above

4. **Trailers** (use these only — see CONSTRAINTS.md C-021):
   ```
   Task: #NNN
   Phase: N
   ```
   No `Agent:`, `Model:`, `Rules-Version:`, or `Co-Authored-By:` lines for AI agents. C-021 prohibits AI co-author attribution to keep commercial-licensing and acquisition IP records clean. Cursor IDE's built-in agent co-author footer setting must also be disabled by every operator.

4b. **GPG signing (T1310)**: read `gpg_signing:` from `.gald3r/config/AGENT_CONFIG.md`
   (default `disabled`). When `enabled`, add `-S` to the commit command.
   - Preflight: verify `git config user.signingkey` is set **and** `gpg` is on PATH
     (`gpg --version`). If either is missing, **STOP** with:
     `gpg_signing: enabled but GPG is not configured — set user.signingkey and install gpg, or set gpg_signing: disabled.`
     Do **not** fall back to an unsigned commit.
   - When `disabled`, omit `-S` (current behavior, unchanged).

5. **Commit** (add `-S` when `gpg_signing: enabled`):
   ```powershell
   git commit -m "$(cat <<'EOF'
   feat(api): implement task NNN
   
   Added JWT authentication middleware with refresh token support.
   
   Task: #103
   Phase: 1
   EOF
   )"
   ```
   
   On Windows PowerShell use single-line form or here-string carefully:
   ```powershell
   $msg = "feat(api): implement auth`n`nTask: #103`nPhase: 1"
   git commit -m $msg
   ```

## Phase Completion Commit
```bash
git add .gald3r/tasks/ .gald3r/TASKS.md
git commit -m "phase(N): Phase Name complete

Tasks completed: task001, task002, task003
Subsystems: api, database"

git tag phase-N-complete
```

---

## Pre-Commit Checklist

Before every commit, run through these checks. An optional `pre-commit` hook (`g-hk-pre-commit.py`) automates the block/warn items.

### Block (fix before committing)

| Check | What to look for |
|-------|-----------------|
| **Secrets** | Staged `.env` files with real values; API key patterns (`sk-`, `Bearer `, `AKIA`) in staged content |
| **Large binaries** | Staged files > 5 MB (use Git LFS or .gitignore) |
| **Empty commit message** | Commit message is blank or only whitespace |
| **Workspace boundary** | Staged paths are outside the active task/bug `workspace_repos`, use an unknown manifest repo ID, attempt member repo writes without compatible `workspace_touch_policy` and manifest permission, or combine separate workspace git roots into one commit |

### Warn (review before committing)

| Check | What to look for |
|-------|-----------------|
| **gald3r sync drift** | `.gald3r/TASKS.md` modified but individual `tasks/` files not staged (or vice versa) |
| **platform parity** | IDE config files modified in one target but not propagated (run `custom_scripts/platform_parity_sync.ps1` report-only — omit `-Sync`) |
| **CHANGELOG/release sync (C-023)** | `CHANGELOG.md` staged with new `## [x.x.x]` version headers that have no matching `.gald3r/releases/` file |

### CHANGELOG/Release Sync Check (C-023)

When `CHANGELOG.md` is staged (appears in `git diff --cached --name-only`):

1. Find all version headers added by the diff:
   ```powershell
   # PowerShell: find newly-added ## [x.x.x] lines in the staged diff
   git diff --cached -- CHANGELOG.md | Where-Object { $_ -match '^\+## \[[\d.]+\]' }
   ```
2. For each added version header (e.g., `## [1.5.0]`):
   a. Convert to filename fragment: `v1-5-0` (replace dots with dashes)
   b. Check: does `.gald3r/releases/` contain any file matching `*v1-5-0*`?
   ```powershell
   $files = Get-ChildItem .gald3r/releases/ -Filter "*v1-5-0*" -ErrorAction SilentlyContinue
   ```
   c. If NOT found: `WARN "C-023: CHANGELOG entry [1.5.0] has no matching .gald3r/releases/ file — run @g-release-new v1.5.0 to create it"`
3. **Severity**: warn-only (exit 0) — future hardening can escalate to block.
4. **Exemption**: `## [Unreleased]` headers are never flagged.

### Workspace-Control Commit Boundary

When `.gald3r/linking/workspace_manifest.yaml` is active, prepare commits inside each manifest repository independently. Review each repo's branch, dirty status, remotes, rollback target, and worktree context before committing. Do not stage or describe one cross-repo commit unless a later release orchestration task explicitly authorizes that flow.

### Gald3r Worktree Isolation Primitive (T170)

Use `gald3r worktree` for agent-owned isolated checkouts in the gald3r source repo. Installed templates also ship the same helper beside this skill at `gald3r worktree` and the peer IDE skill folders.

```powershell
# Report gald3r-owned worktrees for the current repo
gald3r worktree report

# Create or reuse a task worktree outside the active checkout
gald3r worktree create -TaskId 170 -Role code -Owner cursor

# Integration merge: fast-forward a task's code branch into the target (default main), then
# delete code+review branches and the worktree. Dry-run by default; -Apply to write. (T1443)
gald3r worktree merge -TaskId 170                            # dry-run plan (target main)
gald3r worktree merge -TaskId 170 -Apply                     # FF-merge + cleanup
gald3r worktree merge -SourceBranch feature/x -TargetBranch main -Json
```

### Worktree actions (`-Action`)

`Create` | `Report` | `Remove` | `Cleanup` | `Run` | `Cancel` | `CancelAll` | `Checkpoint` | `Resume` | `Steer` | `Queue` | `LockReport` | `Keep` | **`MergeToMain`**

- **`MergeToMain` (T1443 / BUG-099 recurrence prevention)**: fast-forward the task's code branch
  (resolved from worktree metadata, or `-SourceBranch`) into `-TargetBranch` (default `main`).
  **FF-only** — a target that cannot fast-forward is returned `merge-blocked` and is **never**
  force-updated. Dry-run by default (`would-merge` / `merge-blocked` / `noop` plan, read-only);
  `-Apply` performs the merge then deletes the code + review branches and the worktree. Refuses
  with `merge-skipped-dirty` if the main checkout has uncommitted paths. `-Json` for autopilot
  consumption. This is the helper that `g-go-go`'s per-PASS auto-merge step invokes.

- Default root is `$env:GALD3R_WORKTREE_ROOT` when set; otherwise `<repo-parent>/.gald3r-worktrees/<repo-name>`.
- Branches use `gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}`.
- The create path blocks when the active checkout is dirty unless the caller supplies `-AllowDirty` after recording explicit ownership in the owning task or bug `## Status History`.
- **`-AllowDirty` policy**: do not pass `-AllowDirty` for `g-go*`, `g-go-code*`, `g-go-review*`, or any `--swarm` coordinator flow unless every dirty path in **each git root in the active touch set** (orchestration + `workspace_repos` members and v2 expansions per `g-rl-33`) is owned exclusively by the active task or bug and a Status History row documents that override **for that root**. Otherwise clean those checkouts first (`g-rl-33` Clean Controller Gate).
- **Touch-set hygiene**: before creating worktrees for those flows, satisfy the Clean Controller Gate and Pre-Reconciliation Clean Gate in `g-rl-33` on **every root in the computed touch set** so checkpoint and review-result commits are not blocked by unrelated dirty state in any included repository.
- Cleanup is report-only unless `-Apply` is provided, and removal is limited to directories with `.gald3r-worktree.json` ownership metadata.
- When committing from a worktree, run `git status` and `git commit` from that worktree's repository root, not from the control checkout.

### Continuity Artifact & Session Resume (T967)

Long-horizon implementation work in a worktree can be interrupted by a crash, OOM, or power loss. To resume from the last clean state — rather than the conversation transcript — `gald3r worktree` writes a **continuity artifact** at each implementation checkpoint and exposes a `Resume` action that restores it as a context prefix. This is distinct from `gald3r worktree session` (which preserves the literal JSONL transcript): the continuity artifact is a structured *resume summary* (goal, completed/pending ACs, last tool summary, next action, blockers).

```powershell
# At each implementation checkpoint — write continuity_artifact.md + update marker.
# Run this BEFORE the checkpoint commit so the artifact survives a crash mid-commit.
gald3r worktree checkpoint -TaskId 967 -Role code -Owner cursor `
    -Goal "Add session resume to the worktree lifecycle" `
    -CompletedAcs "AC1 artifact write","AC2 marker fields" `
    -PendingAcs "AC3 resume read","AC4 resume banner" `
    -LastToolSummary "Edited gald3r worktree metadata schema" `
    -NextAction "Document --resume in g-go-code" `
    -CheckpointSha (git rev-parse HEAD)

# Resume after a crash — prints the banner + emits the artifact body as a context prefix.
gald3r worktree resume -TaskId 967 -Role code -Owner cursor
```

- **Marker fields (`.gald3r-worktree.json`)**: `Create` seeds `last_checkpoint_sha` and `continuity_artifact_path` as `null`; `Checkpoint` populates both (additive — existing fields preserved) plus a `continuity_updated_at` stamp.
- **Atomic durability**: the artifact is written to a unique sibling temp file, then `Move-Item -Force` renames it over `continuity_artifact.md` in one same-volume rename. An interrupt before the rename leaves the previous good artifact intact.
- **Write timing**: the artifact is written **before** the code-complete checkpoint commit (`g-go-code` step 7b), so a crash during the commit still leaves a resumable artifact on disk. `-CheckpointSha` may be supplied after the commit exists, or left blank when writing pre-commit (the artifact then records the SHA as pending).
- **Resume banner**: `Resume` reads the artifact, counts checked (`- [x]`) vs unchecked (`- [ ]`) AC lines, and prints `Resuming from checkpoint {sha} — {N} ACs complete, {M} remaining`. The full artifact body is returned as `context_prefix` (with `-Json`) for `g-go-code --resume` to inject.

### Session JSONL Capture & Cross-Sandbox Resume (T1124)

`gald3r worktree session` (mirrored beside `gald3r worktree` in each IDE skill folder) preserves the full Claude Code conversation thread from a worktree/sandbox so it can be resumed natively with `claude --resume`. This complements `memory_capture_session` (semantic summaries) — JSONL capture keeps the *literal* transcript, with `cwd` paths rewritten from the worktree to the host repo so resume works from any sandbox.

```powershell
# Dry-run: locate the worktree's session JSONL and report what would be captured
gald3r worktree session -Action Report -WorktreePath ..\.gald3r-worktrees\<gald3r_source>\T1124 -TaskId 1124

# Capture: copy + cwd-rewrite + record metadata (writes only with -Apply)
gald3r worktree session -Action Capture -Apply -WorktreePath ..\.gald3r-worktrees\<gald3r_source>\T1124 -TaskId 1124

# List captured sessions for a project, or resolve one to its resume command
gald3r worktree session -Action List
gald3r worktree session -Action Resolve -SessionId <session-id>
```

- **Path encoding**: Claude Code names each project folder by replacing every non-alphanumeric char in the absolute cwd with `-` (e.g. `<workspace>\<gald3r_source>` → `G--gald3r-ecosystem-gald3r-dev`). The helper reproduces this to find the worktree's session folder.
- **Locations** (overridable): source = `$env:CLAUDE_CONFIG_DIR\projects` or `~/.claude/projects`; captures land in `$env:GALD3R_SESSIONS_ROOT` or `~/.gald3r-sessions/<project_id>/<task_id>/<session_id>.jsonl`.
- **Metadata** is upserted to `~/.gald3r-sessions/<project_id>/sessions.json` (`session_id`, `task_id`, `timestamp`, `worktree_path`, `host_repo_path`, `host_jsonl_path`, `cwd_rewrites`).
- **cwd rewrite** replaces both JSON-escaped (`\\`) and raw worktree path forms with the host repo path across every line, so resumed sessions reference real host files.
- Capture is dry-run without `-Apply`; `-Json` emits a machine-readable result object for `g-go` orchestration.

### Manual Steps

```powershell
# Check for secrets in staged changes
git diff --cached | Select-String -Pattern 'sk-|Bearer |AKIA|password\s*=|api_key\s*='

# List large staged files
git diff --cached --name-only | ForEach-Object { (Get-Item $_).Length / 1MB } | Where-Object { $_ -gt 5 }

# Run gald3r sync check
@g-task-sync-check

# Run workspace-aware pre-commit gate
@g-git-sanity
```

### Hook (Optional)

An **opt-in** pre-commit hook script is available at `.cursor/hooks/g-hk-pre-commit.py`.

To enable in your local repo:
```powershell
git config core.hooksPath .cursor/hooks
```

To disable:
```powershell
git config --unset core.hooksPath
```

> The hook uses `soft-fail` for warnings (exit 0) and `hard-fail` for blocks (exit 1).

---

## Pre-Push gate (regular | release)

Before `git push`, run **`gald3r push-gate`** (or `@g-git-push`) so **routine** work is not blocked by release documentation rules, while **release** pushes enforce CHANGELOG/version discipline (`g-rl-26`, `g-rl-02`).

### Modes

| Mode | Trigger | What it does |
|------|---------|----------------|
| **regular** | Default; or hook without `GALD3R_RELEASE_PUSH` | Shows `git status`, unpushed commits, `.gald3r/` sync hint — **exit 0 always** |
| **release** | `-Release` flag; or `GALD3R_RELEASE_PUSH=1`; or interactive **Y** | Requires a **versioned** `## [x.y.z]` heading in `CHANGELOG.md` (Keep a Changelog). Prints README + `pyproject.toml` / `package.json` version hints. **Exit 1** if gate fails unless `GALD3R_PUSH_GATE_OVERRIDE=1` or interactive override |

### Commands

```powershell
gald3r push-gate                    # interactive mode select
gald3r push-gate -Release          # release checks
$env:GALD3R_RELEASE_PUSH='1'; gald3r push-gate -NonInteractive
gald3r push-gate -DryRun           # verify wiring; always exit 0
```

### Optional pre-push hook

`.cursor/hooks/g-hk-pre-push.py` — same opt-in `core.hooksPath` as pre-commit. In hook mode, **release** checks run only when `GALD3R_RELEASE_PUSH=1`.

### Shared script (DRY)

`.claude/skills/g-skl-git-commit/scripts/gald3r_git_sanity_common.py` supplies secret patterns for **`g-hk-pre-commit.py`**; push gate lives in **`gald3r push-gate`**.
---

## Push Modes

Every push should declare its intent — **regular** or **release**.

### Regular Push

Default for feature branches, WIP, and non-release work.

```powershell
git push                         # Regular push
@g-git-push regular              # Run pre-push checklist (regular mode)
```

- Shows status, unpushed commits, gald3r sync hint
- No CHANGELOG requirement

### Release Push

For tagging, version bumps, and public-facing doc updates.

```powershell
$env:GALD3R_RELEASE_PUSH = "1"
git push                         # Hook enforces release mode
@g-git-push release              # Run pre-push checklist (release mode)
```

Release checklist:
1. `CHANGELOG.md` — `[Unreleased]` must have content; move to versioned heading
2. `README.md` — review version badges and install steps
3. Version strings in `package.json` / `pyproject.toml` / `AGENTS.md`
4. After push → consider `@g-skl-gald3r-export` to publish slim template

### Push Hook (Optional)

```powershell
git config core.hooksPath .cursor/hooks   # Enable (also activates pre-commit hook)
git config --unset core.hooksPath         # Disable
```
---

## Cursor IDE Trailer Workaround (T804 / C-021)

Cursor's AI agent shell silently rewrites every `git commit ...` command issued from the agent to append a `Co-authored-by: Cursor <cursoragent@cursor.com>` trailer. The injection happens at the IDE shell layer (no git hook, no commit template, no git config) and is NOT bypassed by `--no-verify`, `-F <file>`, `--trailer "..."`, or `git commit --amend`. Even the lower-level `git commit-tree` invocation is rewritten by the interceptor.

Per CONSTRAINTS.md C-021 this trailer is forbidden. Use the helper:

```powershell
# Initial commit (no parent, fresh repo):
$msgFile = Join-Path $env:TEMP 'gald3r_msg.txt'
$msg | Set-Content -Path $msgFile -NoNewline -Encoding utf8
cmd.exe /c "scripts\gald3r_clean_commit.bat INITIAL `"$msgFile`""
Remove-Item $msgFile

# Follow-up commit (parented at HEAD):
$msgFile = Join-Path $env:TEMP 'gald3r_msg.txt'
$msg | Set-Content -Path $msgFile -NoNewline -Encoding utf8
cmd.exe /c "scripts\gald3r_clean_commit.bat FOLLOWUP `"$msgFile`""
Remove-Item $msgFile
```

The helper invokes `git write-tree` + `git commit-tree` + `git update-ref` from inside a child `cmd.exe` process — the IDE shell wrapper does not reach inside that subprocess to inject the trailer. Verify with `git cat-file -p HEAD` afterward.

The user should also disable Cursor's "AI as co-author" setting at the IDE level (it lives in Cursor settings, not in any project file). Both layers are required: the helper handles agent commits in this project; the IDE setting handles human commits and any other project.

