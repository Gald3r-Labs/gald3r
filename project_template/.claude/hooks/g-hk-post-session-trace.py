#!/usr/bin/env python3
"""Session-trace closer — fires on the canonical `stop` and `session-end` events.

Reads the session trace marker opened by g-hk-pre-session-trace and logs the
elapsed session duration. Originally a T1055 example keyed to the
gald3r-internal "post_session" event; T1624 (WS-A-1, decision D-8) retired
that internal event name and wired this hook into the canonical core:

- `stop` chain (per agent turn): logs cumulative elapsed_ms and KEEPS the
  marker, so every turn's stop line carries the running session duration.
- `session-end` chain (session termination), invoked with ``--finalize``:
  logs the final elapsed_ms and REMOVES the marker.

The payload arrives on stdin as JSON. Harness payloads carry `session_id`
(Claude Code) or `conversation_id` (Cursor) plus `cwd`/`project_path`; all are
accepted. If no start marker is found it logs duration as unknown.
Non-blocking by design.
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
        description="Log session-trace duration (canonical stop/session-end "
                    "concern hook)."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default="",
        help="Override project-root detection (defaults to nearest .gald3r/ ancestor)",
    )
    parser.add_argument(
        "--finalize", action="store_true",
        help="Close the trace: remove the start marker after logging "
             "(used on the canonical session-end chain).",
    )
    args = parser.parse_args()

    # -- stdin payload (harness event schema) -----------------------------------
    payload = _hook_common.read_stdin_json()
    session_id = str(
        payload.get("session_id") or payload.get("conversation_id") or ""
    )
    project_path = str(payload.get("project_path") or payload.get("cwd") or "")

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
    now_ms = int(now.timestamp() * 1000)

    # -- Read the start marker and compute elapsed ------------------------------
    elapsed_ms = "unknown"
    if session_id:
        safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)
        marker_file = logs_dir / f"session_trace_{safe_id}.json"
        if marker_file.exists():
            try:
                start = json.loads(marker_file.read_text(encoding="utf-8"))
                if isinstance(start, dict) and start.get("epoch_ms") is not None:
                    elapsed_ms = now_ms - int(start["epoch_ms"])
                if args.finalize:
                    marker_file.unlink()
            except (OSError, ValueError):
                pass
    else:
        session_id = "unknown"

    # -- Append a structured log line -------------------------------------------
    event_label = "session-end" if args.finalize else "stop"
    log_line = (
        f"{timestamp} | {event_label} | session={session_id} | "
        f"elapsed_ms={elapsed_ms}"
    )
    try:
        with open(logs_dir / "session_lifecycle.log", "a", encoding="utf-8") as fh:
            fh.write(log_line + "\n")
    except OSError:
        pass

    # -- Non-blocking -----------------------------------------------------------
    print(json.dumps({
        "continue": True,
        "additional_context": (
            f"[session-trace] session {session_id} {event_label} "
            f"(elapsed_ms={elapsed_ms})."
        ),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
