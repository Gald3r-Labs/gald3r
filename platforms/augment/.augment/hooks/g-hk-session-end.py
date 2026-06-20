#!/usr/bin/env python3
"""Python port of g-hk-session-end.ps1 (T1584).

Session-end hook (T1057): records structured session-end metadata and stages
a memory-capture pending marker for the next agent session to action.

Fires under the Cursor "stop" event alongside g-hk-agent-complete and
g-hk-nightly-learn. Unlike those siblings (which write reflection hints and
trigger N-session-rollup learning), this hook focuses exclusively on
persisting a structured session-end record that the next session-start hook
(or @g-learn / memory_capture_session) can act on.

Writes `.gald3r/logs/session_end.log` (append) and
`.gald3r/logs/session_end_pending.json` (overwrite), then emits a compact
JSON `{"continue": true, ...}` line. Non-blocking: never delays session
close; any unexpected error exits 0.
"""
# @subsystems: LOGGING_SYSTEM
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402


def _find_project_root() -> str:
    """Mirror the PS1: walk up from the script dir for a `.gald3r/` ancestor."""
    d = Path(__file__).resolve().parent
    while True:
        if (d / ".gald3r").exists():
            return str(d)
        if d.parent == d:
            return str(Path.cwd())
        d = d.parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Session-end hook: stage memory-capture pending marker (T1057)."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default="",
        help="Override project-root detection (defaults to nearest .gald3r/ ancestor).",
    )
    args = parser.parse_args(argv)

    # -- stdin payload (Cursor stop schema) ----------------------------------
    payload = _hook_common.read_stdin_json()

    # -- Idempotency: do not re-write the marker if already done this session
    if os.environ.get("GALD3R_HK_SESSION_END_APPLIED") == "1":
        print(json.dumps({"continue": True}, separators=(",", ":")))
        return 0
    os.environ["GALD3R_HK_SESSION_END_APPLIED"] = "1"

    # -- Locate project root --------------------------------------------------
    project_root = args.project_root or _find_project_root()

    logs_dir = Path(project_root) / ".gald3r" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # -- Parse stop payload ----------------------------------------------------
    status = "unknown"
    loop_count = 0
    conversation_id = ""
    transcript_path = ""
    if payload.get("status"):
        status = payload["status"]
    if payload.get("loop_count") is not None:
        loop_count = payload["loop_count"]
    if payload.get("conversation_id"):
        conversation_id = payload["conversation_id"]
    if payload.get("transcript_path"):
        transcript_path = payload["transcript_path"]

    # -- Read identity for project_id -------------------------------------------
    identity_file = Path(project_root) / ".gald3r" / ".identity"
    project_id = ""
    project_name = ""
    if identity_file.is_file():
        for line in identity_file.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^project_id=(.+)$", line)
            if m:
                project_id = m.group(1).strip()
            m = re.match(r"^project_name=(.+)$", line)
            if m:
                project_name = m.group(1).strip()

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # -- Append a structured log line --------------------------------------------
    log_line = (
        f"{timestamp} | session_end | status={status} | loop_count={loop_count}"
        f" | project={project_name} | conv={conversation_id}"
    )
    log_file = logs_dir / "session_end.log"
    try:
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(log_line + "\n")
    except OSError:
        pass

    # -- Stage memory-capture pending marker --------------------------------------
    # TODO[T1057→T1263]: replace this marker pattern with an actual
    # memory_capture_session MCP call once the gald3r agent CLI is wired into
    # the hook execution chain (hook shells cannot call MCP tools directly).
    marker_file = logs_dir / "session_end_pending.json"
    marker = {
        "timestamp": timestamp,
        "project_id": project_id,
        "project_name": project_name,
        "conversation_id": conversation_id,
        "transcript_path": transcript_path,
        "status": status,
        "loop_count": loop_count,
        "capture_pending": True,
        "deferred_to": "T1263",
    }
    try:
        marker_file.write_text(json.dumps(marker, indent=2), encoding="utf-8")
    except OSError:
        pass

    # -- Non-blocking: never delay session close -----------------------------------
    print(json.dumps(
        {
            "continue": True,
            "additional_context": "[session-end] Marker staged. Memory capture wiring deferred to T1263.",
        },
        separators=(",", ":"),
    ))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        sys.exit(0)
