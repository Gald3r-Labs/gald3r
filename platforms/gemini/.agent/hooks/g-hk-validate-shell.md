# Hook: g-hk-validate-shell

Shell-command validation guard — blocks dangerous destructive commands before
they execute (Python port of the retired PS1, T1584).

## Fires On

The **tool-start** event for shell tools: Cursor `beforeShellExecution`
(`.cursor/hooks.json`), Claude Code `PreToolUse` with the
`Bash|Shell|Terminal|run_terminal_cmd` matcher (`.claude/settings.json`),
Gemini `.agent` overlay `BeforeTool` with the same matcher
(`.agent/hooks.json`), and the canonical `tool-start` `CONCERN_CHAIN` in
`g_hk_core.py` on every fanned platform.

## What It Does

Reads the tool event JSON (`{ command, ... }`) from stdin and pattern-matches
the command against the destructive-command denylist (recursive deletes of
project roots, force-pushes to protected branches, and similar irreversible
operations). Allows everything else.

## Side Effects

- exit 0: allow — prints `{"permission": "allow"}`.
- exit 2: deny — prints a permission/deny body with `user_message` /
  `agent_message` explaining the block.
- No file writes; the guard is read-only.

## Related Tasks

- T1584 — Python port of the PS1 hook fleet.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
