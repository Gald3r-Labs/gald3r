# g-go-go Companion: Legacy Modes (Rolling Amnesia + Context-Aware Throttle)

> Extracted verbatim from `commands/g-go-go.md` under T588 (file-size decomposition,
> repo threshold g-rl-00) -- content unchanged, relocated only. Both mechanisms below
> are **`--legacy` only**: the default stateless conductor (T630) bounds coordinator
> context by construction (a fresh process per iteration), so neither mechanism is
> active unless `@g-go-go --legacy` is passed. Companion: `commands/g-go-go.md`
> (the base command spec -- see its Default Configuration table for the `--reset-every`
> / `--no-reset` / `--resume` / `--no-context-aware` knob defaults and overrides).

---

## Rolling Amnesia — Scheduled Context Reset (legacy, T635)

> **Legacy — `--legacy` only.** Rolling Amnesia (T635) was the *temporary* symptom-fix for coordinator context accumulation. It is **superseded by the stateless conductor (T630), now the default**, which bounds context by construction — every iteration is a fresh process, so there is nothing to "reset". Rolling Amnesia runs only under `--legacy` and is slated for removal once the stateless conductor proves out (see follow-up task).

**Under `--legacy`, Rolling Amnesia is the in-session context-management mechanism.** Instead of throttling parallelism (N) as a proxy for context fill, the coordinator **proactively recycles its own context window on a schedule**, keeping it bounded without ever reducing N for context reasons.

### Mechanism

Every `reset_every` iterations (default `K=3`, set via `--reset-every <K>`):

1. **Stash** — refresh the extended `ggo_run_state.json` fields so the next coordinator can rebuild working context from disk alone: `completed_iterations[]` (compact per-iter summaries, already maintained), plus `coordinator_notes`, `per_repo_blockers`, `deferred_task_reasons`, and `drift_warnings`. `TASKS.md`/`BUGS.md` are the live queue and are re-read fresh, not stashed.
2. **Authorize the reset** — write `authorized_hard_stop: "scheduled_context_reset"`. This is a reserved, **non-terminal** authorized stop; it is NOT one of the Hard Stops in the table below.
3. **Exit** — the coordinator session ends cleanly.
4. **Re-invoke** — the `g-hk-ggo-stop-detect` hook recognizes `scheduled_context_reset`, consumes the marker, increments `resets_done`, and re-invokes the loop with `@g-go-go --resume .gald3r/logs/ggo_run_state.json`.
5. **Fresh coordinator** — on `--resume`, the new session reads the stash + re-reads `TASKS.md`/`BUGS.md`, reconstructs working context to **≤20K tokens**, and continues at the recorded `iter` with the remaining budget. Raw prior-iteration conversation is never replayed.

**N is never throttled for context reasons under Rolling Amnesia** — context never accumulates across the reset boundary, so the swarm runs at full smart N (hard cap 5) on every iteration, including deep into a long run.

### Knobs

```
@g-go-go                       # Rolling Amnesia on, reset every 3 iterations (default)
@g-go-go --reset-every 5       # reset every 5 iterations instead
@g-go-go --no-reset            # disable Rolling Amnesia; revert to the legacy iteration-count throttle below
@g-go-go --resume <state.json> # resume a run after a scheduled reset (normally issued by the stop hook)
```

### `--resume` reconstruction budget

On resume the coordinator MUST rebuild context from disk only — `ggo_run_state.json` (iter, budget_remaining, completed_iterations[], coordinator_notes, per_repo_blockers, deferred_task_reasons, drift_warnings) + a fresh read of `TASKS.md`/`BUGS.md` — and keep that reconstruction under ~20K tokens before taking its first action. If the stash is insufficient to reconstruct safely, the coordinator re-derives from the file queue rather than guessing.

---

## Context-Aware Throttle (legacy, `--no-reset` only — BUG-107 Fix Direction #3)

> **Superseded by Rolling Amnesia (T635).** The iteration-count throttle below is **inactive by default** and only engages under `--no-reset`. It remains for debugging and as a fallback. With Rolling Amnesia active (the default), N is never reduced for context reasons.

Under `--no-reset`, context-aware throttling applies a deterministic N-reduction based on context usage — instead of stopping when context is tight, the loop **reduces N (the parallel bucket / implementer count)** so the run continues with less parallelism. `--no-context-aware` disables even this legacy throttle (full N at all context levels).
### Behavior (legacy `--no-reset`)

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
