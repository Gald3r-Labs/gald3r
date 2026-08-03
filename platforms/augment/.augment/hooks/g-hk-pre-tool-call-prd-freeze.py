#!/usr/bin/env python3
"""Python port of g-hk-pre-tool-call-prd-freeze.ps1 (T1584).

Pre-tool-call guard: refuse Edit/Write to a PRD file whose YAML status is
`released` or `superseded` (C-019 / g-rl-33 § "PRD Freeze Gate").

A frozen PRD is the audit-of-record. Only @g-prd-revise may touch it, which
creates a successor PRD and updates the supersede chain atomically.

Hook contract: same as g-hk-pre-tool-call-gald3r-guard (Claude Code / Cursor
PreToolUse spec). exit 2 = deny, exit 0 = allow.

BUG-633 (actionability -- the deny reason must also reach stderr): Claude
Code's PreToolUse hook contract treats exit code 2 as a "blocking error" and
reads STDERR for the human-readable reason shown back to the calling agent.
This hook used to print only a `{permission: deny, ...}` JSON body to stdout
on a deny, so the real reason never reached stderr -- the exact defect class
BUG-179 fixed for g-hk-pre-tool-call-gald3r-guard.py and BUG-625 fixed for
g-hk-validate-shell.py. Mirroring BUG-625's additive-only shape: stdout stays
byte-for-byte unchanged, and the deny reason is also written to stderr.

Bypass: GALD3R_HOOK_BYPASS=1.
Revise flow: GALD3R_PRD_REVISE_ACTIVE=1 (set by @g-prd-revise).

Rule reference: .claude/rules/g-rl-33-enforcement_catchall.md § "PRD Freeze Gate"
Constraint: C-019
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations
# --- gald3r calltrace bootstrap (T268) -- injected; inert unless gald3r call tracing is
# enabled. Strip everywhere: python scripts/inject_calltrace_bootstrap.py --strip
import os as _g3ct_os
_g3ct_home = _g3ct_os.environ.get("GALD3R_HOME") or _g3ct_os.path.join(
    _g3ct_os.path.expanduser("~"), ".gald3r")
_g3ct_env = (_g3ct_os.environ.get("GALD3R_TRACE_CALLS") or "").strip().lower()
if _g3ct_env not in ("", "0", "off", "false", "no") or _g3ct_os.path.isfile(
        _g3ct_os.path.join(_g3ct_home, "calltrace.json")):
    try:
        _g3ct_bs = _g3ct_os.path.join(_g3ct_home, "calltrace_bootstrap.py")
        if _g3ct_os.path.isfile(_g3ct_bs):
            with open(_g3ct_bs, "r", encoding="utf-8") as _g3ct_fh:
                exec(compile(_g3ct_fh.read(), _g3ct_bs, "exec"),
                     {"__g3ct_script__": __file__,
                      "__name__": "_gald3r_calltrace_exec"})
    except Exception:
        pass
# --- end gald3r calltrace bootstrap ---

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

    # Resolve full path: if relative, resolve against the real project root
    # (BUG-373), not the hook process's own cwd. Cursor and Claude Code both
    # guarantee the hook process's cwd == project root, so the two were
    # equivalent there and this was always harmless. BUG-372 anchored the
    # Codex *invocation command* to the git root so the hook script is
    # reliably located/launched even when the Codex agent's own session cwd
    # has drifted into a subdirectory -- but that anchoring does not change
    # what cwd the spawned hook subprocess itself inherits, so a drifted cwd
    # could previously resolve a relative PRD path to a nonexistent
    # location, hit the "new PRD creation is allowed" branch below, and
    # silently fail open on an existing released/superseded PRD.
    full = Path(path)
    if not full.is_absolute():
        full = _hook_common.project_root() / path
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
        agent_msg = msg + f" Target: {path} (status={status})"
        print(json.dumps({
            "permission": "deny",
            "user_message": msg,
            "agent_message": agent_msg,
        }, separators=(",", ":")))
        # BUG-633: exit 2 is Claude Code's "blocking error" contract -- the reason
        # MUST also reach STDERR (stdout-only was silently discarded, surfacing as
        # "No stderr output" to the calling agent). Purely additive: stdout is left
        # byte-for-byte unchanged. Mirrors BUG-179/BUG-625's fix for the sibling
        # pre-tool-call guard hooks.
        sys.stderr.write(agent_msg + "\n")
        sys.stderr.flush()
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
