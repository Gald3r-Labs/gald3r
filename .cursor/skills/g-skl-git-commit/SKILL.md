---
name: g-skl-git-commit
description: Create well-structured git commits following gald3r conventions, with proper type prefixes, task references, and agent footers for autonomous commits.
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

4. **For autonomous agent commits**, add footer:
   ```
   Task: #NNN
   Phase: N
   Agent: {agent_id}
   Model: {model_name}
   Rules-Version: {version}
   ```

5. **Commit**:
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

Before every commit, run through these checks. An optional `pre-commit` hook (`g-hk-pre-commit.ps1`) automates the block/warn items.

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
| **platform parity** | IDE config files modified in one target but not propagated (run `scripts/platform_parity_check.ps1`) |

### Workspace-Control Commit Boundary

When `.gald3r/linking/workspace_manifest.yaml` is active, prepare commits inside each manifest repository independently. Review each repo's branch, dirty status, remotes, rollback target, and worktree context before committing. Do not stage or describe one cross-repo commit unless a later release orchestration task explicitly authorizes that flow.

### Gald3r Worktree Isolation Primitive (T170)

Use `scripts/gald3r_worktree.ps1` for agent-owned isolated checkouts in the gald3r source repo. Installed templates also ship the same helper beside this skill at `.cursor/skills/g-skl-git-commit/scripts/gald3r_worktree.ps1` and the peer IDE skill folders.

```powershell
# Report gald3r-owned worktrees for the current repo
.\scripts\gald3r_worktree.ps1 -Action Report

# Create or reuse a task worktree outside the active checkout
.\scripts\gald3r_worktree.ps1 -Action Create -TaskId 170 -Role code -Owner cursor
```

- Default root is `$env:GALD3R_WORKTREE_ROOT` when set; otherwise `<repo-parent>/.gald3r-worktrees/<repo-name>`.
- Branches use `gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}`.
- The create path blocks when the active checkout is dirty unless the caller supplies `-AllowDirty` after recording explicit ownership.
- Cleanup is report-only unless `-Apply` is provided, and removal is limited to directories with `.gald3r-worktree.json` ownership metadata.
- When committing from a worktree, run `git status` and `git commit` from that worktree's repository root, not from the control checkout.

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

An **opt-in** pre-commit hook script is available at `.cursor/hooks/g-hk-pre-commit.ps1`.

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

Before `git push`, run **`scripts/gald3r_push_gate.ps1`** (or `@g-git-push`) so **routine** work is not blocked by release documentation rules, while **release** pushes enforce CHANGELOG/version discipline (`g-rl-26`, `g-rl-02`).

### Modes

| Mode | Trigger | What it does |
|------|---------|----------------|
| **regular** | Default; or hook without `GALD3R_RELEASE_PUSH` | Shows `git status`, unpushed commits, `.gald3r/` sync hint — **exit 0 always** |
| **release** | `-Release` flag; or `GALD3R_RELEASE_PUSH=1`; or interactive **Y** | Requires a **versioned** `## [x.y.z]` heading in `CHANGELOG.md` (Keep a Changelog). Prints README + `pyproject.toml` / `package.json` version hints. **Exit 1** if gate fails unless `GALD3R_PUSH_GATE_OVERRIDE=1` or interactive override |

### Commands

```powershell
./scripts/gald3r_push_gate.ps1                    # interactive mode select
./scripts/gald3r_push_gate.ps1 -Release          # release checks
$env:GALD3R_RELEASE_PUSH='1'; ./scripts/gald3r_push_gate.ps1 -NonInteractive
./scripts/gald3r_push_gate.ps1 -DryRun           # verify wiring; always exit 0
```

### Optional pre-push hook

`.cursor/hooks/g-hk-pre-push.ps1` — same opt-in `core.hooksPath` as pre-commit. In hook mode, **release** checks run only when `GALD3R_RELEASE_PUSH=1`.

### Shared script (DRY)

`scripts/gald3r_git_sanity_common.ps1` supplies secret patterns for **`g-hk-pre-commit.ps1`**; push gate lives in **`scripts/gald3r_push_gate.ps1`**.
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
4. After push → consider `@g-gald3r-export` to publish slim template

### Push Hook (Optional)

```powershell
git config core.hooksPath .cursor/hooks   # Enable (also activates pre-commit hook)
git config --unset core.hooksPath         # Disable
```