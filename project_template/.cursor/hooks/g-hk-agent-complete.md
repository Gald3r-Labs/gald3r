# Hook: g-hk-agent-complete

Agent/stop lifecycle hook — diagnostics, transcript discovery, chat-logger
launch, and reflection staging when an agent finishes responding (Python port
of the retired PS1, T1584).

## Fires On

The **stop** event: Cursor `stop` (`.cursor/hooks.json`), Claude Code `Stop`
(`.claude/settings.json`), Gemini `.agent` overlay `AfterAgent`
(`.agent/hooks.json`), and the canonical `stop` `CONCERN_CHAIN` in
`g_hk_core.py` on every fanned platform. Receives the stop-event payload
(`status`, `loop_count`, `conversation_id`, `transcript_path`) on stdin.

## What It Does

Writes diagnostic entries, discovers a transcript via the T1232 fallback
(most recent non-subagent `.jsonl` under the per-project agent-transcripts
dir) when the payload omits it, launches the sibling chat logger — resolved
through the shared core's `INDIRECT_CONCERNS` map and labeled with the
detected platform (T1625 / BUG-133), never a hardcoded platform filename —
with a 30-second timeout, writes a pending-reflection hint for the next
session-start hook, and optionally stages a skill-capture stub (T1174) when
`AGENT_CONFIG.md` has `skill_capture_hook: true`.

## Side Effects

- Appends to `.gald3r/logs/hook_diag.log`.
- Launches `g-hk-claude-chat-logger` as a subprocess (30 s timeout).
- Writes `.gald3r/logs/pending_reflection.json`.
- May stage a skill-capture stub (T1174).
- Emits `{}` and always exits 0 — never blocks the stop.

## Related Tasks

- T1625 / BUG-133 — chat-logger resolution via the core `INDIRECT_CONCERNS`
  map (a missing logger is a visible warning, never a silent no-op).
- T1232 — transcript-discovery fallback.
- T1584 — Python port of the PS1 hook fleet.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
