---
subsystem_memberships: [LOGGING_SYSTEM]
---
# Hook: g-hk-crash-record

CRASH activation recorder (T433). Appends one activation record to
`.gald3r/logs/crash_activations.jsonl` for the **manual/heuristic** recording path — the
Skills / Agents / Hooks / Rules that have no native IDE harness event.

## Fires On

A gald3r-internal CRASH activation report. The engine auto-records every **Command** it dispatches
(`gald3r.crash` + `adapters/cli.py`); IDE harnesses (Cursor / Claude Code) do **not** emit a
discrete event for every Rule / Skill / Agent / Hook activation, so this hook is the explicit path
those use: a hook event, the gald3r skill/command runner, or an agent invokes it with a JSON
payload describing the component that just activated. Rule "activation" has no native event (rules
are always-loaded context), so a faithful "rule fired" signal must be reported here explicitly.

## Payload (stdin JSON)

| Field | Notes |
|---|---|
| `component_type` | one of `command` / `rule` / `agent` / `skill` / `hook` |
| `component_name` | e.g. `g-skl-tasks`, `g-rl-00-always`, `g-hk-encoding-normalize` |
| `trigger_source` | what triggered it (a command/rule/hook/agent name) |
| `elapsed_ms` | optional duration |
| `session_id` | optional; falls back to `GALD3R_SESSION_ID` / `CURSOR_CONVERSATION_ID` / a per-process id |

## What It Does

- **Zero-overhead gate first:** if `GALD3R_CRASH_STATS` is unset / `off`, records nothing and
  returns immediately (matches the engine hot-path gate, AC #10).
- Otherwise appends one JSONL line matching `gald3r.crash.ActivationRecord`:
  `{component_type, component_name, activated_at, session_id, trigger_source, elapsed_ms}`.
- Non-blocking — always returns `{ continue = true }`, never delays the observed event, never
  touches control-plane state (TASKS.md, BUGS.md, task/bug files).

## Side Effects

- Appends one line to `.gald3r/logs/crash_activations.jsonl`.

## Related

- T433 — CRASH activation tracking. Engine core: `gald3r/crash.py`; report command:
  `@g-crash-stats` (`gald3r crash-stats`).
- T432 — debug-mode call-stack tracer (`@g-... --debug`). When both are active, a command dispatch
  writes the debug trace and the CRASH record in the same event.
- Pattern mirror: `g-hk-post-skill-timing` (gald3r-internal lifecycle, stdin JSON, non-blocking).
