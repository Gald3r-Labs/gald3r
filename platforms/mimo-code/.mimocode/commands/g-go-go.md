---
description: 'Autopilot loop: rolling g-go-code-swarm + g-go-review-swarm cycles across the workspace until a hard stop'
argument-hint: '[--budget N] [--heartbeat Nm] [--controller-only] [--repos ID,...] [--no-auto-merge] [--legacy] [--provider <id>[:<model>]] [--model <id>] [--coordinator-provider <id>] [--coordinator-model <id>] [--implementer-provider <id>] [--implementer-model <id>] [--reviewer-provider <id>] [--reviewer-model <id>] [--coordinator-command CMD]'
subsystem_memberships: [TASK_MANAGEMENT]
execution_tier: orchestration
---
Maximal workspace swarm autopilot — rolling implement/review until a hard stop: $ARGUMENTS

## Mode: AUTOPILOT (rolling implement → review → next batch)

`g-go-go` is the **explicit** "full throttle" command. It composes existing safe primitives (`g-go --swarm --workspace`, T531 housekeeping gate, T532 workspace mode, T212 rolling swarm pipeline, T206/207/208 swarm reconciliation policies, T170-172 worktree isolation, T495/496 per-root clean gates, marker-only `.gald3r/` invariant, WPAC conflict gates) into one continuous loop. It is **not** an alias for bare `/g-go`. Bare `/g-go` remains controller-only and unchanged.

> **Independence guarantee**: Each implementation/review cycle uses fresh reviewer subagents with no Phase 1 context. The autopilot loop never lets implementer agents self-verify their own work.

> **Bounded by design**: Autopilot is powerful but bounded. It cannot bypass WPAC conflict gates, clean gates, marker-only member `.gald3r/` protection, task workspace permissions, verification independence, secrets checks, explicit path staging, or non-destructive member rules. Every documented hard stop in the table below cleanly halts the run with an actionable summary.

> **CLI Invocation Rule: `uv run gald3r` (BUG-591):** every per-iteration coordinator this loop
> spawns runs the `g-go-code-swarm`/`g-go-review-swarm` protocol, which inherits `g-go.md` Step
> 0b — every `gald3r <verb>` call (task/bug status verbs, `gald3r worktree create`, `gald3r
> housekeep`, etc.) MUST run as `uv run gald3r <verb>`, never bare `gald3r`, whenever cwd is a dev
> checkout of `gald3r_core`. A stale PATH binary can silently shadow this checkout's dev source
> across an entire autopilot iteration (BUG-591) — see `g-go.md` Step 0b for full text and the
> optional staleness hard-fail check a coordinator may run before dispatch.

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
| **Bug severity floor** (T432, two-floor triage) | **5** on the 1-10 damage scale (`severity_scale.py` SEVERITY_RUBRIC) — skips the 1-4 nitpick band AND forbids filing new sub-floor bugs during the run | `g-go-go --min-severity <1-10>`; `--min-severity 1` restores full zero-tolerance intake. A floor is a HARD STOP, never a slider — it never auto-lowers, so a focused run cannot burn the backlog to nothing. |
| **Task value floor** (T434-437 mirror) | **0 = work every task** (tasks are deliberate value work; unscored tasks are NEVER skipped — missing score ≠ below the floor) | `g-go-go --min-value <0-10>` on the 1-10 value scale (TASK_VALUE_RUBRIC; 6=public-facing docs, 10=release/demo-critical). `--min-value 7` = best-and-up. Both floors render into the coordinator brief as `{{FOCUS_DIRECTIVE}}`. |
| Repo scope filter | (none — global scope across all manifest members) | `g-go-go --repos <repo_id>[,<repo_id>...]` to scope autopilot to tasks whose `workspace_repos:` contains at least one of the listed IDs. Skipped tasks (not in scope) are NOT marked failed — they're left for the next run. Budget counter only counts iterations that execute in-scope tasks. Example: `g-go-go --repos example_agent --budget 3` runs only `example_agent` tasks. |
| Rolling Amnesia context reset (T635, **legacy**) | **off** by default — superseded by the stateless conductor | Only meaningful under `--legacy`. The default stateless conductor makes every iteration a fresh process, so scheduled in-session resets are unnecessary. Under `--legacy`, `g-go-go --reset-every <K>` sets the cadence and `g-go-go --no-reset` disables it. See `hooks/g-go-go-legacy-modes.md` ("Rolling Amnesia — Scheduled Context Reset"). |
| Context-aware throttle (legacy) | **off** by default (superseded by Rolling Amnesia); **on** under `--no-reset` | Active only when `--no-reset` is set. `g-go-go --no-context-aware` disables the legacy throttle entirely. See `hooks/g-go-go-legacy-modes.md` ("Context-Aware Throttle"). |
| Resume after reset | (n/a) | `g-go-go --resume .gald3r/logs/ggo_run_state.json` — issued by the stop hook to restart a fresh coordinator after a scheduled context reset. |
| Orchestration model (T630) | **stateless conductor** (default) — `gald3r autopilot loop` | The default outer loop is a deterministic Python reconciler that invokes a FRESH coordinator LLM session per iteration (blank context by construction); its only stop conditions are *no eligible work left* or *budget exhausted* — it never halts while runnable work remains. `g-go-go --legacy` opts back into the deprecated single-session in-session LLM loop (Rolling Amnesia + stop-detect re-invoke ceiling). See "Stateless Orchestrator — Python Outer Loop (T630)" below. |
| **Credit-use / overage spend** (T513, owner ruling 2026-07-30) | **OFF** by default — bank-and-wait (BUG-499) is the standard behavior when the five_hour rate-limit window fills | `g-go-go --enable-credit-use` permits the run to keep spawning coordinators into the window instead of waiting, spending account overage/credit. `g-go-go --enable-credit-use --max-spend 150.00` adds a run-wide cap (USD) on cumulative ESTIMATED spend (stream-json `total_cost_usd`, summed) that cleanly hard-stops the run once crossed. `--max-spend` is inert without `--enable-credit-use`. |
| Coordinator scope (T632) | **`all`** (single coordinator) | `g-go-go --subsystem <GROUP>` (wired through `gald3r autopilot loop --subsystem <GROUP>`) scopes a coordinator to one subsystem group so multiple coordinators can partition a project. Disjoint scopes run concurrently; overlapping scopes collide and are rejected at startup — enforced by `gald3r_core.coordination.swarm.coordinator_limit` (T538), a real local SQLite-adjacent registry, not a remote entitlement check. **Count ceiling defaults to 1** (offline-safe); raise it via `GALD3R_MAX_COORDINATORS` or AGENT_CONFIG.md's `max_coordinators:` key — an explicit, opt-in owner override (T538). See "Multi-Coordinator Partitioning (T632)" below. |

