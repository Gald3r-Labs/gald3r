# Hook: g-hk-pre-tool-call-gald3r-guard

Pre-tool-call guard — refuses unsupervised Edit/Write to `.gald3r/` paths,
enforcing the g-rl-33 ".gald3r/ Folder Gate (HARD RULE)" (Python port of the
retired PS1, T1584).

## Fires On

The **tool-start** event for file-mutation tools: Cursor `preToolUse` with the
`Edit|Write|MultiEdit|NotebookEdit|Patch|ApplyPatch|str_replace_editor`
matcher (`.cursor/hooks.json`), Claude Code `PreToolUse`
(`.claude/settings.json`), Gemini `.agent` overlay `BeforeTool`
(`.agent/hooks.json`), and the canonical `tool-start` `CONCERN_CHAIN` in
`g_hk_core.py` on every fanned platform.

## What It Does

Reads the tool event JSON (`{ tool_name, tool_input: { file_path | path |
notebook_path, ... } }`) from stdin and denies the call when the target path
is inside `.gald3r/` and no active gald3r agent is declared. Enforces:
"NEVER read or write any file inside `.gald3r/` without an active gald3r
agent."

- Bypass: `GALD3R_HOOK_BYPASS=1` (T600 §3.3 user override).
- Allow override (active gald3r command): `GALD3R_ACTIVE_AGENT=<agent_id>`.

## Side Effects

- exit 0: allow — prints `{"permission": "allow"}`.
- exit 2: deny — human-readable reason on STDERR (Claude Code's
  blocking-error contract; BUG-179 fix).
- No file writes; the guard is read-only.

## Related Tasks

- g-rl-33 — enforcement catchall (`.gald3r/` Folder Gate).
- BUG-179 — deny reason must go to STDERR for Claude Code.
- T1584 — Python port of the PS1 hook fleet.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
