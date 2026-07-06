# gald3r engine — ships as a compiled binary (v3.0.0)

The gald3r engine does **not** ship as readable source (IP leak-stop, T1645).
This directory intentionally contains only this README.

How the engine is invoked in this install:

1. **Install the compiled binary** (one-time, per machine): run the
   `g-install-agent` command (`/g-install-agent` in Claude Code,
   `@g-install-agent` in Cursor). It downloads the signed `gald3r` binary +
   SHA-256 sidecar from the public `Gald3r-Labs/gald3r_agent` GitHub releases
   into the gald3r home `bin/` directory.
2. **Resolution** is handled by the zero-IP resolver
   `.gald3r_sys/scripts/gald3r_bin.py` (first hit wins):
   `GALD3R_BIN` env var -> `gald3r` on PATH -> bundled
   `.gald3r_sys/bin/gald3r[.exe]` (optional user-side drop location; nothing
   ships there) -> dev source (never present in a shipped install).
3. **No binary?** Every slimmed skill degrades gracefully to its
   `SKILL.full.md` manual fallback — nothing points outside the install.
