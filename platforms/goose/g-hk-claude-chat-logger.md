# Hook: g-hk-claude-chat-logger

Claude Code chat-logging hook — the Claude-side mirror of the Cursor logging flow
(`g-hk-agent-complete.ps1` → `g-hk-cursor-chat-logger.py`). Fixes BUG-091.

## Fires On

Claude Code **`Stop`** event (when Claude finishes responding to a turn). Wired in
`.claude/settings.json` under `hooks.Stop`. Receives the Stop JSON payload on stdin
(`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `stop_hook_active`).

## What It Does

1. Reads the Stop payload from stdin and extracts `transcript_path` + `session_id`.
2. Resolves the project root (payload `cwd`, else walks up from the script to `.gald3r/`).
3. Locates Python (`py` → `python` → `python3`) and invokes
   `g-hk-claude-chat-logger.py --transcript-path <path> --platform claude
   --conversation-id <session_id>`.
4. The Python engine reads Claude's transcript JSONL and writes a human-readable
   transcript to `.gald3r/logs/{YYYY-MM-DD}_{session_id}_claude_chat.log` in the
   same format the Cursor logger produces.

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
