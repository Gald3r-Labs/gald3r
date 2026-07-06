#!/usr/bin/env python3
"""Python port of g-hk-pre-tool-call-gald3r-guard.ps1 (T1584).

Pre-tool-call guard: refuse unsupervised Edit/Write to .gald3r/ paths.

Enforces g-rl-33 ".gald3r/ Folder Gate (HARD RULE)":
  "NEVER read or write any file inside .gald3r/ without an active gald3r agent."

Hook contract (per Claude Code / Cursor PreToolUse spec):
  stdin   : JSON { tool_name, tool_input: { file_path | path | notebook_path, ... } }
  exit 0  : allow (body: { "permission": "allow" } on stdout)
  exit 2  : deny  (human-readable reason on STDERR — Claude Code's blocking-error
            contract; a stdout body is ignored for exit 2). BUG-179 fix.

Bypass: GALD3R_HOOK_BYPASS=1 (mirrors T600 §3.3 user override).
Allow override (active gald3r command): GALD3R_ACTIVE_AGENT=<agent_id>.

Rule reference: .claude/rules/g-rl-33-enforcement_catchall.md
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common

WRITE_TOOLS = [
    "Edit", "Write", "MultiEdit", "NotebookEdit", "Patch", "ApplyPatch",
    "str_replace_editor",
]

PATH_KEYS = ["file_path", "path", "notebook_path", "target_file"]


def _allow() -> int:
    print(json.dumps({"permission": "allow"}, separators=(",", ":")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PreToolUse guard: refuse unsupervised Edit/Write to .gald3r/ paths."
    )
    parser.parse_args()

    event = _hook_common.read_stdin_json()
    tool = str(event.get("tool_name") or "")
    path = ""
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        for k in PATH_KEYS:
            if k in tool_input:
                path = str(tool_input.get(k) or "")
                if path:
                    break

    # Only inspect file-write tools.
    if tool not in WRITE_TOOLS:
        return _allow()

    if not path:
        return _allow()

    # Normalize separators.
    norm = path.replace("\\", "/")

    # Only enforce on .gald3r/ paths anywhere in the path.
    if not re.search(r"(^|/)\.gald3r/", norm):
        return _allow()

    # Bypass switches.
    if os.environ.get("GALD3R_HOOK_BYPASS") == "1":
        return _allow()
    if os.environ.get("GALD3R_ACTIVE_AGENT"):
        return _allow()

    # Refuse.
    msg = (
        "Direct Edit/Write to .gald3r/ refused by g-hk-pre-tool-call-gald3r-guard. "
        "Route the change through the appropriate gald3r agent (g-task-manager / g-qa-engineer / "
        "g-planner / g-ideas-goals / etc.) or set GALD3R_ACTIVE_AGENT before the tool call. "
        "See .claude/rules/g-rl-33-enforcement_catchall.md § '.gald3r/ Folder Gate (HARD RULE)'."
    )
    # BUG-179: exit 2 is Claude Code's "blocking error" contract — the reason MUST
    # be written to STDERR. The old code printed JSON to stdout (silently discarded,
    # surfacing as "No stderr output"). Emit the denial to stderr; exit 2 keeps it a
    # hard block (no fail-open). See .gald3r/bugs/done/bug179_pretool_guard_hook_deny_contract.md
    sys.stderr.write(msg + f" Target path: {path}\n")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Fail open (mirrors the PS1 SilentlyContinue posture): never crash the
        # session on unexpected errors.
        try:
            print(json.dumps({"permission": "allow"}, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
