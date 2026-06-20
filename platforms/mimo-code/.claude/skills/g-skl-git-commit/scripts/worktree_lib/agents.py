"""Agent subprocess lifecycle — Run, Cancel, CancelAll (T1123).

Python port of gald3r_worktree.ps1 (T1585) — cancellation signal threading.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from worktree_lib.gitio import (
    WorktreeError,
    is_blank,
    iso_o,
    run_process,
    utc_now,
)
from worktree_lib import manifest as mf

_IS_WINDOWS = os.name == "nt"
_STILL_ACTIVE = 259
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def pid_alive(pid: int) -> bool:
    """True when a process with `pid` is still running (PS1 Get-Process probe)."""
    if _IS_WINDOWS:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == _STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _request_graceful_stop(pid: int) -> None:
    """Graceful termination request (PS1 CloseMainWindow / kill -TERM)."""
    if _IS_WINDOWS:
        # taskkill without /F posts WM_CLOSE — the closest cross-process
        # equivalent of the PS1 $proc.CloseMainWindow() graceful request.
        run_process(["taskkill", "/PID", str(pid)])
    else:
        import signal

        try:
            os.kill(int(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass  # already gone or not ours; the poll below decides the outcome


def _force_kill(pid: int) -> None:
    """Forced tree-kill (PS1 taskkill /T /F or kill -KILL)."""
    if _IS_WINDOWS:
        run_process(["taskkill", "/PID", str(pid), "/T", "/F"])
    else:
        import signal

        try:
            os.kill(int(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass  # already gone; the post-kill probe decides the outcome


def stop_agent_process(pid: int, grace_seconds: int) -> str:
    """Graceful first, then forced tree-kill after the grace period.

    Returns:
        One of: already-exited | terminated-graceful | killed-forced | kill-failed
    """
    if not pid_alive(pid):
        return "already-exited"

    _request_graceful_stop(pid)

    deadline = time.monotonic() + max(0, grace_seconds)
    while time.monotonic() < deadline:
        if not pid_alive(pid):
            return "terminated-graceful"
        time.sleep(0.2)

    _force_kill(pid)
    time.sleep(0.2)
    if not pid_alive(pid):
        return "killed-forced"
    return "kill-failed"


def write_cancellation_log(repo_root: str, task_id: Any, worktree_path: Any, reason: str) -> None:
    """Append to .gald3r/logs/worktree_cancellations.log (PS1 Write-CancellationLog)."""
    log_dir = Path(repo_root) / ".gald3r" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = iso_o(utc_now())
    line = f"{stamp} | {task_id} | {worktree_path} | {reason}\n"
    with open(log_dir / "worktree_cancellations.log", "a", encoding="utf-8") as fh:
        fh.write(line)


def run_agent_in_worktree(
    repo_root: str,
    metadata: Optional[Dict[str, Any]],
    agent_command: Optional[str],
    agent_arguments: Sequence[str],
    wait: bool,
) -> Dict[str, Any]:
    """PS1 Start-AgentInWorktree — launch and record the agent PID on the marker."""
    if is_blank(agent_command):
        raise WorktreeError("-AgentCommand is required for Run.")
    if metadata is None or not metadata.get("gald3r_owned"):
        raise WorktreeError(
            "Run requires an existing gald3r-owned worktree (create it first with -Action Create)."
        )
    assert agent_command is not None
    worktree_path = metadata.get("worktree_path") or ""
    marker_path = Path(worktree_path) / mf.MARKER_NAME
    if not marker_path.exists():
        raise WorktreeError(f"Ownership marker missing at '{marker_path}' — refusing to Run.")

    argv: List[str] = [agent_command, *list(agent_arguments or [])]
    creationflags = 0
    if _IS_WINDOWS:
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(
        argv,
        cwd=worktree_path,
        creationflags=creationflags,
        stdin=subprocess.DEVNULL if not wait else None,
        stdout=None if wait else subprocess.DEVNULL,
        stderr=None if wait else subprocess.DEVNULL,
    )

    # Persist the PID onto the marker (additive — preserve existing fields).
    updated = dict(metadata)
    updated["agent_pid"] = proc.pid
    updated["agent_command"] = " ".join(argv)
    updated["agent_started_at"] = iso_o(utc_now())
    updated["agent_status"] = "running"
    mf.write_metadata(marker_path, updated)

    exit_code: Optional[int] = None
    if wait:
        exit_code = proc.wait()
        updated["agent_status"] = "exited"
        updated["agent_exit_code"] = exit_code
        mf.write_metadata(marker_path, updated)

    return {
        "action": "ran" if wait else "started",
        "task_id": metadata.get("task_id"),
        "worktree_path": worktree_path,
        "agent_pid": proc.pid,
        "agent_command": updated["agent_command"],
        "agent_status": updated["agent_status"],
        "agent_exit_code": exit_code,
    }


def stop_worktree_agent(
    repo_root: str,
    metadata: Dict[str, Any],
    grace_seconds: int,
    reason: str,
) -> Dict[str, Any]:
    """PS1 Stop-WorktreeAgentByMetadata — cancel the recorded agent; worktree preserved."""
    worktree_path = metadata.get("worktree_path") or ""
    marker_path = Path(worktree_path) / mf.MARKER_NAME
    agent_pid = metadata.get("agent_pid")
    if agent_pid is None:
        return {
            "action": "no-agent",
            "task_id": metadata.get("task_id"),
            "worktree_path": worktree_path,
            "outcome": "no-pid-recorded",
        }

    outcome = stop_agent_process(int(agent_pid), grace_seconds)
    write_cancellation_log(
        repo_root, metadata.get("task_id"), worktree_path, f"{reason} ({outcome})"
    )

    # Update the marker: clear the live PID, record the cancellation.
    # Worktree files are intentionally preserved (forensics).
    if marker_path.exists():
        updated = dict(metadata)
        updated["agent_status"] = "cancelled"
        updated["agent_cancelled_at"] = iso_o(utc_now())
        updated["agent_cancel_reason"] = reason
        updated["agent_cancel_outcome"] = outcome
        updated["agent_pid"] = None
        mf.write_metadata(marker_path, updated)

    return {
        "action": "cancelled",
        "task_id": metadata.get("task_id"),
        "worktree_path": worktree_path,
        "outcome": outcome,
        "reason": reason,
    }


def cancel_all_for_task(
    repo_root: str,
    root: str,
    task_id: Optional[str],
    grace_seconds: int,
    reason: str,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """PS1 Invoke-CancelAllForTask — cancel every agent owned by a task id."""
    if is_blank(task_id):
        raise WorktreeError("-TaskId is required for CancelAll.")
    results: List[Dict[str, Any]] = []
    for metadata in mf.get_report(root, repo_root):
        if not _ci_equal(metadata.get("task_id"), task_id):
            continue
        results.append(stop_worktree_agent(repo_root, metadata, grace_seconds, reason))
    if not results:
        return {"action": "cancel-all", "task_id": task_id, "outcome": "no-worktrees-found"}
    return results


def _ci_equal(a: Any, b: Any) -> bool:
    """Case-insensitive equality matching the PS1 -ne comparison."""
    return (str(a) if a is not None else "").lower() == (str(b) if b is not None else "").lower()
