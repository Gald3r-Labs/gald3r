---
description: "Git workflow conventions — commit message format and branch standards"
globs:
alwaysApply: false
subsystem_memberships: [SECURITY_AND_COMPLIANCE]
---

# Git Workflow

## Commit Message Format
```
{type}({scope}): {brief description}

{optional body}

Task: #{id}
Phase: {N}
```

## Commit Types
| Type | Use For |
|---|---|
| `feat` | New feature or task |
| `fix` | Bug fix |
| `refactor` | Code refactor, no behavior change |
| `docs` | Documentation only |
| `test` | Tests only |
| `chore` | Config, build, maintenance |
| `phase` | Phase completion commit |

## Rules
- Subject line ≤ 72 characters
- Use imperative mood: "add" not "added" or "adds"
- Reference task ID in every task-related commit
- Never commit secrets, API keys, or passwords
- Run `git status` before committing to verify staged files

## Protected Files (NEVER commit these)

Before every `git add` or `git commit`, verify NONE of these are staged:

| Pattern | Why |
|---|---|
| `/.agent/` | Personal IDE config (gitignored) |
| `/.claude/` | Personal IDE config (gitignored) |
| `/.codex/` | Personal IDE config (gitignored) |
| `/.cursor/` | Personal IDE config (gitignored) |
| `/.opencode/` | Personal IDE config (gitignored) |
| `/.gald3r/` | Live project state (gitignored) |
| `/.project_template/` | Root-level template copy (gitignored) |
| `/temp_docs/` | Scratch files (gitignored) |
| `/temp_scripts/` | Scratch files (gitignored) |
| `/AGENTS.md` | Personalized per-user (gitignored) |
| `/CLAUDE.md` | Personalized per-user (gitignored) |
| `/GEMINI.md` | Personalized per-user (gitignored) |
| `/GUARDRAILS.md` | Personalized per-user (gitignored) |
| `/.env` | Secrets (gitignored) |
| `/.mcp.json` | Machine-specific MCP config (gitignored) |

If `git status` shows ANY of these as staged or untracked-to-be-added:
1. **STOP** — do not commit
2. Remove from staging: `git reset HEAD <file>`
3. Verify `.gitignore` still contains the entry
4. Warn the user that a protected file was almost committed

## Branch Model (feature-branches-only — NO long-lived `dev`/`test`)

gald3r uses a **single permanent branch (`main`) plus short-lived feature branches.** There is
**no long-lived `dev` or `test` branch**, and no `dev` -> `main` promotion dance. Long-lived
parallel branches were the root cause of repeated history-loss incidents (divergent merges,
`reset --hard` to resolve conflicts) and are retired.

- **`main`** — the only permanent branch. Always shippable.
- **`feature/{task-id}-brief-description`** — short-lived; branch off `main`, merge back to `main`, delete.
- **`fix/{bug-id}-brief-description`** — short-lived bug-fix branch; same lifecycle.
- **`release/v{major}.{minor}.{patch}`** — optional short-lived release-staging branch; merges to `main`.
- **Gald3r agent worktree**: `gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}` (ephemeral).

**Forbidden**: creating or pushing to a long-lived `dev` or `test` branch; `git push origin dev`;
resolving `dev`/`main` divergence with `reset --hard`. Staging of work-in-progress happens on
feature branches (or, for the distribution pipeline, in staged *folders*), never on a parallel
long-lived integration branch.

## Worktree Isolation

Use `scripts/gald3r_worktree.ps1` as the shared primitive for agent-owned worktrees in the gald3r source repo. Installed templates also include the same helper in the `g-skl-git-commit/scripts/` skill directory for each IDE target.

- Default root: `$env:GALD3R_WORKTREE_ROOT`, or `<repo-parent>/.gald3r-worktrees/<repo-name>` when unset.
- Never create worktrees inside the active repository checkout.
- `Create` blocks on a dirty active checkout unless an explicit `-AllowDirty` override is used after recording ownership.
- For `g-go*`, `g-go-code*`, `g-go-review*`, and `--swarm` flows, follow `g-rl-33` **Clean Controller Gate** and **Pre-Reconciliation Clean Gate** on the **computed touch set** of git roots (orchestration + manifest members from `workspace_repos:` and v2 expansions per `g-rl-33`) before claims, worktrees, and coordinator shared writes; do not use `-AllowDirty` there except with documented task/bug ownership in `## Status History` **per root** that policy allows.
- Task claims created from worktrees should record `worktree_path`, `worktree_branch`, `worktree_created_at`, and `worktree_owner`.
- Cleanup is report-only unless `-Apply` is provided and may remove only directories with `.gald3r-worktree.json` ownership metadata.

## Windows (PowerShell)
```powershell
$msg = "feat(api): implement auth`n`nTask: #103`nPhase: 1"
git commit -m $msg
```

## Pre-Commit Sanity Check

Before every commit, run or rely on the **pre-commit sanity check** defined in `g-skl-git-commit` (PRE-COMMIT CHECKLIST section) and `@g-git-sanity` command:

| Severity | Check | Action |
|----------|-------|--------|
| BLOCK | Secrets / API keys in staged diff | Fix before committing |
| BLOCK | `.env` file staged with values | Fix before committing |
| WARN | Staged files > 5 MB | Use Git LFS or .gitignore |
| WARN | `.gald3r/TASKS.md` / `tasks/` sync drift | Run `@g-task-sync-check` |

### Optional Automation (opt-in hook)

```powershell
# Enable hook-based pre-commit checks
git config core.hooksPath .cursor/hooks

# Disable
git config --unset core.hooksPath
```

Hook file: `.cursor/hooks/g-hk-pre-commit.ps1`

## Pre-Push Gate (regular vs release)

Before `git push`, run **`.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1`** or `@g-git-push`:

| Mode | Trigger | CHANGELOG / docs |
|------|---------|------------------|
| **regular** | Default; interactive **N**; hook without `GALD3R_RELEASE_PUSH` | No changelog requirement — status and unpushed summary only (**never blocks**) |
| **release** | `-Release`; or `GALD3R_RELEASE_PUSH=1`; interactive **Y** | **Versioned** `## [x.y.z]` heading must exist in `CHANGELOG.md` (Keep a Changelog — not only `## [Unreleased]`). Override: `GALD3R_PUSH_GATE_OVERRIDE=1` |

Release mode also reminds you to re-read **README.md** and prints **version** lines from `pyproject.toml` / `package.json` if present (`g-rl-26`).

Shared scripts: `.claude/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1`; `.claude/skills/g-skl-git-commit/scripts/gald3r_git_sanity_common.ps1` (secret patterns for `g-hk-pre-commit.ps1`).

### Optional pre-push hook

Same opt-in `core.hooksPath` as pre-commit. Hook: `.cursor/hooks/g-hk-pre-push.ps1` — in hook mode, **release** checks run only when `GALD3R_RELEASE_PUSH=1`.