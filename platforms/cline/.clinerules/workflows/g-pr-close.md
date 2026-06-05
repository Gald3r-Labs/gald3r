---
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
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
3. **Detect fork PRs first (T1309):** `gh pr view <n> --json headRepositoryOwner,isCrossRepository`.
   If `isCrossRepository: true`, set `is_fork=1` and **skip** any head-branch write
   (head-ref label edits, pushes to the fork) — we lack write on a contributor's fork.
   Base-repo operations (comment, PR labels, merge) still proceed normally.
4. **On PASS:**
   - `g-skl-github-pr READY` (Draft → Ready). *(fork: skip if Ready requires head-branch write; comment instead.)*
   - `g-skl-github-pr COMMENT` — post the review summary (verdict + reviewer agent identity + review-result commit SHA).
   - `g-skl-github-pr CLOSE` — merge using `merge_strategy` (default `squash`); `--delete-branch` when configured.
     - **Merge queue (T1312):** when `merge_queue: enabled`, merge with `gh pr merge --auto <strategy-flag>`
       (queue the PR; GitHub merges when checks pass and the queue front is reached) instead of an
       immediate merge. If `gh` reports auto-merge/queue is unavailable on the repo plan, surface the
       error — do not silently fall back to an immediate merge.
   - Write `pr_status: merged` (or `pr_status: ready` while queued); auto-close the linked `issue_ref` when `auto_close_issue_on_merge: true`.
5. **On FAIL:**
   - `g-skl-github-pr COMMENT` — post the FAIL summary explaining the unmet criteria.
   - Leave the PR open as Draft (do **not** merge); keep `pr_status: draft`.
6. **Fork PRs (T1309) summary:** merge is allowed (base-repo permission); head-branch writes are
   skipped; comments/labels on the PR work. See `github_config.md` § "Forking workflow" and
   `branch_protection.md` § "For external contributors".

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
