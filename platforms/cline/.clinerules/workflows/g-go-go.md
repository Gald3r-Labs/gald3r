---
subsystem_memberships: [TASK_MANAGEMENT]
---
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

**⛔ DISGUISED CONTEXT-PANIC STOPS ARE THE SAME VIOLATION (BUG-107)**: Relabeling a context-pressure halt as a "session checkpoint", "handing off cleanly", "natural stopping point", "I've made good progress — the rest can continue in a fresh session", or any similar softened phrasing does NOT make it valid. It is the forbidden CONTEXT WINDOW PANIC stop wearing a gentler name, and it is the single most common way this rule is broken under load. Enforcement is **self-naming, not self-soothing**:
- If you feel the urge to stop and the underlying reason is context size, subagent count, elapsed iterations, or *anticipated* future accumulation → you MUST either (a) run the next lowest-ID eligible iteration anyway (at N=1 bucket if needed), or (b) if and only if a genuine hard-stop row applies, **quote that hard-stop row verbatim** as your stop reason. There is no third move.
- You may NOT invent a "checkpoint" as a substitute for the next iteration you are avoiding. A mid-run checkpoint is valid ONLY when emitted by the documented checkpoint mechanism *between completed iterations while the loop continues* — never as the loop's exit.
- Before emitting ANY non-final-summary stop, you must be able to point to the exact hard-stop table row that authorizes it. "Context", "complexity", "this is a good place to pause", and "to be safe" are not rows. If no row matches, the correct action is to keep going.

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
| Max parallel implementers | 5 (per swarm hard cap) | `g-go-go --no-code-swarm` to run Phase 1 sequentially (1 coder at a time) |
| Phase 1 driver | `g-go-code-swarm` (N parallel coders → checkpoint → Phase 2) | `--no-code-swarm` reverts Phase 1 to sequential `g-go-code` |
| Review independence | one fresh reviewer agent per implementation checkpoint | non-overrideable |
| Backend dependency | file-first; `example_app` optional | tasks declaring backend dependency in their YAML are deferred when backend down |
| Verification retry ceiling | 3 FAIL cycles → `[🚨]` (T047) | non-overrideable |
| Auto-merge target | `main` (feature-branches-only model — NO `dev` branch; see `g-rl-02`) | `g-go-go --target-branch <branch>` to merge PASS items to a different branch |
| Auto-merge behavior | enabled by default after every PASS verdict | `g-go-go --no-auto-merge` to preserve old `[MERGE-BLOCKED]` behavior |
| Repo scope filter | (none — global scope across all manifest members) | `g-go-go --repos <repo_id>[,<repo_id>...]` to scope autopilot to tasks whose `workspace_repos:` contains at least one of the listed IDs. Skipped tasks (not in scope) are NOT marked failed — they're left for the next run. Budget counter only counts iterations that execute in-scope tasks. Example: `g-go-go --repos example_agent --budget 3` runs only `example_agent` tasks. |
| Context-aware throttle | **on** (default) | `g-go-go --no-context-aware` to disable throttling and allow full N under all context levels. See "Context-Aware Throttle (BUG-107 Fix Direction #3)" below. |

`g-go-go` accepts the same `$ARGUMENTS` filters as `g-go` (`tasks N,M`, `bugs BUG-NNN`, `subsystem ...`, `bugs-only`, `tasks-only`) plus the autopilot knobs above.

### `--repos` filter (T1152)

When `--repos <repo_id>` is supplied, the autopilot's runnable-queue scan filters to tasks where `workspace_repos:` contains at least one of the requested ids. The 6-condition member-auth check applies normally to each surviving candidate. Non-matching tasks are NOT marked failed — they're silently deferred to a future run.

Multiple repos can be comma-separated: `--repos example_agent,example_desktop`. Auto-merge target is `main` (feature-branches-only model — there is no `dev` branch) unless `--target-branch` overrides.

Budget accounting: the iteration counter (`iter`) only increments when at least one in-scope task is actually attempted (claimed and run through Phase 1/Phase 2). Iterations that find an empty in-scope queue (because all remaining work is out-of-scope or blocked) terminate the run with the standard "no runnable work" hard stop — they do NOT burn budget on no-ops.

`--repos` composes with all other filters: `g-go-go --repos example_agent --controller-only` is a no-op (example_agent tasks are workspace-routed by definition, so the controller-only mode strips them all). Use either `--repos` OR `--controller-only`, not both.

