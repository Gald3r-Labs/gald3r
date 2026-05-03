Alias for `@g-go-review --swarm`: $ARGUMENTS

Runs **verification only** in swarm mode — splits the `[🔍]` queue across M parallel
reviewer agents (round-robin). Includes both **tasks** and **bugs** awaiting verification.
Coordinator claims assigned items as `[🕵️]` / `verification-in-progress` before spawning
reviewers, skips non-expired verifier claims, and batch-writes TASKS.md and BUGS.md after
all reviewers complete. The coordinator also establishes one review isolation source per
bucket: a T170 `review-swarm` worktree for branch-addressable sources, or snapshot mode
for uncommitted checkout/worktree sources.
Review bucket agents return PASS/FAIL payloads, evidence, proposed Status History rows, and explicitly authorized fix-forward patches only. They must not write shared `.gald3r` files, changelog/docs, generated prompts, parity output, final staging, or commits.
The review-swarm coordinator creates a review-result commit after PASS or FAIL status writes by default. Do not stop at a commit offer when the commit is safe; commit the verdict. The only allowed non-commit blockers are unresolved conflicts, failed commit hooks, staged or untracked unrelated changes, detected secrets, dirty generated outputs not owned by review, missing user permission for destructive or out-of-scope changes, or repository state that prevents a safe commit.
Default source is the implementation checkpoint commit produced by `g-go-code` / `g-go --swarm`; review buckets should create clean `review-swarm` worktrees from that checkpoint. Use snapshot mode only when the handoff explicitly says the source is uncommitted, dirty, or non-branch-addressable.

This is exactly `@g-go-review --swarm`. Use this command for discoverability.

> ⚠️  **Run this in a NEW agent session** — different window, different invocation.
> If you implemented any of these tasks or bug fixes in this session, skip them.


### PCAC Inbox Gate (Before Claiming Work)

Before task claiming, implementation, verification, planning, or swarm partitioning, run the re-callable PCAC inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary.


### PCAC Inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the PCAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-pcac-read` before continuing.

## Usage

```
@g-go-review-swarm
@g-go-review-swarm tasks 14 15 16 17 18
@g-go-review-swarm bugs BUG-013 BUG-014
@g-go-review-swarm tasks 14 15 bugs BUG-013
```

All filter arguments pass through to `@g-go-review --swarm`.

See `@g-go-review` for full review protocol, verifier claim rules, review worktree/snapshot isolation, and swarm coordinator rules.

Ready to review.
