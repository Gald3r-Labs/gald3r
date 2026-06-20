# OpenHands hooks — canonical-core wiring (T510)

This directory holds the gald3r **shared canonical hook core** for OpenHands.
It backs `.openhands/hooks.json` and replaces the prior Claude-format clone.

## Native trigger config
`.openhands/hooks.json` (snake_case event keys; PascalCase + `{"hooks":{...}}`
wrapper also accepted for Claude-Code compat).
Schema: `{ "<event>": [ { "matcher": "*", "hooks": [ { "command", "timeout" } ] } ] }`
(`command` is a shell command or script path; `timeout` in **seconds**; stdin JSON
payload; exit 2 or `{"decision":"deny"}` blocks). Source:
https://docs.openhands.dev/openhands/usage/customization/hooks

## Native → canonical event mapping
| OpenHands native | canonical | entrypoint |
|---|---|---|
| `session_start` | `session-start` | `g-hk-on-session-start.py` |
| `session_end` | `session-end` | `g-hk-on-session-end.py` |
| `user_prompt_submit` | `user-prompt-submit` | `g-hk-on-user-prompt-submit.py` |
| `pre_tool_use` | `tool-start` | `g-hk-on-tool-start.py` |
| `post_tool_use` | `tool-end` | `g-hk-on-tool-end.py` |
| `stop` | `stop` | `g-hk-on-stop.py` |

Full canonical set wired.

## How it works
Each `g-hk-on-<event>.py` entrypoint is a thin shim that calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`; concern
hooks self-gate on payload, so routing a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-openhands/PLATFORM_SPEC.md` `## Hook System`.
