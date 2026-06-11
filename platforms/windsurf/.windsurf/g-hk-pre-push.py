#!/usr/bin/env python3
"""Python port of g-hk-pre-push.ps1 (T1584).

gald3r optional pre-push gate (opt-in). Delegates to
.cursor/skills/g-skl-git-commit/scripts/gald3r_push_gate -HookMode and exits
with the gate's exit code. Release checks run only when GALD3R_RELEASE_PUSH=1
(or true) — that logic lives inside the gate script, not here.

Transition resolver (T1584): prefers a gald3r_push_gate.py sibling when one
exists at runtime (run with this interpreter), otherwise falls back to
gald3r_push_gate.ps1 via pwsh/powershell. When neither the gate nor a
PowerShell host is available the push is allowed (exit 0), matching the
.ps1's fail-open posture.

INSTALLATION (opt-in):  git config core.hooksPath .cursor/hooks
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; this hook is pure stdlib)

GATE_REL = ".cursor/skills/g-skl-git-commit/scripts/gald3r_push_gate.ps1"


def run_git(args: list) -> str:
    try:
        proc = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.stdout or ""
    except (OSError, subprocess.SubprocessError):
        return ""


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r pre-push gate hook (Python port of g-hk-pre-push.ps1)"
    )
    parser.parse_known_args(argv)  # the .ps1 takes no parameters

    repo_root = run_git(["rev-parse", "--show-toplevel"]).strip()
    if not repo_root:
        return 0

    scripts_dir = Path(repo_root) / ".cursor" / "skills" / "g-skl-git-commit" / "scripts"
    gate_py = scripts_dir / "gald3r_push_gate.py"
    gate_ps1 = scripts_dir / "gald3r_push_gate.ps1"

    # Prefer the Python gate when it exists (T1584 transition period).
    if gate_py.is_file():
        try:
            return subprocess.run(
                [sys.executable, str(gate_py), "-HookMode"]
            ).returncode
        except (OSError, subprocess.SubprocessError):
            return 0  # fail open, same as a missing gate

    if not gate_ps1.is_file():
        print(f"gald3r pre-push: {GATE_REL} not found — allow push")
        return 0

    # PowerShell host resolution: pwsh (cross-platform) first, then Windows
    # PowerShell. On non-Windows systems without pwsh there is no way to run
    # the .ps1 gate — allow the push rather than break it (fail open).
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        print(
            "gald3r pre-push: no PowerShell host (pwsh/powershell) found to run "
            f"{GATE_REL} — allow push"
        )
        return 0

    try:
        return subprocess.run(
            [
                shell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(gate_ps1),
                "-HookMode",
            ]
        ).returncode
    except (OSError, subprocess.SubprocessError):
        return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session; an unexpected failure in
        # this wrapper must not block pushes. The gate's own non-zero exit
        # codes are propagated via sys.exit above and NOT swallowed here.
        sys.exit(0)
