# Augment (Auggie CLI) hooks — canonical-core wiring (T510)

This directory holds the gald3r **shared canonical hook core** for Augment, plus
per-event `.ps1` trigger shims.

## Native trigger config
`.augment/settings.json` `hooks` object.
Schema: Claude-Code-style — per-event `{ matcher, hooks: [ { type:"command", command, timeout } ] }`.
**IMPORTANT:** Augment's `command` MUST be a path to a script with a supported
extension (`.ps1` / `.cmd` / `.bat` / `.sh`) — a bare `python x.py` is rejected.
So each event points at a thin `g-hk-augment-<event>.ps1` shim (this dir) that
pipes the stdin payload to the canonical `g-hk-on-<event>.py` entrypoint. Source:
https://docs.augmentcode.com/cli/hooks

## Native → canonical event mapping
| Augment native | canonical | shim → entrypoint |
|---|---|---|
| `SessionStart` | `session-start` | `g-hk-augment-session-start.ps1` → `g-hk-on-session-start.py` |
| `SessionEnd` | `session-end` | `g-hk-augment-session-end.ps1` → `g-hk-on-session-end.py` |
| `PreToolUse` | `tool-start` | `g-hk-augment-tool-start.ps1` → `g-hk-on-tool-start.py` |
| `PostToolUse` | `tool-end` | `g-hk-augment-tool-end.ps1` → `g-hk-on-tool-end.py` |
| `Stop` | `stop` | `g-hk-augment-stop.ps1` → `g-hk-on-stop.py` |

`PreToolUse` exit code 2 blocks the tool. Augment has no user-prompt-submit in the
canonical map. Shims are PowerShell (matching the kiro-cli precedent); POSIX-only
installs may need parallel `.sh` shims (follow-up).

## How it works
Each shim pipes stdin → `g-hk-on-<event>.py`, which calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`; concern
hooks self-gate on payload, so routing a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-augment/PLATFORM_SPEC.md` `## Hook System`.
