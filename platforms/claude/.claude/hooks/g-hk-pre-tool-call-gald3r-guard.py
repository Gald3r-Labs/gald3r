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
Allow override (active gald3r command): GALD3R_ACTIVE_AGENT=<agent_id>, OR a
time-boxed marker written via `_hook_common.py set-active-agent <agent_id>`
(BUG-414 -- lets an Agent-tool-launched subagent self-authorize a LATER,
separately spawned hook subprocess, which an env var set inside its own
tool-call subprocess cannot reach).

Rule reference: .claude/rules/g-rl-33-enforcement_catchall.md
"""
# @subsystems: PROJECT_IDENTITY_SETUP
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


def _is_within_project_gald3r(path: str, root: Path) -> bool:
    """True when `path` resolves to a location inside THIS project's
    root-level .gald3r/ (the live coordination directory g-rl-33 protects)
    -- not merely a path that contains a ".gald3r/" segment somewhere
    deeper in the tree (e.g. authored template source under
    src/**/template_verification/.gald3r/...). See BUG-244.

    BUG-373: a relative `path` is resolved against the discovered project
    root (the caller's already-resolved `_hook_common.project_root()`,
    which walks up from this hook script's own on-disk location --
    cwd-independent), NOT `Path.cwd()`. Cursor and Claude Code both
    guarantee the hook process's cwd == project root, so the two were
    equivalent there and this was always harmless. BUG-372 anchored the
    Codex *invocation command* to the git root so the hook script is
    reliably located/launched even when the Codex agent's own session cwd
    has drifted into a subdirectory -- but that anchoring does not change
    what cwd the spawned hook subprocess itself inherits, so a drifted cwd
    could previously make a project-root-relative `.gald3r/`-targeting path
    resolve OUTSIDE `gald3r_dir` and silently fail open.

    `root` is passed in by `main()` (computed once there via
    `_hook_common.project_root()`) rather than re-resolved here, so a
    single hook invocation only ever walks the filesystem to find the
    project root once (BUG-414 cleanup -- this function used to call
    `_hook_common.project_root()` itself, redundantly, on every call)."""
    gald3r_dir = (root / ".gald3r").resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        candidate = candidate.resolve()
    except OSError:
        return False
    try:
        candidate.relative_to(gald3r_dir)
    except ValueError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PreToolUse guard: refuse unsupervised Edit/Write to .gald3r/ paths."
    )
    parser.parse_args()

    # Resolved once and reused for both the containment check and the
    # marker-file authorization check below (BUG-414 cleanup).
    root = _hook_common.project_root()

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

    # Cheap pre-filter: skip project-root resolution when no ".gald3r/"
    # segment appears anywhere in the raw path.
    if not re.search(r"(^|/)\.gald3r/", norm):
        return _allow()

    # BUG-244: only enforce when the target resolves INSIDE this project's
    # root-level .gald3r/ -- not merely because a ".gald3r/" segment appears
    # somewhere deeper in the tree (authored template source under src/).
    if not _is_within_project_gald3r(path, root):
        return _allow()

    # Bypass switches.
    if os.environ.get("GALD3R_HOOK_BYPASS") == "1":
        return _allow()
    if os.environ.get("GALD3R_ACTIVE_AGENT"):
        return _allow()
    # BUG-414: an env var set inside one tool call's own subprocess cannot
    # propagate to a LATER, separately spawned Edit/Write hook subprocess --
    # the marker file is a filesystem-backed, time-boxed equivalent an agent
    # (main coordinator or an Agent-tool-launched subagent) can write to
    # itself via a plain Bash call (`_hook_common.py set-active-agent`)
    # before issuing the Edit/Write. Fails closed on anything ambiguous or
    # expired (see `_hook_common.read_active_agent_marker`).
    #
    # BUG-414 Phase-2: the marker is SINGLE-USE. There is no harness signal
    # tying this specific Edit/Write call to a particular agent process, so
    # true per-process binding isn't achievable -- consuming the marker on
    # its first authorized use instead collapses the window during which an
    # unrelated concurrent agent could piggyback on someone else's still-
    # valid marker from the full TTL (up to 300s) down to this one call.
    #
    # BUG-414 atomicity rework: the old read-then-consume two-step (a
    # `read_active_agent_marker()` truthiness check followed by a separate
    # `consume_active_agent_marker()` unlink) was a TOCTOU race -- each
    # guard-hook invocation is its own freshly-spawned process, so two
    # concurrent invocations could both read the marker as valid before
    # either got around to deleting it (live-reproduced with up to 12/12
    # concurrent invocations all allowed off one marker). `claim_active_
    # agent_marker()` claims and validates the marker in a SINGLE atomic
    # filesystem operation (an atomic rename that steals the marker's
    # directory entry), so of N concurrent invocations racing the same
    # marker, AT MOST ONE can ever observe it as valid.
    if _hook_common.claim_active_agent_marker(root):
        return _allow()

    # Refuse.
    msg = (
        "Direct Edit/Write to .gald3r/ refused by g-hk-pre-tool-call-gald3r-guard. "
        "Route the change through the appropriate gald3r agent (g-task-manager / g-qa-engineer / "
        "g-planner / g-ideas-goals / etc.), set GALD3R_ACTIVE_AGENT before the tool call, or "
        "pre-authorize via `_hook_common.py set-active-agent <agent_id>` (BUG-414). "
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
