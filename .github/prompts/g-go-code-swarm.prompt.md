Alias for `@g-go-code --swarm`: $ARGUMENTS

Runs **implementation only** in swarm mode — partitions the work queue into conflict-safe
buckets and spawns N parallel agents. Every completed item is marked `[🔍]`.

This is exactly `@g-go-code --swarm`. Use this command for discoverability.
If swarm eligibility leaves exactly one runnable item after workspace preflight, auto-downgrade to standard `@g-go-code` mode and continue without asking. If workspace preflight fails because the target repo is not registered, is not a git root, or is not authorized for the task/bug routing metadata, stop with that blocker instead of offering fallback.
The coordinator must create or reuse one T170 coding worktree per bucket before spawning
implementation agents, then reconcile bucket outputs back into the primary checkout one at a time.
The coordinator must skip non-expired `[📝]` speccing claims before partitioning and log stale speccing-claim takeovers before worktree allocation.
Bucket agents return patch bundles, generated artifacts, test evidence, changed-file inventories, and proposed status rows. They must not write shared `.gald3r` indexes/status files, `CHANGELOG.md`, generated Copilot prompts, parity outputs, final staging, or commits. The coordinator performs one final shared-write pass and never accepts broad `git add .` output from a bucket.
After the coordinator reconciles buckets and performs final shared writes, it creates a code-complete checkpoint commit. Review swarms use that checkpoint as their default branch-addressable source; dirty snapshot review is fallback-only.


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
@g-go-code-swarm
@g-go-code-swarm tasks 7, 9, 10, 11, 12
@g-go-code-swarm bugs-only
```

All filter arguments pass through to `@g-go-code --swarm`.

See `@g-go-code` for the full implementation protocol, worktree isolation rules, and swarm coordinator rules.

Let's implement.