# Hook: g-hk-post-session-trace

Example reference hook for the **`post_session`** lifecycle event (T1055). Closes
the session trace record opened by `g-hk-pre-session-trace`.

## Fires On

The gald3r-internal **`post_session`** lifecycle event at the very end of a gald3r
work session. Distinct from the harness-native `stop` event (which wires
`g-hk-session-end.ps1`): `post_session` is the **gald3r-level** boundary,
dispatched by the gald3r skill/command runner or fired manually, and **not
auto-wired** into `hooks.json`. The payload arrives on stdin as JSON and SHOULD
carry `session_id` (if available) and `project_path`.

## What It Does

Reads the start marker staged by `g-hk-pre-session-trace`
(`.gald3r/logs/session_trace_<session>.json`), computes elapsed milliseconds,
removes the marker, and appends a duration line. If no start marker is present it
logs `elapsed_ms=unknown`. Non-blocking by design.

## Side Effects

- Reads and then deletes `.gald3r/logs/session_trace_<session>.json`.
- Appends a `post_session | session=... | elapsed_ms=...` line to
  `.gald3r/logs/session_lifecycle.log`.
- Always returns `{ continue = true }` and exits 0 — never blocks, never touches
  control-plane state (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1055 — Add plugin lifecycle hooks (pre/post skill/session). This is the
  `post_session` reference example.
- Companion: `g-hk-pre-session-trace` (opens the session trace).
- Pattern: `commands/g-create-hook.md` (event list + scaffolding contract).
