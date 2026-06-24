#!/usr/bin/env python3
# @subsystems: AGENT_ORCHESTRATION
"""g-go-go Stateless Orchestrator — deterministic Python outer loop (T630/T669).

The clean architectural fix for coordinator context accumulation (BUG-107 class).
Instead of one long-lived LLM coordinator that accumulates context across iterations,
this script is a deterministic Kubernetes-controller-style reconciler::

    while budget_remaining > 0:
        read ggo_run_state.json + TASKS.md from disk   (never cache across iters)
        invoke a FRESH coordinator LLM session (blank context) for ONE iteration
        re-read the state the coordinator wrote
        outer loop owns: budget counting, hard-stop detection, heartbeat
        decrement budget; loop

State lives on disk (TASKS.md + ggo_run_state.json), NOT in the controller's memory.
The coordinator is fully briefable from disk alone (ggo_coordinator_brief_template.txt),
so each invocation starts with a bounded context window by construction — N is never
throttled for context reasons.

This is the --stateless backend for @g-go-go. The legacy single-session LLM-driven loop
is preserved under @g-go-go --legacy (and is the default until --stateless is requested).

Ported from ggo_outer_loop.ps1 (T669, PS1-KILL epic T667). stdlib-only; invokeable via
`uv run python ggo_outer_loop.py ...` or plain `python ggo_outer_loop.py ...` — no
PowerShell dependency.

Parameters (argparse, mirroring the original PowerShell params):
    --project-root        Repo root (defaults to the nearest .gald3r ancestor of this script).
    --budget              Max iterations for a fresh run (ignored when resuming active state).
    --reset-every         Recorded into state for the coordinator's Rolling Amnesia cadence
                          (T635); the stateless loop already resets context every iteration,
                          so this is informational here.
    --heartbeat-minutes   Wall-clock minutes between heartbeat lines.
    --coordinator-command The CLI invoked per iteration. Default: claude headless. The generated
                          brief is passed on stdin. Override for other agents (e.g.
                          'cursor-agent') or for tests (a stub script).
    --dry-run             Do NOT invoke a coordinator. Generate + print the brief, then let the
                          outer loop advance budget/iter itself. Used to inspect briefs and to
                          unit-test the deterministic loop.
    --resume              Continue an existing active run from its on-disk state instead of
                          re-initializing.
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# -- Explicit UTF-8 at startup (no CP1252 ambiguity, AC2) -----------------------
for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        # Older Python or already-wrapped stream — safe to ignore; the I/O below
        # uses explicit encoding="utf-8" on every file read/write regardless.
        pass


# Substrings in coordinator output that mean "stop the whole run NOW" — these are
# deterministic, account-level failures where every retry fails identically and only
# burns the iteration budget (and hides the real reason the run stopped). Matched
# case-insensitively against the coordinator's merged stdout/stderr. Claude is the
# default coordinator model, so its quota/billing/auth messages lead the list.
# (Learned 2026-06-24: a spend-limit cap let the loop grind 296 no-op iters to budget=0.)
FATAL_OUTPUT_SENTINELS = (
    "hit your monthly spend limit",
    "monthly spend limit",
    "credit balance is too low",
    "insufficient credit",
    "invalid api key",
    "invalid x-api-key",
    "authentication_error",
    "authentication error",
    "unauthorized",
)


def now_iso() -> str:
    """UTC timestamp, e.g. 2026-06-22T09:45:00Z (matches the PS Now-Iso helper)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    """Timestamped, line-flushed progress line.

    Every outer-loop event goes through here so a launch that redirects stdout to a
    file (e.g. `.gald3r/logs/ggo_outer_loop_stdout.log`) produces a live, tailable
    pulse — `Get-Content <log> -Wait` shows progress the moment it happens instead of
    only when a coordinator finishes an iteration. flush=True defeats block buffering.
    """
    print(f"[outer-loop {now_iso()}] {msg}", flush=True)


def read_state(state_file: Path):
    """Read on-disk state as a dict, or None if missing/unparseable (matches Read-State)."""
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_state(state: dict, state_file: Path) -> None:
    """Stamp updated_at and persist state as UTF-8 JSON (matches Write-State)."""
    state["updated_at"] = now_iso()
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def new_state(budget: int, reset_every: int) -> dict:
    """Fresh stateless-run state object (matches New-State)."""
    return {
        "active": True,
        "platform": "claude",
        "mode": "stateless",
        "iter": 0,
        "budget_remaining": budget,
        "reset_every": reset_every,
        "resets_done": 0,
        "authorized_hard_stop": "",
        "reinvoke_count": 0,
        "coordinator_notes": [],
        "per_repo_blockers": {},
        "deferred_task_reasons": {},
        "drift_warnings": [],
        "completed_iterations": [],
        "updated_at": now_iso(),
    }


def get_prop(obj, name, default):
    """Get a property with a default, treating None as absent (matches Get-Prop)."""
    if isinstance(obj, dict):
        val = obj.get(name)
        if val is not None:
            return val
    return default


