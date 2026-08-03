---
description: 'Download, verify (minisign), and stage the Gald3r Throne installer from the latest GitHub release.'
argument-hint: '[--release vX.Y.Z] [--require-verification|--allow-unsigned] [--token <token>] [--json]'
subsystem_memberships: [RELEASE_AND_VERSIONING]
execution_tier: orchestration
---
Install the Gald3r Throne desktop app from the latest public GitHub Release: $ARGUMENTS

## What This Command Does

Runs gald3r_core's own **native** `gald3r install throne` verb (T302; `cli/commands/install.py`
+ `core.install.github_release`) to download the precompiled, signed **Gald3r Throne**
installer from the public `Gald3r-Labs/gald3r_throne` releases, verify it (minisign `.sig`,
key `F110B9BD6FF00BA2`), and stage it for the user to run. This repoints the earlier version
of this doc, which referenced a `gald3r install throne` "engine verb (T1615)" — T1615 was a
task id in the donor `gald3r_agent_dev` repo, never one of gald3r_core's own (`gald3r task
show T1615` finds nothing here); T302 is gald3r_core's native implementation of the same
verb, and closes the **fallback gap this doc previously had no answer for** (a `gald3r`
binary is needed to run this verb at all — see "Zero-binary fallback" below).

**Confirmed live** (verified against the real GitHub API while building this verb):
`Gald3r-Labs/gald3r_throne` is a real, actively-releasing repo (latest `v0.2.0`) publishing
signed Windows/Linux assets with minisign `.sig` sidecars — this is a real, cryptographically
verified download, not a stub. **macOS is the one honest gap**: no `.dmg`/`.app` asset has
been published for Throne yet, so `gald3r install throne` on macOS reports that plainly
(`artifact_present: false`) instead of failing with a confusing "no asset found" error.

## Steps

1. Resolve how to invoke `gald3r` for this machine: an already-installed `gald3r`/`gald3r.exe`
   on PATH (MSI, npm, winget, homebrew, ...), or `uv run gald3r` from a gald3r_core dev
   checkout. **If nothing resolves at all**, run `/g-install-update` first (its own "Zero-binary
   fallback" section gets a real `gald3r` binary on PATH), then return here — Throne's
   installer is separate from, and does not require, any other gald3r product once a `gald3r`
   executable exists to invoke this verb.
2. Run the verb in dry-run first to show the plan (fully offline — no network call at plan
   time), then for real:
   ```powershell
   gald3r install throne --dry-run
   gald3r install throne
   ```
3. Pass through any user flags from `$ARGUMENTS` (e.g. `--release vX.Y.Z`,
   `--require-verification`, `--allow-unsigned`, `--token`, `--json`).
4. After install, report the resolved version and the path to the downloaded installer
   (`<gald3r home>/downloads/throne/<asset>`) — the verb does **not** auto-launch or
   auto-elevate it; tell the user to run it themselves:
   - **Windows**: launch the `.exe` (NSIS) or `.msi`.
   - **Linux**: run the `.AppImage` (already `chmod +x`'d) or `sudo dpkg -i` the `.deb`.
   - **macOS**: not available yet (see above) — no fallback exists; report this honestly.

## Zero-binary fallback (no `gald3r` reachable at all)

Same shape as `/g-install-update`'s fallback: if no `gald3r` executable exists yet to run this
verb, either (a) run `/g-install-update`'s zero-binary fallback first (fastest — a `gald3r`
binary can then run this verb natively), or (b) download the Throne installer directly from
the latest `Gald3r-Labs/gald3r_throne` release by hand and verify its `.sig` independently
with [minisign](https://jedisct1.github.io/minisign/) against key `F110B9BD6FF00BA2`
(`minisign -Vm <asset> -P RWSiC/BvvbkQ8b7JpjwjDG4YUbyjBECa/t9EX/CKRe15yBuIQpV81rwA`) before
running it.

## Notes

- `--release vX.Y.Z` pins a specific release; default is latest.
- `--require-verification` fails closed if the minisign `.sig` is missing or invalid (BUG-198).
- `--allow-unsigned` proceeds past a missing/uncheckable `.sig` (not recommended); overridden
  by `--require-verification` when both are passed (fail-closed wins) — the update path's
  `.sha256` path (`/g-install-update`) shares this identical formula (BUG-456).
- Throne ships an OS installer (NSIS `.exe` / MSI / AppImage / deb), not a bare binary — this
  command stages it for the user to launch, never auto-elevates.
- On network failure / 404 (no release at that repo/tag) / missing asset the verb degrades
  gracefully with an honest, specific message — surface it, do not retry blindly.
