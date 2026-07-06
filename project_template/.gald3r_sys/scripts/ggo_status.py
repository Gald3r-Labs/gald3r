#!/usr/bin/env python3
# @subsystems: AGENT_ORCHESTRATION
"""g-go-status — one-shot ALIVE / IDLE-WAIT / STALLED indicator for a g-go-go run (T1585).

When `@g-go-go` runs as a (detached or in-session) conductor there is no glanceable
signal that it is alive and making progress: the launcher session may show a red
"Stop hook error" (the BUG-107 keep-alive, which *looks* like a failure), so a user
staring at the terminal cannot tell a healthy run from a wedged one without manually
running `git log` and probing PIDs. This reader collapses those manual checks into a
single verdict.

It is strictly READ-ONLY. It reads the run-state marker
(`.gald3r/logs/ggo_run_state.json`, reliably refreshed per-iteration after the
BUG-181/182 conductor fixes) and the last git commit, derives "seconds since last
progress", and prints a clear **ALIVE / IDLE-WAIT / STALLED** verdict. It never writes
any `.gald3r/` state, never touches the marker, and never commits.

Progress is the MOST RECENT of two independent signals:
  * the marker's `updated_at` (the conductor stamps this every iteration), and
  * the last git commit time (a healthy iteration produces commits).
Taking the min age of the two means a long single iteration that is committing work is
still seen as ALIVE even while the marker sits between stamps, and a frozen marker with
no commits is correctly seen as STALLED.

Verdict thresholds are the module constants below (`ALIVE_THRESHOLD_SEC`,
`STALLED_THRESHOLD_SEC`). The middle band is IDLE-WAIT — the "healthy but waiting on the
model" state (API I/O wait: 0% CPU but progressing) that the task explicitly wants
distinguished from a true wedge.

Usage:
    python ggo_status.py                 # status of the run rooted at the nearest .gald3r
    python ggo_status.py --project-root <dir>
    python ggo_status.py --json          # machine-readable (mirrors other --json commands)

`--watch` (a refreshing heartbeat view) is a documented follow-up (T1585 option 2), NOT
implemented here — this is the bounded one-shot deliverable (option 1).

stdlib-only; no PowerShell dependency; invokeable via `python ggo_status.py` or
`uv run python ggo_status.py`.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# -- Explicit UTF-8 at startup (no CP1252 ambiguity) ----------------------------
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass


# -- Verdict thresholds (seconds) -----------------------------------------------
# Progress age (the MIN of marker-age and last-commit-age) maps to a verdict:
#   age <= ALIVE_THRESHOLD_SEC                     -> ALIVE
#   ALIVE_THRESHOLD_SEC < age <= STALLED_THRESHOLD -> IDLE-WAIT (healthy, waiting on model)
#   age >  STALLED_THRESHOLD_SEC                   -> STALLED (likely wedged)
#
# Rationale for the defaults: the conductor's per-coordinator hang timeout defaults to
# 25 min (a wedged coordinator is killed and the marker re-stamped at ~that point), and a
# single Phase 1 + Phase 2 iteration legitimately runs many minutes while waiting on the
# model. So a 10-min ALIVE window catches active progress, the 10-30 min band is the
# normal "long iteration / model I/O wait" zone (IDLE-WAIT, not a wedge), and only past
# ~30 min with NO new commits do we call it STALLED.
ALIVE_THRESHOLD_SEC = 600      # 10 minutes — recent progress => ALIVE
STALLED_THRESHOLD_SEC = 1800   # 30 minutes — beyond this with no commit => STALLED

VERDICT_ALIVE = "ALIVE"
VERDICT_IDLE_WAIT = "IDLE-WAIT"
VERDICT_STALLED = "STALLED"
VERDICT_INACTIVE = "INACTIVE"      # marker exists but active:false (run finished)
VERDICT_STOPPED = "STOPPED"        # authorized_hard_stop populated
VERDICT_NO_RUN = "NO-ACTIVE-RUN"   # no marker at all

MARKER_RELPATH = Path(".gald3r") / "logs" / "ggo_run_state.json"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(value):
    """Parse an ISO-8601 timestamp (e.g. '2026-06-25T21:33:53Z') to an aware datetime.

    Returns None for empty / unparseable input — the caller treats that as "unknown age".
    Tolerant of the trailing 'Z' (mapped to +00:00) and of fractional/offset variants.
    """
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    # Fast path: the conductor's exact format.
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    # Tolerant path: fromisoformat (Z -> +00:00; assume UTC if naive).
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def age_seconds(dt):
    """Whole seconds between dt and now (UTC); None if dt is None; never negative."""
    if dt is None:
        return None
    delta = (now_utc() - dt).total_seconds()
    return int(delta) if delta > 0 else 0


def iso_utc(dt):
    """Format an aware datetime as canonical UTC ISO (e.g. '2026-06-25T21:31:57Z').

    Converts to UTC first — `git --format=%cI` emits a LOCAL-offset timestamp, so the
    raw wall-clock numbers must be normalized before stamping the 'Z' suffix.
    """
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_age(seconds):
    """Human-friendly age, e.g. '42s ago', '7m ago', '2h 13m ago', or 'unknown'."""
    if seconds is None:
        return "unknown"
    if seconds < 60:
        return f"{seconds}s ago"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec}s ago"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m ago"


def locate_project_root(explicit, start: Path) -> Path:
    """Resolve repo root: explicit, else nearest .gald3r ancestor, else cwd.

    Mirrors the engine `gald3r autopilot loop` (A3 / T1660) project-root
    resolution so the reader and the conductor agree on which run they target.
    """
    if explicit:
        return Path(explicit).resolve()
    cur = start
    while cur and not (cur / ".gald3r").exists():
        parent = cur.parent
        if parent == cur:
            cur = None
            break
        cur = parent
    return cur.resolve() if cur else Path.cwd().resolve()


def read_marker(state_file: Path):
    """Read the run-state marker as a dict; None if missing, ('__error__', msg) if unparseable."""
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ("__error__", str(exc))


def probe_conductor(marker: dict):
    """Best-effort liveness of the conductor process. Never hard-depends on a PID.

    Returns (status_str, pid_or_None) where status_str is one of:
      * 'alive'         — a recorded PID is confirmed running
      * 'dead'          — a recorded PID is confirmed NOT running
      * 'in-session'    — the marker mode indicates an in-session coordinator (no
                          detached process to probe — the interactive session drives it)
      * 'unknown'       — no PID recorded and we cannot derive one
    """
    # 1. A recorded PID (forward-compatible: the conductor may record one in future).
    pid = None
    for key in ("conductor_pid", "pid"):
        val = marker.get(key)
        if isinstance(val, int) and val > 0:
            pid = val
            break
        if isinstance(val, str) and val.strip().isdigit():
            pid = int(val.strip())
            break
    if pid is not None:
        return ("alive" if _pid_running(pid) else "dead"), pid

    # 2. In-session coordinator — there is no separate conductor process to probe.
    mode = str(marker.get("mode", "")).lower()
    if "in-session" in mode or "coordinator" in mode:
        return "in-session", None

    # 3. Best-effort scan for a detached `gald3r autopilot loop` conductor (optional psutil).
    derived = _scan_for_conductor()
    if derived is not None:
        return "alive", derived

    return "unknown", None


def _pid_running(pid: int) -> bool:
    """Cross-platform best-effort 'is this PID alive?' check. Defensive — never raises."""
    try:
        import psutil  # type: ignore
        return psutil.pid_exists(pid)
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 — psutil edge cases fall through to OS checks
        pass
    if sys.platform.startswith("win"):
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=10,
            )
            return str(pid) in (out.stdout or "")
        except (OSError, subprocess.SubprocessError):
            return False
    # POSIX: signal 0 probes existence without killing.
    try:
        import os
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _scan_for_conductor():
    """Optional: find a running detached conductor by cmdline. Returns a PID or None."""
    try:
        import psutil  # type: ignore
    except ImportError:
        return None
    try:
        for proc in psutil.process_iter(["pid", "cmdline"]):
            cmdline = proc.info.get("cmdline") or []
            joined = " ".join(str(part) for part in cmdline)
            # The A3 outer loop absorbed into the engine runs as
            # `gald3r autopilot loop`; keep the legacy script name for a
            # transitional install still running the pre-absorption conductor.
            if ("autopilot" in joined and "loop" in joined) or "ggo_outer_loop.py" in joined:
                return proc.info.get("pid")
    except Exception:  # noqa: BLE001 — process enumeration is best-effort only
        return None
    return None


def last_git_commit(project_root: Path):
    """Return (committed_datetime, subject) of the last commit, or (None, None).

    Read-only `git log -1`; degrades silently when git is absent or there are no commits.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(project_root), "log", "-1", "--format=%cI%x1f%s"],
            capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None, None
    if out.returncode != 0:
        return None, None
    line = (out.stdout or "").strip()
    if not line or "\x1f" not in line:
        return None, None
    iso, subject = line.split("\x1f", 1)
    return parse_iso(iso), subject.strip()


