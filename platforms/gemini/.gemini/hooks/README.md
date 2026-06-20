# Gemini CLI hooks — canonical-core wiring (T510)

This directory holds the gald3r **shared canonical hook core** for Gemini CLI,
at gemini's REAL native dot-dir (`.gemini/`).

> **Overlay note:** the pre-existing `platforms/gemini/.agent/` tree is a
> Claude-format clone that the gemini product does NOT read. Reconciling/removing
> it is tracked separately (T510 Status History) and is out of scope for the hook
> fan-out. gemini reads `.gemini/settings.json` — authored here.

## Native trigger config
`.gemini/settings.json` `hooks` object.
Schema: `{ "hooks": { "<Event>": [ { "matcher", "hooks": [ { "type":"command", "command" } ] } ] } }`.
Tool-event matchers are regex; lifecycle matchers exact; `*`/`""` matches all;
`timeout` in ms. Hooks run synchronously (loop waits). Source:
https://geminicli.com/docs/hooks/

## Native → canonical event mapping
| Gemini native | canonical | entrypoint |
|---|---|---|
| `SessionStart` | `session-start` | `g-hk-on-session-start.py` |
| `SessionEnd` | `session-end` | `g-hk-on-session-end.py` |
| `BeforeTool` | `tool-start` | `g-hk-on-tool-start.py` |
| `AfterTool` | `tool-end` | `g-hk-on-tool-end.py` |
| `AfterAgent` | `stop` | `g-hk-on-stop.py` |

Mapping per `g_hk_core.PLATFORM_EVENT_MAP['gemini']` (the richer `BeforeAgent`/
`BeforeModel` events are not in the canonical floor — graceful degradation).

## How it works
Each `g-hk-on-<event>.py` entrypoint is a thin shim that calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`; concern
hooks self-gate on payload, so routing a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-gemini/PLATFORM_SPEC.md` `## Hook System`.
