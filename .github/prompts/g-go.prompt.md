Pipeline orchestrator — implement then auto-review: $ARGUMENTS

## Mode: PIPELINE (Implement → Auto-Review)

`g-go` is a **two-phase pipeline**. Phase 1 implements tasks; Phase 2 automatically spawns an
independent reviewer agent on the completed work. You get adversarial QA without manually
alternating between sessions.

> **Independence guarantee**: The Phase 2 reviewer is a fresh Task subagent. It receives only
> the task IDs and the `g-go-review` protocol — it has **no access** to Phase 1's conversation
> history, reasoning, or implementation decisions. It reads the artifacts on disk cold.

---


### PCAC Inbox Gate (Before Claiming Work)

Before task claiming, implementation, verification, planning, or swarm partitioning, run the re-callable PCAC inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary.

## Phase 1: Implementation

Phase 1 runs the full `g-go-code` protocol. Every completed item is marked `[🔍]`.

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
- **Skip `[🚨]` bugs** — log in Skipped section

**Tier 2 — Pending tasks:**
- Status `[ ]` (pending), `[📋]` (ready), or stale `[📝]` (speccing claim expired)
- **Skip non-expired `[📝]` speccing claims** — log owner/expiry as "Speccing-In-Progress"
- For stale `[📝]` claims, append a Status History takeover row naming the prior `spec_owner` before proceeding
- **NOT** `[🚨]` — skip entirely
- No unmet dependencies; not `ai_safe: false`
- Priority: Critical → High → Medium → Low

Supported `$ARGUMENTS` filters:
- Task IDs: `@g-go tasks 7, 9`
- Bug IDs: `@g-go bugs BUG-003`
- Subsystem: `@g-go subsystem vault-hooks-automation`
- `@g-go bugs-only` / `@g-go tasks-only`

### 2a. Resolve Phase 1 Speccing Claims Before Worktrees

Before Phase 1 worktree allocation, resolve task-spec claims in the primary checkout:
- For a bare `[ ]` task with no complete task file, run `g-skl-tasks` `CLAIM-FOR-SPEC` -> `WRITE-SPEC` -> `PROMOTE-SPEC` first.
- Skip non-expired `[📝]` claims before allocating a coding worktree.
- For expired `[📝]` claims, append a Status History takeover row naming the prior `spec_owner`, then finish/promote the spec before worktree creation.
- Only `[📋]` tasks or stale claims successfully promoted to `[📋]` proceed to Phase 1 coding worktree creation.

### 3. Pre-Create Phase 1 Coding Worktrees

After speccing claims are resolved, Phase 1 uses the same isolation contract as `g-go-code`:

```powershell
.\scripts\gald3r_worktree.ps1 -Action Create -TaskId {id} -Role code -Owner {platform_or_agent_slug} -Json
```

Installed templates may call the helper from `g-skl-git-commit/scripts/gald3r_worktree.ps1` when no root `scripts/` copy exists.

Rules:
- Create/reuse all queued item worktrees before implementation edits or primary-checkout status writes.
- Map helper JSON to claim metadata: `worktree_path` → `worktree_path`, `worktree_branch` → `worktree_branch`, `created_at` → `worktree_created_at`, and `owner` → `worktree_owner`.
- Run Phase 1 implementation inside the worktree root.
- Keep the primary checkout for queue coordination, final batched status writes, and Phase 2 reviewer handoff.
- If the helper refuses because the active checkout is dirty, skip the item unless the task explicitly owns direct-root work and an override is documented.
- Leave failed worktrees intact for inspection; do not delete them during the same pipeline run.

### 4. Implement Each Item

For each item:

