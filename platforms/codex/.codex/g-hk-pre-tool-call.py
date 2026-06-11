#!/usr/bin/env python3
"""Python port of g-hk-pre-tool-call.ps1 (T1584).

Pre-tool-call shell output compression hook (T1106, IDEA-HARVEST-191).
Fires under the PreToolUse / preToolUse event. Inspects the incoming tool
event payload (JSON on stdin) for any large stdout/stderr/output text block
and compresses it to the last N lines plus a summary prefix, returning the
compressed form as additional_context. Compression is non-destructive: the
FULL original block is preserved to .gald3r/logs/tool_output_<session>.log
before the compressed summary is emitted.

N comes from .gald3r/config/AGENT_CONFIG.md field
pre_tool_call_compress_lines (default 50; 0 = disabled). Error/warning lines
in the compressed region are surfaced in the summary so signal is preserved.

Always non-blocking: this hook NEVER denies a tool call. On any parse error,
missing field, disabled config, or short output it emits permission=allow
and exits 0.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common

CANDIDATE_FIELDS = ["output", "stdout", "stderr", "tool_output", "result", "text"]
SESSION_KEYS = ["session_id", "sessionId", "conversation_id", "run_id"]
SIGNAL_REGEX = re.compile(
    r"\b(error|warning|fatal|exception|fail(ed|ure)?|traceback|denied)\b",
    re.IGNORECASE,
)


def emit_allow(context: str) -> None:
    """Print the allow verdict (optionally with additional_context) and exit 0."""
    if context:
        print(
            json.dumps(
                {"permission": "allow", "additional_context": context},
                separators=(",", ":"),
            )
        )
    else:
        print(json.dumps({"permission": "allow"}, separators=(",", ":")))
    sys.exit(0)


def get_field_value(obj, name):
    """Mirror Get-FieldValue: stringified property value, or None when absent."""
    if not isinstance(obj, dict) or name not in obj:
        return None
    v = obj[name]
    if v is None:
        return None
    s = v if isinstance(v, str) else str(v)
    return s if s else None


def main(argv: list) -> None:
    parser = argparse.ArgumentParser(
        description="gald3r pre-tool-call output compression hook (Python port of g-hk-pre-tool-call.ps1)"
    )
    parser.add_argument(
        "-ProjectRoot",
        "--project-root",
        dest="project_root",
        default="",
        help="Override project-root detection (defaults to nearest .gald3r/ ancestor).",
    )
    args, _ = parser.parse_known_args(argv)

    # -- stdin payload (PreToolUse event schema) -------------------------------
    event = _hook_common.read_stdin_json()
    if not event:
        emit_allow("")

    # -- Locate project root ----------------------------------------------------
    project_root = args.project_root
    if not project_root:
        d = Path(__file__).resolve().parent
        found = ""
        while True:
            if (d / ".gald3r").exists():
                found = str(d)
                break
            if d.parent == d:
                break
            d = d.parent
        project_root = found if found else os.getcwd()

    # -- Read N from AGENT_CONFIG.md (default 50; 0 = disabled) ------------------
    max_lines = 50
    config_file = Path(project_root) / ".gald3r" / "config" / "AGENT_CONFIG.md"
    if config_file.is_file():
        try:
            cfg = config_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            cfg = ""
        m = re.search(r"pre_tool_call_compress_lines:\s*(\d+)", cfg, re.IGNORECASE)
        if m:
            max_lines = int(m.group(1))
    if max_lines <= 0:
        # Explicitly disabled -- pure no-op.
        emit_allow("")

    # -- Find a large output text block on the event payload --------------------
    block = None
    for f in CANDIDATE_FIELDS:
        v = get_field_value(event, f)
        if v:
            block = v
            break
    if not block and event.get("tool_response"):
        for f in CANDIDATE_FIELDS:
            v = get_field_value(event.get("tool_response"), f)
            if v:
                block = v
                break
    if not block and event.get("tool_input"):
        for f in CANDIDATE_FIELDS:
            v = get_field_value(event.get("tool_input"), f)
            if v:
                block = v
                break

    if not block:
        emit_allow("")

    # -- Split into lines and decide whether compression is warranted -----------
    lines = re.split(r"\r?\n", block)
    total = len(lines)
    if total <= max_lines:
        # Already small enough -- nothing to compress.
        emit_allow("")

    # -- Session/run id (stable per session when provided, else random) ---------
    session_id = ""
    for k in SESSION_KEYS:
        sv = get_field_value(event, k)
        if sv:
            session_id = sv
            break
    if not session_id:
        session_id = uuid.uuid4().hex[:8]
    run_id = uuid.uuid4().hex[:6]

    # -- Preserve full output to .gald3r/logs/ BEFORE compressing ---------------
    logs_dir = Path(project_root) / ".gald3r" / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        safe_session = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)
        log_file = logs_dir / f"tool_output_{safe_session}.log"
        header = "===== run {0} | {1} | {2} lines =====".format(
            run_id,
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            total,
        )
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(header + "\n")
            fh.write(block + "\n")
    except OSError:
        pass

    # -- Surface error/warning signal even when truncated -----------------------
    signal_lines = [ln.strip() for ln in lines if SIGNAL_REGEX.search(ln)][:10]

    # -- Build compressed block: summary prefix + last N lines ------------------
    tail = lines[-max_lines:]
    compressed_count = total - max_lines
    prefix = "... [{0} lines compressed, last {1} shown -- run ID: {2}] ...".format(
        compressed_count, max_lines, run_id
    )

    nl = os.linesep  # StringBuilder.AppendLine uses Environment.NewLine
    parts = [prefix]
    if signal_lines:
        parts.append("[signal lines preserved from compressed region:]")
        parts.extend(f"  {s}" for s in signal_lines)
    parts.extend(tail)
    parts.append(f"[full output: .gald3r/logs/tool_output_{session_id}.log]")

    emit_allow(nl.join(parts) + nl)


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception:
        # Always non-blocking: on ANY unexpected error emit allow and exit 0.
        try:
            print(json.dumps({"permission": "allow"}, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
