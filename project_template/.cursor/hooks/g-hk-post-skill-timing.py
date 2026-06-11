#!/usr/bin/env python3
"""Python port of g-hk-post-skill-timing.ps1 (T1584).

Example post_skill lifecycle hook (T1055): closes the skill-invocation timing
record opened by g-hk-pre-skill-timing and logs elapsed duration. Fires on the
gald3r-internal "post_skill" lifecycle event, immediately after a gald3r skill
body finishes (no native Cursor / Claude Code skill-boundary event exists).
The payload arrives on stdin as JSON and SHOULD include skill_name,
skill_path, and timestamp.

Non-blocking reference example: reads the start marker staged by
g-hk-pre-skill-timing, computes elapsed milliseconds, and appends a timing
line. If no start marker is found it logs duration as unknown.
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
        description="Close the skill-invocation timing record (post_skill lifecycle hook)."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default="",
        help="Override project-root detection (defaults to nearest .gald3r/ ancestor)",
    )
    args = parser.parse_args()

    # -- stdin payload (gald3r skill-event schema) ------------------------------
    payload = _hook_common.read_stdin_json()
    skill_name = str(payload.get("skill_name") or "unknown")
    event_timestamp = str(payload.get("timestamp") or "")

    # -- Locate project root ----------------------------------------------------
    project_root = args.project_root or _find_project_root()

    logs_dir = Path(project_root) / ".gald3r" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = event_timestamp if event_timestamp else now.strftime("%Y-%m-%dT%H:%M:%SZ")
    now_ms = int(now.timestamp() * 1000)

    # -- Read the start marker and compute elapsed --------------------------------
    elapsed_ms = "unknown"
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", skill_name)
    marker_file = logs_dir / f"skill_timing_{safe_name}.json"
    if marker_file.exists():
        try:
            start = json.loads(marker_file.read_text(encoding="utf-8"))
            if isinstance(start, dict) and start.get("epoch_ms") is not None:
                elapsed_ms = now_ms - int(start["epoch_ms"])
            marker_file.unlink()
        except (OSError, ValueError):
            pass

    # -- Append a structured log line ----------------------------------------------
    log_line = f"{timestamp} | post_skill | skill={skill_name} | elapsed_ms={elapsed_ms}"
    try:
        with open(logs_dir / "skill_lifecycle.log", "a", encoding="utf-8") as fh:
            fh.write(log_line + "\n")
    except OSError:
        pass

    # -- Non-blocking ---------------------------------------------------------------
    print(json.dumps({
        "continue": True,
        "additional_context": f"[post_skill] {skill_name} finished (elapsed_ms={elapsed_ms}).",
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
