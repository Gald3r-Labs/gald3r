#!/usr/bin/env python3
"""Antigravity hook adapter (T510).

Antigravity's hook I/O contract differs from the gald3r canonical core:
  - input  : camelCase JSON on stdin (`toolCall.name`, `toolCall.args`, `stepIdx`,
             `terminationReason`, `fullyIdle`, ...).
  - output : a `decision` envelope per event, NOT the core's `{continue,...}`:
       PreToolUse  -> { "decision": "allow" | "deny" | "ask" | "force_ask", "reason"? }
       PostToolUse -> {}                      (empty object)
       Stop        -> { "decision": "continue", "reason"? }  to keep going, else allow stop.

This adapter keeps `g_hk_core.py` BYTE-IDENTICAL across all platforms: it normalizes the
Antigravity payload, runs the standard canonical entrypoint (`g-hk-on-<event>.py`) as a
subprocess (so the same concern chain executes), then translates the core's `{continue, reason}`
result into Antigravity's `decision` schema.

Usage (from .agents/hooks.json): `python <dir>/g-hk-ag-dispatch.py <canonical-event>`
where <canonical-event> is one of: tool-start | tool-end | stop.

STATUS: authored against the Antigravity 2.0 launch docs (antigravity.google/docs/hooks,
2026-06-18). Antigravity launched the same day (replacing Gemini CLI) and its own docs mandate
pinning the payload schema via a live install test, so this adapter is PENDING live verification —
especially the Stop `decision` semantics. Fail-soft: any error -> allow (never blocks the host).
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Antigravity canonical event -> standard gald3r entrypoint file.
_ENTRYPOINT = {
    "tool-start": "g-hk-on-tool-start.py",
    "tool-end": "g-hk-on-tool-end.py",
    "stop": "g-hk-on-stop.py",
}


def _read_stdin() -> dict:
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read() or ""
        return json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError):
        return {}


def _normalize(event: str, ag: dict) -> dict:
    """Map the Antigravity payload onto the field names the concern hooks read."""
    norm: dict = {
        "hook_event_name": event,
        "session_id": ag.get("conversationId", ""),
    }
    tool_call = ag.get("toolCall") or {}
    args = tool_call.get("args") or {}
    if tool_call:
        norm["tool_name"] = tool_call.get("name", "")
        norm["tool_input"] = args
        # run_command -> CommandLine is the shell string our validate-shell concern reads.
        if "CommandLine" in args:
            norm["command"] = args.get("CommandLine", "")
        # file-editing tools expose TargetFile / AbsolutePath.
        for key in ("TargetFile", "AbsolutePath"):
            if key in args:
                norm["file_path"] = args.get(key)
                break
    if "terminationReason" in ag:
        norm["termination_reason"] = ag.get("terminationReason")
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


def _translate(event: str, core: dict) -> dict:
    blocked = core.get("continue") is False
    reason = str(core.get("reason") or core.get("additional_context") or "").strip()
    if event == "tool-start":
        # PreToolUse: a concern blocked -> deny; else allow.
        out = {"decision": "deny" if blocked else "allow"}
        if reason:
            out["reason"] = reason
        return out
    if event == "tool-end":
        # PostToolUse: Antigravity expects an empty object.
        return {}
    if event == "stop":
        # Stop: returning {"decision":"continue"} would re-enter the loop. The stop concerns here
        # are side-effecting (learn / encoding-normalize / agent-complete); force-continue is NOT
        # wired pending live verification of Antigravity's Stop semantics. Allow the stop.
        return {}
    return {}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    event = argv[0] if argv else ""
    if event not in _ENTRYPOINT:
        print("{}")
        return 0
    ag = _read_stdin()
    norm = _normalize(event, ag)
    core = _run_core(event, norm)
    print(json.dumps(_translate(event, core), separators=(",", ":")))
    # Antigravity reads the decision from stdout JSON (exit 0). Exit 2 also hard-blocks; we rely on
    # the JSON `decision: deny` rather than exit 2 to keep behavior explicit.
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
            print("{}")
        except Exception:
            pass
        sys.exit(0)
