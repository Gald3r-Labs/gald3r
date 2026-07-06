#!/usr/bin/env python3
"""Python port of g-hk-nightly-learn.ps1 (T1584); engine-verb dispatch (T1665).

Nightly hook: trigger session summary extraction into learned-facts.md
(T928, T1233). Fires under `stop` (agent session complete). Lightweight by
design:

1. Walks up to find the project root.
2. Reads the per-N-sessions counter at `.gald3r/logs/learn-counter`.
   Increments it. Only proceeds when the counter hits
   `nightly_learn_interval` (default 5; configurable in
   `.gald3r/config/AGENT_CONFIG.md`).
3. Checks `nightly_learn:` in HEARTBEAT.md for an explicit off switch.
4. Resolves the compiled gald3r engine via the zero-IP `gald3r_bin.py`
   resolver and spawns `gald3r learn nightly` (the absorbed GATHER loop,
   T1670) as a fully detached background process. The readable
   `gald3r_nightly_learn.py` skill script was stripped in the v3 IP round
   (T1665); the methodology now lives in the compiled binary. The hook
   itself returns within milliseconds — it never blocks the agent UI.
5. Writes `.gald3r/logs/nightly-learn-last-run.log` with the spawn time,
   PID, engine command, and counter state so future hangs are diagnosable.

Never crashes the host session: any unexpected error exits 0.
"""
# @subsystems: MEMORY_AND_KNOWLEDGE
from __future__ import annotations

import argparse
import datetime
import importlib.util
import os
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


def _resolve_engine_cmd(project_root: Path):
    """Resolve the gald3r engine command prefix via the zero-IP resolver.

    The nightly-learn GATHER loop was absorbed (T1670) into the
    `gald3r learn nightly` verb. Returns the command prefix (e.g.
    ``["gald3r"]``) or ``None`` when the resolver is not shipped (old install)
    or no engine can be found — the caller then logs and skips (fail-open).
    """
    resolver = project_root / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(
            "gald3r_bin_nightly_learn", str(resolver))
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.resolve_engine_cmd(project_root)
    except Exception:
        return None


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

    # ---- Resolve the engine (compiled binary via the zero-IP resolver) ------
    now_iso = datetime.datetime.now().astimezone().isoformat()
    engine = _resolve_engine_cmd(Path(project_root))
    if engine is None:
        with last_run_log.open("a", encoding="utf-8") as fh:
            fh.write(
                f"[{now_iso}] gald3r engine not resolved (run g-install-agent)"
                " -- hook skipped.\n"
            )
        # Reset counter so an installed engine doesn't immediately re-fire.
        counter_file.write_text("0", encoding="ascii")
        return 0

    # ---- Detached spawn of the `gald3r learn nightly` GATHER loop ------------
    # Critical: detached creation flags + redirected stdout/stderr keep the
    # hook non-blocking even if the engine takes a moment.
    helper_out = logs_dir / "nightly-learn-helper.out.log"
    helper_err = logs_dir / "nightly-learn-helper.err.log"

    cmd = [*engine, "learn", "nightly", "--project-root", project_root,
           "--lookback-days", "1"]

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
                f"[{now_iso}] spawned PID={proc.pid} cmd={' '.join(cmd)}"
                f" counter_was={counter} interval={interval}\n"
            )

        # Surface a one-line note to the agent's terminal; the work runs detached.
        print(
            f"[g-hk-nightly-learn] background extraction queued (PID {proc.pid});"
            f" see {last_run_log}"
        )
    except Exception as exc:  # spawn failure must never block the agent's exit path
        try:
            with last_run_log.open("a", encoding="utf-8") as fh:
                fh.write(f"[{now_iso}] FAILED to spawn engine: {exc}\n")
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
