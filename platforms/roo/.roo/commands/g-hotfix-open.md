---
subsystem_memberships: [BUG_AND_QUALITY]
---
Open an urgent hotfix branch + task from the latest release tag: $ARGUMENTS

Hotfix workflow command (T1307). Branches from the latest release tag, scaffolds a
`type: hotfix` task, allocates a T170 worktree, and optionally opens a Draft PR. Part of
the GitHub Integration Bundle (`project_type=software_development`), but the branch/task/
worktree scaffolding works even when `github_integration: disabled` (only the PR step is gated).

## Behavior

1. **Resolve base tag**: `git describe --tags --abbrev=0` (or `--from-tag <tag>`).
2. **Create branch**: `hotfix/{tag}-{slug}` cut from that tag (not from `main`).
3. **Scaffold task** via `g-skl-tasks` CREATE TASK:
   - `type: hotfix`, `priority: high` (or `critical` if stated).
   - `target_branches: [main]` (add `develop` when a `develop` branch exists — Gitflow).
   - `--description <text>` populates the objective.
4. **Allocate worktree**: `gald3r_worktree.py -Action Create` on the hotfix branch (records
   `worktree_branch`, `worktree_owner`, etc. in the task frontmatter).
5. **Optional Draft PR**: if `github_integration: enabled` and not `--no-pr`, invoke
   `g-pr-open --task <id>` (base = `main`).
6. **Cherry-pick guidance**: print the post-merge step — after the hotfix merges to `main`,
   cherry-pick the fix commit(s) onto `develop` (if Gitflow) so the fix isn't lost on the next
   release: `git checkout develop && git cherry-pick <sha>...`.

## Flags

| Flag | Effect |
|---|---|
| `--from-tag <tag>` | Override the base tag (default: latest `git describe`) |
| `--no-pr` | Skip the auto Draft-PR open even when integration is enabled |
| `--description <text>` | Task description / objective |

## Notes

- `hotfix/*` branches are exempt from the "require branches up to date" rule in
  `.gald3r/config/branch_protection.md` (T1295) for speed; they still require PR + checks.
- Cherry-pick to `develop` is **guidance only** — the command never force-pushes or
  cherry-picks automatically (Autonomous Push Gate, g-rl-33).
- Helper logic lives in `g-skl-github-pr` (HOTFIX scaffolding).
