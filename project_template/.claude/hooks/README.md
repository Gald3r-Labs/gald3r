# gald3r Claude Code Hooks

These are the Claude Code lifecycle hooks for gald3r, wired via
`.claude/hooks.json` (PascalCase events: `SessionStart`, `PreToolUse`, …). They
are Python scripts (T1584 port) that import the shared bootstrap
`_hook_common.py`. Other platforms use **different** hook models — see each
platform's `PLATFORM_SPEC.md` `## Hook System` section before assuming a hook is
portable.

## Canonical event model (T424)

gald3r is consolidating Cursor's ~18 native hook events down to a **canonical
reduced set of 6** events that are commonly supported across hook-capable
platforms, all served by **one shared Python core**:

| Canonical event | Meaning |
|---|---|
| `session-start` | A new agent session/conversation begins (context injection) |
| `session-end` | An agent session terminates (final cleanup/reflection) |
| `user-prompt-submit` | The user submits a prompt, before the agent acts |
| `tool-start` | Before a tool/action executes (the blocking guard point) |
| `tool-end` | After a tool/action completes |
| `stop` | The agent finishes responding to a turn (≠ `session-end`) |

`pre-commit` is intentionally **not** a canonical agent-lifecycle event — it is a
git-level hook handled by `g-hk-pre-commit`.

### Files

- **`g_hk_core.py`** — the shared canonical event core. Holds the canonical
  event set, the platform→canonical event map (`PLATFORM_EVENT_MAP`), and the
  per-event concern chain (`CONCERN_CHAIN`). `dispatch(event)` reads the harness
  payload once, runs every concern hook in the chain, merges their
  `additional_context`, honors the first blocking verdict, and emits one
  unified envelope. **This is where behavior is authored once.**
- **`g-hk-on-<event>.py`** — six thin canonical entrypoints (one per event) that
  just call `g_hk_core.dispatch("<event>")`. Platform triggers point here. They
  contain NO business logic.
- **`g-hk-<concern>.py`** — the existing per-concern hooks (e.g.
  `g-hk-session-start.py`, `g-hk-pre-tool-call-gald3r-guard.py`,
  `g-hk-agent-complete.py`). These are the actual behavior; the core fans out to
  them via `CONCERN_CHAIN`.
- **`g-hk-*.md`** — T1171 companion docs for hooks wired in `hooks.json`.

> **Naming note:** canonical event entrypoints are named `g-hk-on-<event>` (e.g.
> `g-hk-on-tool-end`) rather than the bare `g-hk-<event>`, because several bare
> names (`g-hk-session-start`, `g-hk-session-end`) are already the per-concern
> handlers the core invokes. The `on-` prefix disambiguates "canonical event
> entrypoint" from "concern handler" without renaming shipped infra mid-rebuild.

## Migration status (T424 reference increment)

- ✅ Shared core + 6 canonical entrypoints shipped (this folder + `.claude/hooks/`).
- ✅ Claude `hooks.json` wires the two **new** canonical events
  (`PostToolUse` → `g-hk-on-tool-end`, `UserPromptSubmit` →
  `g-hk-on-user-prompt-submit`). Fully additive.
- 🔜 The pre-existing per-concern entries (`SessionStart`/`Stop`/`PreToolUse`)
  are retained as-is; re-pointing them at the canonical entrypoints is the
  **AC4 fan-out** follow-up.

## Other platforms' hook models (do not assume portability)

- **Claude Code** — `settings.json` / `.claude/hooks.json` with PascalCase
  events (`SessionStart`, `PreToolUse`, …). Mirrors this folder.
- **Kiro IDE** — declarative `.kiro/hooks/*.kiro.hook` JSON (file/event
  `fileEdited`/`userTriggered`, `askAgent`/`command`). Does NOT use the Python
  core. See `platforms/kiro/.kiro/hooks/README.md`.
- **Kiro CLI** — lifecycle hooks embedded in the agent JSON `hooks` field (no
  standalone hook files); STDIN-JSON payload, exit-code flow control. Thin
  `.ps1` shims pipe STDIN to the canonical entrypoints. See
  `platforms/kiro-cli/.kiro/hooks-impl/README.md`.
- **opencode / openclaw** — JS/TS plugin hooks (out of scope for the Python core).

Authoritative per-platform capability: each `skills/g-skl-platform-<p>/PLATFORM_SPEC.md`.