def summarize_last_iteration(marker: dict):
    """Compact one-line summary of the most recent completed_iterations[] entry, or None."""
    ci = marker.get("completed_iterations")
    if not isinstance(ci, list) or not ci:
        return None
    last = ci[-1]
    if not isinstance(last, dict):
        return str(last)
    it = last.get("iter", "?")
    p1 = last.get("phase1_tasks") or []
    p2 = last.get("phase2_tasks") or []
    verdict = last.get("phase2_verdict") or last.get("phase1_verdict") or ""
    p1s = ", ".join(str(x) for x in p1) if p1 else "(none)"
    p2s = ", ".join(str(x) for x in p2) if p2 else "(none)"
    summary = f"iter {it}: phase1=[{p1s}] phase2=[{p2s}]"
    if verdict:
        verdict = verdict if len(verdict) <= 160 else verdict[:157] + "..."
        summary += f" — {verdict}"
    return summary


def compute_verdict(active, hard_stop, progress_age):
    """Derive the verdict + a one-line explanation from the run signals.

    Order matters: an explicit stop / inactive marker outranks the freshness bands.
    """
    if hard_stop:
        return VERDICT_STOPPED, f"Run stopped — authorized_hard_stop: {hard_stop}"
    if not active:
        return VERDICT_INACTIVE, "Marker present but active:false — the run has finished."
    if progress_age is None:
        # active:true but we have no usable timestamp from marker OR git — can't confirm progress.
        return VERDICT_STALLED, ("Active marker but no readable progress timestamp "
                                 "(marker + git both unavailable) — treat as stalled.")
    if progress_age <= ALIVE_THRESHOLD_SEC:
        return VERDICT_ALIVE, (f"Progress within {ALIVE_THRESHOLD_SEC // 60}m "
                               f"({fmt_age(progress_age)}) — making progress.")
    if progress_age <= STALLED_THRESHOLD_SEC:
        return VERDICT_IDLE_WAIT, (
            f"Last progress {fmt_age(progress_age)} — within the "
            f"{STALLED_THRESHOLD_SEC // 60}m window. Likely a long iteration / waiting on "
            f"the model (API I/O wait), not a wedge.")
    return VERDICT_STALLED, (
        f"Last progress {fmt_age(progress_age)} (> {STALLED_THRESHOLD_SEC // 60}m) with "
        f"no recent commit — likely wedged. Check the conductor.")


