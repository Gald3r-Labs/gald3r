---
description: 'Download, verify, and install the latest signed gald3r_core release, replacing whatever gald3r currently resolves to on PATH.'
argument-hint: '[--release vX.Y.Z] [--require-verification|--allow-unsigned] [--token <token>] [--target <path>] [--json]'
subsystem_memberships: [RELEASE_AND_VERSIONING]
execution_tier: orchestration
---
Install the latest signed gald3r_core release from the latest public GitHub Release: $ARGUMENTS

## What This Command Does

Runs gald3r_core's own **native** `gald3r install update` verb (T302/BUG-587;
`cli/commands/install.py` + `core.install.github_release`) to download the precompiled,
signed **gald3r_core** binary from the public `Gald3r-Labs/gald3r_core` releases (the same
repo `gald3r release stage` publishes to, T550/D032), verify it (SHA-256 sidecar), and
install it over whatever `gald3r`/`gald3r.exe` currently resolves to on PATH.

This replaces `/g-install-agent`, which used to download a SEPARATE "Agent CLI binary"
product from `Gald3r-Labs/gald3r_agent` -- that product is RETIRED (BUG-587): it was combined
with the templates repo to become gald3r_core, which IS this binary. `/g-install-agent` is
kept only as a deprecated alias that redirects here.

This verb is the download-based sibling of `gald3r install self` (`@g-install-self`, if
present) -- `install self` rebuilds THIS checkout from source (needs a gald3r_core dev
environment); `install update` downloads an already-built, already-signed release (works with
no gald3r source on disk at all, and is the fast path for the MSI/winget update story).

## Steps

1. Resolve how to invoke `gald3r` for this machine: an already-installed `gald3r`/`gald3r.exe`
   on PATH (MSI, npm, winget, homebrew, ...), or `uv run gald3r` from a gald3r_core dev
   checkout. If nothing resolves at all, see "Zero-binary fallback" below.
2. Run the verb in dry-run first to show the plan (fully offline — no network call at plan
   time, shows exactly which file on PATH would be replaced), then for real:
   ```powershell
   gald3r install update --dry-run
   gald3r install update
   ```
3. Pass through any user flags from `$ARGUMENTS` (e.g. `--release vX.Y.Z`,
   `--require-verification`, `--allow-unsigned`, `--token`, `--target <path>`, `--json`).
4. After install, report the resolved version (`gald3r --version` against the refreshed
   binary) and note that the previous binary was backed up alongside it
   (`<target>.bak-<UTC timestamp>`) before being replaced.

## Zero-binary fallback (no `gald3r` reachable at all — the true first-run case)

If nothing resolves in step 1 (a brand-new machine with no gald3r install of any kind and no
dev checkout), there is no verb to run yet — download the asset directly, by hand or script:
- Asset: `gald3r.exe` (Windows) / `gald3r` (Linux/macOS) from the latest
  `Gald3r-Labs/gald3r_core` release.
- Also download the matching `.sha256` sidecar and verify the checksum before trusting the
  binary (fail closed on mismatch; BUG-198).
- Place it on PATH as `gald3r`, `chmod +x` on POSIX.
- From that point on, `/g-install-update` (this command) handles every future update.

## Notes

- `--release vX.Y.Z` pins a specific release; default is latest.
- `--require-verification` fails closed if the `.sha256` checksum is missing or mismatched (BUG-198).
- `--allow-unsigned` proceeds past a missing `.sha256` sidecar (not recommended); overridden
  by `--require-verification` when both are passed (fail-closed wins) — mirrors `install
  throne`'s `.sig` behavior exactly (BUG-456).
- `--target <path>` overrides the binary to refresh (default: `shutil.which('gald3r')` --
  whatever the bare `gald3r` command currently resolves to on PATH).
- If the target binary is locked by a running `gald3r` process (often the very process running
  this command), the verb reports that plainly and suggests stopping other `gald3r` processes
  or passing `--target` to a path nothing has open -- it never force-kills anything.
- On network failure / 404 (no release at that repo/tag) / missing asset the verb degrades
  gracefully with an honest, specific message — surface it, do not retry blindly.
