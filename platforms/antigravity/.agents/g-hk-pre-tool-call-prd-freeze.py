#!/usr/bin/env python3
"""Python port of g-hk-pre-tool-call-prd-freeze.ps1 (T1584).

Pre-tool-call guard: refuse Edit/Write to a PRD file whose YAML status is
`released` or `superseded` (C-019 / g-rl-33 § "PRD Freeze Gate").

A frozen PRD is the audit-of-record. Only @g-prd-revise may touch it, which
creates a successor PRD and updates the supersede chain atomically.

Hook contract: same as g-hk-pre-tool-call-gald3r-guard (Claude Code / Cursor
PreToolUse spec). exit 2 = deny, exit 0 = allow.

Bypass: GALD3R_HOOK_BYPASS=1.
Revise flow: GALD3R_PRD_REVISE_ACTIVE=1 (set by @g-prd-revise).

Rule reference: .claude/rules/g-rl-33-enforcement_catchall.md § "PRD Freeze Gate"
Constraint: C-019
"""
# @subsystems: RELEASE_AND_VERSIONING
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
        description="PreToolUse guard: refuse Edit/Write to released/superseded PRDs (C-019)."
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

    if tool not in WRITE_TOOLS:
        return _allow()
    if not path:
        return _allow()

    norm = path.replace("\\", "/")

    # Only PRD spec files: .gald3r/prds/prdNNN_*.md (case-insensitive)
    if not re.search(r"(?i)(^|/)\.gald3r/prds/prd\d+_[^/]+\.md$", norm):
        return _allow()

    # Resolve full path: if relative, prefix with cwd.
    full = Path(path)
    if not full.is_absolute():
        full = Path(os.getcwd()) / path
    if not full.exists():
        # New PRD creation is allowed; freeze applies only to existing released/superseded.
        return _allow()

    # Bypass switches.
    if os.environ.get("GALD3R_HOOK_BYPASS") == "1":
        return _allow()
    if os.environ.get("GALD3R_PRD_REVISE_ACTIVE") == "1":
        return _allow()

    # Read YAML frontmatter (between first two `---` lines).
    try:
        content = full.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        content = []
    if not content:
        return _allow()

    in_front = False
    status = ""
    for line in content:
        if re.match(r"^---\s*$", line):
            if not in_front:
                in_front = True
                continue
            else:
                break
        if in_front:
            m = re.match(r"^\s*status:\s*([a-zA-Z_-]+)", line)
            if m:
                status = m.group(1).lower()
                break

    if status in ("released", "superseded"):
        msg = (
            f"PRD freeze gate: refused Edit/Write to a {status} PRD. "
            "Released/superseded PRDs are the audit-of-record and are immutable. "
            "Use @g-prd-revise to create a successor PRD instead (atomically updates the supersede chain). "
            "See .claude/rules/g-rl-33-enforcement_catchall.md § 'PRD Freeze Gate (HARD RULE - C-019)'."
        )
        print(json.dumps({
            "permission": "deny",
            "user_message": msg,
            "agent_message": msg + f" Target: {path} (status={status})",
        }, separators=(",", ":")))
        return 2

    return _allow()


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
