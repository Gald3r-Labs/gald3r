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
    --coordinator-timeout-minutes
                          Per-coordinator hang timeout (BUG-181). A wedged coordinator
                          (deadlock / full stdout pipe / nested prompt) is killed (whole
                          process tree) after this long; the iteration is retried once,
                          then skipped — the loop never blocks forever. CLI flag >
                          GALD3R_GGO_COORDINATOR_TIMEOUT_MIN env var > 25 min default;
                          a value <= 0 disables the timeout.
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
import signal
import subprocess
import sys
import threading
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

# Per-coordinator hang timeout (BUG-181). A wedged coordinator (deadlock, full stdout
# pipe, nested permission prompt) must never block the loop forever. Resolution order:
# --coordinator-timeout-minutes CLI flag > GALD3R_GGO_COORDINATOR_TIMEOUT_MIN env var >
# this default. A value <= 0 disables the timeout (legacy "wait forever" behavior).
DEFAULT_COORDINATOR_TIMEOUT_MIN = 25

# Bounded timeout for the per-iteration inbox-intake subprocess (BUG-184). Intake is
# quick; this only guards against a wedged child. Failures are logged, never fatal.
INTAKE_TIMEOUT_SEC = 300


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


def _terminate_process_tree(proc: subprocess.Popen) -> None:
    """Best-effort kill of the coordinator process tree (parent + descendants).

    Order (BUG-181): psutil (cross-platform, walks children) if importable; else an
    OS process-group kill (the child is launched in its own group/session by
    invoke_coordinator); else a bare ``proc.kill()``. Every step is defensive — a
    partial kill must not raise.
    """
    if proc.poll() is not None:
        return
    # 1. psutil — most reliable; recursively terminate then kill any stragglers.
    try:
        import psutil  # type: ignore
        try:
            parent = psutil.Process(proc.pid)
        except psutil.NoSuchProcess:
            return
        procs = parent.children(recursive=True)
        procs.append(parent)
        for p in procs:
            try:
                p.terminate()
            except psutil.Error:
                pass
        _gone, alive = psutil.wait_procs(procs, timeout=10)
        for p in alive:
            try:
                p.kill()
            except psutil.Error:
                pass
        return
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 — psutil edge cases must not mask the fallback kill
        pass
    # 2. OS process-group kill (the group/session was created at launch time).
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True)
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        return
    except (OSError, ValueError, ProcessLookupError):
        pass
    # 3. Last resort — kill just the parent handle.
    try:
        proc.kill()
    except (OSError, ValueError):
        pass


def _split_coordinator_command(command):
    """Tokenize a coordinator command into a Popen argv list (BUG-193).

    Accepts either form:
      * a sequence (list/tuple) — used verbatim as argv. This is the robust, unambiguous
        way to pass an executable path that contains spaces, on any platform.
      * a string — tokenized into ``[exe, *args]``, quoting-aware on BOTH platforms so a
        quoted path with spaces collapses to a single argv element with its surrounding
        quotes stripped.

    On POSIX we use the standard ``shlex.split`` (backslash is an escape character, per the
    POSIX shell). On Windows we tokenize with backslash escaping DISABLED, because backslash
    is a path separator there (e.g. ``C:/Program Files/app.exe``): the old
    ``shlex.split(cmd, posix=False)`` kept the literal quote characters around a spaced path
    and the launch failed, while ``posix=True`` would have eaten the path backslashes.
    """
    if isinstance(command, (list, tuple)):
        return [str(arg) for arg in command]
    text = (command or "").strip()
    if not text:
        return []
    if os.name == "nt":
        lexer = shlex.shlex(text, posix=True)
        lexer.whitespace_split = True
        lexer.escape = ""  # backslash is a Windows path separator, not an escape char
        return list(lexer)
    return shlex.split(text, posix=True)


