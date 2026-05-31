---
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
Open a Draft GitHub PR for the active task: $ARGUMENTS

Thin wrapper over **`g-skl-github-pr OPEN`** (T1288). Part of the optional GitHub
Integration Bundle — gated on `project_type=software_development` + `github_integration`.

## Gate (first)

Run the `g-skl-github-pr` gate. If `github_integration: disabled` (default), or
`project_type` is not `software_development`, or `gh` is not installed → **no-op**
with a friendly message; do not push or call the network.

## Behavior

1. Resolve the task ID:
   - `--task <id>` flag if given, else
   - read the active worktree's `.gald3r-worktree.json` (`task_id`), else
   - infer from the current branch name (`gald3r/{task_id}/...`).
2. Push the current branch to `origin` if not already pushed (`git push -u origin <branch>`).
3. Call `g-skl-github-pr OPEN`:
   - PR title from `github_config.md` `pr_title_format` (default `{type}(T{id}): {title}`).
   - PR body from `## Objective`, `## Acceptance Criteria`, `## Handoff Report` of the task file.
   - Labels: one from `task.type` (feature→enhancement, bug_fix→bug, …) plus `gald3r/auto`.
   - Open as Draft unless `--ready`.
4. Write back `pr_url:` and `pr_status: draft` (or `ready`) + `integration_scope: github`
   to the task frontmatter.

## Stacked PR routing via task dependencies (T1303)

gald3r task `dependencies:` already encode stack order. Before choosing the PR base branch:

1. Read `dependencies:` from the task frontmatter.
2. For each dependency, check whether it has an **open PR** (`pr_url` set **and**
   `pr_status` ∈ {`draft`, `ready`}).
3. Route the base branch:
   - **Exactly one** dependency has an open PR → target **that PR's head branch** (stack on it).
   - **Multiple** dependencies have open PRs → **error** with a diagnostic listing them:
     `Ambiguous stack base: deps T<a>, T<b> both have open PRs. Re-run with --target <branch>.`
   - **Zero** → target `main` / `github_default_branch` (default behavior).
4. `--target <branch>` always overrides this routing.
5. Print the resolved stack chain at open time, e.g. `task1303 → task1288 → main`.

This converts the existing dependency graph into automatic stacked PRs with no extra metadata.

## Flags

| Flag | Effect |
|---|---|
| `--task <id>` | Explicit task ID instead of worktree-detected |
| `--ready` | Open as Ready for review instead of Draft |
| `--target <branch>` | Override base branch (overrides stacked-PR routing, T1303) |
| `--dry-run` | Print the plan (title, body, labels, base, stack chain) without pushing or creating |

## Notes

- Auto-invoked by the `g-go` PR-open hook (T1291) on `[🔄]→[🔍]` when
  `github_integration: enabled` and `github_pr_hooks: enabled`.
- Honors the Autonomous Push Gate (g-rl-33): the push/PR-create is outward-facing —
  surface and confirm per pipeline policy; never push silently.
- See `g-skl-github-pr` for the full operation contract.