---

## Stop-Detection Re-Invoke Hook (BUG-107 Fix Direction #2)

Spec language alone (the forbidden-stop blocks above) cannot guarantee model compliance under context pressure. The `g-hk-ggo-stop-detect` stop hook makes the no-early-stop contract **mechanically self-enforcing**: if the autopilot loop halts mid-run without quoting an authorizing hard-stop row, the hook forces it to continue.

### Run-state marker — `.gald3r/logs/ggo_run_state.json`

The autopilot maintains a single run-state marker that the stop hook reads. The coordinator MUST:

1. **At INIT** — write the marker with the run config:
   ```json
   { "active": true, "platform": "cline",
     "iter": 0, "budget_remaining": 12,
     "authorized_hard_stop": "", "reinvoke_count": 0,
     "updated_at": "<iso-8601>",
     "completed_iterations": [] }
   ```
   Set `"platform"` to `"cline"` (matches the value the stop hook detects from
   its script location). The `session_id` field is NOT written at INIT; the stop
   hook captures it on the first stop via the stop-event stdin payload
   (first-touch registration). Stops from a different platform or session are
   always allowed through without re-invocation.
2. **Each iteration** — refresh `iter` and `budget_remaining` (the hook reads the latest values to bound re-invokes).
3. **On a genuine hard stop** — BEFORE emitting the final summary, write the exact hard-stop table row verbatim into `authorized_hard_stop`. This is the ONLY way to legitimately end the run. A blank `authorized_hard_stop` means "the loop has no authorized reason to stop".
4. **At clean EXIT** (budget exhausted, no runnable work) — set `active` to `false` or delete the marker. The hook also clears it automatically on authorized hard stop, budget exhaustion, or re-invoke-cap.

### What the hook enforces

When the `stop` event fires with an active marker, `g-hk-ggo-stop-detect.ps1`:

- **Allows the stop** when `authorized_hard_stop` is populated (genuine hard stop), when `budget_remaining <= 0` (budget cap IS a hard stop), or when the re-invoke cap is hit.
- **Re-invokes the loop** otherwise — it increments `reinvoke_count` and returns a stop-continuation decision (`decision:block` for Claude Code / `continue:false`+`followup` for Cursor) carrying a verbatim reminder of the forbidden stop reasons. A disguised "checkpoint" cannot end the run.

### Bounding (never infinite-loops)

Re-invokes are capped at `min(budget_remaining, 25)`. A genuine hard stop and budget exhaustion are always honored and never re-invoked. The re-invoke ceiling is the anti-infinite-loop fail-safe: if it is ever reached, the hook allows the exit and treats it as a hard stop. This satisfies the contract that re-invocation always respects genuine hard stops and the configured budget cap.

> The hook is a **no-op** when no `ggo_run_state.json` marker exists — ordinary, non-autopilot stop events are never affected. See `hooks/g-hk-ggo-stop-detect.md` for the full self-description.

---

## Context-Aware Throttle (BUG-107 Fix Direction #3)

Context-aware throttling is **ON by default**. Every `g-go-go` run applies a deterministic N-reduction based on context usage — instead of stopping when context is tight, the loop **reduces N (the parallel bucket / implementer count)** so the run continues with less parallelism. Trading parallelism for continuation is always preferred over halting.

Use `--no-context-aware` to disable throttling entirely (full N at all context levels, for short/controlled runs where you want maximum throughput and are managing context yourself).
### Behavior

Each iteration computes its bucket count N as usual (smart agent count from `g-go --swarm`, hard cap 5), then applies a deterministic reduction based on a deterministic context proxy: the completed iteration count (`iter`) read from `ggo_run_state.json`. This proxy is always observable and eliminates dependence on the model's self-reported context fill percentage, which was the root failure mode in BUG-107.

  | Context proxy condition                          | N adjustment |
  |--------------------------------------------------|--------------|
  | `iter < 4`  (early run, compression active)      | no change (full N) |
  | `iter 4–6`  (mid run)                            | `N = ceil(N / 2)` |
  | `iter 7–9`  (late run)                           | `N = 2` (or current N if already lower) |
  | `iter >= 10` (deep run)                          | `N = 1` (single implementer, single reviewer) |

> **Compression is the primary context management mechanism** (see inter-iteration compression in the LOOP below). The throttle is a secondary adjustment: even with full compression, spawning N=5 new buckets on a late iteration adds meaningful current-iteration context, so reducing N under late-run conditions is still useful. But throttle alone — without compression — cannot prevent O(n²) accumulation, because it only reduces future additions, not existing history.

