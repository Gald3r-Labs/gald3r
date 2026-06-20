#!/usr/bin/env python3
"""Cline hook adapter (T512).

Cline (v3.36+) discovers hooks as **executable scripts named exactly the hook type, with no
extension**, in `.clinerules/hooks/` (project) or `~/Documents/Cline/Rules/Hooks/` (global). Each
receives JSON on stdin and returns:

    { "cancel": bool, "errorMessage"?: str, "contextModification"?: str }

`cancel` blocks/allows the operation; `contextModification` injects text into the next request.
This differs from the gald3r canonical core's `{continue, reason, additional_context}` envelope, so
the six no-extension shims (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `TaskStart`,
`TaskResume`, `TaskCancel`) each call this adapter, which keeps `g_hk_core.py` BYTE-IDENTICAL: it
normalizes cline's payload, runs the standard `g-hk-on-<event>.py` (same concern chain) as a
subprocess, then translates the result into cline's schema.

PLATFORM NOTE: cline hooks are **macOS/Linux only** (no Windows). STATUS: authored against
cline.bot/blog/cline-v3-36-hooks (2025-11-06) — PENDING live-install verification (exact PreToolUse
field names + TaskStart/Resume/Cancel payloads were not fully documented). Fail-soft: any error →
`{"cancel": false}` (never blocks the host).

Usage (from a no-ext shim): `python _cline_adapter.py <canonical-event>`.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

_ENTRYPOINT = {
    "tool-start": "g-hk-on-tool-start.py",
    "tool-end": "g-hk-on-tool-end.py",
    "user-prompt-submit": "g-hk-on-user-prompt-submit.py",
    "session-start": "g-hk-on-session-start.py",
    "session-end": "g-hk-on-session-end.py",
}


def _read_stdin() -> dict:
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read() or ""
        return json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError):
        return {}


def _normalize(event: str, cl: dict) -> dict:
    """Map cline's payload onto the field names the concern hooks read (best-effort)."""
    norm: dict = {
        "hook_event_name": event,
        "session_id": cl.get("taskId", ""),
    }
    # cline PreToolUse/PostToolUse expose a tool name + parameters; field naming is not fully
    # documented, so probe the common shapes.
    tool = cl.get("toolName") or cl.get("tool_name") or cl.get("tool") or ""
    params = cl.get("toolInput") or cl.get("parameters") or cl.get("params") or {}
    if tool:
        norm["tool_name"] = tool
        norm["tool_input"] = params
        if isinstance(params, dict):
            if "command" in params:
                norm["command"] = params.get("command", "")
            for key in ("path", "filePath", "file_path", "TargetFile"):
                if key in params:
                    norm["file_path"] = params.get(key)
                    break
    prompt = cl.get("prompt") or cl.get("promptText") or cl.get("message")
    if prompt:
        norm["prompt"] = prompt
    return norm


def _run_core(event: str, norm: dict) -> dict:
    entry = _ENTRYPOINT.get(event)
    if not entry:
        return {"continue": True}
    target = SCRIPT_DIR / entry
    if not target.is_file():
        return {"continue": True}
    try:
        res = subprocess.run(
            [sys.executable, str(target)],
            input=json.dumps(norm),
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
    except (OSError, subprocess.SubprocessError):
        return {"continue": True}
    out = (res.stdout or "").strip()
    if not out:
        return {"continue": res.returncode != 2}
    try:
        parsed = json.loads(out)
        if isinstance(parsed, dict):
            if res.returncode == 2:
                parsed["continue"] = False
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    return {"continue": res.returncode != 2}


def _translate(core: dict) -> dict:
    blocked = core.get("continue") is False
    out: dict = {"cancel": bool(blocked)}
    reason = str(core.get("reason") or "").strip()
    ctx = str(core.get("additional_context") or "").strip()
    if blocked and reason:
        out["errorMessage"] = reason
    if ctx:
        out["contextModification"] = ctx
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    event = argv[0] if argv else ""
    if event not in _ENTRYPOINT:
        print(json.dumps({"cancel": False}, separators=(",", ":")))
        return 0
    cl = _read_stdin()
    norm = _normalize(event, cl)
    core = _run_core(event, norm)
    print(json.dumps(_translate(core), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        try:
            print(json.dumps({"cancel": False}, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
