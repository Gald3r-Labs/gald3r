# Codex hooks — canonical-core wiring (T510)

This directory holds the gald3r **shared canonical hook core** for OpenAI Codex.
It replaces the prior Claude-format clone that wrongly referenced `.claude/hooks/`.

## Native trigger config
`.codex/hooks.json` (Codex also accepts inline `[hooks]` in `config.toml`).
Schema: Claude-style — per-event `{ matcher, hooks: [ { type:"command", command } ] }`.
Only `type:"command"` handlers run today. Source:
https://developers.openai.com/codex/hooks

## Native → canonical event mapping
| Codex native | canonical | entrypoint |
|---|---|---|
| `SessionStart` | `session-start` | `g-hk-on-session-start.py` |
| `UserPromptSubmit` | `user-prompt-submit` | `g-hk-on-user-prompt-submit.py` |
| `PreToolUse` | `tool-start` | `g-hk-on-tool-start.py` |
| `PostToolUse` | `tool-end` | `g-hk-on-tool-end.py` |
| `Stop` | `stop` | `g-hk-on-stop.py` |

Codex has no `SessionEnd` event → `session-end` is not wired (graceful degradation).

## How it works
Each `g-hk-on-<event>.py` entrypoint is a thin shim that calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`. The
concern hooks self-gate on payload content, so routing a coarse native event
through the full chain is safe — irrelevant concerns no-op.

Authoritative schema: `skills/g-skl-platform-codex/PLATFORM_SPEC.md` `## Hook System`.
