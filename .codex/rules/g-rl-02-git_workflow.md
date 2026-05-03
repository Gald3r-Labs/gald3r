---
description: "Git workflow conventions — commit message format and branch standards"
globs:
alwaysApply: false
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
| `/.gald3r_template/` | Root-level template copy (gitignored) |
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

## Branch Naming
- Feature: `feature/{task-id}-brief-description`
- Bug fix: `fix/{bug-id}-brief-description`
- Release: `release/v{major}.{minor}.{patch}`

## Windows (PowerShell)
```powershell
$msg = "feat(api): implement auth`n`nTask: #103`nPhase: 1"
git commit -m $msg
```

## Pre-Commit Sanity Check

Before every commit, run or rely on the **pre-commit sanity check** defined in `g-skl-git-commit` (PRE-COMMIT CHECKLIST section) and `/g-git-sanity`:

| Severity | Check | Action |
|----------|-------|--------|
| BLOCK | Secrets / API keys in staged diff | Fix before committing |
| BLOCK | `.env` file staged with values | Fix before committing |
| WARN | Staged files > 5 MB | Use Git LFS or .gitignore |
| WARN | `.gald3r/TASKS.md` / `tasks/` sync drift | Run `/g-task-sync-check` |

### Optional Automation (opt-in hook)

```powershell
git config core.hooksPath .cursor/hooks
git config --unset core.hooksPath
```

Hook file: `.cursor/hooks/g-hk-pre-commit.ps1`

## Pre-Push Gate (regular vs release)

Before `git push`, run **`scripts/gald3r_push_gate.ps1`** or `/g-git-push`:

| Mode | Trigger | CHANGELOG / docs |
|------|---------|------------------|
| **regular** | Default; interactive **N**; hook without `GALD3R_RELEASE_PUSH` | No changelog requirement — status and unpushed summary only (**never blocks**) |
| **release** | `-Release`; or `GALD3R_RELEASE_PUSH=1`; interactive **Y** | **Versioned** `## [x.y.z]` heading must exist in `CHANGELOG.md` (Keep a Changelog — not only `## [Unreleased]`). Override: `GALD3R_PUSH_GATE_OVERRIDE=1` |

Release mode also reminds you to re-read **README.md** and prints **version** lines from `pyproject.toml` / `package.json` if present (`g-rl-26`).

Shared scripts: `scripts/gald3r_push_gate.ps1`; `scripts/gald3r_git_sanity_common.ps1` (secret patterns for `g-hk-pre-commit.ps1`).

### Optional pre-push hook

Same opt-in `core.hooksPath` as pre-commit. Hook: `.cursor/hooks/g-hk-pre-push.ps1` — in hook mode, **release** checks run only when `GALD3R_RELEASE_PUSH=1`.
