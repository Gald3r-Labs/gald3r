#!/usr/bin/env python3
"""Python port of g-hk-crash-record.ps1 (T511, originally T433).

CRASH activation recorder hook. Appends one activation record to
.gald3r/logs/crash_activations.jsonl for the manual/heuristic recording path —
the Skills / Agents / Hooks / Rules that have no native IDE harness event.

CRASH = Commands, Rules, Agents, Skills, Hooks. The engine auto-records every
*Command* it dispatches (see gald3r.crash + adapters/cli.py); IDE harnesses
(Cursor / Claude Code) do NOT emit a discrete event for every Rule / Skill /
Agent / Hook activation, so this hook is the explicit recording path for those:
a hook event, the gald3r skill/command runner, or an agent invokes it with a
JSON payload describing the component that just activated. Rule "activation"
has no native event (rules are always-loaded context), so a faithful
"rule fired" signal must be reported here explicitly.

T1624 (WS-A-1) additionally wired this hook into the canonical core's stop
chain (`CONCERN_CHAIN["stop"]` in g_hk_core.py, mirrored in the Claude/Cursor
trigger configs). Because the harness stop payload carries no CRASH fields,
the chained entry declares the component explicitly via CLI args
(``--component-type hook --component-name stop-chain --trigger-source
g_hk_core``). Payload fields, when present, always win over the CLI
declaration — the stdin JSON remains the primary interface.

Payload arrives on stdin as JSON and SHOULD include:
    component_type   one of: command | rule | agent | skill | hook
    component_name   e.g. g-skl-tasks, g-rl-00-always, g-hk-encoding-normalize
    trigger_source   what triggered it (a command/rule/hook/agent name)
    elapsed_ms       optional duration
    session_id       optional; falls back to GALD3R_SESSION_ID /
                     CURSOR_CONVERSATION_ID / a per-process id

Zero overhead when disabled: if GALD3R_CRASH_STATS is unset or 'off', this hook
records nothing and returns immediately (matches the engine's hot-path gate).
Non-blocking by design — never delays the event it observes, never touches
control-plane state (TASKS.md, BUGS.md, task/bug files). Emits a small JSON
object and always exits 0.

This is the transition-target sibling of g-hk-crash-record.ps1 (kept as a
PowerShell fallback). It prefers the bundled engine's
gald3r.crash.record_activation when importable, and falls back to a pure-stdlib
JSONL append that writes the identical ActivationRecord schema otherwise.
"""
# @subsystems: LOGGING_SYSTEM
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

# Output modes that mean "tracking enabled" (mirror gald3r.crash). Anything else
# (unset / empty / "off" / unknown) means disabled -> zero-overhead no-op.
_ENV_VAR = "GALD3R_CRASH_STATS"
_ACTIVE_MODES = ("show_in_response", "show_in_log", "show_in_terminal")
_COMPONENT_TYPES = ("command", "rule", "agent", "skill", "hook")
_LOG_NAME = "crash_activations.jsonl"


def _now_iso() -> str:
    """ISO-8601 UTC, second precision, trailing Z — matches the engine + .ps1."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _tracking_enabled() -> bool:
    return (os.environ.get(_ENV_VAR) or "").strip().lower() in _ACTIVE_MODES


def _resolve_session_id(payload_session: str) -> str:
    """Harness id if exported, else a per-process fallback (matches gald3r.crash)."""
    return (
        (payload_session or "").strip()
        or (os.environ.get("GALD3R_SESSION_ID") or "").strip()
        or (os.environ.get("CURSOR_CONVERSATION_ID") or "").strip()
        or f"proc-{uuid.uuid4().hex[:12]}"
    )


def _record_stdlib(root: Path, *, component_type: str, component_name: str,
                   trigger_source: str, elapsed_ms, session_id: str) -> None:
    """Pure-stdlib append of one JSONL record (engine-free fallback path).

    Writes the exact ActivationRecord schema so the engine's read_records /
    compute_stats parse it identically. Fail-soft: never raise into the host.
    """
    record = {
        "component_type": component_type,
        "component_name": component_name,
        "activated_at": _now_iso(),
        "session_id": session_id,
        "trigger_source": trigger_source,
        "elapsed_ms": elapsed_ms,
    }
    try:
        logs_dir = root / ".gald3r" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / _LOG_NAME, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="gald3r CRASH activation recorder hook (Python port of "
                    "g-hk-crash-record.ps1)")
    parser.add_argument("--project-root", dest="project_root", default="",
                        help="override project-root detection")
    # T1624: chained-invocation declaration args. When this hook runs inside a
    # canonical concern chain the stdin payload is the harness event (no CRASH
    # fields), so the chain entry declares the component here. Payload fields,
    # when present, always take precedence.
    parser.add_argument("--component-type", dest="component_type", default="",
                        help="component type fallback when absent from payload")
    parser.add_argument("--component-name", dest="component_name", default="",
                        help="component name fallback when absent from payload")
    parser.add_argument("--trigger-source", dest="trigger_source", default="",
                        help="trigger source fallback when absent from payload")
    args, _ = parser.parse_known_args()

    # ── Zero-overhead gate: only record when CRASH stats are enabled ─────────
    if not _tracking_enabled():
        print(json.dumps({"continue": True}))
        return 0

    # ── stdin payload (gald3r CRASH-event schema; CLI args as fallback) ─────
    payload = _hook_common.read_stdin_json()
    component_type = str(
        payload.get("component_type") or args.component_type or "skill"
    ).strip().lower()
    if component_type not in _COMPONENT_TYPES:
        # Tolerate free-form types like the engine does (no hard rejection).
        component_type = component_type or "skill"
    component_name = str(
        payload.get("component_name") or args.component_name or "unknown"
    )
    trigger_source = str(payload.get("trigger_source") or args.trigger_source or "")
    elapsed_ms = payload.get("elapsed_ms")
    session_id = _resolve_session_id(str(payload.get("session_id") or ""))

    # ── Locate project root ─────────────────────────────────────────────────
    root = Path(args.project_root) if args.project_root else _hook_common.project_root()

    # ── Record: prefer the engine's recorder (DRY), else pure-stdlib append ──
    recorded = False
    if _hook_common.bootstrap_engine():
        try:
            # T1624: gald3r.crash.record_activation has no session_id parameter —
            # it resolves the id itself from GALD3R_SESSION_ID. Bridge the
            # payload/harness session id through this process's env so the
            # engine-path record matches the stdlib-path record.
            if session_id and not session_id.startswith("proc-"):
                os.environ.setdefault("GALD3R_SESSION_ID", session_id)
            from gald3r import crash as _crash

            _crash.record_activation(
                component_type, component_name,
                trigger_source=trigger_source, elapsed_ms=elapsed_ms,
                root=root, force=True,
            )
            recorded = True
        except Exception:
            recorded = False
    if not recorded:
        _record_stdlib(
            root, component_type=component_type, component_name=component_name,
            trigger_source=trigger_source, elapsed_ms=elapsed_ms,
            session_id=session_id,
        )

    # ── Non-blocking: never delay the observed event ────────────────────────
    print(json.dumps({
        "continue": True,
        "additional_context": f"[crash-record] {component_type}/{component_name} recorded.",
    }))
    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        try:
            print(json.dumps({"continue": True}))
        except Exception:
            pass
        sys.exit(0)
