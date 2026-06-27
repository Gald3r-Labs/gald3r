---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Install the Gald3r Throne desktop app from the latest public GitHub Release: $ARGUMENTS

## What This Command Does

Wraps the engine install verb to download the precompiled, signed **Gald3r Throne** installer
from the public `Gald3r-Labs/gald3r_throne` releases, verify it (minisign `.sig`), and launch
the platform installer. This does NOT reimplement install logic — it invokes the
`gald3r install throne` engine verb (T1615).

## Steps

1. Run the engine verb in dry-run first to show the plan:
   ```powershell
   uv run --project .gald3r_sys/engine gald3r install throne --dry-run
   ```
2. If the plan looks correct, run the real install:
   ```powershell
   uv run --project .gald3r_sys/engine gald3r install throne
   ```
3. Pass through any user flags from `$ARGUMENTS` (e.g. `--release vX.Y.Z`, `--require-verification`).
4. After install, report the resolved version and launch the downloaded installer for the
   user's OS.

## Notes

- `--release vX.Y.Z` pins a specific release; default is latest.
- `--require-verification` fails closed if the minisign `.sig` is missing or invalid (BUG-198).
- Throne ships an OS installer (MSI / EXE / AppImage / deb), not a bare binary — the command
  launches it.
- On network failure / 404 / missing asset the engine degrades gracefully — surface the
  message, do not retry blindly.
