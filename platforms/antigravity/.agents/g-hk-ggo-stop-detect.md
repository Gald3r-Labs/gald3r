# Hook: g-hk-ggo-stop-detect

g-go-go stop-detection re-invoke hook (T1444, BUG-107 Fix Direction #2). Makes the
"disguised context-panic stop" contract mechanically self-enforcing instead of
prose-only: when the autopilot loop halts mid-run without quoting an authorizing
hard-stop row, this hook forces it to continue.

## Fires On

The **`stop`** event (Cursor stop / Claude Code `Stop`). Wired in `.cursor/hooks.json`
and `.claude/hooks.json` under `stop`, alongside `g-hk-agent-complete` and
`g-hk-nightly-learn`. Receives the stop JSON payload on stdin (guarded with
`[Console]::IsInputRedirected`). The hook is a pure no-op (allow exit) unless a
g-go-go run-state marker is present and active, so it never interferes with
ordinary, non-autopilot sessions.

## What It Does

Reads the g-go-go run-state marker `.gald3r/logs/ggo_run_state.json` (written by the
`g-go-go` command at INIT and refreshed each iteration) and decides:

1. **No marker / not active** -> allow exit (no-op).
2. **`authorized_hard_stop` populated** -> a genuine hard-stop row was recorded;
   allow exit and clear the marker. Genuine hard stops are NEVER re-invoked.
3. **`budget_remaining <= 0`** -> budget cap is itself a hard stop; allow exit.
4. **`reinvoke_count >= min(budget_remaining, 25)`** -> anti-infinite-loop fail-safe;
   allow exit.
5. **Otherwise (unauthorized mid-loop stop)** -> increment `reinvoke_count` in the
   marker and emit a re-invoke decision (`decision:block` for Claude /
   `continue:false`+`followup` for Cursor) carrying a verbatim reminder of the
   forbidden stop reasons, forcing the loop to resume.

Bounding guarantees (Acceptance Criterion #3): re-invokes can never exceed
`budget_remaining`, are independently capped by a hard ceiling of 25, and a genuine
hard stop or budget exhaustion is always honored (never re-invoked).

## Side Effects

- Updates `reinvoke_count` and `updated_at` in `.gald3r/logs/ggo_run_state.json`
  on each re-invoke (case 5).
- Removes the run-state marker on authorized hard stop, budget exhaustion, or
  re-invoke-cap exit (cases 2-4).
- Appends diagnostic lines to `.gald3r/logs/hook_diag.log`.
- On case 5 only, returns a **block/continue** stop decision (holds the run open);
  in every other case returns `{ continue = true }` and exits 0 (allows the stop).
- Never blocks tool calls, never touches `.gald3r/` control-plane state files
  (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1444 — robust context-panic enforcement (stop-detection re-invoke hook +
  `--context-aware` throttle). This hook is Fix Direction #2.
- BUG-107 — g-go-go context-panic stops disguised as session checkpoints. Spec
  hardening (Fix Direction #1) lives in `commands/g-go-go.md`; this hook is the
  mechanical enforcement layer that the bug requires before it can close.
- Companion: `commands/g-go-go.md` (documents the run-state marker, the
  `--context-aware` flag for Fix Direction #3, and the re-invoke contract).
