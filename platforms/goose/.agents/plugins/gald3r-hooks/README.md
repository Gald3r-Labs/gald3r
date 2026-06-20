# gald3r-hooks (goose plugin) — T510

goose discovers hooks from **plugins** (Open Plugins spec), not a root `hooks.json`. This plugin
routes goose's native lifecycle events through the shared gald3r canonical hook core.

- `plugin.json` — plugin manifest (goose discovers the plugin by this).
- `hooks/hooks.json` — maps goose events → canonical `g-hk-on-<event>.py` entrypoints.
- `hooks/g_hk_core.py` — the shared dispatcher (byte-identical to every other platform copy).
- `hooks/g-hk-on-*.py` — six thin canonical entrypoints (delegate to `g_hk_core.dispatch`).
- `hooks/g-hk-*.py` — the concern hooks the core runs per event (self-gating).

**Native event → canonical:** `SessionStart`→`session-start`, `SessionEnd`→`session-end`,
`UserPromptSubmit`→`user-prompt-submit`, `PreToolUse`→`tool-start`, `PostToolUse`→`tool-end`,
`Stop`→`stop`. goose passes the payload as JSON on stdin and sets `PLUGIN_ROOT`.

Install location in a real project: `~/.agents/plugins/gald3r-hooks/` (user) or
`<project>/.agents/plugins/gald3r-hooks/` (project). Source: goose-docs.ai hooks guide (2026-06-18).
