# Augment (Auggie CLI) hooks — canonical-core wiring (T510, T1601)

This directory holds the gald3r **shared canonical hook core** for Augment, plus
per-event `.cmd` trigger shims.

## Native trigger config
`.augment/settings.json` `hooks` object.
Schema: Claude-Code-style — per-event `{ matcher, hooks: [ { type:"command", command, timeout } ] }`.
**IMPORTANT:** Augment's `command` MUST be a path to a script with a supported
extension (`.ps1` / `.cmd` / `.bat` / `.sh`) — a bare `python x.py` is rejected.
So each event points at a thin `g-hk-augment-<event>.cmd` shim (this dir) that
forwards the inherited stdin payload to the canonical `g-hk-on-<event>.py`
entrypoint. Source: https://docs.augmentcode.com/cli/hooks

## Native → canonical event mapping
| Augment native | canonical | shim → entrypoint |
|---|---|---|
| `SessionStart` | `session-start` | `g-hk-augment-session-start.cmd` → `g-hk-on-session-start.py` |
| `SessionEnd` | `session-end` | `g-hk-augment-session-end.cmd` → `g-hk-on-session-end.py` |
| `PreToolUse` | `tool-start` | `g-hk-augment-tool-start.cmd` → `g-hk-on-tool-start.py` |
| `PostToolUse` | `tool-end` | `g-hk-augment-tool-end.cmd` → `g-hk-on-tool-end.py` |
| `Stop` | `stop` | `g-hk-augment-stop.cmd` → `g-hk-on-stop.py` |

`PreToolUse` exit code 2 blocks the tool. Augment has no user-prompt-submit in the
canonical map. Shims are Windows batch (`.cmd`), not PowerShell (T1601, PS1-KILL
epic T667) — this retires the `pwsh`/`ExecutionPolicy` dependency the prior `.ps1`
shims carried, since `.cmd` is one of Augment's own schema-accepted extensions.
POSIX-only installs may still need parallel `.sh` shims (follow-up, unchanged).

## How it works
Each shim pipes stdin → `g-hk-on-<event>.py`, which calls
`g_hk_core.dispatch("<event>")`. The shared core `g_hk_core.py` (byte-identical
across every platform overlay) runs the event's ordered `CONCERN_CHAIN`; concern
hooks self-gate on payload, so routing a coarse event through the full chain is safe.

Authoritative schema: `skills/g-skl-platform-augment/PLATFORM_SPEC.md` `## Hook System`.
