#!/usr/bin/env python3
"""Python port of gald3r_push_gate.ps1 (T1585).

gald3r pre-push gate: regular (light) vs release (CHANGELOG/version discipline).

Regular: status, unpushed commits, .gald3r sync hint. Never blocks (exit 0).
Release: requires a versioned ## [x] section in CHANGELOG.md (Keep a Changelog
style); optional override via GALD3R_PUSH_GATE_OVERRIDE=1 or interactive prompt.
Exit codes: 0 = OK / regular / dry-run; 1 = release gate BLOCKED.

Examples:
    python gald3r_push_gate.py
    python gald3r_push_gate.py -Release
    GALD3R_RELEASE_PUSH=1 python gald3r_push_gate.py --non-interactive
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def _bootstrap_engine() -> bool:
    """Make `gald3r.utils` importable (installed package or bundled engine src)."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        engine_src = parent / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()
if _HAS_ENGINE:
    from gald3r.utils import process as _process
else:
    _process = None  # graceful stdlib fallback


def run_git(args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run git and return (returncode, stdout, stderr) without raising."""
    if _process is not None:
        r = _process.run_git(args, cwd=cwd, check=False)
        return r.returncode, r.stdout, r.stderr
    try:
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError:
        return 127, "", "git not found"


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "") in ("1", "true")


def _prompt_yes(question: str) -> bool:
    """Read-Host equivalent: y/yes (case-insensitive) means yes."""
    try:
        if not sys.stdin.isatty():
            return False
        resp = input(question)
        return bool(re.match(r"^(y|yes)$", resp.strip(), re.IGNORECASE))
    except (EOFError, OSError):
        return False  # non-interactive host


def write_release_changelog_hint(repo_root: Path) -> bool:
    """Release-mode CHANGELOG gate; returns False on BLOCK."""
    cl = repo_root / "CHANGELOG.md"
    if not cl.is_file():
        print("BLOCK: CHANGELOG.md missing — add Keep a Changelog-style file at repo root.")
        return False
    try:
        raw = cl.read_text(encoding="utf-8", errors="replace")
    except OSError:
        raw = ""
    if not raw.strip():
        print("BLOCK: CHANGELOG.md is empty.")
        return False
    # Versioned section other than [Unreleased]
    if not re.search(r"(?m)^##\s*\[(?!Unreleased\])[^\]]+\]", raw):
        print("BLOCK: Release push requires a versioned heading in CHANGELOG.md "
              "(e.g. ## [1.2.3] - YYYY-MM-DD) below [Unreleased].")
        print("       Resolve [Unreleased] into a version section per g-rl-26, "
              "or set GALD3R_PUSH_GATE_OVERRIDE=1 to skip.")
        return False
    # Warn if [Unreleased] still has bullet lines (might mean not fully moved)
    m = re.search(r"(?ms)^##\s*\[Unreleased\]\s*\r?\n(?P<body>.*?)(?=^##\s*\[|\Z)", raw)
    if m and re.search(r"(?m)^\s*[-*]\s+\S", m.group("body")):
        print("WARN: [Unreleased] still lists bullets — confirm they should not "
              "move into the new version section.")
    print("CHANGELOG: versioned section present — OK")
    return True


def show_version_files(repo_root: Path) -> None:
    """Print declared version lines from pyproject.toml / package.json."""
    for vf in ("pyproject.toml", "package.json"):
        p = repo_root / vf
        if not p.is_file():
            continue
        pattern = r"^\s*version\s*=" if vf == "pyproject.toml" else r'"version"\s*:'
        try:
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if re.search(pattern, line):
                    print(f"  {line.strip()} ({vf})")
                    break
        except OSError:
            continue
    if (repo_root / "AGENTS.md").is_file():
        print("  AGENTS.md present — spot-check Version / Last Updated if applicable.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="gald3r pre-push gate: regular (light) vs release "
                    "(CHANGELOG/version discipline).")
    parser.add_argument("-Release", "--release", dest="release",
                        action="store_true", help="Force release-mode checks.")
    parser.add_argument("-NonInteractive", "--non-interactive",
                        dest="non_interactive", action="store_true",
                        help="No prompts; use env vars only for overrides.")
    parser.add_argument("-HookMode", "--hook-mode", dest="hook_mode",
                        action="store_true",
                        help="Invoked from git pre-push: non-interactive; "
                             "release only if GALD3R_RELEASE_PUSH=1.")
    parser.add_argument("-DryRun", "--dry-run", dest="dry_run",
                        action="store_true",
                        help="Print mode and checks but always exit 0.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    non_interactive = args.non_interactive or args.dry_run

    rc, out, _ = run_git(["rev-parse", "--show-toplevel"])
    if rc != 0 or not out.strip():
        print("gald3r push gate: not a git repository — skip")
        return 0
    repo_root = Path(out.strip())
    os.chdir(repo_root)

    is_release = args.release or _env_truthy("GALD3R_RELEASE_PUSH")

    if args.hook_mode:
        non_interactive = True
        is_release = _env_truthy("GALD3R_RELEASE_PUSH")
    elif not is_release and not non_interactive:
        if _prompt_yes("Is this a release push? (y/N): "):
            is_release = True

    # --- Regular mode ---
    if not is_release:
        print()
        print("gald3r push gate — REGULAR")
        print("=========================")
        rc, out, _ = run_git(["status", "-sb"], cwd=repo_root)
        if out:
            print(out.rstrip("\n"))
        print()
        rc, _, _ = run_git(["rev-parse", "--abbrev-ref", "@{upstream}"], cwd=repo_root)
        if rc == 0:
            print("Unpushed commits (@{upstream}..HEAD, max 25):")
            _, out, _ = run_git(["--no-pager", "log", "--oneline", "-n", "25",
                                 "@{upstream}..HEAD"], cwd=repo_root)
        else:
            print("Recent commits (no upstream set):")
            _, out, _ = run_git(["--no-pager", "log", "--oneline", "-n", "10"],
                                cwd=repo_root)
        if out.strip():
            print(out.rstrip("\n"))
        print()
        if (repo_root / ".gald3r").exists():
            _, porcelain, _ = run_git(["status", "--porcelain"], cwd=repo_root)
            if re.search(r"(?m)\.gald3r/", porcelain):
                print("NOTE: .gald3r/ has local changes — consider @g-task-sync-check "
                      "before sharing branch state.")
        print("Regular push gate: OK (informational only)")
        print()
        return 0

    # --- Release mode ---
    print()
    print("gald3r push gate — RELEASE")
    print("=========================")

    block = not write_release_changelog_hint(repo_root)

    if block and os.environ.get("GALD3R_PUSH_GATE_OVERRIDE") == "1":
        print("OVERRIDE: GALD3R_PUSH_GATE_OVERRIDE=1 — proceeding despite CHANGELOG gate.")
        block = False
    elif block and not non_interactive:
        if _prompt_yes("Release gate failed. Override and continue? (y/N): "):
            block = False

    if not block:
        print()
        print("README: re-read install, features, and contributor/version sections "
              "before tagging.")
        print("Declared versions (if present):")
        show_version_files(repo_root)

    print()
    if args.dry_run:
        print("DryRun: exit 0")
        return 0
    if block:
        print("Release push gate: BLOCKED")
        return 1
    print("Release push gate: OK")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
