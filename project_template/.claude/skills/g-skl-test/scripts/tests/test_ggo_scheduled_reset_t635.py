#!/usr/bin/env python3
"""Python port of test_ggo_scheduled_reset_t635.ps1 (T1601, PS1-KILL epic T667).

T635 behavioral test - g-hk-ggo-stop-detect.py scheduled_context_reset (Rolling Amnesia).
Proves: an authorized scheduled reset RE-INVOKES with --resume (non-terminal), consumes the
marker, bumps resets_done, keeps the run active; budget exhaustion turns a reset into a
terminal exit; a genuine hard stop still terminates; an unauthorized stop still re-invokes.

# BUG[BUG-199] kind=code: g-hk-ggo-stop-detect.py has no scheduled_context_reset special
# case (falls into the generic hard-stop branch instead) — see .gald3r/bugs/bug199_*.md.
# This fixture preserves the documented Rolling Amnesia contract from the original .ps1
# and is expected to fail T1/T4 until BUG-199 is fixed; it is not wired into the L1/L2/L3
# test manifest, so this pre-existing gap does not block the suite.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

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
    """Make gald3r.utils importable: installed package, else walk up to .gald3r_sys/engine/src."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        cand = parent / ".gald3r_sys" / "engine" / "src"
        if (cand / "gald3r" / "utils" / "__init__.py").is_file():
            sys.path.insert(0, str(cand))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
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
    proc = subprocess.run(
        [sys.executable, str(hook), "-ProjectRoot", str(root)],
        input=payload, capture_output=True, text=True,
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

    print("")
    if _fails == 0:
        cprint("ALL T635 HOOK TESTS PASSED", "green")
        return 0
    cprint(f"{_fails} ASSERTION(S) FAILED", "red")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
