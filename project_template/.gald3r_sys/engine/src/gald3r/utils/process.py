"""Subprocess and git wrappers — replacements for the ``& git ...`` /
``$LASTEXITCODE`` patterns in the PS1 scripts.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple, Union


@dataclass(frozen=True)
class RunResult:
    """Outcome of a completed (or dry-run) command."""

    args: Tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """True when the command exited 0."""
        return self.returncode == 0


class CommandError(RuntimeError):
    """Raised by run_cmd/run_git when check=True and the command failed."""

    def __init__(self, result: RunResult):
        self.result = result
        super().__init__(
            f"command failed (exit {result.returncode}): {' '.join(result.args)}\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


def run_cmd(
    args: Sequence[str],
    cwd: Optional[Union[str, Path]] = None,
    check: bool = True,
    dry_run: bool = False,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> RunResult:
    """Run a command and capture its output.

    Args:
        args: Command argv (no shell interpretation).
        cwd: Working directory.
        check: Raise CommandError on non-zero exit (set False to inspect
            the returncode yourself — needed by push/publish logic).
        dry_run: Print the command with a ``[DRY]`` prefix and return a
            successful empty result without executing.
        env: Replacement environment (default: inherit).
        timeout: Seconds before the process is killed.

    Returns:
        RunResult with stdout/stderr/returncode.
    """
    argv = tuple(str(a) for a in args)
    if dry_run:
        print(f"[DRY] would run: {' '.join(argv)}" + (f"  (cwd={cwd})" if cwd else ""))
        return RunResult(args=argv, returncode=0, stdout="", stderr="")
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    result = RunResult(args=argv, returncode=proc.returncode,
                       stdout=proc.stdout or "", stderr=proc.stderr or "")
    if check and not result.ok:
        raise CommandError(result)
    return result


def run_git(
    args: Sequence[str],
    cwd: Optional[Union[str, Path]] = None,
    check: bool = True,
    dry_run: bool = False,
) -> RunResult:
    """Run a git command (``run_cmd`` with the git executable prepended).

    Args:
        args: Git arguments, e.g. ``["status", "--porcelain"]``.
        cwd: Repository directory.
        check: Raise CommandError on non-zero exit.
        dry_run: Print instead of executing.
    """
    return run_cmd(["git", *args], cwd=cwd, check=check, dry_run=dry_run)
