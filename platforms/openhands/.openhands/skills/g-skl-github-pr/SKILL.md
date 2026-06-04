---
name: g-skl-github-pr
description: GitHub PR/issue lifecycle for software_development projects — open/ready/comment/close PRs, link issues. Gated on github_integration; no-op when disabled. gh-CLI transport.
token_budget: medium
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
# g-skl-github-pr

The operational core of the **GitHub Integration Bundle** (T1287). The thin
`g-pr-open` / `g-pr-close` / `g-issue-sync` commands (T1288–T1290) and the
`g-go` / `g-go-review` PR hooks (T1291/T1292) all route through these operations.

## When to Use

A `g-pr-*` / `g-issue-*` command runs, or a `g-go`/`g-go-review` PR hook fires,
on a `project_type=software_development` project with GitHub integration on.

## Gate (run FIRST, every operation)

1. Read `.gald3r/.identity` `project_type=`. If not `software_development` → no-op:
   `GitHub integration applies only to software_development projects (current: <type>).`
2. Read `.gald3r/config/AGENT_CONFIG.md` `github_integration:`.
   - `disabled` → no-op: `GitHub integration is disabled. Enable in AGENT_CONFIG.md (github_integration: enabled|manual).`
   - `manual` → run only when invoked by a `g-pr-*`/`g-issue-*` command directly, **never** from a `g-go` hook.
   - `enabled` → proceed (hooks allowed when `github_pr_hooks: enabled`).
3. Resolve `github_repo` from `github_config.md` `repo:`, else auto-detect from
   `git remote -v` origin (parse `github.com[:/ ]<owner>/<repo>(.git)`).
4. Verify `gh` is installed (`gh --version`). If missing → no-op:
   `Install gh CLI: https://cli.github.com/`.

All operations accept `--json` for machine-parseable output and emit a single
JSON object: `{ "op": ..., "ok": true|false, "skipped": <reason|null>, ... }`.

## Operations

### OPEN
Open a Draft PR for the task's branch.
1. Resolve the task's branch (`worktree_branch` in frontmatter, else current branch).
2. Push the branch: `gh` requires it on the remote — `git push -u origin <branch>`.
3. Build title from `github_config.md` `pr_title_format` (default `{type}(T{id}): {title}`).
4. Build body from `pr_body_template` (default built-in: Summary, Task link, ACs,
   Test plan) populated from the task file's Objective + Acceptance Criteria.
5. `gh pr create --draft --base <default_branch> --head <branch> --title … --body-file …`
   (`--draft` only when `open_as_draft: true`).
6. Apply labels from task type when `labels_from_task_type: true` (see github_config map).
7. Request reviewers when `reviewer_auto_request: true`.
8. Write back to the task file: `pr_url:`, `pr_status: draft`, `integration_scope: github`.

### READY
Flip Draft → Ready when the task reaches `[🔍]` awaiting-verification.
1. `gh pr ready <pr_url>`.
2. Write `pr_status: ready` to the task file.

### COMMENT
Post a review summary as a PR comment (called when `g-go-review` completes).
1. `gh pr comment <pr_url> --body-file <review-summary>`.
2. Include verdict (PASS/FAIL), criteria results, and the review-result commit SHA.

### CLOSE
Merge or close the PR per the review verdict.
- **PASS** → `gh pr merge <pr_url> --<merge_strategy>` (squash|rebase|merge);
  `--delete-branch` when `delete_branch_on_merge: true`. Write `pr_status: merged`.
  When `auto_close_issue_on_merge: true` and `issue_ref` is set, the merge closes it
  (use `Closes #N` in the PR body) or `gh issue close <issue_ref>`.
- **FAIL / abandon** (`--close`) → `gh pr close <pr_url>`. Write `pr_status: closed`.

### STATUS
Read the current PR state without mutating.
1. `gh pr view <pr_url> --json state,isDraft,mergeable,baseRefName,statusCheckRollup`.
2. Map to `draft | ready | merged | closed | checks-failing`. Return; do not write
   unless invoked with `--sync` (then reconcile `pr_status` in the task file).

**Orphaned stacked base detection (T1304)** — when a PR's `baseRefName` is a
dependency's branch (stacked PR, see g-pr-open T1303) and that base no longer exists
(the dep was merged + branch deleted, or the dep PR was closed):
- **Dep merged cleanly** → GitHub auto-rebases the stack onto the new base; STATUS reports `rebased-onto-main`, no action.
- **Dep merged with squash (branch deleted)** → base is orphaned. Re-target the PR to `main`/`github_default_branch` (`gh pr edit <pr_url> --base <default>`), then attempt `git rebase` onto the new base.
  - Clean rebase → report `re-targeted-to-main`.
  - **Rebase conflicts** → do **NOT** auto-resolve. Post a PR comment describing the conflict + leave the branch as-is, and surface a `⚠️ stacked PR T<id> needs manual rebase onto main` notice. The user resolves.
- **Dep PR closed without merge** → the stacked PR is orphaned with no merged base. Surface the situation and **offer** (never auto-do) either re-target to `main` or close the stacked PR. Always inform before any destructive action.

`--sync` is required before any re-target/rebase write; bare STATUS is read-only.

### LINK_ISSUE
Create or link a GitHub Issue from a task (called by `g-issue-sync`).
1. If `issue_ref` already set → `gh issue view <issue_ref>` to confirm it exists; done.
2. Else create: `gh issue create --title "{title}" --body … --label …`, capture `#N`.
3. Write `issue_ref: "#N"`, `integration_scope: github` to the task file.

### HOTFIX (T1307)
Scaffold an urgent hotfix (called by `@g-hotfix-open`). The branch/task/worktree steps run
even when integration is disabled; only the Draft-PR step is gated.
1. Resolve base tag (`git describe --tags --abbrev=0` or `--from-tag`).
2. Create branch `hotfix/{tag}-{slug}` from that tag.
3. CREATE TASK `type: hotfix`, `target_branches: [main(, develop)]`, allocate a T170 worktree.
4. If integration enabled and not `--no-pr` → OPEN a Draft PR (base `main`).
5. Emit cherry-pick-to-`develop` guidance (never auto cherry-pick / force-push).

## Safety

- Never pushes or opens network calls when the gate fails (disabled / wrong type / no `gh`).
- Reads `github_config.md` for all behavior knobs; falls back to built-in defaults if absent.
- All task-file writes are limited to the five GitHub fields (T1285); never touches
  `status:` or other frontmatter.
- Honors the Autonomous Push Gate (g-rl-33): when called from a hook, `git push` /
  `gh pr create` count as outward-facing — surface and confirm per pipeline policy
  rather than pushing silently.

## Helpers

Non-trivial logic (repo auto-detect, body templating) may live in
`g-skl-github-pr/scripts/`. Phase 1 ships the contract; `gh` CLI does the work.

## Parity

Canonical source: `.gald3r_sys/skills/g-skl-github-pr/`. Propagated to platform
mirrors (`.cursor/`, `.claude/`, `.agent/`, …) and template repos via the
controller parity sync (`platform_parity_sync.ps1 -ApplyFromRoot` / `-SyncGaldSys`,
T1284 / T1294).