`g-go-go` accepts the same `$ARGUMENTS` filters as `g-go` (`tasks N,M`, `bugs BUG-NNN`, `subsystem ...`, `bugs-only`, `tasks-only`) plus the autopilot knobs above — including the two-floor focus mode (`--min-severity` for bugs, `--min-value` for tasks; shorthand like `bugs 5+ tasks 5+` maps to the floors). Any usage/help card rendered for this command MUST list both floors — they are the flagship focus feature (BUG-396).

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
   { "active": true, "platform": "claude",
     "iter": 0, "budget_remaining": 12,
     "authorized_hard_stop": "", "reinvoke_count": 0,
     "reset_every": 3, "resets_done": 0,
     "updated_at": "<iso-8601>",
     "completed_iterations": [],
     "coordinator_notes": [], "per_repo_blockers": {},
     "deferred_task_reasons": {}, "drift_warnings": [] }
   ```
   Set `"platform"` to `"claude"` (matches the value the stop hook detects from
   its script location). The `session_id` field is NOT written at INIT; the stop
   hook captures it on the first stop via the stop-event stdin payload
   (first-touch registration). Stops from a different platform or session are
   always allowed through without re-invocation.
2. **Each iteration** — refresh `iter` and `budget_remaining` (the hook reads the latest values to bound re-invokes).
3. **On a genuine hard stop** — BEFORE emitting the final summary, write the exact hard-stop table row verbatim into `authorized_hard_stop`. This is the ONLY way to legitimately end the run. A blank `authorized_hard_stop` means "the loop has no authorized reason to stop".
4. **At clean EXIT** (budget exhausted, no runnable work) — set `active` to `false` or delete the marker. The hook also clears it automatically on authorized hard stop, budget exhaustion, or re-invoke-cap.
5. **Rolling Amnesia stash (T635)** — every `reset_every` iterations, BEFORE the scheduled reset, refresh the stash fields so a fresh coordinator can rebuild context from disk alone: `coordinator_notes` (free-form "remember this"), `per_repo_blockers` (`repo_id → reason`), `deferred_task_reasons` (`task_id → why deferred`), `drift_warnings`. Then write `authorized_hard_stop: "scheduled_context_reset"` and exit. The stop hook treats this as an **authorized, NON-terminal** stop: it consumes the marker, bumps `resets_done`, and re-invokes the loop with `--resume`. See `hooks/g-go-go-legacy-modes.md` ("Rolling Amnesia — Scheduled Context Reset").

### What the hook enforces

When the `stop` event fires with an active marker, `g-hk-ggo-stop-detect.py`:

- **Allows the stop** when `authorized_hard_stop` is populated (genuine hard stop), when `budget_remaining <= 0` (budget cap IS a hard stop), or when the re-invoke cap is hit.
- **Re-invokes the loop** otherwise — it increments `reinvoke_count` and returns a stop-continuation decision (`decision:block` for Claude Code / `continue:false`+`followup` for Cursor) carrying a verbatim reminder of the forbidden stop reasons. A disguised "checkpoint" cannot end the run.

### Bounding (never infinite-loops)

Re-invokes are capped at `min(budget_remaining, 25)`. A genuine hard stop and budget exhaustion are always honored and never re-invoked. The re-invoke ceiling is the anti-infinite-loop fail-safe: if it is ever reached, the hook allows the exit and treats it as a hard stop. This satisfies the contract that re-invocation always respects genuine hard stops and the configured budget cap.

> The hook is a **no-op** when no `ggo_run_state.json` marker exists — ordinary, non-autopilot stop events are never affected. See `hooks/g-hk-ggo-stop-detect.md` for the full self-description.

---

> **Legacy modes moved.** The Rolling Amnesia scheduled context-reset mechanism (T635,
> `--legacy` only) and the legacy Context-Aware Throttle (`--no-reset` only, BUG-107 Fix
> Direction #3) are documented in full in `hooks/g-go-go-legacy-modes.md`. Both are
> **inert under the default stateless conductor** -- see the Default Configuration table
> above for their knobs (`--reset-every`, `--no-reset`, `--resume`, `--no-context-aware`)
> and defaults.

---

## Stateless Orchestrator — Python Outer Loop (T630)

The **default** `@g-go-go` outer loop is a deterministic Python reconciler —
`gald3r autopilot loop` — that replaces the single long-lived LLM coordinator,
modeled on a Kubernetes controller. (Pass `--legacy` to opt back into the deprecated single-session loop.)
Its only stop conditions are *no eligible work left* or *budget exhausted*; it never halts while runnable work remains:

```
gald3r autopilot loop   (Python, NOT an LLM)
  while budget_remaining > 0:
    read ggo_run_state.json + TASKS.md from disk   (never cached across iterations)
    invoke a FRESH coordinator LLM session (blank context) for ONE iteration via a
      resolved provider-native command -- `claude --model sonnet --dangerously-
      skip-permissions --output-format stream-json --verbose -p "<brief>"` on a
      Claude Code host (unchanged T477/T514 default), or the Cursor-native
      equivalent (`agent --model gpt-5.6-terra-medium --force --output-format
      stream-json -p "<brief>"`) when a Cursor host is detected -- see "Provider
      & Model Routing" below (T580, BUG-612) for the full resolution order and
      host-mapping table. Brief generated from the engine's embedded
      coordinator-brief template, filled entirely from disk state; the brief
      tells this invocation which phase it owes. T477: on the Claude branch the
      coordinator model tier defaults to Sonnet -- deliberately, to conserve the
      5-hour rate-limit window -- and is overridable without a code edit via the
      `GALD3R_GGO_COORDINATOR_MODEL` env var, AGENT_CONFIG.md's
      `coordinator_model:` key, or the new `--provider`/`--model`/
      `--coordinator-provider`/`--coordinator-model` flags; an explicit
      `--coordinator-command` always wins over all of the above)
        |-> phase1: coordinator spawns g-go-code-swarm (full N), fan-in, reconcile,
            checkpoint commit -- then EXITS without touching Phase 2
        |-> phase2: coordinator spawns g-go-review-swarm against the prior iteration's
            checkpoint, writes verdicts, review-result commits -- then EXITS
        |-> coordinator appends its compact summary + refreshes stash before exiting
    re-read state; outer loop decrements budget + increments iter + alternates
      phase1 <-> phase2; loop
