Implementation-only backlog execution: $ARGUMENTS

## Mode: IMPLEMENT ONLY

This command runs **coding and bug-fixing** — it does NOT verify. Every completed item is
marked `[🔍]` (Awaiting Verification) so a **separate agent session** can independently confirm it.

## Implementation-Only Boundary

`g-go-code` and `g-go-code --swarm` must not spawn reviewer agents, run `g-go-review`, run `g-go-review-swarm`, or invoke `gald3r-code-reviewer` / full adversarial review subagents.

Allowed implementation readiness checks are limited to smoke/unit-style evidence:
- Import/build/typecheck/lint commands relevant to the changed files.
- Focused unit tests or existing fast test gates.
- Acceptance-criteria self-check against the task or bug spec.
- Workspace, constraint, stub/TODO, and bug-discovery gates required before marking `[🔍]`.

The output may include a review handoff and checkpoint SHA. It must not perform the review. Use `g-go` / `g-go --swarm` for implement-plus-auto-review, or `g-go-review` / `g-go-review --swarm` for review-only.

---


### PCAC Inbox Gate (Before Claiming Work)

Before task claiming, implementation, verification, planning, or swarm partitioning, run the re-callable PCAC inbox check when the hook exists.

> **Tool routing (BUG-031)**: on Windows, invoke this snippet through the **PowerShell tool**, not Bash. It uses PowerShell-only syntax (`@(...)` array, `Where-Object`, `Test-Path`, `Select-Object`, pipeline). Routing it through Bash produces a parse error such as ``syntax error near unexpected token `('`` — that failure is a tool-selection error, **NOT** a real PCAC conflict gate. Re-run via PowerShell. On Linux/macOS hosts use `pwsh` if available; if neither shell can reach the hook, treat the gate as advisory and let Workspace-Control routing re-evaluate.

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary.

## Execution Protocol

### 1. Load Context (Before Touching Anything)

Read in this order:
- `.gald3r/PROJECT.md` — mission, goals, ecosystem context
- `.gald3r/PLAN.md` — current milestones
- `.gald3r/BUGS.md` — open bugs (**read before TASKS** — bugs run first)
- `.gald3r/TASKS.md` — master task list
- `.gald3r/CONSTRAINTS.md` — guardrails (if exists)
- `.gald3r/DECISIONS.md` — past decisions (if exists, read-only)
- `git log --oneline -10` — recent changes

### 2. Build the Work Queue

**Bugs first (Tier 1), then tasks (Tier 2).**

**Tier 1 — Open bugs:**
- From `BUGS.md` + `bugs/` files; Critical → High → Medium → Low
- Skip bugs with external blockers
- **Skip `[🚨]` bugs** — log in Skipped section as "Requires-User-Attention — human review needed"

**Tier 2 — Pending tasks:**
- Status `[ ]` (pending), `[📋]` (ready), or stale `[📝]` (speccing claim expired)
- **Skip non-expired `[📝]` speccing claims** — log owner/expiry in Skipped section as "Speccing-In-Progress"
- For stale `[📝]` claims, append a Status History takeover row naming the prior `spec_owner` before proceeding
- **NOT** `[🚨]` (requires-user-attention) — **skip entirely**, log in Skipped section as "Requires-User-Attention — human review needed"
- No unmet dependencies, with the rolling-pipeline exception below: a dependency at `[🔍]` counts as **implementation-satisfied** for follow-on coding unless the downstream task declares `requires_verified_dependencies: true`
- Not `ai_safe: false`
- Priority: Critical → High → Medium → Low

Supported `$ARGUMENTS` filters:
- Task IDs: `@g-go-code tasks 7, 9`
- Bug IDs: `@g-go-code bugs BUG-003`
- Subsystem: `@g-go-code subsystem vault-hooks-automation`
- `@g-go-code bugs-only` / `@g-go-code tasks-only`

### 2a. Resolve Speccing Claims Before Worktrees

Before Step 3 worktree allocation, resolve task-spec claims in the primary checkout:
- For a bare `[ ]` task with no complete task file, run `g-skl-tasks` `CLAIM-FOR-SPEC` -> `WRITE-SPEC` -> `PROMOTE-SPEC` first.
- Skip non-expired `[📝]` claims before allocating a coding worktree.
- For expired `[📝]` claims, append a Status History takeover row naming the prior `spec_owner`, then finish/promote the spec before worktree creation.
- Only `[📋]` tasks or stale claims successfully promoted to `[📋]` proceed to coding worktree creation.

### 3. Pre-Create Coding Worktrees (Before Editing)

After speccing claims are resolved and before any implementation file changes or primary-checkout status writes, isolate every queued item with the T170 helper:

```powershell
.\scripts\gald3r_worktree.ps1 -Action Create -TaskId {id} -Role code -Owner {platform_or_agent_slug} -Json
```

Installed templates may call the helper from the `g-skl-git-commit/scripts/gald3r_worktree.ps1` skill directory when no root `scripts/` copy exists.

Rules:
- Worktree root defaults to `$env:GALD3R_WORKTREE_ROOT`, else `<repo-parent>/.gald3r-worktrees/<repo-name>`.
- The helper must refuse nested worktrees inside the active checkout.
- The helper blocks when the active checkout is dirty unless the current task explicitly owns that direct-root work and the operator supplies the documented override.
- Map helper JSON to claim metadata: `worktree_path` → `worktree_path`, `worktree_branch` → `worktree_branch`, `created_at` → `worktree_created_at`, and `owner` → `worktree_owner`.
- Run implementation commands from the worktree root. Keep the primary checkout for queue coordination and final status writes.
- Pre-create all queued item worktrees before marking any item `[🔍]`; this prevents legitimate gald3r status writes from making later worktree creation look unsafe.
- If worktree creation fails, preserve any existing files, record the reason in Deferred Items, and skip the item rather than editing the primary checkout.

### 4. Work Through Items Sequentially

For each item:

**a)** Read the task/bug file — understand objective and acceptance criteria
**b)** If the item is a bare `[ ]` task with no complete spec, run `g-skl-tasks` `CLAIM-FOR-SPEC` → `WRITE-SPEC` → `PROMOTE-SPEC` first; skip non-expired `[📝]` claims. Then create/reuse the coding worktree and implement the solution inside that worktree
**b2) AC gate** — before moving on, walk every `- [ ]` acceptance criterion in the task spec:
  - Is this criterion now satisfied? Check the actual files, not just intent.
  - Any unmet criterion → return to **(b)** and address it.
  - Cannot meet a criterion this session → log as a Blocker in step 5 and **skip this task entirely** (do not mark `[🔍]` for partial work).
  - **Stub/TODO scan**: search files modified for this task for bare `# TODO`, `// TODO`, `pass` (non-abstract), `raise NotImplementedError`, `throw new Error("not implemented")` — each is an unmet criterion until annotated `TODO[TASK-X→TASK-Y]` with a follow-up task created (see `g-rl-34`)
  - **Bug-discovery check**: any pre-existing bug encountered while implementing must have a BUG entry + `BUG[BUG-{id}]` comment before `[🔍]`; bugs introduced by this task must be fixed inline (see `g-rl-35`)
  - **Constraint check**: run `@g-constraint-check` mentally — does this implementation violate any active constraint? Any `🚫 VIOLATION` blocks `[🔍]`
  - **Workspace boundary check**: run `g-skl-workspace` ENFORCE_SCOPE before editing and before `[🔍]`; omitted metadata is current-repo-only, unknown manifest repo IDs block, and member repo writes require explicit `workspace_repos`, compatible `workspace_touch_policy`, authorization text, reviewed member git status, and manifest write permission.
  - All criteria confirmed met → continue.
