# Windsurf (Cascade) hooks — canonical-core wiring (T510)

This directory holds the gald3r **shared canonical hook core** for Windsurf Cascade.
It backs the workspace trigger config and replaces the prior Claude-format clone.

## Native trigger config
`.windsurf/hooks.json` (workspace level; merged with user/system).
Schema: `{ "hooks": { "<event>": [ { "command": <bash>, "powershell": <pwsh>, "show_output" } ] } }`.
Payload is JSON on stdin; pre-hooks BLOCK via **exit code 2**. Source:
https://docs.windsurf.com/windsurf/cascade/hooks

## Native → canonical event mapping
| Windsurf native | canonical | entrypoint |
|---|---|---|
| `pre_user_prompt` | `user-prompt-submit` | `g-hk-on-user-prompt-submit.py` |
| `pre_run_command` | `tool-start` | `g-hk-on-tool-start.py` |
| `pre_write_code` | `tool-start` | `g-hk-on-tool-start.py` |
| `post_run_command` | `tool-end` | `g-hk-on-tool-end.py` |
| `post_write_code` | `tool-end` | `g-hk-on-tool-end.py` |
| `post_cascade_response` | `stop` | `g-hk-on-stop.py` |

Windsurf has no session-start/session-end events → those are not wired (graceful degradation).
Each event carries both a `command` (POSIX `python3`) and a `powershell` (Windows `python`) key.

## How it works
Each `g-hk-on-<event>.py` entrypoint is a thin shim that calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`; concern
hooks self-gate on payload, so routing a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-windsurf/PLATFORM_SPEC.md` `## Hook System`.
