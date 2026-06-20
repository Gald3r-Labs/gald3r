#!/usr/bin/env python3
"""Python port of g-hk-validate-shell.ps1 (T1584).

Hook for shell command validation: blocks dangerous destructive commands
before they execute.

Hook contract:
  stdin   : JSON { command, ... }
  exit 0  : allow (body: { "permission": "allow" })
  exit 2  : deny  (body: { permission: "deny", user_message, agent_message })
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "format c:",
    "del /s /q c:\\*",
    ":(){:|:&};:",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Block dangerous destructive shell commands before they execute."
    )
    parser.parse_args()

    event = _hook_common.read_stdin_json()
    command = str(event.get("command") or "")

    for pattern in DANGEROUS_PATTERNS:
        # PowerShell -like is a case-insensitive wildcard match; fnmatch
        # reproduces the same *, ?, [seq] wildcard semantics.
        if fnmatch.fnmatchcase(command.lower(), f"*{pattern.lower()}*"):
            print(json.dumps({
                "permission": "deny",
                "user_message": f"Dangerous command blocked: {pattern}",
                "agent_message": (
                    "This command has been blocked by a security hook because "
                    "it matches a dangerous pattern."
                ),
            }, separators=(",", ":")))
            return 2

    print(json.dumps({"permission": "allow"}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Fail open: never crash the session on unexpected errors.
        try:
            print(json.dumps({"permission": "allow"}, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
