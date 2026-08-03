# Hook: g-hk-post-session-trace

Session-trace closer. Logs the elapsed duration for the trace record opened by
`g-hk-pre-session-trace`. Originally the T1055 `post_session` reference
example; T1624 (WS-A-1, decision D-8) retired the gald3r-internal event name
and wired this hook into the canonical core.

## Fires On

The **canonical `stop` and `session-end` events**. Wired in `g_hk_core.py`
`CONCERN_CHAIN` — plain on `stop` (per agent turn), with `--finalize` on
`session-end` — and registered directly on the harness-native `Stop`/`stop`
trigger for Claude Code (`.claude/settings.json`) and Cursor
(`.cursor/hooks.json`). The payload arrives on stdin as JSON; `session_id`
(Claude), `conversation_id` (Cursor), and `cwd`/`project_path` are all
accepted. The former gald3r-internal `post_session` event name is retired
(D-8).

## What It Does

Reads the start marker staged by `g-hk-pre-session-trace`
(`.gald3r/logs/session_trace_<session>.json`), computes elapsed milliseconds,
and appends a duration line. On `stop` (default) the marker is KEPT so every
turn logs the cumulative session duration; with `--finalize` (`session-end`)
the marker is removed after logging. If no start marker is present it logs
`elapsed_ms=unknown`. Non-blocking by design.

## Side Effects

- Reads `.gald3r/logs/session_trace_<session>.json`; deletes it only when run
  with `--finalize`.
- Appends a `stop | session=... | elapsed_ms=...` (or
  `session-end | ...` when finalizing) line to
  `.gald3r/logs/session_lifecycle.log`.
- Always returns `{ continue = true }` and exits 0 — never blocks, never touches
  control-plane state (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1624 (WS-A-1) — wired the logging chain into the canonical hook core;
  retired the internal `pre_session`/`post_session` event names (D-8).
- T1055 — original plugin lifecycle hooks (this was the `post_session` example).
- Companion: `g-hk-pre-session-trace` (opens the session trace).
- Pattern: `commands/g-create-hook.md` (event list + scaffolding contract).
