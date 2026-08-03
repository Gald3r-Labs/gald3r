---
description: 'DEPRECATED alias for /g-install-update -- gald3r_agent (the separate Agent CLI binary product) is retired; this now installs the current gald3r_core release instead.'
argument-hint: '[--release vX.Y.Z] [--require-verification|--allow-unsigned] [--token <token>] [--json]'
subsystem_memberships: [RELEASE_AND_VERSIONING]
execution_tier: orchestration
---
DEPRECATED -- use `/g-install-update` instead: $ARGUMENTS

## What This Command Does

**gald3r_agent (the standalone "Agent CLI binary" product) is RETIRED (BUG-587).** It was
combined with the templates repo to BECOME gald3r_core -- there is no current "Agent CLI
binary" product separate from gald3r_core itself, and the public repo this command used to
download from (`Gald3r-Labs/gald3r_agent`) is a dead, superseded artifact. A user who ran the
old version of this command would download a stale binary from that dead repo and believe it
was current `gald3r`.

This command now runs `gald3r install agent`, which is itself a **deprecated CLI alias** that
redirects to `gald3r install update` (T302/BUG-587; `cli/commands/install.py` +
`core.install.github_release`) -- it prints a deprecation warning, then installs the CURRENT
`gald3r_core` binary from `Gald3r-Labs/gald3r_core`, verified via SHA-256 sidecar, over
whatever `gald3r` currently resolves to on PATH.

**Prefer `/g-install-update` directly** for any new script or workflow. This command is kept
only so an existing script or muscle-memory invocation still does something correct instead of
silently failing or fetching a superseded artifact.

## Steps

1. Resolve how to invoke `gald3r` for this machine: an already-installed `gald3r`/`gald3r.exe`
   on PATH (MSI, npm, winget, homebrew, ...), or `uv run gald3r` from a gald3r_core dev
   checkout. If nothing resolves at all, see "Zero-binary fallback" below.
2. Run the verb in dry-run first to show the plan (fully offline — no network call at plan
   time), then for real:
   ```powershell
   gald3r install agent --dry-run
   gald3r install agent
   ```
3. Pass through any user flags from `$ARGUMENTS` (e.g. `--release vX.Y.Z`,
   `--require-verification`, `--allow-unsigned`, `--token`, `--json`).
4. Report the printed deprecation warning AND the resolved version (`gald3r --version` against
   the refreshed binary) -- tell the user to switch to `/g-install-update` / `gald3r install
   update` going forward.

## Zero-binary fallback (no `gald3r` reachable at all — the true first-run case)

If nothing resolves in step 1 (a brand-new machine with no gald3r install of any kind and no
dev checkout), there is no verb to run yet — download the asset directly, by hand or script,
from the CURRENT release repo, `Gald3r-Labs/gald3r_core` (never `Gald3r-Labs/gald3r_agent` --
that repo is retired):
- Asset: `gald3r.exe` (Windows) / `gald3r` (Linux/macOS) from the latest
  `Gald3r-Labs/gald3r_core` release.
- Also download the matching `.sha256` sidecar and verify the checksum before trusting the
  binary (fail closed on mismatch; BUG-198).
- Place it on PATH as `gald3r`, `chmod +x` on POSIX.
- From that point on, `/g-install-update` (or `gald3r install update`) handles every future
  update.

## Notes

- `--release vX.Y.Z` pins a specific release; default is latest.
- `--require-verification` fails closed if the `.sha256` checksum is missing or mismatched (BUG-198).
- `--allow-unsigned` proceeds past a missing `.sha256` sidecar (not recommended); overridden
  by `--require-verification` when both are passed (fail-closed wins).
- On network failure / 404 (no release at that repo/tag) / missing asset the verb degrades
  gracefully with an honest, specific message — surface it, do not retry blindly.