**b3) Queue Status History** — collect the row that will be appended before marking `[🔍]`:
  ```
  | YYYY-MM-DD | pending | awaiting-verification | Implementation complete; {1-line summary} |
  ```
  If the task file has no `## Status History` section yet, add it first (backfill row: `| {created_date} | — | pending | Task created (backfill) |`).
**c)** Validate — lint, test, check files exist
**d)** Record decisions — if you chose approach A over B, append to `.gald3r/DECISIONS.md`
**e)** Update subsystem Activity Log — for each subsystem in the task's `subsystems:` field, append to `.gald3r/subsystems/{name}.md` Activity Log: `| {date} | TASK | {id} | {title} | — |`. Create a stub spec if the file doesn't exist.
**f)** Queue status update → mark `[🔍]` (NOT `[✅]`) in both task file and TASKS.md during the final batch write
**g)** Move to next item

> **IMPORTANT**: Mark every completed item `[🔍]`, never `[✅]`.
> `[✅]` requires a separate agent session running `@g-go-review`.

### 5. Docs Check (Per Task)

After each task, ask: does this add/remove/change user-facing behavior?
- **YES** → Append entry to `CHANGELOG.md` (root); update `README.md` if relevant section exists
- **NO** (internal refactor only) → skip

### 6. Question & Blocker Collection

