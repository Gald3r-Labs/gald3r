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

BUG-638 (actionability -- the deny reason must also reach stderr): Claude
Code's PreToolUse hook contract treats exit code 2 as a "blocking error" and
reads STDERR for the human-readable reason shown back to the calling agent.
This hook used to print only its ``{permission: deny, ...}`` JSON body to
stdout on a deny, so the real org-policy reason never reached stderr -- the
exact defect class BUG-179 fixed for g-hk-pre-tool-call-gald3r-guard.py,
BUG-625 fixed for g-hk-validate-shell.py, and BUG-633 fixed for
g-hk-pre-tool-call-prd-freeze.py / g-hk-pre-tool-call-member-gald3r-guard.py.
Mirrors that additive-only shape: stdout stays byte-for-byte unchanged, and
the deny reason is also written to stderr.
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations
# --- gald3r calltrace bootstrap (T268) -- injected; inert unless gald3r call tracing is
# enabled. Strip everywhere: python scripts/inject_calltrace_bootstrap.py --strip
import os as _g3ct_os
_g3ct_home = _g3ct_os.environ.get("GALD3R_HOME") or _g3ct_os.path.join(
    _g3ct_os.path.expanduser("~"), ".gald3r")
_g3ct_env = (_g3ct_os.environ.get("GALD3R_TRACE_CALLS") or "").strip().lower()
if _g3ct_env not in ("", "0", "off", "false", "no") or _g3ct_os.path.isfile(
        _g3ct_os.path.join(_g3ct_home, "calltrace.json")):
    try:
        _g3ct_bs = _g3ct_os.path.join(_g3ct_home, "calltrace_bootstrap.py")
        if _g3ct_os.path.isfile(_g3ct_bs):
            with open(_g3ct_bs, "r", encoding="utf-8") as _g3ct_fh:
                exec(compile(_g3ct_fh.read(), _g3ct_bs, "exec"),
                     {"__g3ct_script__": __file__,
                      "__name__": "_gald3r_calltrace_exec"})
    except Exception:
        pass
# --- end gald3r calltrace bootstrap ---

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402


def _resolve_engine_cmd(project_root: Path):
    """Resolve the gald3r engine command prefix (P3 Tier-0, T179/T191).

    Delegates to the shared `_hook_common.resolve_engine_argv` (env var ->
    PATH -> legacy loose resolver -> loud degrade) so PATH resolution works
    even when the loose `.gald3r_sys/scripts/gald3r_bin.py` IP script is not
    shipped. Returns the command prefix (e.g. ``["gald3r"]``) or ``None``
    when no engine can be found — the hook then no-ops (allow), exactly like
    the old "skill not installed" path.
    """
    return _hook_common.resolve_engine_argv(
        project_root, hook_name="g-hk-policy-check"
    )


def emit(payload: dict) -> None:
    print(json.dumps(payload, separators=(",", ":")))


def _resolve_project_root() -> Path:
    """Prefer the invoking process's cwd (the actual project being worked on)
    walked up to its `.gald3r/` ancestor; fall back to `_hook_common`'s
    hook-file-relative resolution (correct when a test imports the hook
    in-place inside the canonical repo tree, which has its own `.gald3r/`).

    T516 (T512 inventory row 12 -- policy-as-code enforcement gate): applies
    the shared T512 gitignore-refusal + ambiguity-warning walk-up guard
    (`_hook_common.guarded_walk_up`).
    """
    d = Path.cwd()
    root = _hook_common.guarded_walk_up(
        d, exclude=_hook_common.resolved_global_gald3r_home()
    )
    return root if root is not None else _hook_common.project_root()


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
        # BUG-638: exit 2 is Claude Code's "blocking error" contract -- the reason
        # MUST also reach STDERR (stdout-only was silently discarded, surfacing as
        # "No stderr output" to the calling agent). Purely additive: stdout is left
        # byte-for-byte unchanged. Mirrors BUG-179/BUG-625/BUG-633's fix for the
        # sibling PreToolUse guard hooks.
        sys.stderr.write(reason + "\n")
        sys.stderr.flush()
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
