# Hook: g-hk-pre-tool-call-prd-freeze

Pre-tool-call guard — refuses Edit/Write to a PRD file whose YAML status is
`released` or `superseded` (C-019 / g-rl-33 "PRD Freeze Gate"; Python port of
the retired PS1, T1584).

## Fires On

The **tool-start** event for file-mutation tools: Cursor `preToolUse` with the
`Edit|Write|MultiEdit|NotebookEdit|Patch|ApplyPatch|str_replace_editor`
matcher (`.cursor/hooks.json`), Claude Code `PreToolUse`
(`.claude/settings.json`), Gemini `.agent` overlay `BeforeTool`
(`.agent/hooks.json`), and the canonical `tool-start` `CONCERN_CHAIN` in
`g_hk_core.py` on every fanned platform.

## What It Does

A frozen PRD is the audit-of-record. Only `@g-prd-revise` may touch it, which
creates a successor PRD and updates the supersede chain atomically. The hook
reads the tool event JSON from stdin, inspects the target PRD's YAML
`status:`, and denies the write when the PRD is frozen.

- Bypass: `GALD3R_HOOK_BYPASS=1`.
- Revise flow: `GALD3R_PRD_REVISE_ACTIVE=1` (set by `@g-prd-revise`).

## Side Effects

- exit 0: allow — prints `{"permission": "allow"}`.
- exit 2: deny — prints a permission/deny body explaining the freeze.
- No file writes; the guard is read-only.

## Related Tasks

- C-019 — frozen PRDs are immutable audit records.
- g-rl-33 — enforcement catchall ("PRD Freeze Gate").
- T1584 — Python port of the PS1 hook fleet.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
