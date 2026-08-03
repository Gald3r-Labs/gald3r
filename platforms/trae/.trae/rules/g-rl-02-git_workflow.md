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

## Protected Files (secrets — NEVER commit these, in any repo)

Before every `git add` or `git commit`, verify NONE of the following are staged. Secrets are
the one category that is **always** forbidden, regardless of repo type:

| Pattern | Why |
|---|---|
| `.env`, `*.env.local` | Live credentials |
| `/.mcp.json` (when it carries real keys/tokens, not just server config) | Machine-specific MCP config that can leak secrets |
| Any file containing API keys, tokens, passwords, or private-key material | Secrets |

**Enforcement mechanism**: this is a pre-commit **secret scan**, not a hand-maintained path
list. Run `@g-git-sanity` or rely on the pre-commit sanity check below, which is backed by the
shared secret patterns in `gald3r_git_sanity_common.py` (`sk-`, `Bearer `, `AKIA`,
`password\s*=`, `api_key\s*=`, etc. — see `g-skl-git-commit` Pre-Commit Checklist). If a secrets
check fires on staged content:
1. **STOP** — do not commit
2. Remove from staging: `git reset HEAD <file>`
3. Verify `.gitignore` still contains the entry (if the file should never be tracked at all)
4. Warn the user that a secret was almost committed

### IDE / coordination paths (`.gald3r/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, etc.) — tracked or ignored is per-repo, not a fixed list

`.gald3r/`, `.claude/`, `.cursor/`, `.codex/`, `.opencode/`, `.agent/`, `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`, `GUARDRAILS.md`, and similar IDE/coordination paths are **NOT** universally
"never commit." Whether each one is tracked or gitignored depends on the repo's role — **defer
to that repo's actual `.gitignore`**, never to a hardcoded list in this rule:

- **Distributed / template repos** (e.g. a public template that end users install gald3r into)
  typically gitignore these paths — they are personalized-per-user or IDE-tool-managed payload,
  not authored source.
- **Controller / WPAC-linked repos** (this repo, `gald3r_core_dev`, included) INTENTIONALLY
  TRACK `.gald3r/` — the coordination data (tasks, bugs, plans, constraints, subsystem specs,
  idea board, WPAC topology) IS the value of the repo. Committing it is correct, not a mistake.
  See `g-rl-33`'s **`.gald3r/` Gitignore Gate**: adding `.gald3r/` to `.gitignore` in a
  controller/WPAC repo requires an explicit warning and user confirmation — it is never done
  silently, and it is never assumed to already be the case.

Before treating a path as "protected," check what the repo actually does:
```bash
git check-ignore -v <path>   # non-empty output = ignored; empty output = tracked
```
If `git status` shows an intentionally-tracked coordination path as staged, that's expected —
do not block the commit. If a path the repo's `.gitignore` says should be ignored shows up as
staged, that's drift: reconcile against `.gitignore` (or ask whether the ignore rule itself is
stale), not by refusing the commit against a fixed list.

### Scratch / working directories (`temp_docs/`, `temp_scripts/`)

`temp_docs/` and `temp_scripts/` are **scratch, never source** — working files that are
gitignored by convention and must not be committed. This is the explanation the repo's own
`.gitignore` points back to. Unlike the IDE/coordination paths above, these are *not*
per-repo-tracked: they are transient scratch everywhere. Put durable docs under `docs/` and
durable scripts in their proper package location instead.

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

Use `gald3r worktree` as the shared primitive for agent-owned worktrees in the gald3r source repo. Installed templates also include the same helper in the `g-skl-git-commit/scripts/` skill directory for each IDE target.

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
# Enable hook-based pre-commit checks. Use .githooks -- it is the only
# directory git's core.hooksPath mechanism actually invokes end-to-end here.
# Pointing core.hooksPath at .claude/hooks or .cursor/hooks is a NO-OP: git
# only ever calls a file literally named `pre-commit` (no extension), and
# neither of those directories ships one -- only the .py hook itself, which
# git never calls directly (BUG-401).
git config core.hooksPath .githooks

# Disable
git config --unset core.hooksPath
```

Dispatcher: `.githooks/pre-commit` (T293) runs, in sequence: encoding-normalize,
component-tag-check (g-rl-38), golden-fixture-baseline-freshness (T446), then the
pre-commit sanity hook itself (secrets/protected-files/stub-annotation/validate-gate/
org-policy) -- `.claude/hooks/g-hk-pre-commit.py` or `.cursor/hooks/g-hk-pre-commit.py`,
whichever exists on disk (BUG-401 wired this last stage in; it previously never ran
via any documented activation path).

**Required step after editing this dispatcher's own hook source (T529):** the
dispatcher above calls the LOCAL `.claude/hooks/`/`.cursor/hooks/` copy directly, never
`src/gald3r_core/platform/pipeline/neutral_source/hooks/` -- and both `.claude/` and
`.cursor/` are gitignored in this repo (framework-managed, not authored source), so a
`neutral_source/` hook fix silently never protects this repo's own commits until the
local copies are redeployed. An ad hoc manual file copy is untracked and does not
survive a fresh worktree/clone (BUG-538/BUG-541). Run `uv run gald3r sync --apply`
(or `uv run gald3r sync` first for a dry-run added/changed/identical/orphaned drift
summary) immediately after any `neutral_source/` hooks (or commands/rules/agents/
skills) edit -- this replaces the old manual-copy workaround. See `AGENTS.md`'s
Parity Model section for the full rationale and the companion `gald3r platform
install` verb (which additionally handles MCP + root-doc provisioning for an
EXTERNAL project -- `gald3r sync` deliberately never touches either, since this
repo's own `.mcp.json`/`AGENTS.md`/`CLAUDE.md` are live, not generated stubs).

## Pre-Push Gate (regular vs release)

Before `git push`, run **`gald3r push-gate`** or `@g-git-push`:

| Mode | Trigger | CHANGELOG / docs |
|------|---------|------------------|
| **regular** | Default; interactive **N**; hook without `GALD3R_RELEASE_PUSH` | No changelog requirement — status and unpushed summary only (**never blocks**) |
| **release** | `-Release`; or `GALD3R_RELEASE_PUSH=1`; interactive **Y** | **Versioned** `## [x.y.z]` heading must exist in `CHANGELOG.md` (Keep a Changelog — not only `## [Unreleased]`). Override: `GALD3R_PUSH_GATE_OVERRIDE=1` |

Release mode also reminds you to re-read **README.md** and prints **version** lines from `pyproject.toml` / `package.json` if present (`g-rl-26`).

Shared scripts: `gald3r push-gate`; `.claude/skills/g-skl-git-commit/scripts/gald3r_git_sanity_common.py` (secret patterns for `g-hk-pre-commit.py`).

### Optional pre-push hook

Same opt-in `core.hooksPath` as pre-commit. Hook: `.cursor/hooks/g-hk-pre-push.py` — in hook mode, **release** checks run only when `GALD3R_RELEASE_PUSH=1`.