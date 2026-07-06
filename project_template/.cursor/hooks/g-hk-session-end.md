# Hook: g-hk-session-end

Session-end record keeper (T1057) — persists structured session-end metadata
and stages a memory-capture pending marker for the next session to action
(Python port of the retired PS1, T1584).

## Fires On

The **stop / session-end** events: Cursor `stop` (`.cursor/hooks.json`),
Claude Code `Stop` (`.claude/settings.json`), Gemini `.agent` overlay
`AfterAgent` (`.agent/hooks.json`), and the canonical `session-end`
`CONCERN_CHAIN` in `g_hk_core.py` on every fanned platform. Runs alongside
`g-hk-agent-complete` and `g-hk-nightly-learn`.

## What It Does

Unlike its stop-chain siblings (reflection hints, N-session-rollup learning),
this hook focuses exclusively on persisting a structured session-end record
that the next session-start hook (or `@g-learn` / `memory_capture_session`)
can act on.

## Side Effects

- Appends to `.gald3r/logs/session_end.log`.
- Overwrites `.gald3r/logs/session_end_pending.json`.
- Emits a compact JSON `{"continue": true, ...}` line; never delays session
  close — any unexpected error exits 0.

## Related Tasks

- T1057 — session-end metadata + memory-capture pending marker.
- T1584 — Python port of the PS1 hook fleet.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
