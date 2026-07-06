---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Install the Gald3r Agent CLI from the latest public GitHub Release: $ARGUMENTS

## What This Command Does

Wraps the engine install verb to download the precompiled, signed **Gald3r Agent** binary
from the public `Gald3r-Labs/gald3r_agent` releases, verify it (SHA-256 sidecar), and place
it in the gald3r home `bin/` directory. This does NOT reimplement install logic — it invokes
the `gald3r install agent` engine verb (T1615) when an engine is reachable, and falls back
to a zero-engine bootstrap when none is (installs ship NO engine source — T1645).

## Steps

1. Resolve how to invoke the engine (the gald3r_bin.py order: `GALD3R_BIN` env var →
   `gald3r` on PATH → bundled `.gald3r_sys/bin/gald3r[.exe]` → dev source):
   ```powershell
   python .gald3r_sys/scripts/gald3r_bin.py
   ```
2. **If an engine command resolved** — run the verb in dry-run first to show the plan,
   then for real:
   ```powershell
   gald3r install agent --dry-run
   gald3r install agent
   ```
   (Use the exact command prefix step 1 printed — e.g. a `GALD3R_BIN` path — if bare
   `gald3r` is not on PATH.)
3. **Zero-engine bootstrap** (fresh install, nothing resolved — the normal first run):
   download the binary directly from the latest `Gald3r-Labs/gald3r_agent` GitHub release:
   - Asset: `gald3r-windows-x86_64.exe` (Windows) / `gald3r-linux-x86_64` (Linux);
     macOS assets are not published yet (use `--from-source` on a dev checkout).
   - Also download the `.sha256` sidecar and VERIFY the checksum before trusting the
     binary (fail closed on mismatch; BUG-198).
   - Place it in the gald3r home `bin/` as `gald3r-agent[.exe]`
     (Windows: `%LOCALAPPDATA%\gald3r\bin`; POSIX: `~/.local/bin` — the same directory
     `gald3r install agent` targets), `chmod +x` on POSIX.
   - Register the `gald3r` launcher on PATH: `python .gald3r_sys/scripts/install_global_cli.py`
     (the launcher execs the compiled binary; idempotent).
4. Pass through any user flags from `$ARGUMENTS` (e.g. `--release vX.Y.Z`, `--from-source`,
   `--require-verification`).
5. After install, report the resolved version (`gald3r --version`) and the PATH advisory
   the engine prints (the binary lands in the gald3r home `bin/`; PATH is not auto-mutated).

## Notes

- `--release vX.Y.Z` pins a specific release; default is latest.
- `--from-source` falls back to the legacy `uv sync` source build — dev checkouts only
  (installs do not carry engine source; T1645).
- `--require-verification` fails closed if the `.sha256` checksum is missing or mismatched (BUG-198).
- On network failure / 404 / missing asset the engine degrades gracefully — surface the
  message, do not retry blindly.
