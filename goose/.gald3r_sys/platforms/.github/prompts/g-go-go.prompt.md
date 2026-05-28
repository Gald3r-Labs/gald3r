Maximal workspace swarm autopilot — rolling implement/review until a hard stop: $ARGUMENTS

## Mode: AUTOPILOT (rolling implement → review → next batch)

`g-go-go` is the **explicit** "full throttle" command. It composes existing safe primitives (`g-go --swarm --workspace`, T531 housekeeping gate, T532 workspace mode, T212 rolling swarm pipeline, T206/207/208 swarm reconciliation policies, T170-172 worktree isolation, T495/496 per-root clean gates, marker-only `.gald3r/` invariant, PCAC conflict gates) into one continuous loop. It is **not** an alias for bare `/g-go`. Bare `/g-go` remains controller-only and unchanged.

> **Independence guarantee**: Each implementation/review cycle uses fresh reviewer subagents with no Phase 1 context. The autopilot loop never lets implementer agents self-verify their own work.

> **Bounded by design**: Autopilot is powerful but bounded. It cannot bypass PCAC conflict gates, clean gates, marker-only member `.gald3r/` protection, task workspace permissions, verification independence, secrets checks, explicit path staging, or non-destructive member rules. Every documented hard stop in the table below cleanly halts the run with an actionable summary.

---

### ⛔ NO-PROMPT RULE — READ AND ENFORCE BEFORE DOING ANYTHING ELSE

**The autopilot coordinator MUST NEVER ask the user to confirm a plan, select a scope, choose between options, or approve a proposal mid-run.** This command is fire-and-forget by design — the user typed it expecting unattended progress. The only valid reasons to halt are the documented **hard stops** below; everything else is resolved silently by the auto-plan rules and the loop continues.

Asking "Continue?" "Which next?" "Looks like X — proceed?" mid-run is a **violation of this rule**. Apply the auto-plan, run the next iteration, and if the run cannot continue safely, emit the final summary and exit.

**⛔ MENU ANTI-PATTERN — EXPLICITLY FORBIDDEN**: If you find yourself about to display a numbered list of options (e.g. "1. Run on T841 2. Run on T1006 3. Skip..."), STOP. Do NOT display that list. Instead: pick the highest-throughput option automatically (fast batch, lowest-ID eligible tasks, N=1 if needed) and execute it silently. The user will never see a menu from this command — they will only see work getting done. Displaying a menu and waiting for a keypress is equivalent to refusing to work.

**⛔ CONTEXT WINDOW PANIC — FORBIDDEN STOP REASON**: "A full run would spawn 30+ subagents and consume major context" is NOT a valid reason to stop or ask. Claude Code has a 1M-token context window. The `context_budget_tokens` value in AGENT_CONFIG.md is a **context assembly budget** (how many tokens to use when building task context for a subagent) — it is NOT the model's total context limit. Stopping because of perceived context cost is a complexity-aversion stop, which is forbidden.

### ⛔ ANTI-QUITTING RULE — EQUALLY MANDATORY

**Stopping because tasks appear "complex," "feature-class," "large," or "need scoping decisions" is a VIOLATION of this command.** Those are not hard stops. The hard-stop table is exhaustive — there is no ninth stop.

**"No runnable work"** means EVERY remaining task fails at least one of the explicit 6-condition member authorization checks or a defined hard stop. It does NOT mean "I assessed the tasks and they look difficult." Complexity is never a stop reason.

**The paradox guard**: If you would list a task in "Next safe commands," you MUST have attempted it in this run. Any task that passes all 6 checks is runnable. Run it — at N=1 bucket (no swarm) if necessary. Do not list it and then not run it.

**Large-task handling**: When remaining tasks are individually large or multi-file, attempt them one at a time using N=1 bucket (single implementer + single reviewer) rather than refusing to batch-process them. A large task that is attempted and fails cleanly is better than a large task that was never tried.

