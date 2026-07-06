# Hook: g-hk-session-start

Session-initialization hook — assembles the gald3r context banner injected at
the start of every new agent conversation (Python port of the retired PS1,
T1584).

## Fires On

The **session-start** event: Cursor `sessionStart` (`.cursor/hooks.json`),
Claude Code `SessionStart` (`.claude/settings.json`), Gemini `.agent` overlay
`SessionStart` (`.agent/hooks.json`), and the canonical `session-start`
`CONCERN_CHAIN` in `g_hk_core.py` on every fanned platform.

## What It Does

Ensures platform dirs are populated via `setup_gald3r_project`, guards against
double-application per session, reads and auto-heals `.gald3r/.identity`
(user_id fallback from the per-user appdata config, project_id UUID
regeneration), then assembles the `additional_context` banner: first-time-setup
notice, previous-session reflection reminder, vault context (note count, recent
activity, structure verification, stale-doc and raw-inbox counts), TASKS.md
archive gate, HEARTBEAT no_agent watchdog output (T968), cross-project WPAC
inbox summary, and GUARDRAILS.md. Emits a compact JSON response
`{"continue": true, "additional_context": ...}`.

## Side Effects

- May regenerate `.gald3r/.identity` fields (auto-heal).
- Writes a per-session double-application guard marker under `.gald3r/logs/`.
- Appends diagnostics to `.gald3r/logs/hook_diag.log`.
- Always exits 0 — never blocks session creation.

## Related Tasks

- T1584 — Python port of the PS1 hook fleet.
- T968 — HEARTBEAT no_agent watchdog surfaced in the banner.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