DO NOT stop to ask. Collect silently:

```markdown
## Deferred Items

### Questions (Need Human Answer)
- Q1: [question] (task #X)

### Blockers (Could Not Proceed)
- B1: Task #X — [reason]

### Decisions Made (FYI)
- D1: Task #X — chose A over B because [reason]
```

### 7. Record Decisions

Before the handoff message, append any new decisions to `.gald3r/DECISIONS.md`:
- Use the next sequential ID after the last entry (`D{NNN}`)
- Include: Date | Decision | Rationale | this-agent

### 7a. Coordinator-Only Shared Writes

For swarm mode, bucket agents are patch producers, not shared-ledger writers. They must return:

- Patch bundle or explicit changed-file list.
- Generated artifacts produced inside the assigned worktree.
- Test/lint evidence.
- Proposed Status History rows and status transitions.
- Requested shared writes (`.gald3r`, `CHANGELOG.md`, generated prompts, parity sync) for the coordinator to perform.

Bucket agents must not directly write or commit shared coordination surfaces:

- `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task files, bug files, archive indexes, INBOX/sent_orders ledgers.
- `CHANGELOG.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`.
- Generated Copilot prompts/instructions, parity copies, or platform-wide sync output.
- Final `git add`, `git commit`, `git merge`, or broad staging commands.

The coordinator alone performs shared writes after all bucket outputs are collected and reconciled.

### 7b. Code-Complete Checkpoint Commit

Default review handoff is branch-addressable. After successful implementation reconciliation and shared writes, the coordinator creates a code-complete checkpoint commit before handing work to review:

1. Stage only intended paths by explicit allowlist.
2. Include implementation files plus coordinator-owned shared writes needed for `[🔍]` handoff.
3. Commit with a message that names the implemented task/bug IDs and states that the commit is ready for independent review.
4. Record the checkpoint branch and commit SHA in the handoff summary.

Snapshot review mode is fallback-only. Use it when the user explicitly requests uncommitted review, when a source cannot be made branch-addressable, or when a failed reconciliation must be inspected read-only. Do not make dirty snapshot mode the default.

### 7c. Rolling Implementation Waves

`g-go-code` and `g-go-code --swarm` must optimize for throughput. A code-complete checkpoint is a stable handoff point, not a global stop sign.

After a checkpoint commit is created:

1. Recompute the runnable queue immediately.
2. Treat dependencies that are `[🔍]` / `awaiting-verification` as implementation-satisfied when they have a branch-addressable checkpoint and the downstream task does not declare `requires_verified_dependencies: true`.
3. Start the next coding wave from the latest checkpoint or member-repo branch that contains the dependency output.
4. Record checkpoint-dependent downstream work in the dependent task's Status History:
   `Started on unverified dependency T{id} at checkpoint {sha}; rework required if review fails.`
5. Continue coding until no runnable work remains, a PCAC conflict appears, Workspace-Control preflight fails, or a task explicitly requires verified dependencies.

Review remains mandatory, but `g-go-code*` only prepares the handoff. It must not start the review lane itself. A later review failure requeues only the failed item and any downstream tasks that explicitly consumed its checkpoint. Do not stop unrelated implementation work merely because a prior item is awaiting review.

Tasks may force the old strict behavior with:

```yaml
requires_verified_dependencies: true
```

Use that field for destructive operations, irreversible migrations, public release/signing, production writes, security-sensitive changes, or any task whose acceptance criteria explicitly require verified predecessor behavior.

### 8. Final Status Batch + Handoff

After all attempted items are implemented and validated, reconcile their worktree diffs into the primary checkout, then batch-write `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task files, bug files, docs logs, and changelog entries for all successful items. Do not let one item's status write block another item's worktree creation.

Reconciliation rule for each successful worktree:
1. Inspect `git status --short` in the worktree.
2. Stage only intended implementation files in the worktree with `git add -A -- {paths}` so new files are included. Never use `git add .` in a swarm worktree.
3. Export `git diff --binary --cached HEAD` from the worktree.
4. Apply to the primary checkout with `git apply --3way --index`.
5. If the patch does not apply cleanly, leave the worktree and branch intact and list the item under Skipped / Blocked with its path.
6. Reject or manually resolve any patch that touches shared coordination surfaces; those changes must be represented as coordinator requests, not applied as bucket-owned edits.