**Task selection ordering (MANDATORY)**: After computing the runnable queue (all tasks passing the 6-condition check), select tasks in this order:
1. `priority: critical` tasks first (any ID)
2. Then by **task ID ascending** — lowest numeric ID runs first

`execution_cost`, `blast_radius`, task section name, and recency of surrounding work are NOT selection criteria. They affect N (bucket count) and reviewer thoroughness only. The autopilot MUST run the lowest-ID eligible task rather than self-selecting based on perceived complexity, cost, or "warm context." Cherry-picking higher-ID tasks over lower-ID eligible tasks is a spec violation equivalent to a complexity-aversion stop.

**Controller-only fallback**: When ALL workspace-routed tasks block because every member repo is dirty or has a write-policy mismatch, do NOT stop — automatically fall back to `--controller-only` for that iteration and run any task whose `workspace_touch_policy` is `source_only` or `docs_only`. Only stop when the controller-only queue is also empty or blocked.

---

## Default Configuration

| Knob | Default | Override |
|------|---------|----------|
| Mode | `--swarm --workspace` (T532 expands to manifest-declared repos) | `g-go-go --controller-only` to skip workspace expansion |
| Heartbeat interval | 30 minutes wall-clock | `g-go-go --heartbeat 15m` |
| Run budget (max iterations) | 12 implementation/review cycles | `g-go-go --budget 5` or `--budget 25` |
| Max parallel implementers | 5 (per swarm hard cap) | inherited from `g-go --swarm` |
| Review independence | one fresh reviewer agent per implementation checkpoint | non-overrideable |
| Backend dependency | file-first; `gald3r_valhalla` optional | tasks declaring backend dependency in their YAML are deferred when backend down |
| Verification retry ceiling | 3 FAIL cycles → `[🚨]` (T047) | non-overrideable |
| Auto-merge target | `dev` (B+C pattern — Bot handles dev, Contributor controls main) | `g-go-go --target-branch main` to ship PASS items directly to main |
| Auto-merge behavior | enabled by default after every PASS verdict | `g-go-go --no-auto-merge` to preserve old `[MERGE-BLOCKED]` behavior |

`g-go-go` accepts the same `$ARGUMENTS` filters as `g-go` (`tasks N,M`, `bugs BUG-NNN`, `subsystem ...`, `bugs-only`, `tasks-only`) plus the autopilot knobs above.

---

## PCAC Inbox Gate (Before Claiming Work)

Before each loop iteration claims work, run the re-callable PCAC inbox check:

```powershell
$hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1", ".agent\hooks\g-hk-pcac-inbox-check.ps1", ".codex\hooks\g-hk-pcac-inbox-check.ps1", ".opencode\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { powershell -NoProfile -ExecutionPolicy Bypass -File $hook -ProjectRoot . -BlockOnConflict }
```

