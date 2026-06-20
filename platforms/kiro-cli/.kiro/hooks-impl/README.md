# Kiro CLI lifecycle hooks (agent-JSON `hooks` field)

Kiro CLI declares lifecycle hooks **inside the agent JSON config**
(`.kiro/agents/<name>.json` `hooks` field) — NOT as standalone hook files. The
gald3r agent config is `.kiro/agents/gald3r.json`.

## Architecture (T424 — canonical event + shared core)

Each native kiro-cli event maps to a gald3r **canonical event** and delegates to
the **shared Python core** (`g_hk_core.py`) so behavior matches every other
platform:

| kiro-cli native event | canonical event | shim |
|---|---|---|
| `agentSpawn` | `session-start` | `g-hk-kiro-cli-session-start.ps1` |
| `userPromptSubmit` | `user-prompt-submit` | `g-hk-kiro-cli-user-prompt-submit.ps1` |
| `preToolUse` | `tool-start` | `g-hk-kiro-cli-tool-start.ps1` |
| `postToolUse` | `tool-end` | `g-hk-kiro-cli-tool-end.ps1` |
| `stop` | `stop` | `g-hk-kiro-cli-stop.ps1` |

(kiro-cli has no native `sessionEnd` — `stop` is its session-end-equivalent, so
`session-end` is not wired here.)

## Shim contract

- The shims in this folder are **thin trigger wiring ONLY** — no business logic.
- kiro-cli delivers the event payload as **JSON on STDIN**. Each shim reads
  `$input` and pipes it to the canonical entrypoint
  `.kiro/hooks/g-hk-on-<event>.py`, which calls `g_hk_core.dispatch(<event>)`.
- Flow control is by **exit code**: `0` ok; `2` (preToolUse / `tool-start`)
  blocks the tool call and returns STDERR to the LLM.
- gald3r `.ps1` shims read STDIN (`$input`), **not** `$env:*`.

## Runtime note

The canonical core (`g_hk_core.py`, `_hook_common.py`), the six
`g-hk-on-<event>.py` entrypoints, AND the per-concern hooks the core fans out to
(`g-hk-session-start.py`, `g-hk-session-end.py`, `g-hk-validate-shell.py`,
`g-hk-pre-tool-call*.py`, `g-hk-agent-complete.py`, `g-hk-nightly-learn.py`,
`g-hk-encoding-normalize.py`, `g-hk-ggo-stop-detect.py`) are now all present in
`.kiro/hooks/` (T510 AC4). The canonical handlers therefore run **real behavior**
via the shared core rather than passing through.

Authoritative schema: `skills/g-skl-platform-kiro-cli/PLATFORM_SPEC.md` `## Hook System`.
