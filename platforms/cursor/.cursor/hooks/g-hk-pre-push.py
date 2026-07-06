#!/usr/bin/env python3
"""gald3r optional pre-push gate hook (opt-in).

Delegates to the absorbed engine verb `gald3r push-gate --hook-mode` (A1 /
T1658) and exits with the gate's exit code. Release checks run only when
GALD3R_RELEASE_PUSH=1 (or true) — that logic lives inside the gate verb, not
here. The engine binary is resolved through the zero-IP
`.gald3r_sys/scripts/gald3r_bin.py` resolver; when no engine can be resolved
the push is allowed (exit 0), matching the historical fail-open posture.

INSTALLATION (opt-in):  git config core.hooksPath .cursor/hooks
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; this hook is pure stdlib)


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


def _resolve_engine_cmd(repo_root: str):
    """Resolve the gald3r engine command prefix via the zero-IP resolver.

    Returns the command prefix (e.g. ``["gald3r"]``) or ``None`` when the
    resolver is not shipped or no engine can be found — the hook then allows
    the push (fail-open)."""
    resolver = Path(repo_root) / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("gald3r_bin_prepush", str(resolver))
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.resolve_engine_cmd(Path(repo_root))
    except Exception:
        return None


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r pre-push gate hook (delegates to `gald3r push-gate`)."
    )
    parser.parse_known_args(argv)  # the gate verb takes no hook parameters here

    repo_root = run_git(["rev-parse", "--show-toplevel"]).strip()
    if not repo_root:
        return 0

    engine = _resolve_engine_cmd(repo_root)
    if engine is None:
        print("gald3r pre-push: gald3r engine not found — allow push")
        return 0

    try:
        return subprocess.run([*engine, "push-gate", "--hook-mode"]).returncode
    except (OSError, subprocess.SubprocessError):
        return 0  # fail open, same as a missing gate


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
