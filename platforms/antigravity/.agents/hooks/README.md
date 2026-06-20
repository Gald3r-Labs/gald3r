# gald3r canonical hooks — Antigravity (T510)

> **STATUS: authored against the Antigravity 2.0 launch docs (antigravity.google/docs/hooks,
> 2026-06-18) — PENDING live-install verification.** Antigravity launched the same day (replacing
> Gemini CLI) and its own docs mandate pinning the payload schema via a live install test. Verify
> before relying on it (especially the `Stop` decision semantics and the command path resolution).

Antigravity's hook I/O contract differs from every other gald3r platform, so it does NOT call the
canonical `g-hk-on-<event>.py` entrypoints directly. Instead `g-hk-ag-dispatch.py` is a thin
**adapter** that keeps `g_hk_core.py` byte-identical and translates between the two contracts.

- `hooks.json` (at `.agents/hooks.json`) — maps Antigravity events → the adapter, per the
  documented hook-name→event schema.
- `hooks/g-hk-ag-dispatch.py <event>` — reads Antigravity's camelCase stdin, normalizes the
  payload, runs the standard `g-hk-on-<event>.py` (same concern chain), then emits Antigravity's
  `decision` envelope (`PreToolUse`→`allow/deny`, `PostToolUse`→`{}`, `Stop`→allow-stop).
- `hooks/g_hk_core.py` + `g-hk-on-*.py` + `g-hk-*.py` — the shared core, entrypoints, and concern
  hooks (byte-identical to every other platform copy).

## Native event → canonical
| Antigravity event | canonical | notes |
|---|---|---|
| `PreToolUse` | `tool-start` | adapter emits `{decision: allow\|deny}` |
| `PostToolUse` | `tool-end` | adapter emits `{}` |
| `Stop` | `stop` | runs side-effecting stop concerns; allows stop (force-continue NOT wired pending verify) |
| `PreInvocation` / `PostInvocation` | — | NOT wired: these are model-invocation events with no clean canonical mapping. Antigravity has no SessionStart/SessionEnd/UserPromptSubmit, so session/prompt concerns are not reachable here. |

Source: antigravity.google/docs/hooks (Antigravity 2.0, fetched 2026-06-18).
