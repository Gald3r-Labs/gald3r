#!/usr/bin/env python3
"""Agent-worktree janitor hook (T1592).

Fires on both SessionStart and Stop (session end) so stale native
Cursor/Claude background-agent worktrees under `.claude/worktrees/agent-*`
(and the `.cursor` equivalent) never accumulate silently between g-go-go
runs. Delegates all logic to the absorbed engine verb `gald3r worktree
janitor` (A1 / T1658) — this hook is a thin, non-blocking invocation wrapper
that resolves the engine binary through the zero-IP `.gald3r_sys/scripts/
gald3r_bin.py` resolver.

Non-destructive by default: applies pruning (rescue-then-remove) but never
terminates processes unless GALD3R_JANITOR_REAP_PROCESSES=1 is set (opt-in,
guarded — see task1592 AC). Runs at most once per event type per session via
an idempotency env-var guard, mirroring g-hk-session-end.py.

BUG-106 fail-safe gate: `--apply` (the flag that lets the engine actually
rescue-commit + prune) is withheld whenever the target checkout is the dirty
PRIMARY checkout (git-dir == git-common-dir, no `.gald3r-worktree.json`
marker) or the checkout shape is otherwise ambiguous/unrecognized — see
`_primary_checkout_status`/`_is_agent_worktree_marker` below and
`.gald3r/bugs/done/bug106_*.md`. Durable upstream fix tracked as T93.

Hooks must never crash or block the host session: any unexpected error is
swallowed and the hook exits 0.
"""
# @subsystems: AGENT_ORCHESTRATION
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
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

DEFAULT_STALE_HOURS = "2"

# BUG-106 (T1592 janitor auto-commits on the primary checkout / main):
# the janitor's own scan/classify logic lives inside the compiled `gald3r`
# engine binary and is not source we can patch here. This wrapper instead
# hard-gates the *invocation*: it never lets `--apply` (the flag that
# permits the engine's rescue-commit + prune) run against the primary
# checkout while that checkout is dirty (the exact condition recorded for
# all four observed misfires — see .gald3r/bugs/done/bug106_*.md), and it
# reverts any rescue-style commit that lands on the primary's HEAD anyway.
_RESCUE_COMMIT_PREFIX = "chore(worktree-janitor): rescue uncommitted work"
_AGENT_WORKTREE_ROOT_SEGMENTS = (
    os.path.join(".claude", "worktrees"),
    os.path.join(".cursor", "worktrees"),
)


def _git(args: list, cwd: str):
    """Run ``git *args`` in *cwd*. Returns (returncode, stdout, stderr).

    Never raises — a failure to even spawn git yields ``(None, "", "")`` so
    callers can fail safe (ambiguous state) instead of crashing.
    """
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=15,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception:
        return None, "", ""


def _is_agent_worktree_marker(root: str) -> bool:
    """True when *root* itself carries agent-worktree ownership evidence.

    Either a ``.gald3r-worktree.json`` marker file, or a path that runs
    through a recognized agent-worktree root (``.claude/worktrees/``,
    ``.cursor/worktrees/``) or a ``.gald3r-worktrees/`` parent directory.
    Per BUG-106: the primary checkout must never match this.
    """
    try:
        p = Path(root)
        if (p / ".gald3r-worktree.json").is_file():
            return True
        resolved = p.resolve()
        joined = os.sep.join(resolved.parts)
        if any(seg in joined for seg in _AGENT_WORKTREE_ROOT_SEGMENTS):
            return True
        return any(part == ".gald3r-worktrees" for part in resolved.parts)
    except Exception:
        return False


def _primary_checkout_status(project_root: str) -> dict:
    """Classify *project_root* for janitor invocation safety (BUG-106).

    ``ok=False`` means git state could not be determined — callers must
    treat this as ambiguous and fail safe (never pass ``--apply``).
    ``is_primary=True`` means this checkout's git-dir equals its
    git-common-dir, i.e. it IS the main checkout, not a linked worktree.
    """
    rc_gd, git_dir, _ = _git(["rev-parse", "--git-dir"], project_root)
    rc_gcd, git_common_dir, _ = _git(["rev-parse", "--git-common-dir"], project_root)
    if rc_gd != 0 or rc_gcd != 0 or not git_dir or not git_common_dir:
        return {"ok": False, "is_primary": False, "dirty": True, "head": ""}

    try:
        gd_abs = (Path(project_root) / git_dir).resolve()
        gcd_abs = (Path(project_root) / git_common_dir).resolve()
    except Exception:
        return {"ok": False, "is_primary": False, "dirty": True, "head": ""}
    is_primary = gd_abs == gcd_abs

    rc_st, status_out, _ = _git(["status", "--porcelain"], project_root)
    if rc_st != 0:
        return {"ok": False, "is_primary": is_primary, "dirty": True, "head": ""}
    dirty = bool(status_out)

    rc_head, head, _ = _git(["rev-parse", "HEAD"], project_root)
    head = head if rc_head == 0 else ""

    return {"ok": True, "is_primary": is_primary, "dirty": dirty, "head": head}


