#!/usr/bin/env python3
"""Shared canonical event core for gald3r hooks (T424).

This is the ONE place gald3r hook behavior is authored. Every platform's
trigger layer (Cursor `hooks.json`, Claude `settings.json`/`hooks.json`,
Kiro CLI agent-JSON `hooks` field, etc.) delegates here so behavior is
identical no matter which harness fired the event.

Architecture (T424 — event-consolidation + shared-core):

1. Canonical event set (`CANONICAL_EVENTS`) — the shared FLOOR of lifecycle
   moments COMMONLY supported across hook-capable platforms. This is a floor,
   NOT a ceiling: every capable platform routes at least these through the one
   core so behavior is identical everywhere. A platform's native events fold
   onto these via `PLATFORM_EVENT_MAP`; a RICHER platform (e.g. Cursor, ~18
   native events) keeps ALL of its events and may register additional concern
   chains — it is never dumbed down to only the canonical set. A WEAKER
   platform wires only the subset it supports and degrades gracefully. The
   floor guarantees cross-platform parity; it does not cap any platform.
2. Per-event concern chain (`CONCERN_CHAIN`) — the ordered list of concern
   hook scripts that run for a canonical event. The existing T1584 Python
   hooks (which import `_hook_common`) ARE those concern handlers; this core
   reuses them rather than reinventing their logic.
3. `dispatch(event)` — reads the harness payload from stdin ONCE, runs every
   concern hook in the chain with that same payload, merges their
   `additional_context`, honors the first blocking verdict, and emits a
   single unified response envelope. Thin per-platform shims and the bundled
   canonical entrypoints (`g-hk-<event>.py`) all call this.

Hooks must never crash the host session: `dispatch` is fully fail-soft and
returns exit 0 (continue) on any unexpected error unless a concern hook
explicitly blocked a tool call (exit 2, tool events only).
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent

# ── Canonical reduced event set (T424 AC0) ──────────────────────────────────
# These are the shared FLOOR (not a ceiling): each is COMMONLY supported across
# hook-capable platforms (see PLATFORM_EVENT_MAP), so every platform routes at
# least these through the core for identical behavior. Strong platforms (Cursor,
# ~18 native events) keep their richer events and may add concern chains; weak
# platforms wire only the subset they support. This is the common denominator
# that guarantees parity, NOT a cap on any platform's capability.
CANONICAL_EVENTS: Dict[str, str] = {
    "session-start": "A new agent session/conversation begins. Context injection point.",
    "session-end": "An agent session terminates. Final cleanup / reflection point.",
    "user-prompt-submit": "The user submits a prompt, before the agent acts on it.",
    "tool-start": "Before a tool/action executes. The blocking guard point.",
    "tool-end": "After a tool/action completes. Post-action reaction point.",
    "stop": "The agent finishes responding to a turn (distinct from session-end).",
}

# ── Platform native event -> canonical event (T424 AC0 machine-readable map) ─
# Source: each platform's PLATFORM_SPEC `## Hook System` section (verified
# 2026-06-18). `pre-commit` is a git-level hook, not an agent-lifecycle event,
# so it is intentionally NOT a canonical event here (handled by the existing
# g-hk-pre-commit git hook). Platforms with no native hook surface (warp, roo,
# replit, subq, aider*, mistral*) are omitted.
PLATFORM_EVENT_MAP: Dict[str, Dict[str, str]] = {
    "cursor": {
        "sessionStart": "session-start",
        "sessionEnd": "session-end",
        "beforeSubmitPrompt": "user-prompt-submit",
        "preToolUse": "tool-start",
        "beforeShellExecution": "tool-start",
        "postToolUse": "tool-end",
        "stop": "stop",
    },
    "claude": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "gemini": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "BeforeTool": "tool-start",
        "AfterTool": "tool-end",
        "AfterAgent": "stop",
    },
    "codex": {
        "SessionStart": "session-start",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "qwen": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "goose": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "openhands": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "augment": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "copilot": {
        "sessionStart": "session-start",
        "sessionEnd": "session-end",
        "userPromptSubmitted": "user-prompt-submit",
        "preToolUse": "tool-start",
        "postToolUse": "tool-end",
    },
    "windsurf": {
        "pre_user_prompt": "user-prompt-submit",
        "pre_run_command": "tool-start",
        "pre_write_code": "tool-start",
        "post_run_command": "tool-end",
        "post_write_code": "tool-end",
        "post_cascade_response": "stop",
    },
    "kiro-cli": {
        "agentSpawn": "session-start",
        "userPromptSubmit": "user-prompt-submit",
        "preToolUse": "tool-start",
        "postToolUse": "tool-end",
        "stop": "stop",
    },
    "antigravity": {
        "before_model_call": "session-start",
        "before_tool_call": "tool-start",
        "after_tool_call": "tool-end",
        "on_loop_stop": "stop",
    },
    "opencode": {
        "session.created": "session-start",
        "session.deleted": "session-end",
        "tool.execute.before": "tool-start",
        "tool.execute.after": "tool-end",
        "session.idle": "stop",
    },
    "cline": {
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
    },
    "junie": {
        "SessionStart": "session-start",
    },
    # Kiro IDE uses a file-event model (.kiro.hook fileEdited/userTriggered)
    # that does not map onto the agent-lifecycle canonical set; its trigger
    # is authored directly as a .kiro.hook file, not via this dispatcher.
}

# ── Canonical event -> ordered concern hook chain (T424 AC1) ────────────────
# Each entry is [basename, *extra_args]. The dispatcher locates `<base>.py`
# (preferred) or `<base>.ps1` (fallback) next to this file and runs it with
# the same stdin payload. This reuses the T1584 Python hooks as the concern
# handlers so behavior is authored once. tool-end / user-prompt-submit have
# no concern hooks yet — their canonical handler is a clean pass-through that
# platforms can now fire (and future concern hooks register here).
CONCERN_CHAIN: Dict[str, List[List[str]]] = {
    "session-start": [
        ["g-hk-session-start"],
    ],
    "session-end": [
        ["g-hk-session-end"],
    ],
    "user-prompt-submit": [],
    "tool-start": [
        ["g-hk-validate-shell"],
        ["g-hk-pre-tool-call-gald3r-guard"],
        ["g-hk-pre-tool-call-prd-freeze"],
        ["g-hk-pre-tool-call-member-gald3r-guard"],
        ["g-hk-pre-tool-call"],
    ],
    "tool-end": [],
    "stop": [
        ["g-hk-agent-complete"],
        ["g-hk-nightly-learn"],
        ["g-hk-encoding-normalize", "-Quiet"],
        ["g-hk-ggo-stop-detect"],
    ],
}


def _read_raw_stdin() -> str:
    """Read the raw harness payload once so it can be re-fed to each concern."""
    try:
        if sys.stdin.isatty():
            return ""
        return sys.stdin.read() or ""
    except (OSError, ValueError):
        return ""


def _locate(base_name: str):
    """Resolve a concern hook to a runnable command, preferring .py over .ps1."""
    py_path = SCRIPT_DIR / (base_name + ".py")
    if py_path.is_file():
        return [sys.executable, str(py_path)]
    ps1_path = SCRIPT_DIR / (base_name + ".ps1")
    if ps1_path.is_file():
        import shutil

        exe = shutil.which("powershell") or shutil.which("pwsh")
        if exe:
            return [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    str(ps1_path)]
    return None


def _is_block(payload: Dict[str, Any], returncode: int) -> bool:
    """Detect a blocking verdict from a concern hook's response/exit code."""
    if returncode == 2:
        return True
    if payload.get("continue") is False:
        return True
    decision = str(payload.get("decision", "")).lower()
    if decision in ("block", "deny"):
        return True
    perm = payload.get("permission")
    if isinstance(perm, dict) and str(perm.get("decision", "")).lower() == "deny":
        return True
    return False