def invoke_coordinator(brief: str, coordinator_command, timeout_sec=None):
    """Invoke a fresh LLM session (blank context); brief goes on stdin (matches Invoke-Coordinator).

    CoordinatorCommand may be a string (split into exe + args, quoting-aware) or a
    pre-built argv sequence; the brief is piped in on stdin (BUG-193).
    Returns a ``(returncode, fatal_reason, timed_out)`` tuple:
      * ``fatal_reason`` — first matched FATAL_OUTPUT_SENTINELS substring seen in the
        coordinator's output, or ``None``. A non-None value tells the outer loop to stop
        the whole run (retrying an account-level failure like a spend cap only burns
        budget).
      * ``timed_out`` — True if the coordinator exceeded ``timeout_sec`` and its process
        tree was terminated (BUG-181). ``timeout_sec`` <= 0 / None means "wait forever".

    Output is drained CONTINUOUSLY on a reader thread (BUG-181): a full stdout pipe is a
    classic Windows deadlock, so we never block writing stdin while the child blocks
    writing stdout. A chatty-but-alive coordinator keeps streaming and only a genuinely
    wedged one trips the timeout. The child runs in its own process group/session so the
    whole tree can be signalled on timeout (and the conductor's own Ctrl-C is not
    forwarded into a mid-iteration coordinator).
    """
    parts = _split_coordinator_command(coordinator_command)
    if not parts:
        return 0, None, False
    # bufsize=1 (line-buffered) + per-line flush means the coordinator's work shows up
    # in the (redirected) terminal/log AS IT HAPPENS, not in one dump when it exits.
    popen_kwargs = dict(
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(parts, **popen_kwargs)

    fatal = {"reason": None}

    def _drain() -> None:
        # Continuously pump merged stdout/stderr so the pipe buffer never fills, and scan
        # each line for fatal account sentinels (spend cap / auth / credit).
        if proc.stdout is None:
            return
        try:
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                if fatal["reason"] is None:
                    low = line.lower()
                    for sentinel in FATAL_OUTPUT_SENTINELS:
                        if sentinel in low:
                            fatal["reason"] = sentinel
                            break
        except (OSError, ValueError):
            pass

    reader = threading.Thread(target=_drain, daemon=True)
    reader.start()

    if proc.stdin is not None:
        try:
            proc.stdin.write(brief)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            # Coordinator exited before consuming the brief (e.g. an instant auth/quota
            # failure). Not fatal to the conductor — the exit code + output sentinels
            # still drive the circuit breakers.
            pass

    timed_out = False
    wait_timeout = timeout_sec if (timeout_sec and timeout_sec > 0) else None
    try:
        proc.wait(timeout=wait_timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        log(f"coordinator exceeded {wait_timeout}s hang timeout — terminating its "
            f"process tree and moving on")
        _terminate_process_tree(proc)
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            pass
    reader.join(timeout=5)
    rc = proc.returncode if proc.returncode is not None else -1
    return rc, fatal["reason"], timed_out


def resolve_coordinator_timeout_min(cli_value):
    """Per-coordinator hang-timeout minutes: CLI flag > env var > default (BUG-181).

    A value <= 0 disables the timeout. Returns an int number of minutes.
    """
    if cli_value is not None:
        return cli_value
    env = os.environ.get("GALD3R_GGO_COORDINATOR_TIMEOUT_MIN")
    if env:
        try:
            return int(env)
        except ValueError:
            log(f"ignoring non-integer GALD3R_GGO_COORDINATOR_TIMEOUT_MIN={env!r}")
    return DEFAULT_COORDINATOR_TIMEOUT_MIN


def find_intake_script(project_root: str):
    """Locate hot_inbox_intake.py under the project's installed skill tree (BUG-184).

    The brief documents the Claude path; other IDE installs nest the same script under
    their own config dir, so probe the common ones and fall back to a single glob.
    Returns a Path, or None when no intake script is installed.
    """
    root = Path(project_root)
    rel = Path("skills") / "g-skl-tasks" / "scripts" / "hot_inbox_intake.py"
    primary = root / ".claude" / rel
    if primary.exists():
        return primary
    for ide in (".cursor", ".agents", ".gemini", ".windsurf", ".codex",
                ".opencode", ".kiro", ".roo"):
        cand = root / ide / rel
        if cand.exists():
            return cand
    for cand in root.glob(f"*/{rel.as_posix()}"):
        return cand
    return None


def run_inbox_intake(project_root: str, timeout_sec: int = INTAKE_TIMEOUT_SEC) -> None:
    """Absorb queued task/bug inbox drafts into live TASKS.md/BUGS.md (BUG-184).

    Runs the co-located intake script (the sole ID-assigning / housekeeping-commit
    authority for inbox drafts). Best-effort and fail-open: a missing script, non-zero
    exit, timeout, or launch error is logged and the loop continues — a flaky intake
    must never wedge the conductor.
    """
    script = find_intake_script(project_root)
    if script is None:
        log("inbox intake: hot_inbox_intake.py not found under project root — skipping")
        return
    cmd = [sys.executable, str(script), "-ProjectRoot", str(project_root), "-Quiet"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        log(f"inbox intake: timed out after {timeout_sec}s — skipping this iteration")
        return
    except OSError as exc:
        log(f"inbox intake: failed to launch ({exc}) — skipping this iteration")
        return
    out = (result.stdout or "").strip()
    for ln in out.splitlines():
        log(f"inbox intake: {ln}")
    if result.returncode == 0:
        if not out:
            log("inbox intake: complete")
    else:
        err = (result.stderr or "").strip()
        tail = f" — {err.splitlines()[-1]}" if err else ""
        log(f"inbox intake: non-zero exit {result.returncode}{tail}")


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
    parser.add_argument("--coordinator-timeout-minutes", type=int, default=None,
                        dest="coordinator_timeout_minutes",
                        help="Per-coordinator hang timeout in minutes (BUG-181). A wedged "
                             "coordinator is killed (process tree) after this long; the "
                             "iteration is retried once, then skipped — never blocks "
                             "forever. Overridable via GALD3R_GGO_COORDINATOR_TIMEOUT_MIN; "
                             "<=0 disables. Default: 25.")
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

    # -- Per-coordinator hang timeout (BUG-181): CLI > env > default -------------
    coordinator_timeout_min = resolve_coordinator_timeout_min(
        args.coordinator_timeout_minutes)
    coordinator_timeout_sec = (coordinator_timeout_min * 60
                               if coordinator_timeout_min and coordinator_timeout_min > 0
                               else None)
    if coordinator_timeout_sec:
        log(f"per-coordinator hang timeout: {coordinator_timeout_min} min "
            f"({coordinator_timeout_sec}s)")
    else:
        log("per-coordinator hang timeout: DISABLED (<=0)")

    start_time = datetime.now()
    last_heartbeat = start_time
    exit_reason = ""
    consecutive_failures = 0
    timeout_retry_iter = None  # iter value already granted one hang-timeout retry

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

        # 3a. Hot-inbox intake at the START of EACH iteration (BUG-184). Absorb any
        # task/bug drafts queued mid-run BEFORE briefing the coordinator, so they are
        # eligible THIS iteration instead of waiting for a future run. Because this lives
        # inside the loop body it also fires on the first iteration of a --resume re-entry.
        # Skipped under --dry-run, which must stay side-effect-free (intake writes files
        # and creates a housekeeping commit).
        if not args.dry_run:
            run_inbox_intake(project_root)

        brief = render_brief(state, brief_tpl, project_root)

        if args.dry_run:
            log(f"DRY-RUN brief for iter {cur_iter} (budget {budget}) -----")
            print(brief, flush=True)
        else:
            log(f"iter {cur_iter} / budget {budget} -> invoking fresh coordinator "
                f"(streaming its output below)")
            code, fatal, timed_out = invoke_coordinator(
                brief, args.coordinator_command, coordinator_timeout_sec)
            log(f"iter {cur_iter} coordinator returned exit code {code}"
                + (" (timed out)" if timed_out
                   else ("" if code == 0 else " (non-zero)")))

            if timed_out:
                # Circuit breaker 0 (BUG-181): a wedged coordinator was killed. Record a
                # drift warning + per-repo blocker in the marker (write_state refreshes
                # updated_at), count it toward the consecutive-failure breaker, then retry
                # this iteration ONCE before skipping forward — never block forever.
                consecutive_failures += 1
                warn = (f"iter {cur_iter}: coordinator hang timeout "
                        f"({coordinator_timeout_min} min) — process tree terminated")
                to_state = read_state(state_file) or state
                dw = get_prop(to_state, "drift_warnings", [])
                if not isinstance(dw, list):
                    dw = []
                dw.append(warn)
                to_state["drift_warnings"] = dw
                prb = get_prop(to_state, "per_repo_blockers", {})
                if not isinstance(prb, dict):
                    prb = {}
                prb["__conductor_hang__"] = warn
                to_state["per_repo_blockers"] = prb
                write_state(to_state, state_file)

                if consecutive_failures >= args.max_consecutive_failures:
                    exit_reason = (f"{consecutive_failures} consecutive coordinator "
                                   f"failures (last: hang timeout) — circuit breaker "
                                   f"tripped")
                    log(exit_reason + " — halting run.")
                    stop_state = read_state(state_file) or state
                    stop_state["authorized_hard_stop"] = exit_reason
                    write_state(stop_state, state_file)
                    break
                if timeout_retry_iter != cur_iter:
                    timeout_retry_iter = cur_iter
                    log(f"iter {cur_iter} hang timeout — retrying once (no budget spent) "
                        f"before skipping forward")
                    continue
                log(f"iter {cur_iter} hang timeout again after retry — skipping to the "
                    f"next iteration")
                # fall through to step 4/5 to advance iter/budget (skip this wedged unit)
            else:
                # Circuit breaker 1: fatal account-level signal (spend cap / auth / credit).
                # Retrying fails identically and only burns budget, so stop the whole run
                # NOW and record WHY (so the run doesn't silently grind to budget=0).
                if fatal:
                    exit_reason = f"coordinator fatal signal: '{fatal}'"
                    log(f"FATAL coordinator signal '{fatal}' detected — halting run "
                        f"(retrying would only burn budget). Resolve the account issue "
                        f"and relaunch.")
                    stop_state = read_state(state_file) or state
                    stop_state["authorized_hard_stop"] = exit_reason
                    write_state(stop_state, state_file)
                    break

                # Circuit breaker 2: N consecutive non-zero exits (transient failures).
                if code != 0:
                    consecutive_failures += 1
                    if consecutive_failures >= args.max_consecutive_failures:
                        exit_reason = (f"{consecutive_failures} consecutive coordinator "
                                       f"failures (last exit {code}) — circuit breaker "
                                       f"tripped")
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
