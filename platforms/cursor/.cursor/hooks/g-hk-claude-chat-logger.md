# Hook: g-hk-claude-chat-logger

Claude Code chat-logging hook — the Claude-side mirror of the Cursor logging flow
(`g-hk-agent-complete.py` → `g-hk-cursor-chat-logger.py`). Fixes BUG-091.

## Fires On

The canonical **`stop`** event, **indirectly via `g-hk-agent-complete`** (T1624, WS-A-1).
`g-hk-agent-complete` is the registered stop concern (`g_hk_core.py` `CONCERN_CHAIN["stop"]`,
`.claude/settings.json` `hooks.Stop`, `.cursor/hooks.json` `stop`); it extracts/discovers the
transcript path (T1232 fallback included) and launches this logger as a subprocess. The indirect
wiring is recorded machine-readably in `g_hk_core.py` `INDIRECT_CONCERNS` so the hook-parity lint
(WS-A-5) treats it as chained, not orphaned. Registering this file directly as well would write
every chat log twice. Launcher platform-map resolution polish is tracked in T1625 (BUG-133).

## What It Does

1. `g-hk-agent-complete` reads the stop payload, resolves `transcript_path` +
   `conversation_id`/`session_id` (payload → env → T1232 agent-transcripts scan), and invokes
   `g-hk-claude-chat-logger.py --transcript-path <path> --project-path <root>
   [--conversation-id <id>] ...`.
2. This script reads the transcript JSONL and writes a human-readable
   transcript to `.gald3r/logs/{YYYY-MM-DD}_{id}_{platform}_chat.log` in the
   same format the Cursor logger produced.

## Side Effects

- Writes `.gald3r/logs/{date}_{session_id}_claude_chat.log` (the transcript).
- Appends diagnostic lines to `.gald3r/logs/hook_diag.log` (proves the hook ran;
  records success/exit code).
- Never blocks or alters the Stop decision (emits `{}` and exits 0).
- Does NOT touch tool-call logging, reflection hints, or the rest of the dormant
  Claude hook chain — that migration is tracked separately (see BUG-091 Related).

## Related Tasks

- BUG-091 — Claude Code chat logging broken (Cursor-format hooks.json ignored;
  Cursor logger is DB-coupled). This hook is the chat-logging portion of the fix.
