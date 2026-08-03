#!/usr/bin/env python3
"""Thin resolver+verb dispatcher for the dangerous-shell-command guard (T319).

Python port of g-hk-validate-shell.ps1 (T1584).

Hook for shell command validation: blocks dangerous destructive commands
before they execute.

Hook contract:
  stdin   : JSON { command, ... }
  exit 0  : allow (body: { "permission": "allow" })
  exit 2  : deny  (body: { permission: "deny", user_message, agent_message })

BUG-625 (actionability -- the deny reason must always reach stderr): the verb this hook
dispatches to (`lint_cmd.py::_render_validate_shell_json`) prints its allow/deny body to
STDOUT ONLY, on both exit 0 and exit 2 -- correct for a plain `gald3r lint validate-shell`
CLI invocation, which always wants JSON on stdout regardless of verdict. But Claude Code's
PreToolUse hook contract treats exit code 2 as a "blocking error" and reads STDERR for the
human-readable reason shown back to the calling agent -- this is the exact same defect class
BUG-179 fixed for `g-hk-pre-tool-call-gald3r-guard.py` (see that hook's own inline comment
and `.gald3r/bugs/done/bug179_pretool_guard_hook_deny_contract.md`): a deny with nothing on
stderr surfaced to the agent as a bare, non-actionable "No stderr output", discarding the
real `user_message`/`agent_message` the verb had already computed and printed to stdout. On
every deny, `main()` below mirrors the deny reason onto stderr too (see
`_deny_reason_from_stdout`) -- purely additive: stdout is left byte-for-byte unchanged
(see `test_hook_output_is_byte_identical_to_pre_thin_implementation`), so any other consumer
parsing the structured JSON there is unaffected.

BUG-625 (remaining silent branch, found and closed during T605/BUG-625 re-verification): the
mirror used to be conditioned on the engine subprocess's OWN stderr being completely empty
(`elif proc.returncode == 2`, gated behind an `if proc.stderr:` for the passthrough above). That
left one more silent path: the engine process can write UNRELATED, incidental noise to stderr
on a genuine deny too -- confirmed live, `gald3r_core.core.agent.logging_setup`'s documented
"gald3r: skipped log rotation ... file is locked by another gald3r process" notice, which fires
whenever two concurrent `gald3r` invocations race on the shared global
`~/.gald3r/logs/errors.log` (an everyday occurrence under swarm/multi-bucket agent runs). When
that notice landed on a deny, the old `elif` saw non-empty stderr and skipped the mirror
entirely, so the calling agent's PreToolUse contract read ONLY that irrelevant notice as "the
reason" -- silently discarding the real deny reason all over again, the exact
non-actionable-block symptom this bug was filed against, just gated behind noisy-but-irrelevant
stderr instead of empty stderr. The mirror now runs unconditionally on every exit-2, APPENDING
after whatever else already landed on stderr (never replacing it), so the actionable reason is
guaranteed present regardless of what else wrote there first.

This hook used to hand-roll the dangerous-command blocklist and the case-insensitive
wildcard match inline (flagged fix-thin by the v3 IP classification, T319's continuation of
T318/T179). That check now lives in the binary as `gald3r lint validate-shell` (backed by
`gald3r_core.project.lint.validate_shell.validate_shell_command`, wired in
`cli/commands/lint_cmd.py`). T605 (BUG-643 deferred half) expanded that same verb's coverage to
also deny the BlastRadius agent-worktree-isolation git-mutation patterns (`git stash`, `git
checkout --`/`git checkout .`, `git restore`, `git clean` -- see
`gald3r_core.project.lint.validate_shell.GIT_MUTATION_DENY_PATTERNS`, the single canonical
source shared with `gald3r_core.server_bridge.policy.builtins.BlastRadius`'s runtime-policy-
engine enforcement of the same patterns) -- this hook itself needed NO changes for that: it
already dispatches every command through the same verb, so the expanded coverage is automatic.
This hook is reduced to the same resolver+dispatch pattern
already used by `g-hk-component-tag-check.py`, `g-hk-policy-check.py`,
`g-hk-agent-worktree-janitor.py`, `g-hk-pre-push.py`, and
`g-hk-pre-tool-call-member-gald3r-guard.py`: read the hook payload from stdin (same as
before -- the verb takes the command as a CLI argument, not on stdin, so this hook still
owns the JSON stdin parse), resolve the engine via `_hook_common.resolve_engine_argv`, invoke
`lint validate-shell --command <command>` with stdio inherited (no capture), and propagate
the verb's exit code untouched -- the printed allow/deny JSON is byte-for-byte identical to
the old inline implementation because the verb's renderer
(`lint_cmd.py::_render_validate_shell_json`) is a direct copy of this hook's old `print(json.
dumps(...))` calls.

Fail-open when the engine can't be resolved (no `gald3r` binary on PATH / not shipped on this
tier): this is a deliberate, disclosed trade-off matching every other absorbed-verb hook in
this tree (see e.g. `g-hk-component-tag-check.py`'s docstring) -- before this thin, the check
ran unconditionally (pure stdlib, no engine dependency); after, a project without the
compiled binary installed gets no enforcement from this hook (same fail-open shape the
`tool-start` chain already tolerates from its other pre-tool-call guards).

Verb: `gald3r lint validate-shell --command TEXT`
(`src/gald3r_core/cli/commands/lint_cmd.py`,
`src/gald3r_core/project/lint/validate_shell.py`).
Hook contract reference: `.gald3r/config/ENFORCEMENT_MATRIX.md` ("Hook contract (matches
`g-hk-validate-shell.py` precedent)").
"""
# @subsystems: PLATFORM_INTEGRATION
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
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common