**a)** Read the task/bug file — understand objective and acceptance criteria
**b)** If the item is a bare `[ ]` task with no complete spec, run `g-skl-tasks` `CLAIM-FOR-SPEC` → `WRITE-SPEC` → `PROMOTE-SPEC` first; skip non-expired `[📝]` claims. Then create/reuse the coding worktree and implement the solution inside that worktree
**b2) AC gate** — before moving on, walk every `- [ ]` acceptance criterion:
  - Is this criterion satisfied in actual files? → proceed
  - Unmet → return to **(b)**
  - Cannot meet this session → log as Blocker, skip task entirely (no partial `[🔍]`)
  - **Stub/TODO scan**: bare `# TODO`, `pass`, `raise NotImplementedError` → annotate `TODO[TASK-X→TASK-Y]` + create follow-up task (see `g-rl-34`)
  - **Bug-discovery check**: pre-existing bugs → BUG entry + `BUG[BUG-{id}]` comment; current-task bugs → fix inline (see `g-rl-35`)
  - **Constraint check**: any `🚫 VIOLATION` blocks `[🔍]`
  - **Workspace boundary check**: run `g-skl-workspace` ENFORCE_SCOPE before editing and before `[🔍]`; omitted metadata is current-repo-only, unknown manifest repo IDs block, and member repo writes require explicit `workspace_repos`, compatible `workspace_touch_policy`, authorization text, reviewed member git status, and manifest write permission.
**b3) Queue Status History** — collect the row that will be appended before marking `[🔍]`:
  ```
  | YYYY-MM-DD | pending | awaiting-verification | Implementation complete; {1-line summary} |
  ```
**c)** Validate — lint, test, check files exist
**d)** Record decisions → append to `.gald3r/DECISIONS.md`
**e)** Update subsystem Activity Log for each subsystem in `subsystems:` field
**f)** Queue `[🔍]` (NOT `[✅]`) status for the final Phase 1 batch write; add task ID to `phase1_results`
**g)** Move to next item

### 5. Phase 1 Completion

After all items are processed, reconcile successful worktree diffs into the primary checkout, batch-write task/bug status, then create a code-complete checkpoint commit before reviewer handoff. For each successful worktree, stage only intended files in that worktree with `git add -A -- {paths}`, export `git diff --binary --cached HEAD`, and apply it to the primary checkout with `git apply --3way --index` so new files are included. Never use `git add .` in swarm worktrees. If the patch does not apply cleanly, preserve the worktree and list the item as skipped.

```
[PIPELINE] Phase 1 complete
  Implemented → [🔍]: {phase1_results IDs}
  Checkpoint → {branch}@{commit_sha}
  Blocked/Skipped: {list with reasons}
```

If `phase1_results` is empty → skip Phase 2:
```
[PIPELINE] Phase 1 completed 0 items — Phase 2 skipped. Nothing to review.
```

---

## Phase 2: Auto-Spawn Independent Reviewer

> **Only runs if Phase 1 marked at least 1 item `[🔍]`.**

### Spawn

Print the handoff notice:
```
[PIPELINE] Spawning Phase 2 reviewer for: Task {task IDs} / Bug {bug IDs}
[PIPELINE] Reviewer is a fresh agent — no Phase 1 context. Adversarial independence: ✓
```

Spawn a Task subagent with:
- The full `g-go-review` prompt
- Filter: `tasks {phase1_task_result_ids} bugs {phase1_bug_result_ids}` (omit either clause when empty)
- Coordinator-managed override: "Return PASS/FAIL payloads and Status History rows only. Do not write task/bug files, `TASKS.md`, or `BUGS.md`; the `g-go` coordinator owns final writes."
- No other context from Phase 1

### Reviewer Protocol

The spawned agent runs the standard `g-go-review` protocol:
- Claims each Phase 2 item as `[🕵️]` / `verification-in-progress` before inspection
- Establishes review isolation before inspection:
  - T170 `review` worktree from the Phase 1 checkpoint commit by default
  - Snapshot mode only when the candidate changes are explicitly left uncommitted or cannot be made branch-addressable
- Verifies the selected review source contains the candidate changes; if the candidate diff is dirty or not reachable from the chosen source branch, uses snapshot mode instead of a stale `HEAD` worktree
- Skips non-expired verifier claims and may only take over expired claims with Status History logging
- Reads each task/bug spec and checks ACs or fix criteria against actual files
- PASS → returns PASS payload + verification note
- FAIL → returns FAIL payload + Status History row; stuck-loop check (≥3 FAILs → `[🚨]`)
- **Does NOT write task/bug files, TASKS.md, or BUGS.md** — returns result payload to coordinator

