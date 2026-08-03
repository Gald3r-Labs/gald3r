#!/usr/bin/env python3
"""Thin resolver+verb dispatcher for the member-repo `.gald3r/` guard (T179/T191).

Pre-tool-call guard: refuse Edit/Write to a Workspace-Control member
repository's .gald3r/ that targets anything other than the marker pair
(.identity / PROJECT.md).

Enforces g-rl-36 "Workspace-Control Member `.gald3r/` Marker-Only Guard
(HARD RULE)" and BUG-021 (T213).

This hook used to hand-roll the workspace_manifest.yaml parse and the
marker-only membership decision inline (flagged fix-thin by the v3 IP
classification, T1679/T179). That enforcement logic now lives in the
binary as `gald3r workspace member guard` (backed by
`gald3r_core.project.workspace_member.guard.run_guard`, wired in
`cli/commands/workspace.py`). This hook is reduced to the same
resolver+dispatch pattern already used by `g-hk-policy-check.py` and
`g-hk-agent-worktree-janitor.py`: resolve the engine via
`_hook_common.resolve_engine_argv`, extract the write-tool target path
from the event, pipe it to the verb, and branch on the JSON verdict.
Fail-open (allow) whenever the engine can't be resolved or the verb call
errors — a broken guard must never brick a session.

Hook contract: same as g-hk-pre-tool-call-gald3r-guard (Claude Code / Cursor
PreToolUse spec). exit 2 = deny, exit 0 = allow. The tool event JSON is read
from stdin; every allow path prints {"permission":"allow"}; the deny path
prints a permission/deny JSON object and exits 2 (documented blocking
behavior — preserved). Any unexpected error fails open (allow, exit 0).

BUG-633 (actionability -- the deny reason must also reach stderr): Claude
Code's PreToolUse hook contract treats exit code 2 as a "blocking error" and
reads STDERR for the human-readable reason shown back to the calling agent.
This hook used to print only the `{permission: deny, ...}` JSON body to
stdout on a deny, so the real reason never reached stderr -- the exact defect
class BUG-179 fixed for g-hk-pre-tool-call-gald3r-guard.py and BUG-625 fixed
for g-hk-validate-shell.py. Mirroring BUG-625's additive-only shape: stdout
stays byte-for-byte unchanged, and the deny reason is also written to stderr.

Bypass: GALD3R_HOOK_BYPASS=1.
Marker init: GALD3R_MARKER_INIT_ACTIVE=1 (set by
bootstrap_member_gald3r_marker.ps1 — or its .py sibling where present;
allows writing the marker pair itself) — forwarded to the verb as
`--allow-marker-init`.

Rule reference: .claude/rules/g-rl-36-workspace-member-gald3r-guard.md
Verb: `gald3r workspace member guard --target-path PATH [--dot-gald3r-path
REL] [--allow-marker-init] [--manifest-path PATH] [--json]`
(`src/gald3r_core/cli/commands/workspace.py`,
`src/gald3r_core/project/workspace_member/guard.py`).
"""
# @subsystems: WORKSPACE_COORDINATION
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

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

_ALLOW = json.dumps({"permission": "allow"}, separators=(",", ":"))

_WRITE_TOOLS = (
    "Edit", "Write", "MultiEdit", "NotebookEdit", "Patch",
    "ApplyPatch", "str_replace_editor",
)


def _resolve_engine_cmd(project_root: Path):
    """Resolve the gald3r engine command prefix (P3 Tier-0, T179/T191).

    Same shared resolver as `g-hk-policy-check.py` -- env var -> PATH ->
    legacy loose resolver -> loud degrade. Returns the command prefix or
    ``None`` when no engine can be found, in which case the hook no-ops
    (allow).
    """
    return _hook_common.resolve_engine_argv(
        project_root, hook_name="g-hk-pre-tool-call-member-gald3r-guard"
    )


def _resolve_project_root() -> Path:
    """Prefer the invoking process's cwd walked up to its `.gald3r/`
    ancestor; fall back to `_hook_common`'s hook-file-relative resolution.

    T516 (T512 inventory row 17 -- HIGHEST PRIORITY): this IS the
    g-rl-36 member-`.gald3r/` write guard's own root-of-truth resolver. If
    it resolved onto a gitignored decoy `.gald3r/`, the guard's own
    root-of-truth was exactly what could be silently spoofed -- applies the
    shared T512 gitignore-refusal + ambiguity-warning walk-up guard
    (`_hook_common.guarded_walk_up`).
    """
    d = Path.cwd()
    root = _hook_common.guarded_walk_up(
        d, exclude=_hook_common.resolved_global_gald3r_home()
    )
    return root if root is not None else _hook_common.project_root()


