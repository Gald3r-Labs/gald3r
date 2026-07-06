#!/usr/bin/env python3
"""gald3r policy-as-code guardrail hook (T1611, D12).

Concern hook registered in `g_hk_core.py`'s `tool-start` chain (and invoked
directly by `g-hk-pre-commit.py` for the git-level check). Evaluates the
incoming tool-call payload against the active org policy bundle by calling the
absorbed engine verb `gald3r policy check` (A6 / T1663) — the CHECK op that
used to live in `g-skl-policy`'s `scripts/policy_engine.py`. The engine binary
is resolved through the zero-IP `.gald3r_sys/scripts/gald3r_bin.py` resolver;
the event payload is piped to the verb on STDIN and the JSON verdict is read
back.

Enforcement is by CODE, not model discretion (g-rl-38): this hook returns a
deterministic block/allow verdict; the model's role is limited to explaining
why (surfaced via the block reason / additional_context). No-ops gracefully
everywhere policy-as-code doesn't apply: free/retail installs (no org tier),
platforms with no hook surface (never invoked), engine not installed, and any
parse/lookup error (fail-open — a broken policy bundle must never brick a
session).
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402


def _resolve_engine_cmd(project_root: Path):
    """Resolve the gald3r engine command prefix via the zero-IP resolver.

    Returns the command prefix (e.g. ``["gald3r"]``) or ``None`` when the
    resolver is not shipped or no engine can be found — the hook then no-ops
    (allow), exactly like the old "skill not installed" path.
    """
    resolver = project_root / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("gald3r_bin_policy", str(resolver))
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.resolve_engine_cmd(project_root)
    except Exception:
        return None


def emit(payload: dict) -> None:
    print(json.dumps(payload, separators=(",", ":")))


def _resolve_project_root() -> Path:
    """Prefer the invoking process's cwd (the actual project being worked on)
    walked up to its `.gald3r/` ancestor; fall back to `_hook_common`'s
    hook-file-relative resolution (correct when a test imports the hook
    in-place inside the canonical repo tree, which has its own `.gald3r/`)."""
    d = Path.cwd()
    for candidate in [d] + list(d.parents):
        if (candidate / ".gald3r").is_dir():
            return candidate
    return _hook_common.project_root()


def main(argv: list) -> int:
    event = _hook_common.read_stdin_json()
    if not event:
        emit({"permission": "allow"})
        return 0

    root = _resolve_project_root()
    engine = _resolve_engine_cmd(root)
    if engine is None:
        # Engine not installed / not shipped on this tier — pure no-op.
        emit({"permission": "allow"})
        return 0

    try:
        # `gald3r policy check` reads the event JSON from STDIN (the hook path)
        # and emits the verdict object on stdout. --exit-zero keeps a `block`
        # verdict from raising exit 2 so we branch on the parsed JSON instead.
        proc = subprocess.run(
            [*engine, "policy", "check", "--json", "--exit-zero", "--root", str(root)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            timeout=15,
        )
        result = json.loads(proc.stdout.strip() or "{}")
    except Exception:
        # Fail-open: a broken bundle or engine error must never block a tool call.
        emit({"permission": "allow"})
        return 0

    if result.get("verdict") == "block":
        reason = result.get("message") or "Blocked by org policy."
        emit({
            "permission": "deny",
            "continue": False,
            "reason": reason,
            "decision": "block",
        })
        return 2

    if result.get("verdict") == "warn" and result.get("message"):
        emit({"permission": "allow", "additional_context": f"[org policy warning] {result['message']}"})
        return 0

    emit({"permission": "allow"})
    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:
        try:
            print(json.dumps({"permission": "allow"}, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
