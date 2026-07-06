#!/usr/bin/env python3
"""Python port of g-hk-graph-update.ps1 (T1584).

Refresh the gald3r_muninn codebase graph index (T1158). Runs the muninn
indexers (Python AST + TypeScript) incrementally so graph_impact,
graph_callers, etc. return current results for the next g-go-code Step b0
Impact Scan.

Wiring (T1624, WS-A-1): fires on the canonical `stop` event —
`CONCERN_CHAIN["stop"]` in g_hk_core.py plus the Claude/Cursor trigger
configs — so the graph refreshes at the end of every agent turn (commits
happen mid-turn; a turn-end refresh keeps the next turn's Impact Scan
current). It remains directly invocable as a git post-commit hook.

Non-blocking by design: if the muninn plugin / Python / Node.js are not
available, the hook logs the reason and exits 0. Installs without the muninn
plugin (the common case) skip in milliseconds. Each indexer run is capped at
60 seconds so a wedged indexer can never stall the host session's stop chain.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; pure-stdlib path used here)


def _default_project_root() -> str:
    """Mirror the PS1 default: strip the trailing IDE hooks dir (T1159) so the
    same script body works under .cursor/, .claude/, .agent/, .codex/, or
    .opencode/."""
    script_dir = str(Path(__file__).resolve().parent)
    return re.sub(
        r"[\\/]\.(cursor|claude|agent|codex|opencode)[\\/]hooks$", "", script_dir
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the gald3r_muninn codebase graph index (post-commit)."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root",
        default=_default_project_root(),
        help="Project root (default: derived from the hook's own location)",
    )
    args = parser.parse_args()

    project_root = args.project_root
    if not project_root:
        project_root = os.getcwd()

    # Resolve project root by walking up to .gald3r/ when needed.
    if not (Path(project_root) / ".gald3r").exists():
        d = Path(os.getcwd())
        while d != d.parent:
            if (d / ".gald3r").exists():
                project_root = str(d)
                break
            d = d.parent

    os.chdir(project_root)
    root = Path(project_root)

    python_indexer = root / "docker" / "gald3r" / "tools" / "plugins" / "muninn" / "indexers" / "python_indexer.py"
    ts_indexer = root / "docker" / "gald3r" / "tools" / "plugins" / "muninn" / "indexers" / "ts_indexer.js"

    logs_dir = root / ".gald3r" / "logs"
    log_file = logs_dir / "muninn_updates.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def write_muninn_log(line: str) -> None:
        if logs_dir.is_dir():
            try:
                with open(log_file, "a", encoding="utf-8") as fh:
                    fh.write(f"{timestamp} | {line}\n")
            except OSError:
                pass

    # Skip silently if the muninn plugin is not present (e.g. on a non-gald3r-dev clone).
    if not python_indexer.exists() and not ts_indexer.exists():
        write_muninn_log("muninn-update | skipped: no indexer files found")
        return 0

    def run_indexer(label: str, exe: str, indexer: Path) -> None:
        exe_path = shutil.which(exe)
        if not exe_path:
            write_muninn_log(f"muninn-update | {label} | skipped: {exe} not on PATH")
            return
        try:
            result = subprocess.run(
                [exe_path, str(indexer), "--root", project_root, "--incremental"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            out = " ".join(((result.stdout or "") + (result.stderr or "")).splitlines())
            write_muninn_log(
                f"muninn-update | {label} | exit={result.returncode} | {out}"
            )
        except subprocess.TimeoutExpired:
            # T1624: this hook now runs on the live stop chain — a wedged
            # indexer must never stall the host session.
            write_muninn_log(f"muninn-update | {label} | timeout after 60s")
        except (OSError, subprocess.SubprocessError) as exc:
            write_muninn_log(f"muninn-update | {label} | exception={exc}")

    # Python AST indexer
    # BUG-207: launch with the interpreter this hook is already running under
    # -- bare `python` does not exist on stock python3-only Linux.
    if python_indexer.exists():
        run_indexer("python-indexer", sys.executable, python_indexer)

    # TypeScript / JavaScript indexer (Node.js)
    if ts_indexer.exists():
        run_indexer("ts-indexer", "node", ts_indexer)

    # Non-blocking: always exit 0 so git commit is not blocked.
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
