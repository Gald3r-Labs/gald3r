#!/usr/bin/env python3
"""Session-trace opener — fires on the canonical `session-start` event.

Records a session-start trace marker for richer per-session observability.
Originally a T1055 example keyed to the gald3r-internal "pre_session" event;
T1624 (WS-A-1, decision D-8) retired that internal event name and wired this
hook into the canonical core: it now runs in `CONCERN_CHAIN["session-start"]`
(g_hk_core.py) and is registered on the harness-native SessionStart /
sessionStart trigger for Claude Code and Cursor.

The payload arrives on stdin as JSON. Harness payloads carry `session_id`
(Claude Code) or `conversation_id` (Cursor) plus `cwd`/`project_path`; all are
accepted. Non-blocking reference: only stages a session start record so the
companion g-hk-post-session-trace hook can compute session duration on
stop/session-end. Stale markers (>7 days) are pruned on each run so wired
installs never accumulate marker files.
"""
# @subsystems: LOGGING_SYSTEM
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common

#: Session-trace markers older than this are pruned on each run (T1624).
_MARKER_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


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


def _prune_stale_markers(logs_dir: Path) -> None:
    """Remove session_trace_*.json markers older than the max age (fail-soft)."""
    cutoff = time.time() - _MARKER_MAX_AGE_SECONDS
    try:
        for marker in logs_dir.glob("session_trace_*.json"):
            try:
                if marker.stat().st_mtime < cutoff:
                    marker.unlink()
            except OSError:
                continue
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record a session-start trace marker (canonical "
                    "session-start concern hook)."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default="",
        help="Override project-root detection (defaults to nearest .gald3r/ ancestor)",
    )
    args = parser.parse_args()

    # -- stdin payload (harness event schema) -----------------------------------
    # Claude Code sends session_id; Cursor sends conversation_id; the retired
    # gald3r-internal schema sent session_id + project_path. Accept all.
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
    _prune_stale_markers(logs_dir)

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
    log_line = f"{timestamp} | session-start | session={session_id} | project={project_root}"
    try:
        with open(logs_dir / "session_lifecycle.log", "a", encoding="utf-8") as fh:
            fh.write(log_line + "\n")
    except OSError:
        pass

    # -- Non-blocking: never delay session start --------------------------------
    print(json.dumps({
        "continue": True,
        "additional_context": f"[session-trace] session {session_id} start recorded.",
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
