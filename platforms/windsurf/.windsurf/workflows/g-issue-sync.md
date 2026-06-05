---
subsystem_memberships: [VAULT_AND_RESEARCH]
---
Two-way sync between gald3r tasks and GitHub Issues: $ARGUMENTS

Wraps **`g-skl-github-pr LINK_ISSUE`** plus issue read/update logic (T1290). Part of
the optional GitHub Integration Bundle. Lets either side — a teammate in the GitHub
UI or an agent in gald3r — drive the work without losing the other side's edits.

## Gate (first)

Run the `g-skl-github-pr` gate. If `github_integration: disabled`, wrong `project_type`,
or `gh` missing → **no-op** with a friendly message.

## Modes

| Invocation | Action |
|---|---|
| `g-issue-sync pull` | Fetch open issues; create a gald3r task for any without a matching `issue_ref`. |
| `g-issue-sync push` | Push open tasks (`[📋]`/`[🔄]`) without `issue_ref` as new GitHub Issues. |
| `g-issue-sync update <task_id>` | Sync one task's state to its linked issue. |
| `g-issue-sync` (no args) | Interactive triage of new + changed items. |

## Field mapping

- `task.title` ↔ `issue.title`
- `task.priority` ↔ label `priority:high|medium|low`
- `task.type` ↔ label `type:feature|bug_fix|…`
- `task.status` ↔ issue state (open/closed) + label `status:awaiting-verification` etc.
- task body ←→ issue body (one direction per sync; never round-trip the same edit)

## Conflict resolution

1. Compare `task.last_synced_at` (frontmatter) against `issue.updated_at`.
2. Newer side wins **by default**.
3. If **both** changed since the last sync → surface the diff to the user and
   **never auto-overwrite** without confirmation.

## Flags

| Flag | Effect |
|---|---|
| `--dry-run` | Show the sync plan without writing either side |
| `--repo <owner/name>` | Override `github_repo` |
| `--label-filter <label>` | Only sync issues carrying this label |
| `--no-create` | Update only; never create new tasks/issues |

## Notes

- New PCAC/issue-derived tasks follow normal `g-skl-tasks` CREATE rules; populate
  `issue_ref`, `integration_scope: github`, and `last_synced_at`.
- Edge cases to handle: issue closed externally while task is `[🔄]`; task cancelled
  while issue still open; issue reopened. Surface, don't silently diverge.
- See `g-skl-github-pr` for the issue-link operation contract.