> **Tool routing (BUG-031)**: invoke this snippet through the **PowerShell tool**, not Bash. PowerShell-only syntax (`@(...)` array, `Where-Object`, `Test-Path`) routed to Bash produces a parse error such as ``syntax error near unexpected token `('``  — that failure is a tool-selection error, **NOT** a real PCAC conflict gate.

If the check reports `INBOX CONFLICT GATE` or exits with code `2`, **HARD STOP**: emit the final summary and exit. Do not claim more work, spawn more agents, or commit.

The autopilot also re-runs the PCAC inbox check at every heartbeat interval and once before each rolling-wave bucket spawn.

---

## Gald3r Housekeeping Commit Gate (T531)

Before each iteration claims/spawns/commits, run the safety classifier helper at the orchestration root:

```powershell
.\scripts\gald3r_housekeeping_commit.ps1 -Mode preflight -Apply -Json
```

Behavior matches `g-go`:

- **`clean`** — continue.
- **`safe-gald3r-housekeeping`** — helper auto-commits classified-safe `.gald3r/` paths into a focused `chore(gald3r): preflight gald3r housekeeping` commit; loop continues.
- **`unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` / unknown / member `config-fault`** — **HARD STOP** with the exact unsafe paths listed.

After every coordinator-owned shared write, re-run with `-Mode post-write -Apply` to land safe coordination state in a `chore(gald3r): commit g-go coordination state` commit before the next phase.

---

## Clean Controller Gate + Touch-Set v1/v2

Same per-root contract as `g-go --workspace`:

- Orchestration root is **always** in the touch set.
- v1 — every manifest member listed in any selected task's `workspace_repos:` joins the touch set.
- v2 — optional `extended_touch_repos:`, swarm `touch_repos:` handoffs, and absolute paths from subsystem `locations:` may union additional roots.
- Each root gets its own `git status --short`. Unrelated dirty paths in any per-repo touch set block coordinator-owned writes to that repo only — they do **not** block unrelated clean repos.
- The marker-only `.gald3r/` invariant for `controlled_member` and `migration_source` repositories remains absolute. `g-go-go` does NOT relax it.

If a per-root gate fails, the autopilot defers ALL work routed to that repo and **continues** with work routed to clean repos only — until no runnable work remains, at which point it stops with a final summary.

### Member-scoped task authorization

A selected task may run against a member repository only when ALL of the following are true (same six-condition contract as `g-go --workspace`):

1. The member's manifest `repository.id` appears in the task's `workspace_repos:` list.
2. The task's `workspace_touch_policy` is in the manifest entry's `allowed_write_policy.allowed_touch_policies`.
3. The manifest entry's `allowed_write_policy.write_allowed` is `true`.
4. Every dependency, blocker, PCAC inbox, and `[🚨]` check passes for that member root.
5. Per-repo clean check passes (or `-AllowDirty` is documented per-root in the task's `## Status History`).
6. No member `.gald3r/` control-plane path is targeted (marker-only invariant).

If any check fails for a member, the autopilot defers that task with a per-repo reason and continues. Autopilot **never** silently degrades authorization to keep the loop running.

---

## The Autopilot Loop

```
INIT
  ├─ PCAC inbox gate (HARD STOP on conflict)
  ├─ Housekeeping preflight at orchestration root
  ├─ Clean Controller Gate per-root
  ├─ Initialize: iter=0, budget_remaining=12 (or user override)
  └─ Snapshot: tasks, bugs, manifest at start

LOOP (iter < budget_remaining)
  ├─ Re-evaluate runnable queue (T532 workspace selection unless --controller-only)
  ├─ If queue is truly empty (every task fails an explicit 6-condition check) → STOP (all-clear)
  │   NOTE: "looks complex" or "feature-class" is NOT empty. See Anti-Quitting Rule above.
  ├─ If all workspace-routed tasks block on member repo issues, fall back to --controller-only
  │   for this iteration and retry source_only / docs_only tasks before stopping.
  │
  ├─ [BUG-FIX INTERLACE] Before Phase 1 task work each iteration:
  │   ├─ Check BUGS.md for any Open bugs with severity critical or high
  │   │   If found → run @g-go-bugs severity:critical,high FIRST (within this iteration)
  │   │   This ensures high-severity bugs (T1114 auto-bridged) don't sit behind lower-priority tasks
  │   ├─ After critical/high bug-fix pass: proceed to Phase 1 task work (existing behavior)
  │   └─ If budget_remaining > 1 and task queue is clear: run @g-go-bugs severity:medium,low
  │       (capacity-permitting low-severity sweep)
  │
  ├─ Phase 1 (g-go-code --swarm --workspace protocol):
  │   ├─ Skip non-expired [📝] / [🔄] / [🕵️] claims
  │   ├─ Partition into N buckets (N = smart agent count from g-go)
  │   ├─ Pre-create one coding worktree per bucket
  │   ├─ Spawn N implementer subagents (handoff mode — return patches/artifacts/evidence/proposed-status only)
  │   ├─ Wait for all bucket handoffs
  │   ├─ Pre-Reconciliation Clean Gate per-root (HARD STOP on dirty drift)
  │   ├─ Coordinator reconciles bucket patches into primary checkout one at a time
  │   ├─ Coordinator owns shared writes: TASKS.md, BUGS.md, task/bug status files,
  │   │   CHANGELOG.md, generated Copilot prompts, parity output, per-repo final staging
  │   ├─ Coordinator creates per-repo code-complete checkpoint commits
  │   └─ phase1_results = list of [🔍] items per bucket
  ├─ Phase 2 (g-go-review --swarm protocol):
  │   ├─ Spawn M fresh reviewer subagents (no Phase 1 context)
  │   ├─ Each reviewer runs from a review-swarm worktree based on the Phase 1 checkpoint
  │   ├─ Reviewers return PASS/FAIL payloads + Status History rows + evidence (no writes)
  │   ├─ Coordinator batch-writes TASKS.md/BUGS.md verdicts (PASS → [✅], FAIL → [📋])
  │   ├─ Coordinator creates per-repo review-result commits (PASS, FAIL, mixed)
  │   └─ Detect ≥3 FAIL cycles per item → [🚨] Requires-User-Attention (T047)
  ├─ Heartbeat check: if elapsed >= heartbeat_interval, emit heartbeat summary
  ├─ Increment iter; recompute budget_remaining
  └─ Loop again

EXIT
  └─ Emit final summary
```

