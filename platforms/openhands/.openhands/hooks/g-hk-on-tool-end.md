# Hook: g-hk-on-tool-end

Canonical **`tool-end`** event entrypoint (T424). A thin per-platform trigger
shim that delegates to the shared canonical event core
(`g_hk_core.dispatch("tool-end")`). It holds NO business logic.

## Fires On

The canonical `tool-end` lifecycle event — after a tool/action completes.
Mapped from each platform's native event by `g_hk_core.PLATFORM_EVENT_MAP`
(Cursor `postToolUse`, Claude `PostToolUse`, kiro-cli `postToolUse`, …).

## What It Does

Calls `g_hk_core.dispatch("tool-end")`, which reads the harness payload once
from stdin, runs the event's concern chain (currently empty — a clean
pass-through that platforms can now fire), merges any `additional_context`,
and emits a single `{ "continue": true }` envelope.

## Side Effects

- None of its own. Side effects come only from concern hooks registered in
  `g_hk_core.CONCERN_CHAIN["tool-end"]` (none yet).
- Always returns `{ "continue": true }` and exits 0 — never blocks.

## Related Tasks

- T424 — Canonical event set + shared-core handlers. This is the `tool-end`
  canonical entrypoint.
- Shared core: `g_hk_core.py` (`dispatch`, `CANONICAL_EVENTS`).
