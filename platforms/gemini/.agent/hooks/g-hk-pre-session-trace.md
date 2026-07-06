# Hook: g-hk-pre-session-trace

Session-trace opener for per-session observability at the session boundary.
Originally the T1055 `pre_session` reference example; T1624 (WS-A-1, decision
D-8) retired the gald3r-internal event name and wired this hook into the
canonical core.

## Fires On

The **canonical `session-start` event**. Wired in `g_hk_core.py`
`CONCERN_CHAIN["session-start"]` (all dispatcher-driven platforms) and
registered directly on the harness-native trigger for Claude Code
(`.claude/settings.json` `hooks.SessionStart`) and Cursor (`.cursor/hooks.json`
`sessionStart`). The payload arrives on stdin as JSON; `session_id` (Claude),
`conversation_id` (Cursor), and `cwd`/`project_path` are all accepted. The
former gald3r-internal `pre_session` event name is retired (D-8).

## What It Does

Parses the session-event payload (falling back to a timestamp-derived
`session_id` when none is supplied), resolves the project root, prunes stale
trace markers (older than 7 days), and stages a per-session start marker
(`.gald3r/logs/session_trace_<session>.json`) with the start timestamp and an
epoch-ms stamp. The companion `g-hk-post-session-trace` reads it to compute
session duration on `stop` / `session-end`. Non-blocking by design.

## Side Effects

- Writes `.gald3r/logs/session_trace_<session>.json` (start marker).
- Prunes `session_trace_*.json` markers older than 7 days.
- Appends a `session-start | session=... | project=...` line to
  `.gald3r/logs/session_lifecycle.log`.
- Always returns `{ continue = true }` and exits 0 — never blocks session start,
  never touches control-plane state (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1624 (WS-A-1) — wired the logging chain into the canonical hook core;
  retired the internal `pre_session`/`post_session` event names (D-8).
- T1055 — original plugin lifecycle hooks (this was the `pre_session` example).
- Companion: `g-hk-post-session-trace` (logs/closes the session trace).
- Pattern: `commands/g-create-hook.md` (event list + scaffolding contract).