def _extract_tool_and_path(event: dict) -> "tuple[str, str]":
    """Pull the tool name and the write-target path out of the event payload.

    This is event-shape parsing (the resolver's job), not enforcement
    logic -- the actual member/marker decision is delegated entirely to
    the `gald3r workspace member guard` verb below.
    """
    tool = str(event.get("tool_name", "") or "")
    path = ""
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "notebook_path", "target_file"):
            if key in tool_input and tool_input[key]:
                path = str(tool_input[key])
                break
    return tool, path


def main(argv=None) -> int:
    event = _hook_common.read_stdin_json()
    if not event:
        print(_ALLOW)
        return 0

    tool, path = _extract_tool_and_path(event)
    if tool not in _WRITE_TOOLS or not path:
        print(_ALLOW)
        return 0

    norm = path.replace("\\", "/")
    if not re.search(r"(^|/)\.gald3r/", norm):
        # Fast no-op: nothing under any .gald3r/ in the path at all --
        # avoids an engine round-trip for the overwhelming common case.
        print(_ALLOW)
        return 0

    if os.environ.get("GALD3R_HOOK_BYPASS") == "1":
        print(_ALLOW)
        return 0

    # BUG-373: resolve a relative target against the already-discovered
    # project root (`_resolve_project_root()`, an ancestor walk from cwd to
    # the nearest `.gald3r/` -- tolerant of a drifted-but-still-nested cwd),
    # not a second, independent raw `os.getcwd()` read. Cursor and Claude
    # Code both guarantee the hook process's cwd == project root, so this
    # was always harmless there; BUG-372 anchored the Codex *invocation
    # command* to the git root without changing what cwd the spawned hook
    # subprocess itself inherits. Live-tested (BUG-373): for the realistic
    # "agent cwd drifted into a subdirectory of the SAME repo it is already
    # working in" scenario this hook's `gald3r workspace member guard`
    # ancestor-prefix repo match and right-anchored `.gald3r/`-suffix
    # extraction are both invariant to an extra mid-path segment, so this
    # was not independently exploitable the way the primary guard's strict
    # `relative_to()` check was -- reusing `root` here is still correct
    # and removes a redundant ambient `os.getcwd()` read.
    root = _resolve_project_root()
    full = path if os.path.isabs(path) else str(root / path)
    full_norm = full.replace("\\", "/")

    m = re.search(r"(?:^|/)\.gald3r/(.*)$", full_norm, re.IGNORECASE)
    dot_gald3r_path = m.group(1) if m else ""

    engine = _resolve_engine_cmd(root)
    if engine is None:
        # Engine not installed / not shipped on this tier -- pure no-op.
        print(_ALLOW)
        return 0

    verb_argv = [*engine, "workspace", "member", "guard",
                 "--target-path", full, "--json"]
    if dot_gald3r_path:
        verb_argv += ["--dot-gald3r-path", dot_gald3r_path]
    if os.environ.get("GALD3R_MARKER_INIT_ACTIVE") == "1":
        verb_argv.append("--allow-marker-init")

    try:
        proc = subprocess.run(
            verb_argv,
            capture_output=True,
            text=True,
            timeout=15,
        )
        result = json.loads(proc.stdout.strip() or "{}")
    except Exception:
        # Fail-open: a broken guard/manifest must never block a tool call.
        print(_ALLOW)
        return 0

    if str(result.get("Status", "")).lower() == "block":
        msg = result.get("Message") or (
            "Member .gald3r/ marker-only guard: write blocked. "
            "See .claude/rules/g-rl-36-workspace-member-gald3r-guard.md and BUG-021."
        )
        agent_msg = msg + f" Target: {path}"
        print(json.dumps(
            {
                "permission": "deny",
                "user_message": msg,
                "agent_message": agent_msg,
            },
            separators=(",", ":"),
        ))
        # BUG-633: exit 2 is Claude Code's "blocking error" contract -- the reason
        # MUST also reach STDERR (stdout-only was silently discarded, surfacing as
        # "No stderr output" to the calling agent). Purely additive: stdout is left
        # byte-for-byte unchanged. Mirrors BUG-179/BUG-625's fix for the sibling
        # pre-tool-call guard hooks.
        sys.stderr.write(agent_msg + "\n")
        sys.stderr.flush()
        return 2

    # allow / warn / error (fail-open) -- all pass through.
    print(_ALLOW)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Fail open: never crash the host session on unexpected errors.
        print(_ALLOW)
        sys.exit(0)