The loop never blocks on `[🔍]` dependencies of newly runnable downstream work unless the dependent task declares `requires_verified_dependencies: true`. Review failures that invalidate downstream checkpoints requeue the affected items.

---

## Hard Stops (autopilot HALTS, emits final summary, exits)

| Stop reason | Trigger | Action |
|-------------|---------|--------|
| **PCAC conflict** | inbox check exit code `2` | halt before next claim |
| **Unsafe dirty orchestration root** | housekeeping gate returns `unsafe-gald3r` / `mixed-dirty` / `conflict` / `drift-detected` | halt; do not stage |
| **Unsafe dirty member root** for ALL routed work | every selected member root has unrelated dirty paths | halt with per-root listing |
| **Marker-only violation** | guard helper rejects member `.gald3r/` write | halt; log file + reason |
| **Secret detection** | secret-pattern scanner fires on staged content | halt; do not commit |
| **Missing required dependency** | task has `requires_verified_dependencies: true` and any dep is non-`[✅]` | skip task; if all queue is so blocked → halt |
| **`[🚨]` user-attention item** | task or bug has user-attention status | skip item; never auto-retry |
| **`[⏸️]` paused task** | task is in `paused` status / `tasks/paused/` folder | skip item; never auto-claim; user must manually unpause |
| **`[🚫]` cancelled task** | task is in `cancelled` status / `tasks/cancelled/` folder | skip item; terminal state; never eligible for autopilot |
| **Verification retry ceiling** | task has ≥3 FAIL cycles in Status History | mark `[🚨]`; halt if all queue is `[🚨]` |
| **Run budget exhausted** | `iter >= budget_remaining` | clean halt |
| **No runnable work** | recomputed queue is empty after a successful iteration — meaning EVERY remaining task fails at least one explicit 6-condition check or a listed hard stop. Complexity, task size, and "needs scoping" are NOT valid reasons. If ANY task passes all 6 checks, it is runnable — attempt it. | clean halt |
| **Manifest unparseable** | `workspace_manifest.yaml` missing/broken on a multi-repo run | halt; report manifest error |
| **Workspace-Control preflight denial** | unknown manifest repo IDs / not a git root / unauthorized routing | halt with the specific blocker |

Hard stops are not failures — they are the **purpose** of the safety contract. The final summary documents the stop reason and the next safe command.

---

## Heartbeat Summary (every `heartbeat_interval`)

