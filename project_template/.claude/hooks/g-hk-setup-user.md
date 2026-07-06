---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# Hook: g-hk-setup-user

One-time interactive gald3r user-identity setup. Companion `.md` added with the
T1624 orphan-disposition pass (the script predates the T1171 companion
contract).

## Keep-Justification (T1624, decision D-7)

Reviewed for retire-vs-keep under D-7 ("delete setup-user/component-tag-check if
superseded"): **KEPT — not superseded.** No other component provides the
interactive identity flow: it suggests a user ID from git global email / the
Cursor cached email / the OS username, prompts once, and writes the unified
per-user identity record via `gald3r.user_config` / `gald3r.home` (T530/T531,
reconciled onto the unified home by T627). It is covered by the bundled engine
test `test_setup_user_hook_t627.py` and referenced by the platform instructions
(`claude_instructions.md` / `cursor_instructions.md`). Intentionally NOT an
agent-lifecycle event hook: it is a run-once terminal utility (interactive
`input()` prompts must never run inside a harness event). Allowlist it in the
WS-A-5 hook-parity lint as a manual utility.

## Fires On

Manual invocation only — run once from a terminal:

```
python .claude/hooks/g-hk-setup-user.py
```

Never wired to `settings.json` / `hooks.json` / `CONCERN_CHAIN` (interactive).

## What It Does

Suggests a user ID (git global email → Cursor cached email → OS username),
prompts with a `[1]` default hint, and stores the chosen ID in the ONE unified
per-user identity record (`<gald3r-home>/user_config.json`;
`%LOCALAPPDATA%/gald3r` on Windows, `~/.config/gald3r` on POSIX). Extra setup
fields (mcp_url, platform, setup_completed, setup_date, created_by) go to a
separate `setup_meta.json` sidecar. A pre-existing legacy `~/.gald3r`
identity file is migrated in once, never regenerated.

## Side Effects

- Writes/updates `<gald3r-home>/user_config.json` (identity) and
  `<gald3r-home>/setup_meta.json` (setup metadata).
- Drops a `.migrated-to-unified-home` breadcrumb next to a migrated legacy file.
- Never touches project state (`.gald3r/`), never blocks anything.

## Related Tasks

- T627 — reconcile onto the unified home (retired the `~/.gald3r` identity file).
- T530/T531 — unified per-user identity record (`gald3r.user_config` / `gald3r.home`).
- T1624 (WS-A-1, D-7) — orphan disposition: kept with this justification.
- Engine test: `.gald3r_sys/engine/tests/test_setup_user_hook_t627.py`.
