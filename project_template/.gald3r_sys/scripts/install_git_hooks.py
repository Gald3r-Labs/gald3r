#!/usr/bin/env python3
"""Python port of install_git_hooks.ps1 (T1586).

Install gald3r git hooks (T1428) into the target repository.

Points the repo's git hooks at the tracked .githooks/ directory by setting
``core.hooksPath``. This makes the pre-commit encoding-normalization hook
(.githooks/pre-commit) active on every clone without writing into the
untracked .git/hooks/ directory.

Why core.hooksPath instead of copying into .git/hooks/?
  - .git/hooks/ is never tracked by git, so a fresh clone gets no hook.
  - The .githooks/ directory IS tracked (shipped by the install scaffold),
    so a single ``core.hooksPath .githooks`` makes the hook portable.

Cross-platform: on POSIX every file in .githooks/ is additionally marked
executable (git refuses to run non-executable hooks); on Windows the chmod
step is a no-op.

Idempotent: re-running just re-sets the config value.

Usage:
    python install_git_hooks.py [--repo-root PATH] [--uninstall]
"""
# @subsystems: SECURITY_AND_COMPLIANCE

from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence


def _git(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command in `cwd`, capturing output (never raises on exit code).

    Args:
        args: Git arguments, e.g. ``["config", "core.hooksPath", ".githooks"]``.
        cwd: Repository directory.

    Returns:
        The completed process (check ``returncode`` yourself).
    """
    return subprocess.run(
        ["git", *args], cwd=str(cwd),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _make_hooks_executable(hooks_dir: Path) -> int:
    """chmod +x every file in `hooks_dir` on POSIX; no-op on Windows.

    Args:
        hooks_dir: The tracked .githooks/ directory.

    Returns:
        Number of files whose mode was updated.
    """
    if os.name == "nt":
        return 0
    changed = 0
    for entry in hooks_dir.iterdir():
        if not entry.is_file():
            continue
        mode = entry.stat().st_mode
        exec_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        if (mode & exec_bits) != exec_bits:
            entry.chmod(mode | exec_bits)
            changed += 1
    return changed


def install(repo_root: Path, uninstall: bool = False) -> int:
    """Install (or uninstall) the gald3r hooks path in `repo_root`.

    Mirrors install_git_hooks.ps1: warns and skips (exit 0) when the target
    is not a git repository or .githooks/ is missing.

    Args:
        repo_root: Repository root directory.
        uninstall: When True, unset ``core.hooksPath`` instead.

    Returns:
        Process exit code (0 on success/skip, 1 on git config failure).
    """
    probe = _git(["rev-parse", "--is-inside-work-tree"], cwd=repo_root)
    if probe.returncode != 0:
        print(f"WARNING: install_git_hooks: '{repo_root}' is not a git repository. "
              "Skipping.", file=sys.stderr)
        return 0

    if uninstall:
        _git(["config", "--unset", "core.hooksPath"], cwd=repo_root)
        print("gald3r git hooks: uninstalled (core.hooksPath unset)")
        return 0

    hooks_dir = repo_root / ".githooks"
    if not hooks_dir.is_dir():
        print(f"WARNING: install_git_hooks: '.githooks/' not found at {repo_root}. "
              "Run gald3r setup first.", file=sys.stderr)
        return 0

    result = _git(["config", "core.hooksPath", ".githooks"], cwd=repo_root)
    if result.returncode != 0:
        print(f"ERROR: git config core.hooksPath failed: "
              f"{result.stderr.strip()}", file=sys.stderr)
        return 1

    _make_hooks_executable(hooks_dir)
    print("gald3r git hooks: installed (core.hooksPath -> .githooks)")
    print("  pre-commit will normalize encodings "
          "(UTF-8 BOM for .ps1, no-BOM + LF otherwise).")
    print("  Disable with: install_git_hooks.py --uninstall")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point — same surface as install_git_hooks.ps1."""
    parser = argparse.ArgumentParser(
        prog="install_git_hooks.py",
        description="Install gald3r git hooks (core.hooksPath -> .githooks).",
        allow_abbrev=False,
    )
    parser.add_argument("--repo-root", "-RepoRoot", dest="repo_root",
                        default=str(Path.cwd()),
                        help="Repository root. Defaults to the current directory.")
    parser.add_argument("--uninstall", "-Uninstall", dest="uninstall",
                        action="store_true",
                        help="Remove the gald3r hooks path "
                             "(git config --unset core.hooksPath).")
    args = parser.parse_args(argv)
    return install(Path(args.repo_root).expanduser().resolve(), args.uninstall)


if __name__ == "__main__":
    sys.exit(main())
