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
g-go-go run-state marker is present, active, AND owned by the same platform and
session — so it never interferes with ordinary, non-autopilot sessions, and never
blocks a different agent's stop event.

## What It Does

Detects the calling platform from `$PSScriptRoot` (`.cursor/hooks` → `cursor`,
`.claude/hooks` → `claude`) and extracts the current `session_id` from the stop
event stdin payload (`session_id` field, or derived from `transcript_path`).

Reads the g-go-go run-state marker `.gald3r/logs/ggo_run_state.json` (written by the
`g-go-go` command at INIT and refreshed each iteration) and decides:

0. **No marker / not active** → allow exit (no-op).
1. **Platform mismatch** (`stored.platform` ≠ calling platform) → allow exit. The
   stored run belongs to a different agent (e.g. a Cursor agent does not block a
   Claude Code g-go-go loop, and vice versa).
2. **Session mismatch** (`stored.session_id` ≠ current session) → allow exit. A
   fresh chat session is never forced to resume a prior session's run.
3. **`authorized_hard_stop` populated** → a genuine hard-stop row was recorded;
   allow exit and clear the marker. Genuine hard stops are NEVER re-invoked.
4. **`budget_remaining <= 0`** → budget cap is itself a hard stop; allow exit.
5. **`reinvoke_count >= min(budget_remaining, 25)`** → anti-infinite-loop fail-safe;
   allow exit.
6. **Otherwise (unauthorized mid-loop stop by the owning session)** → increment
   `reinvoke_count` and emit a re-invoke decision (`decision:block` for Claude /
   `continue:false`+`followup` for Cursor) carrying a verbatim reminder of the
   forbidden stop reasons, forcing the loop to resume.

### First-touch session registration

The `g-go-go` INIT write includes `platform` but not `session_id` (the agent does
not have the session ID at start time). On the FIRST stop the hook sees for an
active run without a stored `session_id`, it captures the ID from the stop-event
stdin payload and writes it back to the state file. All subsequent stops compare
against this stored ID.

## Side Effects

- Updates `reinvoke_count` and `updated_at` in `.gald3r/logs/ggo_run_state.json`
  on each re-invoke (case 6).
- Writes `session_id` (and backfills `platform` if absent) on first-touch
  registration.
- Removes the run-state marker on authorized hard stop, budget exhaustion, or
  re-invoke-cap exit (cases 3–5).
- Appends diagnostic lines to `.gald3r/logs/hook_diag.log` (includes platform tag).
- On case 6 only, returns a **block/continue** stop decision (holds the run open);
  in every other case returns `{ continue = true }` and exits 0 (allows the stop).
- Never blocks tool calls, never touches `.gald3r/` control-plane state files
  (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1444 — robust context-panic enforcement (stop-detection re-invoke hook +
  `--context-aware` throttle). This hook is Fix Direction #2.
- BUG-107 — g-go-go context-panic stops disguised as session checkpoints. Spec
  hardening (Fix Direction #1) lives in `commands/g-go-go.md`; this hook is the
  mechanical enforcement layer that the bug requires before it can close.
- Companion: `commands/g-go-go.md` (documents the run-state marker schema,
  the `--context-aware` flag for Fix Direction #3, and the re-invoke contract).
