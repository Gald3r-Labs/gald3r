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

Hooks must never crash or block the host session: any unexpected error is
swallowed and the hook exits 0.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

DEFAULT_STALE_HOURS = "2"


def _find_project_root() -> str:
    here = Path(__file__).resolve().parent
    for d in (here, *here.parents):
        if (d / ".gald3r").is_dir():
            return str(d)
    return str(Path.cwd())


def _resolve_engine_cmd(project_root: str):
    """Resolve the gald3r engine command prefix via the zero-IP resolver.

    Returns the command prefix (e.g. ``["gald3r"]``) or ``None`` when the
    resolver is not shipped (pre-T1642 install) or no engine can be found —
    in which case the hook no-ops gracefully, exactly like the old
    script-missing path.
    """
    resolver = Path(project_root) / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("gald3r_bin_janitor", str(resolver))
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.resolve_engine_cmd(Path(project_root))
    except Exception:
        return None


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

    stale_hours = os.environ.get("GALD3R_JANITOR_STALE_HOURS", DEFAULT_STALE_HOURS)
    cmd = [
        *engine, "worktree", "janitor",
        "--repo-path", project_root,
        "--stale-hours", stale_hours,
        "--apply", "--quiet",
    ]
    if os.environ.get("GALD3R_JANITOR_REAP_PROCESSES") in ("1", "true", "True"):
        cmd.append("--reap-processes")

    context = "[worktree-janitor] skipped (unexpected error)"
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        context = (
            f"[worktree-janitor] {args.event_name}: exit={proc.returncode}"
        )
    except Exception:  # noqa: BLE001 — never block the host session
        pass

    print(json.dumps({"continue": True, "additional_context": context}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