def _join_text(value, sep: str) -> str:
    """Join a list with sep; pass through a scalar as its string form."""
    if isinstance(value, list):
        return sep.join(str(v) for v in value)
    return str(value)


def render_brief(state: dict, brief_tpl: Path, project_root: str) -> str:
    """Render the coordinator brief from disk state (matches Render-Brief)."""
    if brief_tpl.exists():
        tpl = brief_tpl.read_text(encoding="utf-8")
    else:
        tpl = ("Run one g-go-go iteration from disk state. "
               "iter={{ITER}} budget={{BUDGET_REMAINING}}")

    ci = get_prop(state, "completed_iterations", [])
    if isinstance(ci, list) and len(ci) > 0:
        ci_text = "\n".join(json.dumps(item, separators=(",", ":")) for item in ci)
    else:
        ci_text = "(none yet)"

    repl = {
        "{{ITER}}": str(get_prop(state, "iter", 0)),
        "{{BUDGET_REMAINING}}": str(get_prop(state, "budget_remaining", 0)),
        "{{RESETS_DONE}}": str(get_prop(state, "resets_done", 0)),
        "{{PROJECT_ROOT}}": project_root,
        "{{COMPLETED_ITERATIONS}}": ci_text,
        "{{COORDINATOR_NOTES}}": _join_text(get_prop(state, "coordinator_notes", []), "; "),
        "{{PER_REPO_BLOCKERS}}": json.dumps(
            get_prop(state, "per_repo_blockers", {}), separators=(",", ":")),
        "{{DEFERRED_TASK_REASONS}}": json.dumps(
            get_prop(state, "deferred_task_reasons", {}), separators=(",", ":")),
        "{{DRIFT_WARNINGS}}": _join_text(get_prop(state, "drift_warnings", []), "; "),
    }
    for key, value in repl.items():
        tpl = tpl.replace(key, value)
    return tpl


