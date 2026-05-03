Alias for `@g-go --swarm`: $ARGUMENTS

Runs the full **pipeline orchestrator** in swarm mode:
- **Phase 1**: N parallel implementation agents (subsystem-boundary partition)
- **Phase 2**: M parallel reviewer agents (round-robin, fresh context each)
- **Rolling waves**: implementation continues on newly runnable downstream work while review catches up on committed checkpoints

This is exactly `@g-go --swarm`. Use this command for discoverability.
Phase 1 implementer agents use the `g-go-code --swarm` implementation-only boundary: they may run smoke/unit readiness checks, but must not launch full adversarial review. Phase 2 is the only review lane in this pipeline.
If Phase 1 has exactly one runnable item after workspace preflight, auto-downgrade Phase 1 to standard `@g-go` / `@g-go-code` single-agent implementation and continue the pipeline. Do not stop merely because swarm partitioning would produce one bucket. Workspace preflight blockers still stop the run.
Phase 1 must create or reuse one T170 coding worktree per implementation bucket before
spawning agents; Phase 2 remains governed by the review workflow.
All bucket agents run in handoff mode: they return patches/artifacts/evidence and proposed status rows. They must not write shared `.gald3r` status files, changelog/docs, generated prompts, parity output, final staging, or commits. The coordinator performs those shared writes once after deterministic reconciliation.
The coordinator then creates a code-complete checkpoint commit and passes its branch/SHA to review. Review swarms should create clean `review-swarm` worktrees from that checkpoint by default; snapshot mode is fallback-only for explicitly uncommitted or non-branch-addressable sources.
Do not stop the swarm pipeline just because an upstream item is `[🔍]`. A checkpointed `[🔍]` dependency is implementation-satisfied for downstream coding unless the downstream task declares `requires_verified_dependencies: true`. Review failures requeue the failed item and any downstream checkpoint consumers; unrelated waves keep moving.


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
@g-go-swarm
@g-go-swarm tasks 7, 9, 10, 11, 12
@g-go-swarm bugs-only
```

All filter arguments pass through to `@g-go --swarm`.

See `@g-go` for full pipeline documentation, worktree isolation, and swarm agent count / partition rules.

Let's go.