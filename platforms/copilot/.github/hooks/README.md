# GitHub Copilot hooks — canonical-core wiring (T510)

This directory holds the gald3r **shared canonical hook core** for GitHub Copilot
(Copilot CLI; VS Code agent hooks are preview). These are agent-session hooks —
NOT git hooks, CI, or Actions.

## Native trigger config
`.github/hooks/gald3r-hooks.json` (Copilot loads `.github/hooks/*.json`).
Schema: `{ "version": 1, "hooks": { "<event>": [ { "type":"command", "command", "timeoutSec" } ] } }`.
`command` is the cross-platform fallback (copied to both bash + powershell);
`preToolUse` returning `deny` blocks the tool. Source:
https://docs.github.com/en/copilot/reference/hooks-configuration

## Native → canonical event mapping
| Copilot native | canonical | entrypoint |
|---|---|---|
| `sessionStart` | `session-start` | `g-hk-on-session-start.py` |
| `sessionEnd` | `session-end` | `g-hk-on-session-end.py` |
| `userPromptSubmitted` | `user-prompt-submit` | `g-hk-on-user-prompt-submit.py` |
| `preToolUse` | `tool-start` | `g-hk-on-tool-start.py` |
| `postToolUse` | `tool-end` | `g-hk-on-tool-end.py` |

Copilot has no `stop` event → `stop` is not wired (graceful degradation).

## How it works
Each `g-hk-on-<event>.py` entrypoint is a thin shim that calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`; concern
hooks self-gate on payload, so routing a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-copilot/PLATFORM_SPEC.md` `## Hook System`.