def build_report(project_root: Path):
    """Assemble the full status dict (the single source for both text and --json output)."""
    state_file = project_root / MARKER_RELPATH
    marker = read_marker(state_file)

    commit_dt, commit_subject = last_git_commit(project_root)
    commit_age = age_seconds(commit_dt)

    report = {
        "project_root": str(project_root),
        "marker_path": str(state_file),
        "marker_present": False,
        "last_commit_iso": iso_utc(commit_dt),
        "last_commit_subject": commit_subject,
        "last_commit_age_seconds": commit_age,
    }

    if marker is None:
        report["verdict"] = VERDICT_NO_RUN
        report["explanation"] = "No g-go-go run-state marker found — no active run."
        return report

    if isinstance(marker, tuple) and marker and marker[0] == "__error__":
        report["marker_present"] = True
        report["verdict"] = VERDICT_STALLED
        report["explanation"] = f"Marker is present but unparseable: {marker[1]}"
        report["marker_parse_error"] = marker[1]
        return report

    report["marker_present"] = True
    active = bool(marker.get("active", False))
    hard_stop = str(marker.get("authorized_hard_stop", "") or "").strip()
    marker_dt = parse_iso(marker.get("updated_at"))
    marker_age = age_seconds(marker_dt)

    # Progress = the MOST RECENT of marker stamp and last commit.
    ages = [a for a in (marker_age, commit_age) if a is not None]
    progress_age = min(ages) if ages else None

    cond_status, cond_pid = probe_conductor(marker)

    verdict, explanation = compute_verdict(active, hard_stop, progress_age)

    report.update({
        "active": active,
        "platform": marker.get("platform"),
        "mode": marker.get("mode"),
        "run_scope": marker.get("run_scope"),
        "session_id": marker.get("session_id"),
        "iter": marker.get("iter"),
        "budget_remaining": marker.get("budget_remaining"),
        "authorized_hard_stop": hard_stop or None,
        "updated_at": marker.get("updated_at"),
        "marker_age_seconds": marker_age,
        "progress_age_seconds": progress_age,
        "conductor_status": cond_status,
        "conductor_pid": cond_pid,
        "last_iteration_summary": summarize_last_iteration(marker),
        "verdict": verdict,
        "explanation": explanation,
        "thresholds": {
            "alive_threshold_sec": ALIVE_THRESHOLD_SEC,
            "stalled_threshold_sec": STALLED_THRESHOLD_SEC,
        },
    })
    return report