### Coordinator Collects and Finalises

After reviewer completes:
1. Batch-update `TASKS.md` (all PASS → `[✅]`, all FAIL → `[📋]`) in a single write
2. Batch-update `BUGS.md` (all PASS → `[✅]`, all FAIL → `[📋]`) in a single write
3. Create the review-result commit after PASS/FAIL status writes, using explicit path staging only
4. Write Pipeline Session Summary (see format below), including the review-result commit SHA or the explicit non-commit blocker

The coordinator commits the review result by default for PASS, FAIL, and mixed verdicts. Allowed reasons not to commit are limited to unresolved conflicts, failed commit hooks, staged or untracked unrelated changes, detected secrets, dirty generated outputs not owned by review, missing user permission for destructive or out-of-scope changes, or repository state that prevents a safe commit.

---

## Pipeline Session Summary

```markdown
## Pipeline Session Summary

### Phase 1: Implementation
- Items attempted: {N}
- Completed → [🔍]: Task 7, Task 9, Bug BUG-003
- Blocked/Skipped: Task 10 — {reason}

### Phase 2: Adversarial Review (independent agent)
- Reviewer: 1 fresh Task subagent
- Reviewer had NO Phase 1 context ✓

| Task | Result | Notes |
|------|--------|-------|
| Task 7 | [✅] PASS | all ACs met |
| Task 9 | [✅] PASS | all ACs met |
| BUG-003 | [📋] FAIL | AC-2 not met — {reason} |

### Final Status
- ✅ Completed (verified): 2
- 📋 Failed (back to pending): 1
- Blocked (not attempted): 1

### Re-implement failed tasks
@g-go tasks {failed_ids}
```

---


### PCAC Inbox Heartbeats (Swarm / Long Runs)

For swarm mode or any run lasting more than 30 minutes, the coordinator reruns the PCAC inbox check every 30 minutes and once more before the final summary. If a conflict appears mid-run, pause new claims/spawns/reconciliation, preserve worktrees and partial outputs, and require `@g-pcac-read` before continuing.

## Swarm Mode (`--swarm`)

When `$ARGUMENTS` includes `--swarm`, both phases run in swarm mode.

### Phase 1 Swarm (g-go-code swarm protocol)

Before partitioning, evaluate Phase 1 swarm eligibility after Workspace-Control preflight. If exactly one runnable item remains and preflight passes, automatically downgrade Phase 1 to the standard single-agent `g-go-code` path and continue the pipeline without asking for confirmation. If preflight fails because a workspace member is unknown, not a git root, or not authorized for the task/bug routing metadata, stop with that blocker; invalid workspace routing is not a swarm/single-agent choice.

**Smart Agent Count:**

| Queue size | Agents |
|-----------|--------|
| 1 | 1 (no swarm — fallback) |
| 2–4 | 2 |
| 5–9 | `ceil(count / 3)` (2–3) |
| 10–14 | 4 |
| 15+ | 5 (hard cap) |

**Conflict-safe partition** (subsystem-boundary):
```
1. For each pair (A, B): CONFLICT if shared subsystem OR A depends_on B OR B depends_on A
2. Greedy assign: item → first bucket with no conflict (open new bucket up to agent_count limit)
3. Tasks touching TASKS.md/BUGS.md directly → single bucket
```

Before spawning implementer agents, skip non-expired `[📝]` speccing claims, log stale `[📝]` takeovers with prior `spec_owner`, then create or reuse one coding worktree per bucket with role `code-swarm` and `-Json`. Pass each bucket's `worktree_path` and `worktree_branch` to its implementer. Implementers run from their assigned worktree and MUST return patch bundles or explicit diffs, generated artifacts, test evidence, changed-file inventories, and proposed Status History rows. Implementers MUST NOT directly write shared `.gald3r/TASKS.md` / `.gald3r/BUGS.md`, task/bug status files, `CHANGELOG.md`, generated Copilot prompts, parity outputs, or commits. They also MUST NOT run `git add .`; explicit path staging only, excluding `.gald3r-worktree.json`, ownership metadata, terminal transcripts, local logs, and other non-deliverables.