def _run_concern(cmd: List[str], extra_args: List[str], raw_stdin: str):
    """Run one concern hook with the shared payload; return (payload, rc)."""
    try:
        res = subprocess.run(
            cmd + list(extra_args),
            input=raw_stdin,
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
    except (OSError, subprocess.SubprocessError):
        return {}, 0
    payload: Dict[str, Any] = {}
    out = (res.stdout or "").strip()
    if out:
        try:
            parsed = json.loads(out)
            if isinstance(parsed, dict):
                payload = parsed
        except (json.JSONDecodeError, ValueError):
            # Non-JSON stdout is treated as additional_context text.
            payload = {"additional_context": out}
    return payload, res.returncode


def dispatch(event: str) -> int:
    """Run the concern chain for a canonical event; emit a unified envelope.

    Returns the process exit code (2 when a tool event was blocked, else 0).
    """
    if event not in CANONICAL_EVENTS:
        # Unknown event — never block, just continue.
        print(json.dumps({"continue": True}, separators=(",", ":")))
        return 0

    raw_stdin = _read_raw_stdin()
    context_parts: List[str] = []
    blocked = False
    block_reason = ""

    for entry in CONCERN_CHAIN.get(event, []):
        base_name = entry[0]
        extra_args = entry[1:]
        cmd = _locate(base_name)
        if cmd is None:
            continue
        payload, rc = _run_concern(cmd, extra_args, raw_stdin)
        ctx = payload.get("additional_context")
        if isinstance(ctx, str) and ctx.strip():
            context_parts.append(ctx.strip())
        if not blocked and _is_block(payload, rc):
            blocked = True
            block_reason = str(
                payload.get("reason")
                or payload.get("block_reason")
                or ("%s blocked the %s event" % (base_name, event))
            )

    response: Dict[str, Any] = {"continue": not blocked}
    if context_parts:
        response["additional_context"] = "\n\n".join(context_parts)
    if blocked and block_reason:
        response["reason"] = block_reason

    print(json.dumps(response, separators=(",", ":")))
    # Only tool events use exit-code blocking (Cursor preToolUse, kiro-cli
    # preToolUse exit 2). Lifecycle events never hard-block via exit code.
    if blocked and event in ("tool-start",):
        return 2
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        # No event given: print the canonical event list as JSON (introspection).
        print(json.dumps({"canonical_events": list(CANONICAL_EVENTS.keys())},
                         separators=(",", ":")))
        return 0
    return dispatch(argv[0])


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
            print(json.dumps({"continue": True}, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