- **N is never reduced below 1.** A reduced N still runs the next lowest-ID eligible task — reduction throttles parallelism, it never skips or defers work for context reasons.
- The reduction is **per-iteration and reversible**: when context pressure subsides on a later iteration, N is recomputed from the table and may rise back toward the full smart count.
- Context-aware reduction is **never a stop reason**. Reducing to N=1 and continuing is the correct response to context pressure — halting is the forbidden CONTEXT WINDOW PANIC stop (see above).

### Interaction with the stop-detection hook

The context-aware throttle is the proactive valve; the stop-detection hook is the reactive backstop. Under pressure the loop first throttles N (Fix #3); if the agent still attempts an unauthorized halt, the hook re-invokes it (Fix #2). Together they close BUG-107 from both directions.

---

## Task/Bug Inbox Intake (T1573 — First Step Each Iteration)

Before the PCAC gate, before any claim, run the inbox intake to absorb any tasks/bugs
dropped into the gitignored staging zones during this or a prior run:

```powershell
uv run python custom_scripts\hot_inbox_intake.py -ProjectRoot . -Quiet
```

If `N > 0` items were ingested: log `"Ingested N task(s) / M bug(s) from inbox"` and continue.
If inbox is empty: exits 0, no output, no commit — continue immediately.

> **Why this runs first**: Writing to `TASKS.md` or `BUGS.md` outside the iteration's
> coordinator staging allowlist triggers the Housekeeping Commit Gate `mixed-dirty`
> hard-block. The intake script is the sole writer of those index files in its commit,
> so the gate classifies it as `safe-gald3r-housekeeping` and allows it. Running intake
> before the PCAC and clean gates ensures the tree is already normalized when those
> gates run.

> **Tool routing**: invoke through the **PowerShell tool**, not Bash (same reason as PCAC hook below).

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

## Integration-Branch Detection + Divergence Hard-Stop (T1443 / BUG-099 recurrence prevention)

BUG-099 occurred because the autopilot blindly defaulted to a long-lived `dev` integration
branch even when it was ~143k lines behind the active feature branch. The `dev`/`test` model is
now retired (see `g-rl-02-git_workflow` — feature-branches-only). The integration target is
**`main`**. The detection + divergence guard below is retained to prevent any stale-target
recurrence.

### Detection heuristic (read-only — no checkout/commit/merge side effects)

1. **Default integration target is `main`** — the single permanent branch.
2. **Prefer the branch the main checkout is currently on** when it is a `feature/*` or `fix/*`
   branch actively being integrated (`git rev-parse --abbrev-ref HEAD`); otherwise use `main`.
3. **NEVER select a branch that is strictly *behind* a candidate** (the BUG-099 failure):
   compute ahead/behind with `git rev-list --left-right --count A...B` and disqualify a target
   that is behind the active source branch.
4. The `--target-branch <name>` override still applies, but is validated against the same
   divergence gate below — an explicit stale target also hard-stops.

### Divergence hard-stop

When the chosen integration target and the active work branch **diverge beyond a configured
threshold**, HARD-STOP with a clear message instead of blindly merging:

- Threshold default: target is **> 200 commits behind** the source, OR the two branches have
  diverged (both ahead of their merge-base) by **> 50 commits on the target side**. Configurable
  via `integration_divergence_max_commits` in `AGENT_CONFIG.md`.
- A target that cannot fast-forward from the source (would require a merge commit / conflict) is
  reported by `gald3r_worktree.ps1 -Action MergeToMain` as `merge-blocked` and is **never**
  force-updated; the autopilot logs `[MERGE-BLOCKED]` as a human action item.

This detection runs once at INIT (read-only). The actual integration is performed only at the
per-PASS auto-merge step via `gald3r_worktree.ps1 -Action MergeToMain` (FF-only, `-Apply`).

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
  ├─ Integration-branch detection (T1443 — HARD STOP on excessive divergence; see below)
  ├─ Clean Controller Gate per-root
  ├─ Initialize: iter=0, budget_remaining=12 (or user override)
  ├─ Write run-state marker .gald3r/logs/ggo_run_state.json
  │   { active:true, iter:0, budget_remaining:B, authorized_hard_stop:"", reinvoke_count:0 }
  └─ Snapshot: tasks, bugs, manifest at start

LOOP (iter < budget_remaining)
  ├─ Re-evaluate runnable queue (T532 workspace selection unless --controller-only)
  ├─ If --repos <ids> supplied: filter queue to tasks whose workspace_repos: intersects <ids>
  │   (T1152) Out-of-scope tasks are NOT marked failed — deferred for a future run.
  │   Apply the 6-condition member-auth check to surviving candidates normally.
  ├─ If queue is truly empty (every task fails an explicit 6-condition check) → STOP (all-clear)
  │   NOTE: "looks complex" or "feature-class" is NOT empty. See Anti-Quitting Rule above.
  ├─ If all workspace-routed tasks block on member repo issues, fall back to --controller-only
  │   for this iteration and retry source_only / docs_only tasks before stopping.
  │   NOTE: When --repos is active, controller-only fallback is DISABLED — controller-only
  │   work is by definition out-of-scope when the user has narrowed to specific member repos.
  │
  ├─ [BUG-FIX INTERLACE] Before Phase 1 task work each iteration:
  │   ├─ Check BUGS.md for any Open bugs with severity critical or high
  │   │   If found → run @g-go-bugs severity:critical,high FIRST (within this iteration)
  │   │   This ensures high-severity bugs (T1114 auto-bridged) don't sit behind lower-priority tasks
  │   ├─ After critical/high bug-fix pass: proceed to Phase 1 task work (existing behavior)
  │   └─ If budget_remaining > 1 and task queue is clear: run @g-go-bugs severity:medium,low
  │       (capacity-permitting low-severity sweep)
  │
  ├─ Refresh run-state marker: update iter + budget_remaining (the stop hook reads these to bound re-invokes)
  ├─ Phase 1 — CODING SWARM (invoke `g-go-code-swarm`):
  │   ⚡ The coordinator MUST invoke `g-go-code-swarm` (equivalent: `g-go-code --swarm`) as the
  │      Phase 1 sub-driver — NOT bare `g-go` or `g-go-code`. This is what makes Phase 1 parallel.
  │      Exception: `--no-code-swarm` flag → fall back to sequential `g-go-code` (1 task at a time).
  │   ├─ Skip non-expired [📝] / [🔄] / [🕵️] claims
  │   ├─ Compute N = smart agent count from g-go swarm partition logic (hard cap: 5)
  │   │   If --context-aware: reduce N per the context-usage table (never below 1); reversible per-iteration
  │   │   If --no-code-swarm: force N=1 (sequential coding, no parallel buckets)
  │   ├─ Invoke `g-go-code-swarm` with the partitioned queue and computed N:
  │   │   - g-go-code-swarm pre-creates one T170 coding worktree per bucket
  │   │   - g-go-code-swarm spawns N implementer subagents in parallel (handoff mode)
  │   │     Each bucket agent returns: patch bundle, artifacts, evidence, proposed status rows
  │   │     Bucket agents MUST NOT write shared .gald3r/ files, CHANGELOG, or commits
  │   ├─ WAIT for all N bucket handoffs before proceeding (fan-in barrier)
  │   ├─ Pre-Reconciliation Clean Gate per-root (HARD STOP on dirty drift)
  │   ├─ Coordinator reconciles bucket patches into primary checkout one at a time (deterministic order)
  │   ├─ Coordinator owns all shared writes: TASKS.md, BUGS.md, task/bug status files,
  │   │   CHANGELOG.md, generated Copilot prompts, parity output, per-repo final staging
  │   ├─ Coordinator creates per-repo code-complete checkpoint commits
  │   └─ phase1_results = list of [🔍] items per bucket
  ├─ Phase 2 — REVIEW SWARM (invoke `g-go-review-swarm`):
  │   ⚡ The coordinator invokes `g-go-review-swarm` (equivalent: `g-go-review --swarm`) as the
  │      Phase 2 sub-driver, passing the Phase 1 checkpoint branch/SHA as the review source.
  │   ├─ Spawn M fresh reviewer subagents in parallel (no Phase 1 context — independence guaranteed)
  │   ├─ Each reviewer runs from a review-swarm worktree based on the Phase 1 checkpoint
  │   ├─ Reviewers return PASS/FAIL payloads + Status History rows + evidence (no writes)
  │   ├─ Coordinator batch-writes TASKS.md/BUGS.md verdicts (PASS → [✅], FAIL → [📋])
  │   ├─ Coordinator creates per-repo review-result commits (PASS, FAIL, mixed)
  │   └─ Detect ≥3 FAIL cycles per item → [🚨] Requires-User-Attention (T047)
  ├─ [INTER-ITERATION COMPRESSION] Mandatory before iter increment:
  │   ├─ Serialize this iteration's result into a compact summary (≤100 words):
  │   │   { iter, phase1_tasks[], phase1_verdict, phase2_tasks[], phase2_verdict,
  │   │     checkpoint_sha, review_sha }
  │   ├─ Append the compact summary to ggo_run_state.json .completed_iterations[]
  │   ├─ Update ggo_run_state.json .updated_at = now
  │   ├─ DISCARD the full raw Phase 1 + Phase 2 conversation outputs from working
  │   │   context. The compact summary IS the entire record for this iteration.
  │   │   Bucket patches, evidence blobs, and verbose handoff payloads are NOT
  │   │   retained in the coordinator's conversational history after this step.
  │   └─ The coordinator's primary context for subsequent iterations is:
  │       - TASKS.md + BUGS.md (re-read fresh each iteration)
  │       - ggo_run_state.json .completed_iterations[] (compact summaries only)
  │       - Current iteration's own Phase 1/Phase 2 outputs
  ├─ Heartbeat check: if elapsed >= heartbeat_interval, emit heartbeat summary
  ├─ Increment iter; recompute budget_remaining
  └─ Loop again

EXIT
  ├─ On a genuine hard stop: write the verbatim hard-stop row into the marker's
  │   authorized_hard_stop field BEFORE emitting the summary (this authorizes the stop)
  ├─ Clear / deactivate run-state marker (set active:false or delete it)
  └─ Emit final summary
```

The loop never blocks on `[🔍]` dependencies of newly runnable downstream work unless the dependent task declares `requires_verified_dependencies: true`. Review failures that invalidate downstream checkpoints requeue the affected items.

---

## Hard Stops (autopilot HALTS, emits final summary, exits)

| Stop reason | Trigger | Action |
|-------------|---------|--------|
| **PCAC conflict** | inbox check exit code `2` | halt before next claim |
| **Stale / divergent integration branch** (T1443/BUG-099) | INIT detection finds candidate integration branches diverge beyond `integration_divergence_max_commits`, or the only available target is strictly behind the active source branch | halt; report the ahead/behind counts and the disqualified target; never blindly default to a stale `dev` |
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

`g-go-go` MUST work without `example_app` services. Optional backend failures are surfaced and degraded:

- Vault MCP unavailable → file-first vault reads only; tasks that explicitly declare `requires_backend: true` in their YAML are deferred with `Deferred — example_app unavailable` in the summary.
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
- <gald3r_source>: {commits} commits, last {sha}
- <template_full>: SKIPPED (unrelated dirty: .github/...)
- example_desktop: {commits} commits, last {sha}

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

### Push offer (final summary only)
This summary is the ONE place to offer a push. Do NOT offer push between iterations, between task commits, or at partial-run checkpoints — it interrupts the loop. The single end-of-run offer:

```
{N} commits are ready on {branch}. Review changes and push when satisfied:
  git log origin/{branch}..HEAD --oneline
  git push origin {branch}
Want me to push now?
```
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
| **`--repos` filter (T1152)** — when `--repos <ids>` is supplied, runnable-queue scan filters to tasks whose `workspace_repos:` intersects the requested ids; out-of-scope tasks are silently deferred (NOT marked failed); budget counter only increments on iterations that execute in-scope tasks; controller-only fallback is disabled while `--repos` is active | Lets the autopilot be scoped to one or more member repos (e.g. `--repos example_agent`) without burning the budget on unrelated tasks; preserves the deferred-task safety of pre-T1152 behavior |
| **Auto-merge member repo branches on PASS (MANDATORY)** -- after the review-result commit for each PASS item, run `gald3r_worktree.ps1 -Action MergeToMain -RepoPath <member_path> -TaskId {id} -TargetBranch main -Apply` in dependency order (lowest ID first); default target is `main` (feature-branches-only model — NO `dev` branch, see `g-rl-02`); override with `--target-branch <branch>` for a custom target; on success the helper FF-merges the feature branch into `main` (or override target) and deletes both code + review branches and worktree folders; log `[AUTO-MERGED→main]` in session summary; on merge-blocked (conflict), missing target branch, or member-dirty: preserve branch, log `[MERGE-BLOCKED]` / `[MERGE-SKIPPED-DIRTY]` as human action item (fallback, not default); pass `--no-auto-merge` to skip entirely and use old `[MERGE-BLOCKED]` behavior; never run auto-merge for FAIL items | Eliminates manual branch merge ceremony after every autopilot run — feature branches merge straight to `main` |
| Autopilot composes existing safe primitives — never bypasses any gate | One command, same safety contract |
| Implementation agents NEVER self-verify their own work | Adversarial independence preserved across all loop iterations |
| Hard stops emit final summaries and exit cleanly | Stops are not failures; they are the safety boundary |
| Run budget bounds the loop | Prevents runaway autonomous runs |
| Heartbeats are output-only — never prompt the user | Fire-and-forget design |
| File-first fallback when optional backends are down | `example_app` is optional, not required |
| Per-repo commits only — no cross-repo single commits | Each manifest member is an independent git root |
| Marker-only `.gald3r/` invariant is absolute | Member control-plane writes are forbidden, period |
| `[🚨]` items are NEVER auto-retried | Human-only resolution by policy (T047) |
| **Stop-detection re-invoke (BUG-107 #2)** — the `g-hk-ggo-stop-detect` stop hook re-invokes the loop when it halts without an authorized hard-stop row; bounded by `min(budget_remaining, 25)` re-invokes; genuine hard stops and budget exhaustion are never re-invoked | Makes the no-early-stop contract mechanically self-enforcing instead of prose-only |
| **Context-aware throttle (BUG-107 #3)** — ON by default; reduces bucket count N under context pressure (never below 1; reversible per-iteration) instead of stopping. Use `--no-context-aware` to disable. | Trades parallelism for continuation; context pressure is never a stop reason. Default-on prevents BUG-107 without requiring the user to remember the flag. |
| **Inter-iteration compression (MANDATORY)** - after Phase 2 review result for each iteration, serialize the compact iteration summary (<=100 words: iter, phase1_tasks[], phase1_verdict, phase2_tasks[], phase2_verdict, checkpoint_sha, review_sha) to `ggo_run_state.json .completed_iterations[]` and discard raw Phase 1 + Phase 2 conversation outputs. The coordinator's prior-iteration record is the compact summary ONLY. | Prevents O(n^2) coordinator history growth that causes BUG-107 context saturation before budget is exhausted. Compression is the primary fix; throttle is secondary. |
| **Phase 1 coding swarm (T1526)** — Phase 1 MUST invoke `g-go-code-swarm` (N parallel coders), NOT bare `g-go`. Phase 2 MUST invoke `g-go-review-swarm`. Both phases are parallel by default. Use `--no-code-swarm` to revert Phase 1 to sequential coding when needed. | Parallel coding swarm is the default; sequential is the opt-out. Without this, throughput is bottlenecked by sequential Phase 1 even when N>1 is configured. |
| **Run-state marker is mandatory under autopilot** — write `.gald3r/logs/ggo_run_state.json` at INIT, refresh `iter`/`budget_remaining` each iteration, and write `authorized_hard_stop` verbatim before any genuine hard-stop exit | The stop hook depends on this marker to distinguish authorized stops from disguised context-panic stops |

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
@g-go-go --target-branch main           # default: PASS items merge to main (feature-branches-only model)
@g-go-go --no-auto-merge                # disable auto-merge; reviewer leaves [MERGE-BLOCKED] for human
@g-go-go --target-branch staging        # merge to a custom branch instead of main
@g-go-go --repos example_agent --budget 3   # scope autopilot to example_agent tasks only
@g-go-go --repos example_agent,example_desktop # scope autopilot to two specific member repos
@g-go-go --no-context-aware              # disable context-aware throttle (full N at all context levels)
@g-go-go --no-context-aware --budget 3  # short burst: max parallelism, no throttle
@g-go-go --no-code-swarm                 # Phase 1 sequential coding (1 task at a time); Phase 2 review swarm unchanged
@g-go-go --no-code-swarm --budget 3      # safe debugging mode: sequential coding, parallel review
```

The defaults (workspace mode, 12-iteration budget, 30-minute heartbeat) are tuned for a multi-hour overnight or background run. Use `--budget 3` and `--heartbeat 5m` for quick autopilot bursts.

**For supervised pipeline runs (one batch only), use `@g-go --swarm --workspace` instead — that is one iteration of this loop.**

Let's go.

