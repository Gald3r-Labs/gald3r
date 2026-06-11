#!/usr/bin/env python3
"""Python port of g-hk-nightly-learn.ps1 (T1584).

Nightly hook: trigger session summary extraction into learned-facts.md
(T928, T1233). Fires under `stop` (agent session complete). Lightweight by
design:

1. Walks up to find the project root.
2. Reads the per-N-sessions counter at `.gald3r/logs/learn-counter`.
   Increments it. Only proceeds when the counter hits
   `nightly_learn_interval` (default 5; configurable in
   `.gald3r/config/AGENT_CONFIG.md`).
3. Checks `nightly_learn:` in HEARTBEAT.md for an explicit off switch.
4. Spawns the heavy helper (`gald3r_nightly_learn.py` preferred, falling
   back to `gald3r_nightly_learn.ps1` via PowerShell) as a fully detached
   background process. The hook itself returns within milliseconds — it
   never blocks the agent UI waiting for LLM extraction.
5. Writes `.gald3r/logs/nightly-learn-last-run.log` with the spawn time,
   PID, helper path, and counter state so future hangs are diagnosable.

Never crashes the host session: any unexpected error exits 0.
"""
# @subsystems: MEMORY_AND_KNOWLEDGE
from __future__ import annotations

import argparse
import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402,F401


def _find_project_root() -> str:
    """Mirror the PS1: walk up from the script dir for a `.gald3r/` ancestor."""
    d = Path(__file__).resolve().parent
    while True:
        if (d / ".gald3r").exists():
            return str(d)
        if d.parent == d:
            return str(Path.cwd())
        d = d.parent


def _resolve_helper(project_root: str) -> Path:
    """Prefer a .py sibling of the helper script; fall back to the .ps1.

    Candidate locations (same order as the PS1, with a D015 legacy fallback):
      1. .gald3r_sys/skills/g-skl-learn/scripts/gald3r_nightly_learn.*
      2. scripts/gald3r_nightly_learn.*  (legacy)
    Returns the first existing candidate; when none exist, returns the
    legacy .ps1 path (matching the PS1's final value used in the log line).
    """
    root = Path(project_root)
    bases = [
        root / ".gald3r_sys" / "skills" / "g-skl-learn" / "scripts" / "gald3r_nightly_learn",
        root / "scripts" / "gald3r_nightly_learn",
    ]
    for base in bases:
        for ext in (".py", ".ps1"):
            candidate = base.with_suffix(ext)
            if candidate.is_file():
                return candidate
    return bases[-1].with_suffix(".ps1")


def _powershell_exe() -> str:
    if os.name == "nt":
        return shutil.which("powershell.exe") or shutil.which("pwsh") or "powershell.exe"
    return shutil.which("pwsh") or "pwsh"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Nightly learn hook: every-N-sessions background extraction trigger."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default="",
        help="Root of the gald3r project. Defaults to nearest .gald3r/ ancestor.",
    )
    parser.add_argument(
        "-Force", "--force", dest="force", action="store_true",
        help="Bypass the every-N-sessions counter and run the extraction immediately.",
    )
    args = parser.parse_args(argv)

    project_root = args.project_root or _find_project_root()

    helper_script = _resolve_helper(project_root)
    logs_dir = Path(project_root) / ".gald3r" / "logs"
    counter_file = logs_dir / "learn-counter"
    last_run_log = logs_dir / "nightly-learn-last-run.log"
    config_file = Path(project_root) / ".gald3r" / "config" / "AGENT_CONFIG.md"
    heartbeat = Path(project_root) / ".gald3r" / "config" / "HEARTBEAT.md"

    logs_dir.mkdir(parents=True, exist_ok=True)

    # ---- Disable switch (HEARTBEAT.md `nightly_learn: false`) --------------
    if heartbeat.is_file():
        import re
        hb = heartbeat.read_text(encoding="utf-8", errors="replace")
        if re.search(r"nightly_learn:\s*false", hb):
            # Cheap exit — do not increment counter when explicitly disabled.
            return 0

    # ---- Read interval (default: every 5 sessions) -------------------------
    interval = 5
    if config_file.is_file():
        import re
        cfg = config_file.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"nightly_learn_interval:\s*(\d+)", cfg)
        if m:
            candidate = int(m.group(1))
            if candidate > 0:
                interval = candidate

    # ---- Counter (only fire every N sessions) ------------------------------
    counter = 0
    if counter_file.is_file():
        try:
            counter = int(counter_file.read_text(encoding="ascii", errors="replace").strip())
        except (ValueError, OSError):
            counter = 0
    counter += 1

    if not args.force and counter < interval:
        # Not yet time — bump counter and exit silently within a few ms.
        counter_file.write_text(str(counter), encoding="ascii")
        return 0

    # ---- Helper script existence check --------------------------------------
    now_iso = datetime.datetime.now().astimezone().isoformat()
    if not helper_script.is_file():
        with last_run_log.open("a", encoding="utf-8") as fh:
            fh.write(
                f"[{now_iso}] gald3r_nightly_learn.ps1 not found at {helper_script}"
                " -- hook skipped.\n"
            )
        # Reset counter so a fixed helper doesn't immediately re-fire on next session.
        counter_file.write_text("0", encoding="ascii")
        return 0

    # ---- Detached spawn of the heavy extraction work ------------------------
    # Critical: detached creation flags + redirected stdout/stderr keep the
    # hook non-blocking even when the helper takes minutes.
    helper_out = logs_dir / "nightly-learn-helper.out.log"
    helper_err = logs_dir / "nightly-learn-helper.err.log"

    helper_args = ["-ProjectRoot", project_root, "-LookbackDays", "1"]
    if helper_script.suffix.lower() == ".py":
        cmd = [sys.executable, str(helper_script)] + helper_args
    else:
        cmd = [
            _powershell_exe(),
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(helper_script),
        ] + helper_args

    try:
        popen_kwargs = {}
        if os.name == "nt":
            popen_kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.CREATE_NO_WINDOW
            )
        else:
            popen_kwargs["start_new_session"] = True
        with helper_out.open("ab") as out_fh, helper_err.open("ab") as err_fh:
            proc = subprocess.Popen(
                cmd,
                stdout=out_fh,
                stderr=err_fh,
                stdin=subprocess.DEVNULL,
                **popen_kwargs,
            )

        # Reset counter on successful spawn.
        counter_file.write_text("0", encoding="ascii")

        with last_run_log.open("a", encoding="utf-8") as fh:
            fh.write(
                f"[{now_iso}] spawned PID={proc.pid} helper={helper_script}"
                f" counter_was={counter} interval={interval}\n"
            )

        # Surface a one-line note to the agent's terminal; the heavy work runs detached.
        print(
            f"[g-hk-nightly-learn] background extraction queued (PID {proc.pid});"
            f" see {last_run_log}"
        )
    except Exception as exc:  # spawn failure must never block the agent's exit path
        try:
            with last_run_log.open("a", encoding="utf-8") as fh:
                fh.write(f"[{now_iso}] FAILED to spawn helper: {exc}\n")
        except OSError:
            pass
        print(f"WARNING: [g-hk-nightly-learn] spawn failed: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        sys.exit(0)