```
[AUTOPILOT] Heartbeat — iter {N} / budget {B} — elapsed {HH:MM}
[AUTOPILOT] Mode: {workspace|controller-only}, swarm: {N implementers / M reviewers}
[AUTOPILOT] Active repos: {ids touched this run}
[AUTOPILOT] Completed → [✅]: {count}    Awaiting review → [🔍]: {count}    Failed → [📋]: {count}    [🚨]: {count}
[AUTOPILOT] Currently implementing: {task IDs in flight}
[AUTOPILOT] Currently reviewing:    {task IDs in review}
[AUTOPILOT] Per-repo blockers: {repo_id → reason, ...}
[AUTOPILOT] Next iteration starts in: {seconds}
```

Heartbeats are append-only to the session output; they do NOT trigger user prompts.

---

## File-First Fallback

`g-go-go` MUST work without `gald3r_valhalla` services. Optional backend failures are surfaced and degraded:

- Vault MCP unavailable → file-first vault reads only; tasks that explicitly declare `requires_backend: true` in their YAML are deferred with `Deferred — gald3r_valhalla unavailable` in the summary.
- Memory MCP unavailable → no memory capture/recall; loop continues using local task/bug specs only.
- Oracle MCP unavailable → tasks routed through Oracle subsystems are deferred.
- Platform-docs search unavailable → loop falls back to local docs reads.

Never crash on optional backend failure; deferring affected work and continuing is the safe default.

---

## Final Summary

```markdown
## g-go-go Autopilot Session Summary

### Run config
- Mode: {workspace|controller-only} {+swarm}
- Budget: {used}/{max} iterations
- Elapsed: {HH:MM}
- Stop reason: {hard stop name OR "no runnable work" OR "budget exhausted"}

### Per-iteration log
| Iter | Implementers | Reviewers | [✅] | [📋] | Checkpoint commit | Review commit |
|------|--------------|-----------|-----|-----|-------------------|---------------|
| 1    | 3            | 2         | 4   | 1   | abc123            | def456        |
| 2    | 2            | 1         | 2   | 0   | 789abc            | 012def        |

### Repos touched
- gald3r_dev: {commits} commits, last {sha}
- gald3r_template_full: SKIPPED (unrelated dirty: .github/...)
- gald3r_throne: {commits} commits, last {sha}

### Failed / blocked items
- Task {id}: FAIL — {reason}; ≥3 cycles → marked [🚨]
- Bug BUG-{id}: blocked — {reason}

### Final state
- ✅ Completed (verified): {N}
- 📋 Failed (back to pending): {M}
- 🚨 Requires user attention: {U}
- ⏸️  Skipped (blocked): {K}
- Total commits this run: {C}

### Next safe command
@g-go-go --budget 5    # if you want another short run
@g-go tasks {failed_ids}    # to retry specific failures
@g-pcac-read    # if a PCAC conflict halted the run
```

---

## Behavioral Rules