def render_text(report: dict) -> str:
    """Human-readable rendering of the report dict."""
    lines = []
    verdict = report.get("verdict", "?")
    lines.append("=" * 60)
    lines.append(f"  g-go-go status: {verdict}")
    lines.append("=" * 60)
    lines.append(report.get("explanation", ""))

    if verdict == VERDICT_NO_RUN:
        lines.append("")
        lines.append(f"Looked for marker: {report['marker_path']}")
        if report.get("last_commit_subject"):
            lines.append(f"Last commit:       {fmt_age(report.get('last_commit_age_seconds'))}"
                         f"  \"{report['last_commit_subject']}\"")
        return "\n".join(lines)

    lines.append("")
    lines.append(f"  Active            : {report.get('active')}")
    if report.get("iter") is not None:
        lines.append(f"  Iteration         : {report.get('iter')}")
    if report.get("budget_remaining") is not None:
        lines.append(f"  Budget remaining  : {report.get('budget_remaining')}")
    if report.get("mode"):
        lines.append(f"  Mode              : {report.get('mode')}")
    if report.get("run_scope"):
        lines.append(f"  Run scope         : {report.get('run_scope')}")
    if report.get("platform"):
        lines.append(f"  Platform          : {report.get('platform')}")
    if report.get("session_id"):
        lines.append(f"  Session id        : {report.get('session_id')}")

    cond = report.get("conductor_status", "unknown")
    pid = report.get("conductor_pid")
    if cond == "alive":
        cond_str = f"alive (pid {pid})" if pid else "alive"
    elif cond == "dead":
        cond_str = f"NOT running (pid {pid} dead)"
    elif cond == "in-session":
        cond_str = "in-session coordinator (no detached conductor process to probe)"
    else:
        cond_str = "unknown (no PID recorded / not derivable)"
    lines.append(f"  Conductor process : {cond_str}")

    lines.append("")
    lines.append(f"  Marker updated    : {report.get('updated_at')}  "
                 f"({fmt_age(report.get('marker_age_seconds'))})")
    if report.get("last_commit_subject"):
        lines.append(f"  Last commit       : {fmt_age(report.get('last_commit_age_seconds'))}"
                     f"  \"{report['last_commit_subject']}\"")
    else:
        lines.append("  Last commit       : (none / git unavailable)")
    lines.append(f"  Since last progress: {fmt_age(report.get('progress_age_seconds'))}")

    if report.get("authorized_hard_stop"):
        lines.append("")
        lines.append(f"  Hard stop         : {report.get('authorized_hard_stop')}")

    if report.get("last_iteration_summary"):
        lines.append("")
        lines.append(f"  Last iteration    : {report.get('last_iteration_summary')}")

    return "\n".join(lines)


# Exit codes: 0 ALIVE/IDLE-WAIT/INACTIVE/STOPPED/NO-RUN (informational), 1 STALLED.
# A non-zero exit only for STALLED lets a watchdog/CI gate trigger on a likely wedge.
EXIT_OK = 0
EXIT_STALLED = 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="One-shot ALIVE / IDLE-WAIT / STALLED status for a g-go-go run (T1585).")
    parser.add_argument("--project-root", default="",
                        help="Repo root (defaults to the nearest .gald3r ancestor of cwd).")
    parser.add_argument("--json", action="store_true",
                        help="Emit the status report as JSON (mirrors other --json commands).")
    args = parser.parse_args(argv)

    project_root = locate_project_root(args.project_root, Path.cwd())
    report = build_report(project_root)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))

    return EXIT_STALLED if report.get("verdict") == VERDICT_STALLED else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