def invoke_coordinator(brief: str, coordinator_command: str):
    """Invoke a fresh LLM session (blank context); brief goes on stdin (matches Invoke-Coordinator).

    CoordinatorCommand is split into exe + args; the brief is piped in on stdin.
    Returns a ``(returncode, fatal_reason)`` tuple — ``fatal_reason`` is the first
    matched FATAL_OUTPUT_SENTINELS substring seen in the coordinator's output, or
    ``None``. A non-None fatal_reason tells the outer loop to stop the whole run
    (retrying an account-level failure like a spend cap only burns budget).
    """
    parts = shlex.split(coordinator_command.strip(), posix=(os.name != "nt"))
    if not parts:
        return 0, None
    # Stream the coordinator's output line-by-line instead of inheriting+buffering it.
    # bufsize=1 (line-buffered) + per-line flush means the coordinator's work shows up
    # in the (redirected) terminal/log AS IT HAPPENS, not in one dump when it exits.
    proc = subprocess.Popen(
        parts,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    fatal_reason = None
    if proc.stdin is not None:
        try:
            proc.stdin.write(brief)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            # Coordinator exited before consuming the brief (e.g. an instant auth/quota
            # failure). Not fatal to the conductor — the exit code + output sentinels below
            # still drive the circuit breakers.
            pass
    if proc.stdout is not None:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if fatal_reason is None:
                low = line.lower()
                for sentinel in FATAL_OUTPUT_SENTINELS:
                    if sentinel in low:
                        fatal_reason = sentinel
                        break
    proc.wait()
    return proc.returncode, fatal_reason


def locate_project_root(explicit: str, script_dir: Path) -> str:
    """Resolve repo root: explicit, else nearest .gald3r ancestor, else cwd (matches PS logic)."""
    if explicit:
        return explicit
    cur = script_dir
    while cur and not (cur / ".gald3r").exists():
        parent = cur.parent
        if parent == cur:
            cur = None
            break
        cur = parent
    return str(cur) if cur else str(Path.cwd())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="g-go-go Stateless Orchestrator — deterministic Python outer loop (T630).")
    parser.add_argument("--project-root", default="",
                        help="Repo root (defaults to nearest .gald3r ancestor of this script).")
    parser.add_argument("--budget", type=int, default=12,
                        help="Max iterations for a fresh run (ignored when resuming).")
    parser.add_argument("--reset-every", type=int, default=3,
                        help="Recorded into state for the Rolling Amnesia cadence (informational).")
    parser.add_argument("--heartbeat-minutes", type=int, default=30,
                        help="Wall-clock minutes between heartbeat lines.")
    parser.add_argument("--max-consecutive-failures", type=int, default=3,
                        help="Stop the run after this many back-to-back non-zero coordinator "
                             "exits (circuit breaker). A fatal output signal (spend cap / auth / "
                             "credit) stops immediately regardless of this count.")
    parser.add_argument("--coordinator-command",
                        default="claude --dangerously-skip-permissions -p",
                        help="CLI invoked per iteration; brief is passed on stdin.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do NOT invoke a coordinator; print the brief and advance the loop.")
    parser.add_argument("--resume", action="store_true",
                        help="Continue an existing active run from on-disk state.")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    project_root = locate_project_root(args.project_root, script_dir)

    logs_dir = Path(project_root) / ".gald3r" / "logs"
    state_file = logs_dir / "ggo_run_state.json"
    tasks_file = Path(project_root) / ".gald3r" / "TASKS.md"
    brief_tpl = script_dir / "ggo_coordinator_brief_template.txt"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # -- Resolve starting state -------------------------------------------------
    state = read_state(state_file)
    if args.resume and state and get_prop(state, "active", False):
        log(f"Resuming active run at iter {get_prop(state, 'iter', 0)}, "
            f"budget {get_prop(state, 'budget_remaining', 0)}")
    else:
        state = new_state(args.budget, args.reset_every)
        write_state(state, state_file)
        log(f"Fresh stateless run: budget {args.budget}, reset_every {args.reset_every}")

    start_time = datetime.now()
    last_heartbeat = start_time
    exit_reason = ""
    consecutive_failures = 0

    while True:
        # 1. Read state FRESH from disk every iteration (never cache across iterations).
        state = read_state(state_file)
        if not state:
            exit_reason = "state-marker-missing"
            break

        cur_iter = int(get_prop(state, "iter", 0))
        budget = int(get_prop(state, "budget_remaining", 0))
        hard = str(get_prop(state, "authorized_hard_stop", ""))

        # 2. Hard-stop detection (outer loop owns it, NOT the LLM).
        if len(hard.strip()) > 0:
            exit_reason = f"authorized_hard_stop: {hard}"
            break
        if budget <= 0:
            exit_reason = "budget exhausted"
            break

        # 3. Brief the fresh coordinator entirely from disk state.
        if not tasks_file.exists():
            exit_reason = "TASKS.md missing"
            break
        brief = render_brief(state, brief_tpl, project_root)

        if args.dry_run:
            log(f"DRY-RUN brief for iter {cur_iter} (budget {budget}) -----")
            print(brief, flush=True)
        else:
            log(f"iter {cur_iter} / budget {budget} -> invoking fresh coordinator "
                f"(streaming its output below)")
            code, fatal = invoke_coordinator(brief, args.coordinator_command)
            log(f"iter {cur_iter} coordinator returned exit code {code}"
                + ("" if code == 0 else " (non-zero)"))

            # Circuit breaker 1: fatal account-level signal (spend cap / auth / credit).
            # Retrying fails identically and only burns budget, so stop the whole run NOW
            # and record WHY (so the run doesn't silently grind to budget=0 hiding the cause).
            if fatal:
                exit_reason = f"coordinator fatal signal: '{fatal}'"
                log(f"FATAL coordinator signal '{fatal}' detected — halting run "
                    f"(retrying would only burn budget). Resolve the account issue and relaunch.")
                stop_state = read_state(state_file) or state
                stop_state["authorized_hard_stop"] = exit_reason
                write_state(stop_state, state_file)
                break

            # Circuit breaker 2: N consecutive non-zero exits (transient/unknown failures).
            if code != 0:
                consecutive_failures += 1
                if consecutive_failures >= args.max_consecutive_failures:
                    exit_reason = (f"{consecutive_failures} consecutive coordinator failures "
                                   f"(last exit {code}) — circuit breaker tripped")
                    log(exit_reason + " — halting run.")
                    stop_state = read_state(state_file) or state
                    stop_state["authorized_hard_stop"] = exit_reason
                    write_state(stop_state, state_file)
                    break
                log(f"consecutive coordinator failures: {consecutive_failures}"
                    f"/{args.max_consecutive_failures}")
            else:
                consecutive_failures = 0

        # 4. Re-read the state the coordinator wrote (stash/queue updates, maybe a hard stop).
        state = read_state(state_file)
        if not state:
            state = new_state(0, args.reset_every)  # defensive: coordinator deleted it

        # 5. Outer loop owns budget + iteration counters (deterministic, not the LLM).
        state["iter"] = int(get_prop(state, "iter", cur_iter)) + 1
        state["budget_remaining"] = int(get_prop(state, "budget_remaining", budget)) - 1
        write_state(state, state_file)
        log(f"iter advanced -> {state['iter']} / budget {state['budget_remaining']} "
            f"(marker stamped {state['updated_at']})")

        # 6. Heartbeat.
        now = datetime.now()
        if (now - last_heartbeat).total_seconds() / 60.0 >= args.heartbeat_minutes:
            elapsed = now - start_time
            total_min = int(elapsed.total_seconds() // 60)
            hh, mm = divmod(total_min, 60)
            log(f"heartbeat — iter {state['iter']} / budget {state['budget_remaining']} "
                f"— elapsed {hh:02d}:{mm:02d}")
            last_heartbeat = now

    # -- Terminal: deactivate marker + summary ----------------------------------
    final = read_state(state_file)
    if final:
        final["active"] = False
        write_state(final, state_file)
    log(f"STATELESS RUN COMPLETE — {exit_reason}")
    log(f"iterations executed: {get_prop(final, 'iter', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
