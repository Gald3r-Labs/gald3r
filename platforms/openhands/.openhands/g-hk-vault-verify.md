# Hook: g-hk-vault-verify

Vault existence / structure verification (T1456). Confirms that a configured
centralized vault is actually built before a session relies on it, so vault
writes do not silently fail.

## Fires On

Sourced and invoked by `g-hk-session-start.ps1` while building the Vault Context
banner. Can also be run standalone (`uv run python g-hk-vault-verify.py`) to
print the status line.

## What It Does

1. Reads the configured `vault_location` directly from `.gald3r/.identity` (the
   declared value, not a resolved/auto-created path).
2. Skips silently when `vault_location` is absent or `{LOCAL}` (local fallback) —
   there is nothing centralized to verify.
3. Emits one status line:
   - `Vault at {path}: OK` — root exists and all `research/` subdirs present.
   - `Vault at {path}: NOT FOUND` — configured path does not exist; offers
     `@g-vault init`.
   - `Vault at {path}: PARTIAL (missing: ...)` — root exists but `research/` or
     one of its subdirs (`articles`, `github`, `harvests`, `papers`, `platforms`,
     `videos`) is missing; offers `@g-vault init`.

The expected `research/` subdir set mirrors the canonical vault layout documented
in `skills/g-skl-vault/SKILL.md`.

## Side Effects

- None. Read-only. Fail-soft: any error returns an empty banner.
- Always exits 0 in standalone mode and never blocks session start (warning only).

## Related Tasks

- T1456 — Add vault existence/structure verification at session start.
- Companion resolver: `g-hk-vault-resolve.ps1` (resolves/creates the working vault
  path; this hook verifies the *configured* path independently).
