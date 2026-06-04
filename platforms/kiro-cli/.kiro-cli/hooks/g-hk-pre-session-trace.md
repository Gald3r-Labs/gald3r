# Hook: g-hk-pre-session-trace

Example reference hook for the **`pre_session`** lifecycle event (T1055).
Demonstrates per-session observability/tracing at the gald3r session boundary.

## Fires On

The gald3r-internal **`pre_session`** lifecycle event at the very start of a gald3r
work session. This is distinct from the harness-native `sessionStart` event (which
wires `g-hk-session-start.ps1`): `pre_session` is the **gald3r-level** boundary,
dispatched by the gald3r skill/command runner or fired manually, so gald3r can
trace its own session lifecycle independent of which harness (Cursor / Claude /
CLI) launched the session. It is **not auto-wired** into `hooks.json`. The payload
arrives on stdin as JSON and SHOULD carry `session_id` (if available) and
`project_path`.

## What It Does

Parses the session-event payload (falling back to a timestamp-derived `session_id`
when none is supplied), resolves the project root, and stages a per-session start
marker (`.gald3r/logs/session_trace_<session>.json`) with the start timestamp and
an epoch-ms stamp. The companion `g-hk-post-session-trace` reads it to compute
session duration. Non-blocking by design.

## Side Effects

- Writes `.gald3r/logs/session_trace_<session>.json` (start marker).
- Appends a `pre_session | session=... | project=...` line to
  `.gald3r/logs/session_lifecycle.log`.
- Always returns `{ continue = true }` and exits 0 — never blocks session start,
  never touches control-plane state (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1055 — Add plugin lifecycle hooks (pre/post skill/session). This is the
  `pre_session` reference example.
- Companion: `g-hk-post-session-trace` (closes the session trace).
- Pattern: `commands/g-create-hook.md` (event list + scaffolding contract).