```

**Split-phase design (BUG-214/T336):** by default, each fresh coordinator invocation owns
exactly ONE phase — Phase 1 (implement -> fan-in -> reconcile -> checkpoint commit) or
Phase 2 (review swarm -> verdicts -> review-result commit against the prior checkpoint) —
never both. `ggo_run_state.json`'s `phase` field (outer-loop-owned, alternates once per
invocation) tells each fresh coordinator which one it owes; the brief surfaces this as
`You owe : PHASE 1 (...)` / `PHASE 2 (...)`. This structurally bounds each iteration's wall
clock instead of guessing a single number for a 2-phase iteration, and the Phase 1 -> Phase 2
handoff reuses the existing Review Checkpoint Gate branch/SHA seam. A run resumed from a state
file written before T336 (no `phase` key) keeps the original combined behavior — one
invocation runs both phases, unchanged.

**What the outer loop owns (deterministic, never the LLM):** budget counting, hard-stop
detection (`authorized_hard_stop`), heartbeat, the iteration counter, and the `phase`
alternation. The coordinator owns only the work of a single iteration/phase plus the
stash/queue updates it writes to disk.

**Primary stop trigger (BUG-273 (f)):** the coordinator is invoked with `--output-format
stream-json`, and a coordinator whose measured context usage crosses `CONTEXT_EXHAUSTION_PCT`
(90% of the model's own declared context window) is treated as done — not hung — and its
process tree is reclaimed so the run can move on with whatever it already committed. Per-
iteration context%, token counts, and `total_cost_usd` are logged every iteration (the burn-rate
report).

**Per-coordinator hang timeout:** now an OUT-OF-BAND PATHOLOGY BACKSTOP only — never a work-
sizing scheduler. Defaults to `DEFAULT_COORDINATOR_TIMEOUT_MIN` (120 min as of BUG-273 (f)).
Elapsed time was the ORIGINAL stop trigger (25 min, then 50 min as of BUG-214/T336) and tuning
it never converged: 25 min gave a 50% false-kill rate on legitimate work (and self-throttled
smart-N 5→2 to fit, abandoning claimed tasks); 50 min still killed 1 of 7 productive N=5
iterations that had already committed 5 buckets. 120 min sits far above the measured ~48-min
P99 so it should fire on genuine pathology only. Override with `--coordinator-timeout-minutes`
or `GALD3R_GGO_COORDINATOR_TIMEOUT_MIN`.

**Graceful wind-down (T366):** `gald3r autopilot stop [--reason TEXT] [--now]` asks a running
loop to end early without crashing it. Default: the in-flight coordinator finishes its
iteration and commits normally, then the loop exits at the boundary — no work lost. `--now`
terminates the coordinator process tree immediately (that iteration's uncommitted work is
lost). SIGINT/SIGTERM in the loop's own process follow the same convention: first signal =
graceful, second = immediate. `gald3r autopilot status` shows a pending stop request.

**Credit-use opt-in (T513, owner ruling 2026-07-30, decision 3):** account extra-usage
credits stay OFF by default — when the five_hour rate-limit window fills, the loop banks
the iteration and waits for the reset (BUG-499 bank-and-wait), exactly as before.
`gald3r autopilot loop --enable-credit-use` (equivalently `g-go-go --enable-credit-use`) is
the explicit opt-in that lets the run keep spawning coordinators into that window instead of
waiting, spending account overage/credit. `--max-spend <USD>` (e.g. `--max-spend 150.00`) is
its companion safety cap: once this run's cumulative ESTIMATED spend — every iteration's
stream-json terminal `total_cost_usd`, summed, clearly labeled an estimate rather than a real
bill — crosses the cap, the run hard-stops cleanly (commits already made are kept). Without
`--enable-credit-use`, `--max-spend` is inert and bank-and-wait is unchanged.

**Resident-process restart note (BUG-252):** a currently-running `gald3r autopilot loop`
process already holds its imported Python modules in memory for its lifetime — regenerating
deployed `.claude`/`.cursor` command copies from this canonical doc (via `gald3r platform
install --force`) does not retroactively change an already-running resident loop's behavior.
Restart the resident `gald3r autopilot loop` process itself before it will pick up any
T336-class canonical doc/behavior update.

**Why N is never throttled:** each coordinator invocation is a brand-new context window by
construction, so context cannot accumulate across iterations — the swarm runs at full smart N
(hard cap 5) every iteration, including deep into a long run.

**DB integration (when T631 is live):** the coordinator brief includes the DB claim token
instead of the file-based `[🔄]` claimed status, so atomic claims survive the per-iteration reset.

**Flags:**

```
@g-go-go                          # DEFAULT: stateless conductor (gald3r autopilot loop)
@g-go-go --budget 8               # stateless conductor with an 8-iteration budget
@g-go-go --stateless              # explicit opt-in (identical to the default; kept for clarity)
@g-go-go --legacy                 # force the DEPRECATED single-session LLM loop (Rolling Amnesia + re-invoke ceiling)
@g-go-go --enable-credit-use                     # T513: continue into overage/credit spend instead of bank-and-wait (BUG-499) when the five_hour window fills
@g-go-go --enable-credit-use --max-spend 150.00  # T513: same, but hard-stop once cumulative estimated spend crosses $150.00
@g-go-go --provider cursor-agent                 # T580: force Cursor-native coordinator/implementer/reviewer sessions
@g-go-go --model opus                            # T580: global model override (every role, Claude branch feeds GALD3R_GGO_COORDINATOR_MODEL)
@g-go-go --coordinator-model opus --implementer-model haiku --reviewer-model sonnet  # T580: independent per-role overrides
```

The stateless conductor is the **default**. The legacy single-session loop is **deprecated**,
preserved only under `--legacy` for fallback and comparison, and slated for removal once the
stateless conductor proves out. Both bound coordinator context, but the conductor does it
**by construction** (a fresh process per iteration) while Rolling Amnesia did it **within a
session** (scheduled reset). Because every conductor iteration is already a fresh context,
Rolling Amnesia and `--reset-every` are inert except under `--legacy`.

## Provider & Model Routing (T580, BUG-612 companion)

Full flag reference, the deterministic resolution order (role-specific CLI override ->
global CLI override -> invoking host / parent-model mapping -> task `preferred_model:` /
`--mode` policy -> project config default), the host-native default mapping table (Claude
Code vs Cursor), env-var propagation, validation, and verification-scope notes now live in
`hooks/g-go-go-provider-routing.md` -- see that file for the complete T580/BUG-612 contract.

**Quick reference:** `--provider <id>[:<model>]`, `--model <id>` (global overrides);
`--coordinator-provider/-model`, `--implementer-provider/-model`, `--reviewer-provider/-model`
(per-role overrides); `--coordinator-command <cmd>` (lower-level expert override, always
wins). Known providers: `claude` (default), `cursor-agent`.

## Multi-Coordinator Partitioning (T632, real gate landed T538)

`@g-go-go --subsystem <GROUP>` (wired straight through to `gald3r autopilot loop --subsystem
<GROUP>`) scopes a coordinator to one subsystem group (from `PRODUCT_SYSTEMS.md`
`defined_groups`), so two or three coordinators can safely partition the same project — e.g. one
on `AGENT_ORCHESTRATION`, one on `PLATFORM_INTEGRATION`.

> **T538 correction.** This section previously described an "engine gate"
> (`db.can_register_coordinator`, a `coordinator_sessions` table, a world_tree
> `plan.max_coordinators` tier lookup) as already built. A T538 investigation searched this
> entire `src/` tree for any of those names and found **none of them existed in code** — it was
> aspirational documentation the coordinator LLM was expected to self-enforce by reading this
> file, not a real, code-enforced limit. T538 replaced it with the real thing below.

**What is real today (T538):**
- `gald3r_core.coordination.swarm.coordinator_limit` — a local, file-backed, pid-liveness-self-
  healing registry (`.gald3r/coordinators/active/*.json`, reusing the same proven pattern as the
  `gald3r swarm run` active-session store, T236/T241) that enforces BOTH rules below on every
  `gald3r autopilot loop --subsystem <GROUP>` startup, BEFORE the loop is ever entered.
- **Scope collision (unconditional, every tier):** identical scopes collide; either scope being
  unscoped (`""`/`"all"`) collides with EVERYTHING (prevents silent cross-scope claiming);
  disjoint named scopes never collide. A collision refuses with exit code 2 and:
  `Coordinator collision. Active coordinator (session_id=..., pid=...) owns scope '<scope>'. Choose a non-overlapping --subsystem or stop the existing coordinator.`
- **Count ceiling (opt-in override):** resolved via `resolve_max_coordinators()` — env var
  `GALD3R_MAX_COORDINATORS` (highest precedence) > `.gald3r/config/AGENT_CONFIG.md`'s
  `max_coordinators:` key > **`1`** (the SAME "offline falls back to 1" safe default this section
  always documented — a project that sets neither override sees zero behavior change).
  Raising the ceiling NEVER weakens collision detection — an overlapping scope is refused
  regardless of how high the ceiling is set.
- **Per-scope state isolation:** each scoped coordinator gets its own run-state marker
  (`ggo_run_state__<GROUP>.json`) and stop-request sidecar, so concurrent scoped coordinators
  never corrupt each other's budget/iteration bookkeeping. `gald3r autopilot stop --subsystem
  <GROUP>` / `gald3r autopilot status --subsystem <GROUP>` target that same scoped marker.
- **Default (unscoped) run is untouched:** omitting `--subsystem` never calls the gate at all —
  the overwhelmingly common single-coordinator case has zero added overhead or new failure mode.

**Scope rules (unchanged from the original design):**
- Default scope is `all` — a single coordinator that may claim any task, including the
  UNSCOPED pool (tasks with empty/`[]` `subsystems:`).
- A specific `--subsystem <GROUP>` coordinator claims ONLY tasks whose `subsystems:` intersect
  its scope (via the SAME `--subsystem` filter `gald3r go`/`gald3r autoclaim` already use for
  single-task claims). It NEVER claims UNSCOPED tasks.
- **Claim atomicity is NOT in this layer** — real, already-working task-claim atomicity
  (`claim_expires_at`, SQLite-backed) and the T1059 worktree file-lock manifest
  (`gald3r_core.coordination.worktree.dispatch` / `core.worktree.locks`) are what actually
  prevent two coordinators from double-claiming the same task or file; `coordinator_limit` is a
  policy layer on top (stop two coordinators fighting over the same scope), not a substitute.

**Launch recipe (2 disjoint-subsystem coordinators):**
```powershell
$env:GALD3R_MAX_COORDINATORS = "2"     # explicit opt-in -- required, not automatic
gald3r autopilot loop --subsystem AGENT_ORCHESTRATION --budget 12    # terminal 1
gald3r autopilot loop --subsystem PLATFORM_INTEGRATION --budget 12   # terminal 2
```
See `docs/20260730_223000_Claude_MULTI_COORDINATOR_LAUNCH_RECIPE.md` for the full walkthrough,
verified test evidence, and known limitations (T538).

**Not yet implemented (future T633 scope, honestly still aspirational):** a live `gald3r doctor`
coordinator-session panel, heartbeat-based stale-session sweeping (T538's self-heal is pid-
liveness only, not a heartbeat TTL), a real world_tree entitlement/tier lookup for the count
ceiling (T538 deliberately chose the simpler local config-override path instead — see
`coordinator_limit.py`'s module docstring), and multi-machine Redis coordination.

### Interaction with the stop-detection hook

The context-aware throttle is the proactive valve; the stop-detection hook is the reactive backstop. Under pressure the loop first throttles N (Fix #3); if the agent still attempts an unauthorized halt, the hook re-invokes it (Fix #2). Together they close BUG-107 from both directions.

---

## Task/Bug Inbox Intake (T1573 — First Step Each Iteration)

Before the WPAC gate, before any claim, run the inbox intake to absorb any tasks/bugs
dropped into the gitignored staging zones during this or a prior run. **Prefer the engine
verb** (it reuses the same ID-assignment, frontmatter, and index regeneration as every other
gald3r write); the legacy co-located intake script was retired (T1652 D6) — the engine verb is the only path:

```powershell
# Primary — engine op (absorbs the old script; pure Mode-A, no git: the housekeeping commit below stages the result)
gald3r inbox            # or: python -m gald3r inbox

```

If `N > 0` items were ingested: log `"Ingested N task(s) / M bug(s) from inbox"` and continue.
If inbox is empty: reports nothing ingested — continue immediately.

> **Why this runs first**: Writing to `TASKS.md` or `BUGS.md` outside the iteration's
> coordinator staging allowlist triggers the Housekeeping Commit Gate `mixed-dirty`
> hard-block. The intake script is the sole writer of those index files in its commit,
> so the gate classifies it as `safe-gald3r-housekeeping` and allows it. Running intake
> before the WPAC and clean gates ensures the tree is already normalized when those
> gates run.

> **Tool routing**: invoke through the **PowerShell tool**, not Bash (same reason as WPAC hook below).

---

## WPAC Inbox Gate (Before Claiming Work)

Before each loop iteration claims work, run the re-callable WPAC inbox check:

```powershell
$hook = @( ".cursor\hooks\g-hk-wpac-inbox-check.py", ".claude\hooks\g-hk-wpac-inbox-check.py", ".agent\hooks\g-hk-wpac-inbox-check.py", ".codex\hooks\g-hk-wpac-inbox-check.py", ".opencode\hooks\g-hk-wpac-inbox-check.py" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($hook) { python $hook -ProjectRoot . -BlockOnConflict }
```

> **Tool routing (BUG-031)**: invoke this snippet through the **PowerShell tool**, not Bash. PowerShell-only syntax (`@(...)` array, `Where-Object`, `Test-Path`) routed to Bash produces a parse error such as ``syntax error near unexpected token `('``  — that failure is a tool-selection error, **NOT** a real WPAC conflict gate.

If the check reports `INBOX CONFLICT GATE` or exits with code `2`, **HARD STOP**: emit the final summary and exit. Do not claim more work, spawn more agents, or commit.

The autopilot also re-runs the WPAC inbox check at every heartbeat interval and once before each rolling-wave bucket spawn.

---

## Gald3r Housekeeping Commit Gate (T531)

Before each iteration claims/spawns/commits, run the safety classifier helper at the orchestration root:

```powershell
gald3r housekeep -Mode preflight -Apply -Json
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
  reported by `gald3r worktree merge` as `merge-blocked` and is **never**
  force-updated; the autopilot logs `[MERGE-BLOCKED]` as a human action item.

This detection runs once at INIT (read-only). The actual integration is performed only at the
per-PASS auto-merge step via `gald3r worktree merge` (FF-only, `-Apply`).

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
4. Every dependency, blocker, WPAC inbox, and `[🚨]` check passes for that member root.
5. Per-repo clean check passes (or `-AllowDirty` is documented per-root in the task's `## Status History`).
6. No member `.gald3r/` control-plane path is targeted (marker-only invariant).

If any check fails for a member, the autopilot defers that task with a per-repo reason and continues. Autopilot **never** silently degrades authorization to keep the loop running.

---

## The Autopilot Loop

> **Execution entry — which backend runs.** By **default** `@g-go-go` runs the **stateless conductor**: launch the deterministic Python outer loop and supervise it to completion —
>
> ```
> gald3r autopilot loop --budget <B> --heartbeat-minutes <H>
> # plain `gald3r autopilot loop ...` also works (stdlib only)
> ```
>
> The Python loop owns budget / iteration / hard-stop / heartbeat and spawns a **fresh coordinator LLM session per iteration** (blank context by construction). The pseudocode below is therefore **(a)** what each fresh per-iteration coordinator does for ONE iteration, and **(b)** the complete in-session behavior under `--legacy`. Under `--legacy` you (this agent) run the whole loop yourself in-session, with Rolling Amnesia + the stop-detect re-invoke hook bounding context. Under the default conductor those mechanisms are **inert** — the process boundary per iteration IS the context reset, and the only stop conditions are *no eligible work left* or *budget exhausted*.

```
INIT
  ├─ WPAC inbox gate (HARD STOP on conflict)
  ├─ Housekeeping preflight at orchestration root
  ├─ Integration-branch detection (T1443 — HARD STOP on excessive divergence; see below)
  ├─ Clean Controller Gate per-root
  ├─ If --resume <state.json> (scheduled-reset restart, T635): SKIP fresh init — read the
  │   stash (iter, budget_remaining, completed_iterations[], coordinator_notes, per_repo_blockers,
  │   deferred_task_reasons, drift_warnings), re-read TASKS.md/BUGS.md, reconstruct working
  │   context to <=20K tokens, and RESUME the LOOP at the stashed iter with remaining budget.
  ├─ Initialize (fresh run): iter=0, budget_remaining=12 (or user override), reset_every=3 (or --reset-every K)
  ├─ Write run-state marker .gald3r/logs/ggo_run_state.json
  │   { active:true, iter:0, budget_remaining:B, reset_every:K, resets_done:0,
  │     authorized_hard_stop:"", reinvoke_count:0, coordinator_notes:[], per_repo_blockers:{},
  │     deferred_task_reasons:{}, drift_warnings:[] }
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
  │   ├─ Coordinator writes verdicts (PASS → [✅], FAIL → [📋]) via the mandatory `task verify`/
  │   │   `bug resolve` CLI verbs (BUG-511) — never a hand-edit of TASKS.md/BUGS.md
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
  ├─ [ROLLING AMNESIA — T635] Scheduled context reset (LEGACY — --legacy only; the default stateless conductor needs no in-session reset):
  │   ├─ If (iter > 0) AND (iter mod reset_every == 0) AND (budget_remaining > 0):
  │   │   ├─ Refresh stash in ggo_run_state.json: coordinator_notes, per_repo_blockers,
  │   │   │   deferred_task_reasons, drift_warnings (so a fresh session can rebuild context)
  │   │   ├─ Write authorized_hard_stop = "scheduled_context_reset" (authorized, NON-terminal)
  │   │   └─ EXIT cleanly. The stop hook re-invokes `@g-go-go --resume <state.json>`; the fresh
  │   │       session rebuilds context (<=20K tokens) and continues at this iter. N is NOT throttled.
  │   └─ Else: continue in the same session (no reset this iteration).
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
| **WPAC conflict** | inbox check exit code `2` | halt before next claim |
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

> **Not a hard stop:** `scheduled_context_reset` (Rolling Amnesia, T635) is an *authorized, non-terminal* stop, deliberately **absent** from this table. The stop hook re-invokes the loop with `--resume` rather than halting. It terminates the run only if it coincides with budget exhaustion.

---

## Heartbeat Summary (every `heartbeat_interval`)

```
[AUTOPILOT] Heartbeat — iter {N} / budget {B} — elapsed {HH:MM}
[AUTOPILOT] Platform: {resolved coordinator provider, e.g. claude|cursor-agent — T580/BUG-612}
[AUTOPILOT] Mode: {workspace|controller-only}, swarm: {N implementers / M reviewers}
[AUTOPILOT] Active repos: {ids touched this run}
[AUTOPILOT] Completed → [✅]: {count}    Awaiting review → [🔍]: {count}    Failed → [📋]: {count}    [🚨]: {count}
[AUTOPILOT] Currently implementing: {task IDs in flight}
[AUTOPILOT] Currently reviewing:    {task IDs in review}
[AUTOPILOT] Per-repo blockers: {repo_id → reason, ...}
[AUTOPILOT] Next iteration starts in: {seconds}
```

Heartbeats are append-only to the session output; they do NOT trigger user prompts.

**Structured progress events (T579).** Alongside this heartbeat block, the outer loop emits
one versioned `[AUTOPILOT][<KIND>]` event at run start (`STARTUP`), before/after every
iteration (`PRE-ITER` / `POST-ITER`, always carrying exactly one of `RUNNING`/`BLOCKED`/
`IDLE`), on a persistent blocker (`BLOCKER`, consuming BUG-609's `per_repo_blockers` state
without duplicating its fail-fast contract), and at run end (`FINAL`). The same schema
renders identically in `gald3r go-status`/`--watch` and `ggo_tui`. See
`docs/20260802_004405_Claude_AUTOPILOT_PROGRESS_EVENTS.md` for the full contract.

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
@g-wpac-read    # if a WPAC conflict halted the run

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

## Spawned-agent task/bug creation (T585 AC3)

During this run, **any** task or bug a spawned agent needs to create (deferred sub-feature,
newly discovered bug, follow-up) goes into the **hot inbox**, never a direct `tasks/open/` /
`bugs/open/` write + index regeneration:

- **Preferred** — call the engine verb (`gald3r task create …` / `gald3r bug report …`, or the
  `gald3r_task_*` / `gald3r_bug_*` MCP tools). When the run marker
  (`.gald3r/logs/ggo_run_state.json` `active: true`, or `GALD3R_AGENT_RUN=1`) is set, the engine
  **auto-routes** the new item to `tasks/inbox/` / `bugs/inbox/` as an id-less, uuid-suffixed
  draft — no id is assigned at create time.
- **Manual fallback** (no engine) — hand-write the draft directly into `tasks/inbox/` /
  `bugs/inbox/` (id-less, uuid-suffixed filename). Do **not** write `tasks/open/` / `bugs/open/`
  or touch `TASKS.md` / `BUGS.md`.

The hot-inbox **intake** (run at each iteration boundary — see the inbox-intake step) is the
*single ID-assigning authority*: it assigns ids atomically, so N concurrent agents can never
collide on the next id. This is the spawn-side complement of that intake step.

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
| **Auto-merge member repo branches on PASS (MANDATORY)** -- after the review-result commit for each PASS item, run `gald3r worktree merge -RepoPath <member_path> -TaskId {id} -TargetBranch main -Apply` in dependency order (lowest ID first); default target is `main` (feature-branches-only model — NO `dev` branch, see `g-rl-02`); override with `--target-branch <branch>` for a custom target; on success the helper FF-merges the feature branch into `main` (or override target) and deletes both code + review branches and worktree folders; log `[AUTO-MERGED→main]` in session summary; on merge-blocked (conflict), missing target branch, or member-dirty: preserve branch, log `[MERGE-BLOCKED]` / `[MERGE-SKIPPED-DIRTY]` as human action item (fallback, not default); pass `--no-auto-merge` to skip entirely and use old `[MERGE-BLOCKED]` behavior; never run auto-merge for FAIL items | Eliminates manual branch merge ceremony after every autopilot run — feature branches merge straight to `main` |
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

Full example list (the complete invocation-pattern catalog covering swarm mode, budget,
heartbeat, repo scoping, Rolling Amnesia knobs, provider/model overrides, subsystem
partitioning, context-aware throttle, and code-swarm toggles) lives in
`hooks/g-go-go-examples.md`. Quick reference:

```
@g-go-go
@g-go-go --budget 5
@g-go-go --controller-only
@g-go-go --repos example_agent --budget 3   # scope autopilot to example_agent tasks only
@g-go-go --legacy                        # force the DEPRECATED single-session loop (was the old default)
```

See `hooks/g-go-go-examples.md` for the complete list.

The defaults (workspace mode, 12-iteration budget, 30-minute heartbeat) are tuned for a multi-hour overnight or background run. Use `--budget 3` and `--heartbeat 5m` for quick autopilot bursts.

**For supervised pipeline runs (one batch only), use `@g-go --swarm --workspace` instead — that is one iteration of this loop.**

Let's go.

