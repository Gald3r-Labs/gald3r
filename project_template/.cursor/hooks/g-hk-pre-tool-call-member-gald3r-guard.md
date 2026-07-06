# Hook: g-hk-pre-tool-call-member-gald3r-guard

Pre-tool-call guard — refuses Edit/Write to a Workspace-Control member
repository's `.gald3r/` that targets anything other than the marker pair
(`.identity` / `PROJECT.md`), enforcing g-rl-36 (Python port of the retired
PS1, T1584).

## Fires On

The **tool-start** event for file-mutation tools: Cursor `preToolUse` with the
`Edit|Write|MultiEdit|NotebookEdit|Patch|ApplyPatch|str_replace_editor`
matcher (`.cursor/hooks.json`), Claude Code `PreToolUse`
(`.claude/settings.json`), Gemini `.agent` overlay `BeforeTool`
(`.agent/hooks.json`), and the canonical `tool-start` `CONCERN_CHAIN` in
`g_hk_core.py` on every fanned platform.

## What It Does

Member repos may keep ONLY `.gald3r/.identity` and `.gald3r/PROJECT.md`;
everything else (TASKS.md, tasks/, BUGS.md, bugs/, PLAN.md, ...) is forbidden
there (g-rl-36 "Workspace-Control Member `.gald3r/` Marker-Only Guard",
BUG-021 / T213). The hook reads the tool event JSON from stdin and denies
writes that violate the marker-only contract. Any unexpected error fails open
(allow, exit 0).

- Bypass: `GALD3R_HOOK_BYPASS=1`.
- Marker init: `GALD3R_MARKER_INIT_ACTIVE=1` (set by
  `bootstrap_member_gald3r_marker` — allows writing the marker pair itself).

## Side Effects

- exit 0: allow — prints `{"permission": "allow"}`.
- exit 2: deny — prints a permission/deny JSON object (documented blocking
  behavior — preserved).
- No file writes; the guard is read-only and makes no cross-script calls at
  runtime.

## Related Tasks

- g-rl-36 — workspace-member `.gald3r/` marker-only guard.
- BUG-021 / T213 — member repos accumulating full `.gald3r/` control planes.
- T1584 — Python port of the PS1 hook fleet.
- T1628 (WS-A-5) — hook-parity lint; this companion hook.md added for the
  T1171 contract.