def _find_project_root() -> str:
    """T516 (T512 inventory row 9): applies the shared T512 gitignore-refusal
    + ambiguity-warning walk-up guard (`_hook_common.guarded_walk_up`)."""
    here = Path(__file__).resolve().parent
    root = _hook_common.guarded_walk_up(
        here, exclude=_hook_common.resolved_global_gald3r_home()
    )
    return str(root) if root is not None else str(Path.cwd())


def _resolve_engine_cmd(project_root: str):
    """Resolve the gald3r engine command prefix (P3 Tier-0, T179/T191).

    Delegates to the shared `_hook_common.resolve_engine_argv` (env var ->
    PATH -> legacy loose resolver -> loud degrade) so PATH resolution works
    even when the loose `.gald3r_sys/scripts/gald3r_bin.py` IP script is not
    shipped. Returns the command prefix (e.g. ``["gald3r"]``) or ``None``
    when no engine can be found — in which case the hook no-ops gracefully,
    exactly like the old script-missing path.
    """
    return _hook_common.resolve_engine_argv(
        Path(project_root), hook_name="g-hk-agent-worktree-janitor"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Auto-prune stale agent worktrees on session start/end (T1592)."
    )
    parser.add_argument("-EventName", "--event-name", dest="event_name", default="unknown",
                         help="Which hook event triggered this run (SessionStart|Stop).")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root", default="",
                         help="Override project-root detection.")
    args = parser.parse_args(argv)

    # -- stdin payload (not currently inspected, but drained so the host never blocks)
    _hook_common.read_stdin_json()

    guard_var = f"GALD3R_HK_WORKTREE_JANITOR_{args.event_name.upper()}_APPLIED"
    if os.environ.get(guard_var) == "1":
        print(json.dumps({"continue": True}, separators=(",", ":")))
        return 0
    os.environ[guard_var] = "1"

    project_root = args.project_root or _find_project_root()
    engine = _resolve_engine_cmd(project_root)
    if engine is None:
        # Engine binary not resolvable (or resolver not shipped) — no-op.
        print(json.dumps({"continue": True}, separators=(",", ":")))
        return 0

    # BUG-106 safety gate — decide whether --apply (mutating mode) is
    # allowed at all. Fail safe (no --apply) on any ambiguity.
    pre_status = _primary_checkout_status(project_root)
    is_agent_worktree = _is_agent_worktree_marker(project_root)
    allow_apply = True
    safety_note = ""
    if not pre_status["ok"]:
        allow_apply = False
        safety_note = "ambiguous-git-state"
    elif pre_status["is_primary"] and not is_agent_worktree:
        # Primary checkout, never an agent worktree to rescue/prune. Its
        # subdirectories are still legitimate scan targets, but the
        # engine must not be allowed to mutate/commit here while it is
        # dirty -- that dirty-primary condition is exactly the trigger
        # recorded for all four BUG-106 misfires.
        if pre_status["dirty"]:
            allow_apply = False
            safety_note = "primary-checkout-dirty"
    elif not pre_status["is_primary"] and not is_agent_worktree:
        # Neither a confirmed primary checkout nor a recognized agent
        # worktree marker -- unrecognized checkout shape. Fail safe.
        allow_apply = False
        safety_note = "unrecognized-checkout-shape"

    stale_hours = os.environ.get("GALD3R_JANITOR_STALE_HOURS", DEFAULT_STALE_HOURS)
    cmd = [
        *engine, "worktree", "janitor",
        "--repo-path", project_root,
        "--stale-hours", stale_hours,
        "--quiet",
    ]
    if allow_apply:
        cmd.append("--apply")
        if os.environ.get("GALD3R_JANITOR_REAP_PROCESSES") in ("1", "true", "True"):
            cmd.append("--reap-processes")

    context = "[worktree-janitor] skipped (unexpected error)"
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        context = (
            f"[worktree-janitor] {args.event_name}: exit={proc.returncode}"
        )
        if not allow_apply:
            context += f" (dry-run: {safety_note}, BUG-106 guard)"
    except Exception:  # noqa: BLE001 — never block the host session
        pass

    # Defense-in-depth: even when --apply was allowed, verify no
    # rescue-style commit landed directly on the primary checkout's HEAD.
    # If one did (engine misfire despite the pre-check above), revert it
    # immediately with a soft reset -- the working tree is preserved
    # exactly like the manual coordinator recovery already on record for
    # BUG-106; nothing is force-discarded.
    if (
        allow_apply
        and pre_status.get("ok")
        and pre_status.get("is_primary")
        and not is_agent_worktree
        and pre_status.get("head")
    ):
        _rc, new_head, _ = _git(["rev-parse", "HEAD"], project_root)
        if new_head and new_head != pre_status["head"]:
            _rc2, subject, _ = _git(["log", "-1", "--format=%s", new_head], project_root)
            _rc3, parent, _ = _git(["rev-parse", f"{new_head}^"], project_root)
            if subject.startswith(_RESCUE_COMMIT_PREFIX) and parent == pre_status["head"]:
                _git(["reset", "--soft", pre_status["head"]], project_root)
                context += (
                    f" (BUG-106: auto-reverted misfired rescue-commit {new_head[:8]})"
                )

    print(json.dumps({"continue": True, "additional_context": context}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
