# Hook: g-hk-goal-stop-detect

Goal quit-condition stop hook (BUG-645). Gives gald3r's persistent session-goal
mechanism (`@g-goal`, `.gald3r/config/ACTIVE_GOAL.md`) the same mechanically
self-enforcing quit conditions `g-hk-ggo-stop-detect.py` already proved out for
the g-go-go autopilot loop (T1444/BUG-107), instead of leaving the goal contract
as prose-only agent self-discipline.

## Why

A live incident (2026-08-03, ~70 minutes) showed a goal-locked session
re-blocking Stop with IDENTICAL feedback long after the goal's underlying work
was genuinely complete. The goal condition was inventory-shaped ("N tasks are
not complete"), so once the work was done the literal premise became
PERMANENTLY unsatisfiable, and nothing in gald3r's goal machinery recognized
that terminal state or bounded the re-block count. See BUG-645 for the full
incident writeup.

## Fires On

The **`stop`** event (Cursor `stop` / Claude Code `Stop`). Wired in
`.cursor/hooks.json` and `.claude/settings.json` alongside `g-hk-ggo-stop-detect`
and `g-hk-agent-complete`, and in the canonical `g_hk_core.CONCERN_CHAIN["stop"]`
for every other platform routed through the shared dispatcher.

Pure no-op (allow exit) when `.gald3r/config/ACTIVE_GOAL.md` does not exist —
the overwhelming majority of sessions, since `@g-goal` is opt-in. Never blocks
tool calls, never touches TASKS.md/BUGS.md, never interferes with a session
that has no active goal.

## What It Does

Reads `.gald3r/config/ACTIVE_GOAL.md`'s frontmatter and decides, in order:

1. **Explicit terminal-state clause** — `condition_discharged: true` (set by
   an agent or operator that recognized a genuine no-runnable-work terminal
   state, mirroring `authorized_hard_stop` semantics) → allow exit.
2. **Automatic terminal-state clause** — the project's open task/bug queue
   (`.gald3r/gald3r.db`, no value/severity floor) reads zero across **2**
   consecutive sweeps → allow exit, set `condition_discharged: true`, and
   surface a `@g-goal clear` notification. A single zero reading is not
   trusted alone (transient DB-read races are possible).
3. **Turn budget exhausted** (`turns_consumed >= turn_budget`) — `g-goal.md`'s
   own pre-existing documented contract, now mechanically enforced → allow
   exit.
4. **Re-invoke ceiling** — `min(turn_budget - turns_consumed,
   GOAL_REINVOKE_CEILING=5)`, the same `min(budget, ceiling)` shape
   `g-hk-ggo-stop-detect.py` uses (there: `min(budget_remaining, 25)`) → allow
   exit once reached.
5. **Escalation over repetition** — the remaining-work count is UNCHANGED
   across **3** consecutive checks (zero forward progress, even if work
   remains and the ceiling has not been hit) → allow exit and notify, rather
   than waiting for the numeric ceiling.
6. **Otherwise** (genuinely in-progress, satisfiable goal) — re-block with a
   reminder (`decision:block` for Claude / `continue:false`+`followup` for
   Cursor), incrementing `turns_consumed`/`reinvoke_count`.

This NEVER weakens enforcement for a genuinely in-progress goal — case 6 still
re-blocks exactly as `g-goal.md` documents. It only guarantees the re-block
count is bounded and that a documented terminal state (explicit or
auto-detected) is always honored.

## Side Effects

- Patches `turns_consumed`, `reinvoke_count`, `last_remaining_work_count`,
  `stagnant_checks`, `zero_remaining_work_streak`, and (on an auto-discharge)
  `condition_discharged` fields in `.gald3r/config/ACTIVE_GOAL.md`, preserving
  every other frontmatter field and the file body untouched.
- Never deletes `ACTIVE_GOAL.md` — `@g-goal clear` remains the only way to
  remove it.
- On every "allow" branch returns `{ continue: true, additional_context: ... }`
  and exits 0. On the "block" branch (case 6) returns the Stop-hook
  continuation contract (`decision: block` / `continue: false`) and exits 0.

## Related

- BUG-645 — this bug's own Fix Direction items 2/3/4 (terminal-state clause,
  re-invoke ceiling, escalation over repetition). Fix Direction item 1
  (reject/normalize inventory-shaped goal conditions at `@g-goal` SET time) is
  agent-level prose guidance documented in `commands/g-goal.md`, not this hook
  — that judgment (is this description outcome-shaped or inventory-shaped?)
  is not reliably a deterministic string check.
- Pattern source: `g-hk-ggo-stop-detect.py` / T1444 / BUG-107 (the
  `authorized_hard_stop` + `min(budget, ceiling)` re-invoke pattern this hook
  mirrors for the goal mechanism).
- Companion: `commands/g-goal.md` (documents `.gald3r/config/ACTIVE_GOAL.md`'s
  schema, including the fields this hook reads/writes).