After the final shared-write pass, create the checkpoint commit before review. If the checkpoint commit cannot be created, leave the implemented items at `[🔍]` only when the handoff explicitly names snapshot mode and the dirty checkout path reviewers must inspect.

```markdown
## Implementation Session Summary

### Moved to [🔍] (Awaiting Verification)
- [🔍] Task #X: {title}
- [🔍] Bug BUG-00N: {title}

### Skipped (Blocked)
- Task #Y: {reason}

### Deferred Questions & Blockers
{collected items from step 5}

### Decisions Made This Session
{append these to .gald3r/DECISIONS.md}

### Handoff
{N} task(s) / {M} bug(s) moved to [🔍].
Implementation checkpoint: {branch}@{commit_sha} (default review source)
Handoff only: for independent verification, open a NEW agent session and run @g-go-review. Do not launch that reviewer from g-go-code.
Rolling waves: {continued|stopped}; next runnable queue: {ids or none}; verified-dependency blockers: {ids or none}
```

## Behavioral Rules

| Rule | Why |
|------|-----|
| Never ask questions mid-execution | Uninterrupted autonomous work |
| Never spawn reviewer agents from g-go-code* | Implementation mode stays focused on coding and readiness checks |
| Mark completed items `[🔍]`, never `[✅]` | Enforce independent verification gate |
| Keep coding across `[🔍]` dependencies unless strict verification is declared | Preserve fast product development while review catches up |
| Log every decision made | Future agents and humans need the audit trail |
| Skip tasks you can't complete | Maximize total output |
| Respect CONSTRAINTS.md | Never violate project guardrails |
| Abort if destructive (schema drop, data loss) | Safety first — log it as a blocker |


### PCAC Inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the PCAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-pcac-read` before continuing.

## Swarm Mode (`--swarm`)

When `$ARGUMENTS` includes `--swarm`, activate the **COORDINATOR PHASE** before any implementation.
Swarm mode partitions the work queue into conflict-safe buckets and spawns N parallel agents.

### Coordinator Phase (runs FIRST when --swarm is present)

**Step S1: Build full work queue** — same rules as standard mode (Steps 1–2 above), including skipping non-expired `[📝]` speccing claims and logging stale-claim takeovers.

**Step S2: Evaluate swarm eligibility after workspace preflight**
- If 0 qualifying items remain → exit with the existing empty queue or blocker message.
- If workspace preflight rejects a candidate (unknown `workspace_repos` member, target path is not a git root, unauthorized member write, or similar Workspace-Control denial) → stop with a blocker message. Do not offer swarm fallback for invalid workspace routing.
- If exactly 1 qualifying item remains and preflight passes → automatically downgrade to standard single-agent implementation mode and continue without asking for confirmation:
  `[SWARM] Single runnable item — auto-downgrading to @g-go-code standard mode`
- If 2 or more qualifying items remain → continue with swarm agent-count calculation and partitioning.
- After each checkpoint, rerun S1/S2 as a rolling wave. Previously completed `[🔍]` dependencies from this or earlier checkpoints count as implementation-satisfied unless a downstream task declares `requires_verified_dependencies: true`.

**Step S3: Compute agent count** (Smart Agent Count Formula)

| Queue size | Agents |
|-----------|--------|
| 1 | 1 (no swarm — fallback) |
| 2–4 | 2 |
| 5–9 | `ceil(count / 3)` (2–3) |
| 10–14 | 4 |
| 15+ | 5 (hard cap) |

**Step S4: Partition into conflict-safe buckets**

```
1. Build conflict_graph:
   For each pair (A, B) in work_queue:
     CONFLICT if: shared subsystem in subsystems[] OR A depends_on B OR B depends_on A

2. Greedy partition:
   Sort work_queue by priority (Critical→Low)
   For each item:
     Assign to the first existing bucket with no conflict with any item already in it
     If no bucket fits → open new bucket (up to agent_count limit)
     If max buckets hit → assign to smallest bucket (accept conflict; note it)

3. Output: buckets = [[task_ids...], [task_ids...], ...]
```

**Primary axis**: subsystem boundaries (same subsystem → same bucket).
**Secondary axis**: file-lock zones (tasks both touching TASKS.md/BUGS.md directly → same bucket).
**Dependency rule**: if A depends on B → same bucket, or B's bucket runs first.

