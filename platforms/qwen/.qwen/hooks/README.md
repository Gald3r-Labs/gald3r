# Qwen Code hooks — canonical-core wiring (T510)

This directory holds the gald3r **shared canonical hook core** for Qwen Code.

## Native trigger config
`.qwen/settings.json` `hooks` object.
Schema: Claude-Code-style — per-event `{ matcher, hooks: [ { type:"command", command, timeout } ] }`
(`timeout` in ms; `command` may invoke any shell incl. PowerShell). Source:
https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/

## Native → canonical event mapping
| Qwen native | canonical | entrypoint |
|---|---|---|
| `SessionStart` | `session-start` | `g-hk-on-session-start.py` |
| `SessionEnd` | `session-end` | `g-hk-on-session-end.py` |
| `UserPromptSubmit` | `user-prompt-submit` | `g-hk-on-user-prompt-submit.py` |
| `PreToolUse` | `tool-start` | `g-hk-on-tool-start.py` |
| `PostToolUse` | `tool-end` | `g-hk-on-tool-end.py` |
| `Stop` | `stop` | `g-hk-on-stop.py` |

Full canonical set wired (Qwen tracks both Gemini CLI and Claude Code hooks).

## How it works
Each `g-hk-on-<event>.py` entrypoint is a thin shim that calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`; concern
hooks self-gate on payload, so routing a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-qwen/PLATFORM_SPEC.md` `## Hook System`.
