#!/usr/bin/env python3
"""Python port of test_ggo_scheduled_reset_t635.ps1 (T1601, PS1-KILL epic T667).

T635 behavioral test - g-hk-ggo-stop-detect.py scheduled_context_reset (Rolling Amnesia).
Proves: an authorized scheduled reset RE-INVOKES with --resume (non-terminal), consumes the
marker, bumps resets_done, keeps the run active; budget exhaustion turns a reset into a
terminal exit; a genuine hard stop still terminates; an unauthorized stop still re-invokes.

# BUG-128 (migrated from donor BUG-199) kind=code: g-hk-ggo-stop-detect.py was missing
# the scheduled_context_reset special case (it fell into the generic hard-stop branch
# instead) — see .gald3r/bugs/open/bug128_g-hk-ggo-stop-detect-py-missing-schedule.md.
# Fixed: the hook now consumes the marker and re-invokes with --resume when budget
# remains. This fixture is not wired into the L1/L2/L3 test manifest; run it directly.
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

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional


def _bootstrap_engine_utils() -> bool:
    """Make gald3r.utils importable via the installed package.

    T274 (P5-E blocker): the pre-retirement ".gald3r_sys/engine/src" fallback
    walk is removed -- ".gald3r_sys/" is actively purged from every project
    by the deploy pipeline (T335) and never exists in a fresh install, so
    that branch was permanently dead code, not a real fallback.
    """
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        return False


_HAS_UTILS = _bootstrap_engine_utils()


def _color_enabled() -> bool:
    if _HAS_UTILS:
        from gald3r.utils import console
        return console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "gray": "90"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


def find_repo_root(start: Path) -> Path:
    """Walk up from ``start`` to the nearest ancestor containing .gald3r."""
    d = start
    while True:
        if (d / ".gald3r").is_dir():
            return d
        parent = d.parent
        if parent == d:
            return start
        d = parent


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(SCRIPT_DIR)


def locate_hook() -> Optional[Path]:
    for candidate in (
        # Tracked source of truth (T177) — prefer this so the test always
        # exercises the file that is actually fixed/reviewed/committed, even
        # in a fresh checkout/worktree where the gitignored, regenerated
        # per-platform copies below have not been synced yet.
        REPO_ROOT / "src" / "gald3r_core" / "platform" / "pipeline"
        / "neutral_source" / "hooks" / "g-hk-ggo-stop-detect.py",
        REPO_ROOT / ".claude" / "hooks" / "g-hk-ggo-stop-detect.py",
        REPO_ROOT / ".cursor" / "hooks" / "g-hk-ggo-stop-detect.py",
    ):
        if candidate.is_file():
            return candidate
    return None


_fails = 0


def assert_(cond: bool, msg: str) -> None:
    global _fails
    if cond:
        cprint(f"  [PASS] {msg}", "green")
    else:
        cprint(f"  [FAIL] {msg}", "red")
        _fails += 1


def new_root(state: dict) -> Path:
    r = Path(tempfile.gettempdir()) / f"t635_{uuid.uuid4().hex[:8]}"
    (r / ".gald3r" / "logs").mkdir(parents=True, exist_ok=True)
    (r / ".gald3r" / "logs" / "ggo_run_state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    return r


def invoke_hook(hook: Path, root: Path, session_id: str) -> dict:
    payload = json.dumps({"session_id": session_id})
    # BUG-337: explicitly stamp GALD3R_GGO_COORDINATOR=1 rather than relying on
    # whatever the ambient shell happens to have set. g-hk-ggo-stop-detect.py's
    # Case 0.5 (BUG-217) allow-exits immediately when this var is unset/falsy,
    # which otherwise short-circuits the Rolling Amnesia (BUG-128/BUG-107) logic
    # this test exists to exercise -- making the suite pass or fail based on
    # ambient environment instead of the hook's actual behavior.
    env = dict(os.environ, GALD3R_GGO_COORDINATOR="1")
    proc = subprocess.run(
        [sys.executable, str(hook), "-ProjectRoot", str(root)],
        input=payload, capture_output=True, text=True, env=env,
    )
    return json.loads(proc.stdout)


def main() -> int:
    hook = locate_hook()
    if hook is None:
        cprint(f"FAIL: stop hook not found under {REPO_ROOT}", "red")
        return 1

    cprint("\n=== T1: scheduled_context_reset with budget => RE-INVOKE (--resume) ===", "cyan")
    root = new_root({
        "active": True, "platform": "claude", "session_id": "sess-1", "iter": 3,
        "budget_remaining": 10, "authorized_hard_stop": "scheduled_context_reset",
        "reinvoke_count": 0, "resets_done": 0,
    })
    res = invoke_hook(hook, root, "sess-1")
    assert_(res.get("decision") == "block", "decision=block (re-invoke, not allow-exit)")
    assert_(res.get("continue") is False, "continue=false (Cursor re-invoke contract)")
    assert_("--resume" in (res.get("reason") or ""), "reason instructs --resume")
    assert_("Rolling Amnesia" in (res.get("reason") or ""), "reason names Rolling Amnesia")
    state_path = root / ".gald3r" / "logs" / "ggo_run_state.json"
    # BUG-199: a non-reinvoke hook clears/deletes the marker entirely, so guard the read
    # rather than crash the suite over an already-flagged pre-existing gap.
    st = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    assert_(st.get("authorized_hard_stop") == "", "marker consumed (authorized_hard_stop cleared)")
    assert_(int(st.get("resets_done", 0)) == 1, "resets_done incremented to 1")
    assert_(bool(st.get("active")) is True, "run still active (non-terminal)")
    shutil.rmtree(root, ignore_errors=True)

    cprint("\n=== T2: scheduled_context_reset with budget=0 => TERMINAL exit ===", "cyan")
    root = new_root({
        "active": True, "platform": "claude", "session_id": "sess-2", "iter": 12,
        "budget_remaining": 0, "authorized_hard_stop": "scheduled_context_reset",
        "reinvoke_count": 0, "resets_done": 3,
    })
    res = invoke_hook(hook, root, "sess-2")
    assert_(res.get("continue") is True, "continue=true (terminal exit at budget exhaustion)")
    assert_(res.get("decision") is None or res.get("decision") != "block",
            "not a block decision")
    assert_(not (root / ".gald3r" / "logs" / "ggo_run_state.json").exists(),
            "marker cleared on terminal exit")
    shutil.rmtree(root, ignore_errors=True)

    cprint("\n=== T3: genuine terminal hard stop still TERMINATES (regression) ===", "cyan")
    root = new_root({
        "active": True, "platform": "claude", "session_id": "sess-3", "iter": 5,
        "budget_remaining": 7, "authorized_hard_stop": "No runnable work | clean halt",
        "reinvoke_count": 0, "resets_done": 0,
    })
    res = invoke_hook(hook, root, "sess-3")
    assert_(res.get("continue") is True, "continue=true (genuine hard stop allowed through)")
    assert_(not (root / ".gald3r" / "logs" / "ggo_run_state.json").exists(), "marker cleared")
    shutil.rmtree(root, ignore_errors=True)

    cprint("\n=== T4: unauthorized mid-loop stop still RE-INVOKES (BUG-107 regression) ===", "cyan")
    root = new_root({
        "active": True, "platform": "claude", "session_id": "sess-4", "iter": 2,
        "budget_remaining": 9, "authorized_hard_stop": "", "reinvoke_count": 0,
        "resets_done": 0,
    })
    res = invoke_hook(hook, root, "sess-4")
    assert_(res.get("decision") == "block", "decision=block (unauthorized-stop re-invoke intact)")
    assert_("BUG-107" in (res.get("reason") or ""), "reason cites BUG-107 contract")
    shutil.rmtree(root, ignore_errors=True)

    cprint("\n=== T5: stuck reset at re-invoke ceiling => TERMINAL exit (BUG-128) ===", "cyan")
    # A coordinator that re-declares scheduled_context_reset without making real
    # progress must NOT spin forever: once reinvoke_count reaches the shared
    # ceiling (min(budget_remaining, 25)), a reset degrades to a terminal
    # allow-exit like any other stop -- the coordinator-independent backstop.
    root = new_root({
        "active": True, "platform": "claude", "session_id": "sess-5", "iter": 4,
        "budget_remaining": 5, "authorized_hard_stop": "scheduled_context_reset",
        "reinvoke_count": 5, "resets_done": 5,
    })
    res = invoke_hook(hook, root, "sess-5")
    assert_(res.get("continue") is True,
            "continue=true (reset degraded to terminal at ceiling)")
    assert_(res.get("decision") is None or res.get("decision") != "block",
            "not a block decision (no unbounded reset re-invoke)")
    assert_(not (root / ".gald3r" / "logs" / "ggo_run_state.json").exists(),
            "marker cleared on ceiling-terminal exit")
    shutil.rmtree(root, ignore_errors=True)

    print("")
    if _fails == 0:
        cprint("ALL T635 HOOK TESTS PASSED", "green")
        return 0
    cprint(f"{_fails} ASSERTION(S) FAILED", "red")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
