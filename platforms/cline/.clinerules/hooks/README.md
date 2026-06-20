# gald3r canonical hooks — Cline (T512)

> **PLATFORM NOTE: Cline hooks are macOS/Linux ONLY (no Windows).**
> **STATUS: authored against cline.bot/blog/cline-v3-36-hooks (2025-11-06) — PENDING live-install
> verification** (exact PreToolUse field names + TaskStart/Resume/Cancel payload shapes were not
> fully documented).

Cline (v3.36+) discovers hooks as **executable scripts named exactly the hook type, with NO
extension**, in `.clinerules/hooks/` (project) or `~/Documents/Cline/Rules/Hooks/` (global). Cline
runs the file directly, so each must have a `#!/usr/bin/env python3` shebang and the executable bit.

Because Cline's I/O contract (`{cancel, errorMessage, contextModification}`) differs from the gald3r
canonical core (`{continue, reason, additional_context}`), the six hook-type files are **thin shims**
that call `_cline_adapter.py`, which keeps `g_hk_core.py` byte-identical and translates.

## Files
- `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `TaskStart`, `TaskResume`, `TaskCancel` —
  no-extension executable shims (each `exec`s `_cline_adapter.py <canonical-event>`).
- `_cline_adapter.py` — normalizes cline's payload, runs the standard `g-hk-on-<event>.py`, emits
  cline's `{cancel, contextModification}`. (NOT named a hook type, so cline ignores it as a hook.)
- `g_hk_core.py` + `g-hk-on-*.py` + `g-hk-*.py` — the shared core, entrypoints, and concern hooks
  (byte-identical to every other platform copy).

## Native hook → canonical
| Cline hook | canonical | translation |
|---|---|---|
| `PreToolUse` | `tool-start` | `cancel = !continue`, `errorMessage = reason` |
| `PostToolUse` | `tool-end` | `contextModification = additional_context` |
| `UserPromptSubmit` | `user-prompt-submit` | context only |
| `TaskStart` | `session-start` | context only |
| `TaskResume` | `session-start` | context only |
| `TaskCancel` | `session-end` | context only |

The six shim files must keep their executable bit on macOS/Linux (set in git via
`git update-index --chmod=+x`). Source: cline.bot/blog/cline-v3-36-hooks.