| Rule | Why |
|------|-----|
| Bare `/g-go` is unchanged — `/g-go-go` is a separate explicit command | Autopilot must be opt-in, never silent |
| **Complexity aversion stops are forbidden** — "feature-class," "needs scoping," or "too large" never qualify as "no runnable work" | Anti-Quitting Rule: hard-stop table is exhaustive |
| **Paradox guard** — any task in "Next safe commands" must have been attempted this run; if not, that is a spec violation | Fire-and-forget means: do it, don't suggest it |
| **Large tasks run at N=1** — attempt complex tasks individually (single bucket, single reviewer) rather than refusing to process them | Attempting and failing is better than not attempting |
| **Task selection ordering** — within the runnable queue, `critical` tasks first, then lowest task ID first; `execution_cost`, `blast_radius`, and recency are NOT selection signals | Prevents cherry-picking easy high-ID tasks over foundational low-ID work |
| **TASKS.md dual-format scan (MANDATORY)** — TASKS.md contains tasks in two formats that MUST both be scanned: (1) bullet-list `- [STATUS] **Task NNN**:...` and (2) markdown-table `\| [STATUS] \| [NNN](path) \| title \| type \| deps \|`. A grep that only matches the bullet format silently drops the entire table backlog. Before declaring "no runnable work", verify both patterns were searched. Missing table-format tasks and claiming the queue is empty is a spec violation equivalent to a complexity-aversion stop. | Queue completeness — prevents silent task starvation |
| **Dependency resolution includes archive (MANDATORY)** — when checking condition 4 (all dependencies resolved), if a dependency task file is NOT found in `.gald3r/tasks/task{id}_*.md`, ALSO check `.gald3r/archive/tasks/*/task{id}_*.md`. A task found in the archive with `status: completed` (or `status: verified`) counts as a fully satisfied dependency. Never treat a missing-in-active-tasks dependency as unresolved without first checking the archive. Marking a task as blocked because a dep "file not found" when that dep lives in the archive is a spec violation equivalent to a complexity-aversion stop. | Prevents archived completed deps from silently blocking downstream chains |
| **Controller-only fallback** — when all workspace member repos block, retry `source_only`/`docs_only` tasks before stopping | Never stop while controller-only work remains |
| **Auto-merge member repo branches on PASS (MANDATORY)** -- after the review-result commit for each PASS item, run `gald3r_worktree.ps1 -Action MergeToMain -RepoPath <member_path> -TaskId {id} -TargetBranch dev -Apply` in dependency order (lowest ID first); default target is `dev` (B+C pattern — Bot handles dev, Contributor controls main); override with `--target-branch main` to ship directly to main; on success the helper FF-merges the code branch into `dev` (or override target) and deletes both code + review branches and worktree folders; log `[AUTO-MERGED→dev]` in session summary; on merge-blocked (conflict), missing target branch, or member-dirty: preserve branch, log `[MERGE-BLOCKED]` / `[MERGE-SKIPPED-DIRTY]` as human action item (fallback, not default); pass `--no-auto-merge` to skip entirely and use old `[MERGE-BLOCKED]` behavior; never run auto-merge for FAIL items | Eliminates manual branch merge ceremony after every autopilot run — B+C pattern keeps human in control of dev→main promotion |
| Autopilot composes existing safe primitives — never bypasses any gate | One command, same safety contract |
| Implementation agents NEVER self-verify their own work | Adversarial independence preserved across all loop iterations |
| Hard stops emit final summaries and exit cleanly | Stops are not failures; they are the safety boundary |
| Run budget bounds the loop | Prevents runaway autonomous runs |
| Heartbeats are output-only — never prompt the user | Fire-and-forget design |
| File-first fallback when optional backends are down | `gald3r_valhalla` is optional, not required |
| Per-repo commits only — no cross-repo single commits | Each manifest member is an independent git root |
| Marker-only `.gald3r/` invariant is absolute | Member control-plane writes are forbidden, period |
| `[🚨]` items are NEVER auto-retried | Human-only resolution by policy (T047) |

---

## Usage Examples

```
@g-go-go
@g-go-go --budget 5
@g-go-go --heartbeat 15m
@g-go-go --controller-only
@g-go-go --controller-only --budget 3
@g-go-go tasks 220, 222, 223
@g-go-go bugs-only
@g-go-go subsystem multiple-ide-platform-parity
@g-go-go --target-branch main           # ship PASS items directly to main instead of dev
@g-go-go --no-auto-merge                # disable auto-merge; reviewer leaves [MERGE-BLOCKED] for human
@g-go-go --target-branch staging        # merge to a custom branch instead of dev
```

The defaults (workspace mode, 12-iteration budget, 30-minute heartbeat) are tuned for a multi-hour overnight or background run. Use `--budget 3` and `--heartbeat 5m` for quick autopilot bursts.

**For supervised pipeline runs (one batch only), use `@g-go --swarm --workspace` instead — that is one iteration of this loop.**

Let's go.
