# Pi hooks — canonical-core wiring (T510 / T1628)

This directory holds the gald3r **shared canonical hook core** for Pi
(badlogic/pi-mono).

## Native trigger config
`.pi/extensions/gald3r-hooks.ts` — Pi has NO declarative hooks.json; lifecycle
hooks are registered programmatically via `pi.on(event, handler)` in that
extension. Each handler shells out to `g_hk_core.dispatch(<canonical-event>)`,
resolving the core from THIS directory first (T1628: previously the bridge only
probed the Goose plugin path and `.gald3r_sys/hooks/`, neither of which ships
on a pi install — a silent no-op). Source:
https://pi.dev/docs/latest/extensions

## Native → canonical event mapping
| Pi native | canonical | dispatched by |
|---|---|---|
| `session_start` | `session-start` | `gald3r-hooks.ts` → `g_hk_core.dispatch` |
| `session_shutdown` | `session-end` | `gald3r-hooks.ts` → `g_hk_core.dispatch` |
| `tool_call` | `tool-start` | `gald3r-hooks.ts` → `g_hk_core.dispatch` |
| `tool_result` | `tool-end` | `gald3r-hooks.ts` → `g_hk_core.dispatch` |

Pi exposes no native `user-prompt-submit`/`stop` events; the bundled
`g-hk-on-<event>.py` entrypoints ship for parity and manual dispatch.

## How it works
The extension bridge pipes the Pi event payload as JSON on stdin — the identical
contract `_hook_common.read_stdin_json()` parses everywhere else. The shared
core `g_hk_core.py` (byte-identical across every platform overlay) runs the
event's ordered `CONCERN_CHAIN`; concern hooks self-gate on payload, so routing
a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-pi/PLATFORM_SPEC.md` `## Hook System`.