The coordinator reconciles bucket outputs one at a time by staging only intended bucket files in the bucket worktree with `git add -A -- {paths}`, exporting `git diff --binary --cached HEAD`, and applying it to the primary checkout with `git apply --3way --index`. Before applying, the coordinator detects overlapping shared-file edits and defers shared surfaces to one final coordinator write. Failed worktrees are preserved for inspection, then the coordinator batch-writes final task/bug status, changelog/docs updates, generated prompt changes, and parity sync output once. The coordinator then creates one code-complete checkpoint commit and passes its branch/SHA to Phase 2 as the default review source. Collect `phase1_results` = union of all reconciled `[🔍]` items.

### Phase 2 Swarm (g-go-review swarm protocol)

Partition mixed `phase1_results` (tasks and bugs) round-robin across M reviewer agents (same count formula).
Coordinator claims each review bucket as `[🕵️]` before spawning reviewers, skips non-expired verifier claims, and establishes one review isolation source per bucket (`review-swarm` worktree or snapshot mode).
Each reviewer produces a result payload only: PASS/FAIL, evidence, proposed Status History rows, and any fix-forward patch if explicitly authorized. Reviewers do not write `TASKS.md`, `BUGS.md`, task/bug files, changelog/docs, generated prompts, parity output, or commits.
Coordinator performs one final shared-write pass for `TASKS.md`, `BUGS.md`, task/bug files, changelog/docs updates, generated prompts, parity sync output, final staging, and the review-result commit. The coordinator commits PASS, FAIL, and mixed review verdicts by default after status writes, unless a narrow non-commit blocker applies.

### Swarm Pipeline Summary

```markdown
## Swarm Pipeline Session Summary

### Phase 1: Swarm Implementation
- Implementers: N
- Partition: subsystem-boundary
- Checkpoint: {branch}@{commit_sha}
| Bucket | Tasks | [🔍] | Blocked |
|--------|-------|------|---------|
| 1 | 7, 9 | 2 | 0 |
| 2 | 10, 11 | 1 | 1 |

### Phase 2: Swarm Review (N fresh agents — no Phase 1 context)
- Reviewers: M
- Partition: round-robin by priority
| Reviewer | Tasks | PASS | FAIL |
|----------|-------|------|------|
| R-1 | 7, 10 | 2 | 0 |
| R-2 | 9 | 0 | 1 |

### Final Status
- ✅ Completed (verified): {N}
- 📋 Failed (back to pending): {M}
- Blocked: {K}
```

---

## Behavioral Rules

| Rule | Why |
|------|-----|
| Phase 1 never marks `[✅]` — only `[🔍]` | Phase 2 reviewer owns `[✅]` |
| Phase 2 reviewer spawned with no Phase 1 context | Adversarial independence guarantee |
| Phase 2 inspects through a review worktree or read-only snapshot | Prevents reviewers from mutating implementation checkouts |
| Coordinator batch-writes TASKS.md and BUGS.md after Phase 2 | Prevents concurrent line-edit conflicts |
| Never ask questions mid-execution | Uninterrupted autonomous work |
| Skip tasks you can't complete | Maximize total output |
| Respect CONSTRAINTS.md | Never violate project guardrails |
| Abort if destructive (schema drop, data loss) | Safety first — log as blocker |

---

## Usage Examples

```
@g-go
@g-go tasks 7, 9, 12
@g-go bugs BUG-003, BUG-007
@g-go subsystem vault-hooks-automation
@g-go bugs-only
@g-go --swarm
@g-go --swarm tasks 7, 9, 10, 11, 12
@g-go --swarm bugs-only
```

**For manual control (two separate sessions):**
```
Session 1:  @g-go-code
Session 2 (new agent window):  @g-go-review
```

Let's go.