**Step S5: Display partition plan**
```
[SWARM] Work queue: {M} items → {N} agents
  Bucket 1: Task 7 (vault-knowledge-store), Task 9 (vault-knowledge-store)
  Bucket 2: Task 10 (task-lifecycle-management), Task 11 (behavioral-rules-engine)
  Bucket 3: Task 12 (cross-project-coordination-pcac)
Spawning {N} implementation agents...
```

**Step S6: Spawn sub-agents**
- Before spawning, create or reuse one coding worktree per bucket:
  ```powershell
  .\scripts\gald3r_worktree.ps1 -Action Create -TaskId bucket-{bucket_number} -Role code-swarm -Owner {platform_or_agent_slug} -Json
  ```
- Branch/worktree names must include the bucket role plus repo/owner suffix from the helper contract.
- Each bucket agent receives its assigned `worktree_path` and `worktree_branch` and must run implementation from that worktree root.
- Bucket agents MUST NOT directly write shared `.gald3r/TASKS.md` / `.gald3r/BUGS.md`, task/bug status files, `CHANGELOG.md`, generated Copilot prompts, parity output, or commits. They return proposed status changes, changed-file inventory, generated artifacts, and evidence to the coordinator.
- Bucket agents MUST NOT run `git add .`; use explicit path staging only when creating a patch bundle, and exclude `.gald3r-worktree.json`, worktree ownership metadata, terminal transcripts, local logs, and other non-deliverable artifacts.
- Use the Agent tool to spawn N agents, each receiving:
  - The full `g-go-code` prompt (this command file content)
  - A `tasks X, Y, Z` filter argument restricting to that bucket's items only
  - The bucket worktree metadata
- Run all agents. Each follows the standard protocol on its slice.

**Step S7: Collect and merge**
After all sub-agents complete:
1. Inspect each bucket worktree with `git status --short` and `git diff --stat`.
2. Detect overlapping shared-file edits before applying patches. If two buckets request the same shared file, defer that file to the coordinator's final write.
3. Reconcile one bucket at a time: stage only intended bucket files in the bucket worktree with `git add -A -- {paths}`, export `git diff --binary --cached HEAD`, then apply it to the primary checkout with `git apply --3way --index`; do not overwrite user edits.
4. If reconciliation cannot be completed cleanly, leave the bucket worktree and branch intact and list it under Skipped / Blocked with its path.
5. Batch-write `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task files, bug files, `CHANGELOG.md`, generated Copilot prompts/instructions, and parity outputs only after bucket outputs are reconciled.
6. Run parity sync and prompt regeneration at most once from the coordinator after final shared writes.
7. Create one code-complete checkpoint commit from the primary checkout so review swarms can create clean `review-swarm` worktrees from a committed source.
8. Recompute the work queue for the next rolling wave. Continue immediately when new items become runnable through `[🔍]` checkpoint dependencies and no strict verification gate applies.
9. Write the unified handoff when no further coding wave can run:

```markdown
## Swarm Implementation Session Summary

### Swarm Configuration
- Agents spawned: N
- Partition strategy: subsystem-boundary
- Total items in queue: M

### Bucket Results
| Bucket | Agent | Tasks | Status |
|--------|-------|-------|--------|
| 1 | Agent-1 | 7, 9 | [🔍] ×2 |
| 2 | Agent-2 | 10, 11 | [🔍] ×1, Blocked ×1 |

### Moved to [🔍] (Awaiting Verification)
{merged list from all agents}

### Skipped / Blocked
{merged list from all agents}

### Handoff
{total} task(s) / {total} bug(s) moved to [🔍].
Implementation checkpoint: {branch}@{commit_sha} (default review-swarm source)
Handoff only: for independent verification, open a NEW agent session and run @g-go-review --swarm. Do not launch that reviewer from g-go-code-swarm.
Rolling waves completed: {count}; checkpoint-dependent downstream items: {ids}; strict verified-dependency blockers: {ids or none}
```

---

## Usage Examples

```
@g-go-code
@g-go-code tasks 14, 15
@g-go-code bugs BUG-001, BUG-002
@g-go-code subsystem cross-project
@g-go-code bugs-only
@g-go-code --swarm
@g-go-code --swarm tasks 7, 9, 10, 11, 12
@g-go-code --swarm bugs-only
```

Let's implement.