def _resolve_engine_cmd(project_root: Path):
    """Resolve the gald3r engine command prefix (P3 Tier-0, T179/T191).

    Same shared resolver as `g-hk-component-tag-check.py` / `g-hk-policy-check.py` -- env
    var -> PATH -> legacy loose resolver -> loud degrade. Returns the command prefix or
    ``None`` when no engine can be found, in which case the hook no-ops (allow the command --
    fail-open).
    """
    return _hook_common.resolve_engine_argv(
        project_root, hook_name="g-hk-validate-shell"
    )


def _deny_reason_from_stdout(stdout_bytes: bytes) -> str:
    """Best-effort extraction of a human-readable deny reason from the verb's stdout JSON
    body (BUG-625), for the stderr echo `main()` adds on a deny with empty stderr.

    Never raises -- falls back to a generic-but-still-actionable message so the calling
    agent always gets SOME reason on stderr even if the JSON shape ever changes, rather than
    silently reverting to the "No stderr output" failure this fix exists to eliminate.
    """
    fallback = (
        "Dangerous command blocked by g-hk-validate-shell "
        "(see stdout JSON for the matched pattern/details)."
    )
    try:
        payload = json.loads(stdout_bytes.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return fallback
    if not isinstance(payload, dict):
        return fallback
    # `user_message` carries the specific, actionable part (which pattern matched);
    # `agent_message` is generic boilerplate. Prefer both together so the calling agent
    # gets the concrete "what" as well as the "why" -- falling back to whichever one is
    # actually present if the payload shape is ever narrowed.
    user_msg = payload.get("user_message")
    agent_msg = payload.get("agent_message")
    parts = [
        m.strip()
        for m in (user_msg, agent_msg)
        if isinstance(m, str) and m.strip()
    ]
    if parts:
        # De-dupe in the rare case both fields carry the same text.
        seen: list[str] = []
        for p in parts:
            if p not in seen:
                seen.append(p)
        return " ".join(seen)
    return fallback


def _find_project_root() -> Path:
    """Walk up from cwd for a `.gald3r/` ancestor; fall back to `_hook_common`'s
    hook-file-relative resolution.

    T516 (T512 inventory row 19 -- destructive-shell-command guard): applies
    the shared T512 gitignore-refusal + ambiguity-warning walk-up guard
    (`_hook_common.guarded_walk_up`).
    """
    d = Path.cwd()
    root = _hook_common.guarded_walk_up(
        d, exclude=_hook_common.resolved_global_gald3r_home()
    )
    return root if root is not None else _hook_common.project_root()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Block dangerous destructive shell commands before they execute."
    )
    parser.parse_args()

    event = _hook_common.read_stdin_json()
    # Claude Code / Cursor nest the shell command under tool_input.command; older
    # payloads used a top-level command. Read both -- reading only the top-level key
    # yields "" on a current payload, and on Windows an empty-string arg is dropped
    # so `--command ""` reaches the verb as a missing argument -> argparse error ->
    # the hook fails closed and BLOCKS EVERY shell command. An empty command has
    # nothing to validate, so allow it.
    _ti = event.get("tool_input")
    _ti = _ti if isinstance(_ti, dict) else {}
    command = str(event.get("command") or _ti.get("command") or "")
    if not command.strip():
        print(json.dumps({"permission": "allow"}, separators=(",", ":")))
        return 0

    root = _find_project_root()
    engine = _resolve_engine_cmd(root)
    if engine is None:
        # Engine not installed / not shipped on this tier -- pure no-op (fail-open),
        # matching every other absorbed-verb hook in this tree.
        print(json.dumps({"permission": "allow"}, separators=(",", ":")))
        return 0

    cmd = [*engine, "lint", "validate-shell", "--command", command]

    try:
        # Capture and re-emit the verb's stdout/stderr from THIS process instead of
        # console-inherited passthrough (BUG-495): under a windowless (pythonw) hook
        # parent, an inherit-stdio console child gets its own fresh console on Windows,
        # so the allow/deny JSON lands in a visible phantom window instead of the
        # tool-call pipeline -- the verdict is LOST (fails open) while a console pops.
        # Explicit capture keeps the payload byte-for-byte and lets _hook_common's
        # CREATE_NO_WINDOW injection suppress the child console entirely.
        proc = subprocess.run(cmd, timeout=30, capture_output=True)
        if proc.stdout:
            sys.stdout.buffer.write(proc.stdout)
            sys.stdout.buffer.flush()
        if proc.stderr:
            sys.stderr.buffer.write(proc.stderr)
            sys.stderr.buffer.flush()
        if proc.returncode == 2:
            # BUG-625: the verb never writes to stderr on its own (see module docstring).
            # Without this, a deny reaches Claude Code as exit 2 with empty stderr -> "No
            # stderr output", discarding the user_message/agent_message that DID reach
            # stdout. Mirror it onto stderr too so the calling agent always gets an
            # actionable reason.
            #
            # BUG-625 (remaining silent branch, found during T605/BUG-625 re-verification):
            # this used to be an `elif` gated on `proc.stderr` being EMPTY -- but the engine
            # process can write UNRELATED incidental noise to stderr on a genuine deny too
            # (confirmed live: `gald3r_core.core.agent.logging_setup`'s documented "gald3r:
            # skipped log rotation ... file is locked by another gald3r process" notice,
            # which fires whenever two concurrent `gald3r` invocations race on the shared
            # global `~/.gald3r/logs/errors.log` -- an everyday occurrence for concurrent
            # swarm/bucket agents). When that fires exactly on a deny, the old `elif` saw
            # non-empty stderr and skipped mirroring entirely, so Claude Code's PreToolUse
            # contract read ONLY the irrelevant log-rotation notice as "the reason" --
            # silently discarding the real deny reason all over again, the exact
            # non-actionable-block symptom this bug was filed against. Appending
            # unconditionally on every exit-2 (never REPLACING whatever incidental stderr
            # text preceded it) closes that gap: the actionable reason is now guaranteed to
            # be present in stderr on every deny, regardless of what else landed there.
            if proc.stderr:
                sys.stderr.write("\n")
            sys.stderr.write(_deny_reason_from_stdout(proc.stdout) + "\n")
            sys.stderr.flush()
        return proc.returncode
    except Exception:
        # Fail-open: a broken engine invocation must never block a tool call outright beyond
        # what the verb itself would have decided.
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
