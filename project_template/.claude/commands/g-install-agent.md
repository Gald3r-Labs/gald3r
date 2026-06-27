---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Install the Gald3r Agent CLI from the latest public GitHub Release: $ARGUMENTS

## What This Command Does

Wraps the engine install verb to download the precompiled, signed **Gald3r Agent** binary
from the public `Gald3r-Labs/gald3r_agent` releases, verify it (SHA-256 sidecar), and place
it in the gald3r home `bin/` directory. This does NOT reimplement install logic — it invokes
the `gald3r install agent` engine verb (T1615).

## Steps

1. Run the engine verb in dry-run first to show the plan:
   ```powershell
   uv run --project .gald3r_sys/engine gald3r install agent --dry-run
   ```
2. If the plan looks correct, run the real install:
   ```powershell
   uv run --project .gald3r_sys/engine gald3r install agent
   ```
3. Pass through any user flags from `$ARGUMENTS` (e.g. `--release vX.Y.Z`, `--from-source`,
   `--require-verification`).
4. After install, report the resolved version and the PATH advisory the engine prints (the
   binary lands in the gald3r home `bin/`; PATH is not auto-mutated).

## Notes

- `--release vX.Y.Z` pins a specific release; default is latest.
- `--from-source` falls back to the legacy `uv sync` source build instead of downloading.
- `--require-verification` fails closed if the `.sha256` checksum is missing or mismatched (BUG-198).
- On network failure / 404 / missing asset the engine degrades gracefully — surface the
  message, do not retry blindly.
