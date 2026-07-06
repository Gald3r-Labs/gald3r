# Kiro CLI lifecycle hooks (agent-JSON `hooks` field)

Kiro CLI declares lifecycle hooks **inside the agent JSON config**
(`.kiro/agents/<name>.json` `hooks` field) — NOT as standalone hook files. The
gald3r agent config is `.kiro/agents/gald3r.json`.

## Architecture (T424 — canonical event + shared core; T1601 — PS1-KILL)

Each native kiro-cli event maps to a gald3r **canonical event** and delegates to
the **shared Python core** (`g_hk_core.py`) so behavior matches every other
platform. As of T1601 (PS1-KILL epic T667), `gald3r.json`'s `command` field
invokes `python .kiro/hooks/g-hk-on-<event>.py` directly — no PowerShell shim is
needed, because kiro-cli's agent-JSON `command` field accepts an arbitrary
command string (unlike Augment's hook runner, which requires a script-file path
with a specific extension). This folder (`hooks-impl/`) is now retained only for
historical/documentation purposes; it no longer holds any hook implementation
files.

| kiro-cli native event | canonical event | entrypoint (invoked directly) |
|---|---|---|
| `agentSpawn` | `session-start` | `.kiro/hooks/g-hk-on-session-start.py` |
| `userPromptSubmit` | `user-prompt-submit` | `.kiro/hooks/g-hk-on-user-prompt-submit.py` |
| `preToolUse` | `tool-start` | `.kiro/hooks/g-hk-on-tool-start.py` |
| `postToolUse` | `tool-end` | `.kiro/hooks/g-hk-on-tool-end.py` |
| `stop` | `stop` | `.kiro/hooks/g-hk-on-stop.py` |

(kiro-cli has no native `sessionEnd` — `stop` is its session-end-equivalent, so
`session-end` is not wired here.)

## Invocation contract

- kiro-cli delivers the event payload as **JSON on STDIN**. Each canonical
  entrypoint's `g_hk_core.dispatch(<event>)` reads `sys.stdin` directly — the
  gald3r agent-JSON `command` inherits the parent process's stdin automatically,
  so no explicit piping wrapper is required.
- Flow control is by **exit code**: `0` ok; `2` (preToolUse / `tool-start`)
  blocks the tool call and returns STDERR to the LLM.

## Runtime note

The canonical core (`g_hk_core.py`, `_hook_common.py`), the six
`g-hk-on-<event>.py` entrypoints, AND the per-concern hooks the core fans out to
(`g-hk-session-start.py`, `g-hk-session-end.py`, `g-hk-validate-shell.py`,
`g-hk-pre-tool-call*.py`, `g-hk-agent-complete.py`, `g-hk-nightly-learn.py`,
`g-hk-encoding-normalize.py`, `g-hk-ggo-stop-detect.py`) are now all present in
`.kiro/hooks/` (T510 AC4). The canonical handlers therefore run **real behavior**
via the shared core rather than passing through.

Authoritative schema: `skills/g-skl-platform-kiro-cli/PLATFORM_SPEC.md` `## Hook System`.
