# Hook: g-hk-on-user-prompt-submit

Canonical **`user-prompt-submit`** event entrypoint (T424). A thin per-platform
trigger shim that delegates to the shared canonical event core
(`g_hk_core.dispatch("user-prompt-submit")`). It holds NO business logic.

## Fires On

The canonical `user-prompt-submit` lifecycle event — the user submits a prompt,
before the agent acts on it. Mapped from each platform's native event by
`g_hk_core.PLATFORM_EVENT_MAP` (Cursor `beforeSubmitPrompt`, Claude
`UserPromptSubmit`, kiro-cli `userPromptSubmit`, …).

## What It Does

Calls `g_hk_core.dispatch("user-prompt-submit")`, which reads the harness
payload once from stdin, runs the event's concern chain (currently empty — a
clean pass-through that platforms can now fire), merges any
`additional_context`, and emits a single `{ "continue": true }` envelope.

## Side Effects

- None of its own. Side effects come only from concern hooks registered in
  `g_hk_core.CONCERN_CHAIN["user-prompt-submit"]` (none yet).
- Always returns `{ "continue": true }` and exits 0 — never blocks.

## Related Tasks

- T424 — Canonical event set + shared-core handlers. This is the
  `user-prompt-submit` canonical entrypoint.
- Shared core: `g_hk_core.py` (`dispatch`, `CANONICAL_EVENTS`).
