Pipeline orchestrator — implement then auto-review: $ARGUMENTS

## Mode: PIPELINE (Implement → Auto-Review)

`g-go` is a **two-phase pipeline**. Phase 1 implements tasks; Phase 2 automatically spawns an
independent reviewer agent on the completed work. You get adversarial QA without manually
alternating between sessions.

> **Independence guarantee**: The Phase 2 reviewer is a fresh Task subagent. It receives only
> the task IDs and the `g-go-review` protocol — it has **no access** to Phase 1's conversation
> history, reasoning, or implementation decisions. It reads the artifacts on disk cold.

---

### ⛔ NO-PROMPT RULE — READ AND ENFORCE BEFORE DOING ANYTHING ELSE

**The coordinator MUST NEVER ask the user to confirm a plan, select a scope, choose between options, or approve a proposal.** This command is designed for fire-and-forget operation across multi-window workflows and scheduled automation. The user has already expressed intent by typing the command; they are not watching this session.

The **only** valid reasons to stop mid-run are the explicitly documented **hard-gate failures** listed below (PCAC conflict exit-code `2`, dirty orchestration root outside this run's staging allowlist, manifest / `workspace_repos` resolution error on multi-repo work). Any ambiguity that is NOT one of those hard gates is **resolved silently by the auto-plan rules below** and the run proceeds without comment.

Asking "Go?" or "Confirm?" or "Which tasks?" or "Conservative or expanded?" is a **violation of this rule**. If you find yourself composing a confirmation question, apply the auto-plan instead and start working.

#### Auto-Plan Algorithm (no explicit task IDs in `$ARGUMENTS`)

When `$ARGUMENTS` is empty or contains no task/bug IDs, the coordinator selects the work queue **immediately and silently** using these ordered rules:

1. **Scope filter** — branches on the `--workspace` flag (T532):
   - **Bare `/g-go` (default, no `--workspace`)** — include only items that are **gald3r_dev-scoped**: the task's `workspace_repos` field is absent, empty, or contains only the controller repo's own manifest ID (`gald3r_dev`). Items whose `workspace_repos` lists other member repos are **deferred** (logged as `Deferred — member-repo scope` in the session summary; no prompt to the user). Bare `/g-go` MUST NEVER scan all manifest workspace repositories — that is the explicit `--workspace` opt-in below.
   - **`/g-go --workspace`** — include items routed to any manifest-declared workspace repository whose `repository.local_path` exists, whose `lifecycle_status` permits work, and whose `allowed_write_policy` is compatible with the task's `workspace_touch_policy`. Items routing to repos that are missing/planned/unavailable, write-disallowed, or unauthorized are **deferred** with explicit per-repo reasons in the summary. The orchestration controller and every selected member repo each get their own per-root clean check, worktree context, and blocker reporting; no per-repo blocker silently affects unrelated repos.
2. **Phase 1 queue** — all `[📋]` / `[ ]` / stale-`[📝]` items that pass the scope filter, ordered Critical → High → Medium → Low. Apply the auto-downgrade rule: if exactly one implementation item passes the filter, downgrade to single-agent `g-go-code` and continue — do not stop.
3. **Phase 2 queue** — all `[🔍]` items that pass the scope filter and are reachable from the Phase 1 checkpoint.
4. **Zero runnable items** — output `[PIPELINE] No runnable items after scope filter. Deferred: {list with reasons}. Nothing to commit.` and exit cleanly. **Do not ask what to do.**

When `$ARGUMENTS` provides explicit task/bug IDs, use those IDs exactly — skip scope filtering. The user's explicit selection is the plan. The `--workspace` flag still affects per-repo clean-check and authorization behavior even with explicit IDs: every repo touched by the explicit task list is gated per-root.

---

### PCAC Inbox Gate (Only When PCAC Is Configured)

Before task claiming, implementation, verification, planning, or swarm partitioning, first determine whether this project is a PCAC participant. PCAC is configured only when `.gald3r/linking/link_topology.md` declares at least one parent/child/sibling relationship, or `.gald3r/PROJECT.md` explicitly declares PCAC project linking relationships. A Workspace-Control manifest and local `INBOX.md` alone do not make the project a PCAC group member.

If PCAC is configured, run the re-callable inbox check when the hook exists:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

Installed templates may call the equivalent hook from the active IDE folder. If the check reports `INBOX CONFLICT GATE` or exits with code `2`, stop immediately and run `@g-pcac-read`; do not claim tasks, create worktrees, spawn reviewers, or continue planning until conflicts are resolved. Non-conflict requests, broadcasts, and syncs are advisory and should be surfaced in the session summary. If PCAC is not configured, skip this gate and report `PCAC: not configured / skipped`.


### Gald3r Housekeeping Commit Gate (T531)

<!-- T531-HOUSEKEEPING-GATE -->
After the PCAC gate is skipped or passes and **before** the Clean Controller Gate hard-blocks the run, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -TaskId <id-when-known> -Json
```

Behavior:

- **`clean`** -> continue.
- **`safe-gald3r-housekeeping`** -> the helper stages **only** allowlisted controller `.gald3r/` paths via explicit `git add -- <paths>` (never `git add .`), re-checks for drift, and creates a focused `chore(gald3r): preflight gald3r housekeeping` commit. The run continues automatically.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown `.gald3r` paths / member-repo `config-fault`** -> the helper exits non-zero, the existing Clean Controller Gate hard-block applies, and the run STOPs with the exact unsafe paths listed.

The helper allowlist covers the safe controller `.gald3r/` coordination surfaces (TASKS.md, BUGS.md, FEATURES.md, PRDS.md, SUBSYSTEMS.md, IDEA_BOARD.md, learned-facts.md, tasks/, bugs/, features/, prds/, subsystems/, reports/, logs/pcac_auto_actions.log, linking/sent_orders/, linking/INBOX.md). The deny list covers `.identity`, `.user_id`, `.project_id`, `.vault_location`, `vault/`, `config/`, `.gald3r-worktree.json`, secret-named files, and unknown `.gald3r/` paths. Member-repo targets (marker-only `.gald3r/`) are refused -- this gate is **controller-only**.

Re-run the helper in `-Mode post-write -Apply` immediately after coordinator-owned shared `.gald3r` writes (task/bug status writes, review-result writes, sent_orders ledger updates, safe report/log outputs) and before the next major phase so the shared-state dirty window stays short. In `--swarm` flows only the coordinator runs the helper; bucket agents remain handoff producers.
### Clean Controller Gate (before claims, worktrees, reconciliation)

After the PCAC gate is skipped or passes:

1. At the **orchestration git root** (the repo from which you run this command — normally the Workspace-Control owner, e.g. `gald3r_dev`): run `git status --short`. If anything is listed **outside** this run's explicit coordinator staging allowlist for the active task and bug IDs, **STOP** here. Do not claim tasks or bugs, create or reuse T170 worktrees, partition swarms, or write coordinator-owned updates to `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, other shared `.gald3r` coordination files, `CHANGELOG.md`, generated Copilot prompts, or parity output until unrelated changes are committed, stashed, or moved to a prior focused commit. Preserve any bucket handoff artifacts already produced and list the paths that blocked progress.

2. **`gald3r_worktree.ps1 -AllowDirty`**: do not use this switch for `g-go`, `g-go-code`, `g-go-review`, or any `--swarm` variant **except** when every dirty path is owned exclusively by the active task/bug scope and a `## Status History` row documents that override. Otherwise clean the checkout first. The same **per-root** `-AllowDirty` discipline applies to every repository included in the touch set below when multi-repo work is in scope.

3. **Member touch-set (v1 — `workspace_repos`)** — The orchestration root is **always** gated. When the active task or bug declares **`workspace_repos:`** with manifest `repository.id` entries, extend the gate to each **other** resolved member root (blast radius follows declared cross-repo scope). Read `.gald3r/linking/workspace_manifest.yaml` when present; map each listed ID (deduplicated) to `repositories[?].local_path`. For each existing path, run `git -C "<path>" rev-parse --show-toplevel` then `git status --short` at that root. Apply the same **explicit coordinator staging allowlist** per root. Skip IDs whose paths are missing while `lifecycle_status` is a planned/bootstrap gap (report only; do not expand the touch set). If the manifest is missing while `workspace_repos` is non-empty, or an ID is unknown under `repositories:`, **STOP** multi-repo coordinator work until manifest or frontmatter is repaired (controller-only queue items whose `workspace_repos` lists only the owner id may proceed once that id resolves).

4. **Touch-set expansion (v2 — optional signals)** — Union extra repository roots into the same per-root checks (still **not** a blanket scan of every manifest member):
   - **`extended_touch_repos:`** — optional task/bug YAML list of additional manifest `repository.id` values beyond `workspace_repos`.
   - **`touch_repos:` (swarm handoffs)** — In `--swarm` runs, when bucket work edits roots not already covered by `workspace_repos` + `extended_touch_repos:`, bucket summaries and the coordinator reconciliation block MUST list those ids under `touch_repos:` so the union is gated before shared writes.
   - **Subsystem `locations:` absolutes** — When the active item declares **`subsystems:`**, read each `.gald3r/subsystems/{name}.md` frontmatter **`locations:`** (all nested strings). For values matching a host **absolute** path (`^[A-Za-z]:[/\\]` on Windows, or POSIX `/` rooted at `/` elsewhere), if the path exists, resolve `git -C <dir> rev-parse --show-toplevel` (use the file's parent directory when the path is a file). Each distinct root **other than** the orchestration root joins the touch set. Relative paths do not expand the set.

### Pre-Reconciliation Clean Gate (before coordinator shared writes)

Also re-run the **Gald3r Housekeeping Commit Gate** with `-Mode post-write -Apply` against the orchestration root immediately after each coordinator-owned shared `.gald3r` write so safe controller coordination state lands in a focused `chore(gald3r): commit g-go coordination state` commit before the next major phase begins.


Immediately before the coordinator merges bucket results into the primary checkout, updates shared `.gald3r` indexes or task/bug files as coordinator-owned writes, touches `CHANGELOG.md`, or creates checkpoint / review-result commits: **re-run** `git status --short` on the **orchestration root and every other repository root in the computed touch set** (steps 1 + 3 + 4). For `--swarm` runs, if unrelated dirty paths appear in **any** of those roots during parallel bucket work, **fail closed** — do not apply those shared writes; keep patches, artifacts, and evidence; report **per-root** blockers using the same blocker family as checkpoint and review-result commits.

## Phase 1: Implementation

Phase 1 runs the full `g-go-code` protocol. Every completed item is marked `[🔍]`.
During Phase 1, the implementation-only boundary still applies: run smoke/unit readiness checks only, and do not invoke full adversarial review. Only Phase 2 may spawn the independent reviewer.

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
- No unmet dependencies, with the rolling-pipeline exception: checkpointed `[🔍]` dependencies count as implementation-satisfied unless the downstream task declares `requires_verified_dependencies: true`; not `ai_safe: false`
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

Phase 2 is a parallel review lane, not a default global pause. In swarm mode, the coordinator should launch review from the checkpoint and then continue Phase 1 rolling implementation waves for newly runnable items whose dependencies are checkpointed at `[🔍]`. Only block the implementation lane for tasks that declare `requires_verified_dependencies: true`, a review failure that invalidates a downstream checkpoint dependency, a PCAC conflict, Workspace-Control preflight denial, or a repository state that prevents a safe checkpoint.

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

When Phase 2 review and later Phase 1 rolling waves overlap, the coordinator serializes shared writes by checkpoint generation:

1. A review-result write may update only the items reviewed from its named checkpoint and any direct downstream checkpoint consumers it must requeue after FAIL.
2. A rolling implementation wave may write only its own newly implemented items to `[🔍]` and must preserve review-result status changes already committed for earlier checkpoints.
3. If review and implementation finish at the same time, apply the review-result commit first, recompute the queue, then reconcile the implementation wave against the updated primary checkout.
4. Never allow two coordinators to write `.gald3r/TASKS.md`, `.gald3r/BUGS.md`, task/bug files, changelog/docs, generated prompts, or final commits concurrently.

If review FAILs an item that later rolling-wave work consumed, requeue the failed item and mark each dependent consumer as pending rework unless its implementation can be trivially proven independent of the failed behavior. Do not roll back unrelated completed or in-progress waves.

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

Swarm mode is a rolling pipeline by default. Phase 1 emits checkpoint commits; Phase 2 reviews those checkpoints from fresh `review-swarm` worktrees; Phase 1 then continues with the next runnable wave instead of waiting for every review verdict. `[🔍]` dependencies count as implementation-satisfied for downstream coding unless the downstream task has `requires_verified_dependencies: true`.

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

## Workspace Mode (`--workspace`)

`--workspace` is the **explicit, opt-in** mode that expands queue selection across manifest-declared workspace repositories. It composes with `--swarm`, with task-ID filters, and with bug filters. Bare `/g-go` is unchanged — it remains current-controller-scoped by default. **Bare `/g-go` MUST NEVER scan member repos automatically.** All existing safety gates remain in force.

### When to use

- `/g-go --workspace` — workspace-aware pipeline; runs the full Phase 1 → Phase 2 flow, but selects from items routed across manifest-declared workspace repos.
- `/g-go --swarm --workspace` — workspace-aware swarm; partitions work across buckets respecting per-repo conflict-safety and per-repo touch-set gating.
- Bare `/g-go` and `/g-go --swarm` — unchanged. Member-repo items are deferred with `Deferred — member-repo scope` in the summary.

### Workspace queue selection

When `--workspace` is present, the coordinator:

1. Reads `.gald3r/linking/workspace_manifest.yaml` (the canonical Workspace-Control registry).
2. Resolves the repository set: orchestration controller (`gald3r_dev`) plus every entry under `repositories:` whose `local_path` exists on disk and whose `lifecycle_status` permits work (e.g. excluding `planned`/`bootstrap_gap`/`frozen` archives).
3. Filters the queue: each runnable task or bug is included only if every entry in its `workspace_repos:` resolves to a manifest member that is (a) locally available, (b) write-permitted by `allowed_write_policy.write_allowed`, and (c) compatible with the task's `workspace_touch_policy`.
4. Honors all standard ordering rules: Critical → High → Medium → Low, dependencies (with the rolling-pipeline `[🔍]` checkpoint exception unless `requires_verified_dependencies: true`), `[🚨]` skips, stale claim takeovers, PCAC-derived priority floor, and `ai_safe: false` exclusions.
5. Logs per-deferral reasons in the session summary. Reasons include: `member-repo path missing`, `lifecycle_status forbids work`, `write_allowed: false`, `unknown repository.id in workspace_repos`, `workspace_touch_policy mismatch`, and `manifest missing or unparseable`.

### Per-repo clean and touch-set gates

The Clean Controller Gate, Pre-Reconciliation Clean Gate, and Gald3r Housekeeping Commit Gate (T531) apply **per-root** to every repository in the computed touch set:

- The orchestration controller is **always** in the touch set.
- v1: every manifest member listed in any selected task's `workspace_repos:` joins the touch set.
- v2: optional `extended_touch_repos:`, swarm-handoff `touch_repos:`, and absolute paths from subsystem `locations:` may union additional roots into the touch set (per `g-rl-33`).
- Each member root is checked independently with `git -C "<path>" status --short`. Unrelated dirty paths in any per-repo touch set block coordinator-owned writes to that repo only — they do not block unrelated clean repos unless the selected coordinator action requires all selected repos (e.g. a single-task multi-repo reconciliation).
- The **marker-only `.gald3r/` invariant** for `controlled_member` and `migration_source` repositories remains absolute. `--workspace` does NOT relax it. Attempted writes to member `.gald3r/` paths outside the marker allowlist (`.identity`, `PROJECT.md`) MUST be blocked by `g-rl-36` / the guard helper before the edit lands.

### Member-scoped task authorization

A selected task is permitted to edit a member repository only when ALL of the following are true:

1. The member's manifest `repository.id` appears in the task's `workspace_repos:` list.
2. The task's `workspace_touch_policy` is in the manifest entry's `allowed_write_policy.allowed_touch_policies`.
3. The manifest entry's `allowed_write_policy.write_allowed` is `true`.
4. Every dependency, blocker, PCAC inbox, and `[🚨]` check passes for that member root.
5. Per-repo clean check passes (or `-AllowDirty` is documented per-root in the task's `## Status History`).
6. No member `.gald3r/` control-plane path is targeted (marker-only invariant).

If any check fails, the task is deferred (workspace mode never silently degrades authorization).

### Workspace swarm coordination

Under `/g-go --swarm --workspace`:

- Bucket planning includes per-repo conflict-safety: items targeting different members can run in parallel; items sharing a member root must serialize on that root's coordinator-owned writes.
- Bucket worktrees follow `g-rl-02` (branch `gald3r/{task_id}/{role}/{repo_slug}/{owner}-{suffix}`); the `repo_slug` is the manifest `repository.id`.
- Bucket handoff metadata MUST include `touch_repos:` listing every member root the bucket actually edited; the coordinator unions those into its Pre-Reconciliation Clean Gate.
- Bucket agents return patches/artifacts/evidence/proposed-status only. The coordinator owns all shared `.gald3r/`, `CHANGELOG.md`, generated Copilot prompt, parity, and per-repo final-staging writes. `git add .` is forbidden in bucket worktrees; explicit path allowlists only.
- Checkpoint and review-result commits are created **per repository root** with focused messages. No single commit spans multiple repositories.

### Workspace summary output

Both at the periodic 30-minute heartbeats and at the final summary, `--workspace` runs print:

```
[WORKSPACE] Mode: workspace[+swarm]
[WORKSPACE] Manifest: .gald3r/linking/workspace_manifest.yaml
[WORKSPACE] Considered repos: gald3r_dev, gald3r_template_*, gald3r_throne, ...
[WORKSPACE] Skipped repos: gald3r_valhalla (lifecycle: frozen_marker_only), maestro2 (write_allowed: false)
[WORKSPACE] Runnable items: {N}    Blocked: {K}    Deferred: {D}
[WORKSPACE] Per-repo blockers: gald3r_template_full (unrelated dirty: .github/...), ...
[WORKSPACE] Next recommended: {command}
```

The summary makes it explicit which repos were considered, which were skipped, which were blocked, and what to run next. `--workspace` runs never finish silently with implicit cross-repo work.

### Marker-only protection (recap)

Member `.gald3r/` may contain ONLY `.identity` and `PROJECT.md`. `g-skl-workspace`, `g-skl-pcac-spawn`, `g-skl-pcac-adopt`, `g-skl-setup`, and `gald3r_install` all consult `scripts/check_member_repo_gald3r_guard.ps1` before any member `.gald3r/` write. `--workspace` runs do NOT add a bypass; the guard is non-negotiable. Any attempted write to a forbidden member `.gald3r/` path is logged as a blocker and excluded from the run.

---

## Behavioral Rules

| Rule | Why |
|------|-----|
| Phase 1 never marks `[✅]` — only `[🔍]` | Phase 2 reviewer owns `[✅]` |
| Phase 2 reviewer spawned with no Phase 1 context | Adversarial independence guarantee |
| Phase 2 inspects through a review worktree or read-only snapshot | Prevents reviewers from mutating implementation checkouts |
| Coordinator batch-writes TASKS.md and BUGS.md after Phase 2 | Prevents concurrent line-edit conflicts |
| **NEVER ask questions, propose options, or request confirmation** — apply the auto-plan and work | This is fire-and-forget; the user has moved on |
| Skip tasks you can't complete | Maximize total output |
| Respect CONSTRAINTS.md | Never violate project guardrails |
| Abort if destructive (schema drop, data loss) | Safety first — log as blocker |
| Bare `/g-go` is **always** controller-only — never silently scans member repos | Workspace expansion requires explicit `--workspace` opt-in |
| `--workspace` honors per-repo clean gates, marker-only `.gald3r/` invariant, manifest write policy, and `workspace_touch_policy` | A single global flag must not weaken per-repo safety |
| Workspace summary names every considered repo, skipped repo, and per-repo blocker | Multi-repo runs MUST be explicit about scope |
| Workspace checkpoint and review-result commits are **per repository root** | No single commit may span multiple member repositories |

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
@g-go --workspace
@g-go --workspace tasks 220, 221
@g-go --swarm --workspace
@g-go --swarm --workspace tasks 220, 221, 222
```

**For manual control (two separate sessions):**
```
Session 1:  @g-go-code
Session 2 (new agent window):  @g-go-review
```

Let's go.

