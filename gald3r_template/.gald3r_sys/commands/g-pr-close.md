Finalize a GitHub PR after review (merge on PASS / keep Draft on FAIL): $ARGUMENTS

Thin wrapper over **`g-skl-github-pr` READY/COMMENT/CLOSE** (T1289). Part of the
optional GitHub Integration Bundle.

## Gate (first)

Run the `g-skl-github-pr` gate. If `github_integration: disabled`, wrong `project_type`,
or `gh` missing → **no-op** with a friendly message.

## Behavior

1. Resolve task ID (`--task <id>` or active worktree / branch).
2. Read the review verdict from the most recent `## Status History` row of the task file:
   - `[✅]` / `verification-in-progress → completed` ⇒ **PASS**
   - `FAIL:` / back-to-`pending` ⇒ **FAIL**
3. **On PASS:**
   - `g-skl-github-pr READY` (Draft → Ready).
   - `g-skl-github-pr COMMENT` — post the review summary (verdict + reviewer agent identity + review-result commit SHA).
   - `g-skl-github-pr CLOSE` — merge using `merge_strategy` (default `squash`); `--delete-branch` when configured.
   - Write `pr_status: merged`; auto-close the linked `issue_ref` when `auto_close_issue_on_merge: true`.
4. **On FAIL:**
   - `g-skl-github-pr COMMENT` — post the FAIL summary explaining the unmet criteria.
   - Leave the PR open as Draft (do **not** merge); keep `pr_status: draft`.
5. **Fork-originated PRs (T1309)**: skip head-branch writes (no `gh pr ready` write-back, no `--delete-branch` on a fork); merge + comment from the base side normally.
6. **Merge queue (T1312)**: when `github_config.md` `merge_queue: enabled`, use `gh pr merge --auto` (queued — GitHub merges with the configured `merge_strategy` when checks pass and position is reached) instead of an immediate merge.

## Flags

| Flag | Effect |
|---|---|
| `--task <id>` | Explicit task ID |
| `--no-merge` | Comment + flip to Ready but skip the merge (manual merge desired) |
| `--strategy <squash\|rebase\|merge>` | Override the configured merge strategy |
| `--dry-run` | Print the plan without commenting/merging |

## Notes

- Auto-invoked by the `g-go-review` PR-close hook (T1292) after PASS/FAIL status writes,
  when `github_integration: enabled` and `github_pr_hooks: enabled`.
- Honors the Autonomous Push Gate (g-rl-33): a merge is outward-facing — confirm per
  pipeline policy; never merge silently.
- See `g-skl-github-pr` for the full operation contract.
