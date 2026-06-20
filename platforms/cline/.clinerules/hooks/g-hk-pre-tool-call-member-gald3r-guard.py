#!/usr/bin/env python3
"""Python port of g-hk-pre-tool-call-member-gald3r-guard.ps1 (T1584).

Pre-tool-call guard: refuse Edit/Write to a Workspace-Control member
repository's .gald3r/ that targets anything other than the marker pair
(.identity / PROJECT.md).

Enforces g-rl-36 "Workspace-Control Member `.gald3r/` Marker-Only Guard
(HARD RULE)" and BUG-021 (T213).

Member repos may keep ONLY .gald3r/.identity and .gald3r/PROJECT.md.
Everything else (TASKS.md, tasks/, BUGS.md, bugs/, PLAN.md, ...) is
forbidden.

Hook contract: same as g-hk-pre-tool-call-gald3r-guard (Claude Code / Cursor
PreToolUse spec). exit 2 = deny, exit 0 = allow. The tool event JSON is read
from stdin; every allow path prints {"permission":"allow"}; the deny path
prints a permission/deny JSON object and exits 2 (documented blocking
behavior — preserved). Any unexpected error fails open (allow, exit 0).

Bypass: GALD3R_HOOK_BYPASS=1.
Marker init: GALD3R_MARKER_INIT_ACTIVE=1 (set by
bootstrap_member_gald3r_marker.ps1 — or its .py sibling where present;
allows writing the marker pair itself).

Rule reference: .claude/rules/g-rl-36-workspace-member-gald3r-guard.md
Guard helper: .cursor/skills/g-skl-workspace/scripts/
check_member_repo_gald3r_guard.ps1 (prefer a .py sibling at the same path
when one exists). This hook itself makes no cross-script calls at runtime.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

_ALLOW = json.dumps({"permission": "allow"}, separators=(",", ":"))


def _find_workspace_manifest(start: Path):
    """Walk up from `start`; return the first workspace_manifest.yaml found."""
    d = start
    while True:
        candidate = d / ".gald3r" / "linking" / "workspace_manifest.yaml"
        if candidate.is_file():
            return candidate
        if d.parent == d:
            return None
        d = d.parent


def _marker_only_members(manifest: Path):
    """Member local_paths whose workspace_role is controlled_member or
    migration_source (those are the marker-only members)."""
    try:
        m_lines = manifest.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    if not m_lines:
        return []

    members = []
    cur_path = None
    cur_role = None
    for line in m_lines:
        if re.match(r"^\s*-\s+id:\s+\S+", line):
            # New repository entry — flush previous if it qualifies.
            if cur_path and cur_role in ("controlled_member", "migration_source"):
                members.append(cur_path.replace("\\", "/").rstrip("/"))
            cur_path = None
            cur_role = None
            continue
        m = re.match(r"^\s*local_path:\s*(.+)$", line)
        if m:
            cur_path = m.group(1).strip().strip('"').strip("'")
            continue
        m = re.match(r"^\s*workspace_role:\s*(\S+)", line)
        if m:
            cur_role = m.group(1).strip()
    # Flush the last entry.
    if cur_path and cur_role in ("controlled_member", "migration_source"):
        members.append(cur_path.replace("\\", "/").rstrip("/"))
    return members


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "PreToolUse guard: deny Edit/Write inside a Workspace-Control"
            " member repo's .gald3r/ except the .identity/PROJECT.md marker"
            " pair. Reads the tool event JSON from stdin; exit 2 = deny."
        )
    )
    parser.parse_args(argv)

    event = _hook_common.read_stdin_json()
    tool = str(event.get("tool_name", "") or "")
    path = ""
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "notebook_path", "target_file"):
            if key in tool_input and tool_input[key]:
                path = str(tool_input[key])
                break

    write_tools = ("Edit", "Write", "MultiEdit", "NotebookEdit", "Patch",
                   "ApplyPatch", "str_replace_editor")
    if tool not in write_tools:
        print(_ALLOW)
        return 0
    if not path:
        print(_ALLOW)
        return 0

    norm = path.replace("\\", "/")
    if not re.search(r"(^|/)\.gald3r/", norm):
        print(_ALLOW)
        return 0

    if os.environ.get("GALD3R_HOOK_BYPASS") == "1":
        print(_ALLOW)
        return 0

    # Build an absolute path.
    full = path
    if not os.path.isabs(full):
        full = os.path.join(os.getcwd(), path)
    full_norm = full.replace("\\", "/")

    # Discover the workspace manifest. Walk up from cwd; stop at filesystem root.
    manifest = _find_workspace_manifest(Path.cwd())
    if not manifest:
        # Not inside a workspace controller — allow (orchestration-only project).
        print(_ALLOW)
        return 0

    members = _marker_only_members(manifest)
    if not members:
        print(_ALLOW)
        return 0

    # Does the target path live inside any marker-only member's .gald3r/?
    # (case-insensitive, matching PowerShell -like / -eq semantics)
    full_lower = full_norm.lower()
    hit = None
    for mpath in members:
        member_gald3r = (mpath + "/.gald3r/").lower()
        if full_lower.startswith(member_gald3r) or full_lower == member_gald3r.rstrip("/"):
            hit = mpath
            break
    if not hit:
        print(_ALLOW)
        return 0

    # Compute the suffix inside the member's .gald3r/.
    prefix = hit + "/.gald3r/"
    suffix = full_norm[len(prefix):]
    marker_files = (".identity", "PROJECT.md")
    is_marker = suffix.lower() in tuple(m.lower() for m in marker_files)

    if os.environ.get("GALD3R_MARKER_INIT_ACTIVE") == "1" and is_marker:
        # Sanctioned marker bootstrap — allow.
        print(_ALLOW)
        return 0

    if is_marker and not Path(full).exists():
        # Allow creation of marker pair without active flag too — bootstrap
        # helper will set the flag in normal flow, but allow the case where a
        # marker is being repaired by the controller.
        print(_ALLOW)
        return 0

    if is_marker:
        # Editing an existing marker file is allowed (parity sync uses this).
        print(_ALLOW)
        return 0

    # Anything else inside a member's .gald3r/ is forbidden.
    msg = (
        f"Member .gald3r/ marker-only guard: refused Edit/Write to '{suffix}'"
        f" inside member repository '{hit}'. "
        "Workspace-Control member repositories may keep ONLY .gald3r/.identity"
        " and .gald3r/PROJECT.md. "
        "Live control-plane state (TASKS.md, tasks/, BUGS.md, PLAN.md, ...) is"
        " forbidden in members. "
        "Use the workspace controller (<gald3r_source>) for orchestration writes. "
        "See .claude/rules/g-rl-36-workspace-member-gald3r-guard.md and BUG-021."
    )
    print(json.dumps(
        {
            "permission": "deny",
            "user_message": msg,
            "agent_message": msg + f" Target: {path} (member={hit}, suffix={suffix})",
        },
        separators=(",", ":"),
    ))
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Fail open: never crash the host session on unexpected errors.
        print(_ALLOW)
        sys.exit(0)
