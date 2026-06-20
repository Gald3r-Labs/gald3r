# gald3r hooks — OpenCode plugin

OpenCode uses **JS/TS plugins** (not command hooks). This dir ships a thin trigger layer that defers
all logic to the shared gald3r Python core.

## Layout

```
.opencode/plugins/
├── gald3r-hooks.js        # OpenCode plugin (trigger layer) — exports Gald3rHooks
├── gald3r-hooks/          # shared Python core (byte-identical to every other platform)
│   ├── g_hk_core.py
│   ├── _hook_common.py
│   ├── g-hk-on-<event>.py # canonical entrypoints
│   └── g-hk-*.py          # concern hooks
└── README.md
```

## Event mapping (OpenCode → canonical)

| OpenCode plugin event | Canonical entrypoint        | Behavior                          |
|-----------------------|-----------------------------|-----------------------------------|
| `tool.execute.before` | `g-hk-on-tool-start.py`     | throws → **blocks** when a concern blocks |
| `tool.execute.after`  | `g-hk-on-tool-end.py`       | observe                           |
| `session.created`     | `g-hk-on-session-start.py`  | observe                           |
| `session.deleted`     | `g-hk-on-session-end.py`    | observe                           |
| `session.idle`        | `g-hk-on-stop.py`           | observe                           |

## Requirements

- `python` on PATH (the JS plugin shells out to the Python core).
- OpenCode auto-loads `*.js`/`*.ts` from `.opencode/plugins/`; the `.py` files in `gald3r-hooks/`
  are ignored by the plugin loader by design.

## Status

**PENDING live-install verification.** Authored against the OpenCode plugin docs (2026-06-18). The
exact `input`/`output` argument shapes for `tool.execute.*` and the session event payloads should be
confirmed against the installed OpenCode SDK version. The plugin is **fail-soft**: any error allows
(never blocks the host) except an explicit concern block on `tool-start`.
