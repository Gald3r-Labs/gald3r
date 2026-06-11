#!/usr/bin/env python3
"""Python port of g-hk-pre-session-trace.ps1 (T1584).

Example pre_session lifecycle hook (T1055): records a session-start trace
marker for richer per-session observability. Fires on the gald3r-internal
"pre_session" lifecycle event at the very start of a gald3r work session
(distinct from the harness-native sessionStart event). The payload arrives on
stdin as JSON and SHOULD include session_id (if available) and project_path.

Non-blocking reference example: only stages a session start record so the
companion post_session hook can compute session duration.
"""
# @subsystems: LOGGING_SYSTEM
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common


def _find_project_root() -> str:
    """Walk up from the hook's own directory to the nearest .gald3r/ ancestor;
    fall back to the current working directory (mirrors the PS1)."""
    d = Path(__file__).resolve().parent
    while True:
        if (d / ".gald3r").exists():
            return str(d)
        if d.parent == d:
            break
        d = d.parent
    return os.getcwd()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record a session-start trace marker (pre_session lifecycle hook)."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default="",
        help="Override project-root detection (defaults to nearest .gald3r/ ancestor)",
    )
    args = parser.parse_args()

    # -- stdin payload (gald3r session-event schema) ---------------------------
    payload = _hook_common.read_stdin_json()
    session_id = str(payload.get("session_id") or "")
    project_path = str(payload.get("project_path") or "")

    # -- Locate project root ---------------------------------------------------
    project_root = args.project_root
    if not project_root:
        if project_path and (Path(project_path) / ".gald3r").exists():
            project_root = project_path
        else:
            project_root = _find_project_root()

    logs_dir = Path(project_root) / ".gald3r" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if not session_id:
        session_id = now.strftime("%Y%m%d%H%M%S")

    # -- Stage a per-session start marker (keyed by session id) ----------------
    start_marker = {
        "session_id": session_id,
        "project_path": project_path if project_path else project_root,
        "started_at": timestamp,
        "epoch_ms": int(now.timestamp() * 1000),
    }
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)
    marker_file = logs_dir / f"session_trace_{safe_id}.json"
    try:
        marker_file.write_text(
            json.dumps(start_marker, indent=2), encoding="utf-8"
        )
    except OSError:
        pass

    # -- Append a structured log line -------------------------------------------
    log_line = f"{timestamp} | pre_session | session={session_id} | project={project_root}"
    try:
        with open(logs_dir / "session_lifecycle.log", "a", encoding="utf-8") as fh:
            fh.write(log_line + "\n")
    except OSError:
        pass

    # -- Non-blocking: never delay session start --------------------------------
    print(json.dumps({
        "continue": True,
        "additional_context": f"[pre_session] session {session_id} start recorded.",
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
