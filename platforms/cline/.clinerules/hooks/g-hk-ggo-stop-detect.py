#!/usr/bin/env python3
"""Python port of g-hk-ggo-stop-detect.ps1 (T1584).

g-go-go stop-detection re-invoke hook (T1444, BUG-107 Fix Direction #2).
Fires under the "stop" event. Detects when a g-go-go autopilot run halts
mid-loop WITHOUT quoting an authorizing hard-stop row, and forces the loop
to continue by emitting a re-invoke decision plus a verbatim reminder of
the forbidden stop reasons.

State machine (file-first, .gald3r/logs/ggo_run_state.json):
  0. No active run            -> no-op (continue, exit 0).
  1. Platform mismatch        -> allow exit (different agent's run).
  2. Session mismatch         -> allow exit (different chat session).
  3. authorized_hard_stop set -> genuine hard stop; allow exit, clear marker.
  4. budget exhausted         -> allow exit (the budget cap IS a hard stop).
  5. re-invoke ceiling hit    -> allow exit (anti-infinite-loop fail-safe).
  6. otherwise (unauthorized) -> re-invoke: increment reinvoke_count, emit
     block/continue decision with the forbidden-reason reminder.

The calling platform is derived from this script's own folder path (the same
script is deployed to every platform's hook folder). A stored run owned by a
DIFFERENT platform or DIFFERENT session is NEVER re-invoked. First stop seen
for a run without a stored session_id registers the current session
(first-touch). The "block" is expressed via the stop-hook continuation
contract on stdout (Claude Code: {"decision":"block","reason":...}; Cursor:
{"continue":false,"followup":...}); the process itself always exits 0.
"""
# @subsystems: TASK_MANAGEMENT
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

# Hard ceiling on re-invokes regardless of budget (anti-infinite-loop
# fail-safe).
GGO_REINVOKE_CEILING = 25

SCRIPT_DIR = Path(__file__).resolve().parent

# Pattern order matters: '.kiro-cli' before '.kiro', '.agents' before
# '.agent'. (The '\.agent\' pattern cannot match '\.agents\' because the
# trailing separator is part of the needle.)
_PLATFORM_PATTERNS = (
    (".cursor", "cursor"),
    (".windsurf", "windsurf"),
    (".codex", "codex"),
    (".kiro-cli", "kiro-cli"),
    (".kiro", "kiro"),
    (".openhands", "openhands"),
    (".codebuddy", "codebuddy"),
    (".agents", "antigravity"),
    (".agent", "gemini"),
)


def detect_platform(script_dir):
    """Detect the calling platform from the hook's own folder path."""
    s = str(script_dir)
    if not s.endswith(("\\", "/")):
        s += "\\"
    for needle, platform in _PLATFORM_PATTERNS:
        if ("\\%s\\" % needle) in s or ("/%s/" % needle) in s:
            return platform
    return "claude"


def _utc_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser(
        description="g-go-go stop-detection re-invoke hook (Python port of "
                    "g-hk-ggo-stop-detect.ps1)")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default="",
                        help="Override project-root detection (defaults to "
                             "nearest .gald3r/ ancestor).")
    args, _unknown = parser.parse_known_args()

    current_platform = detect_platform(SCRIPT_DIR)

    # -- stdin payload (stop event schema) -----------------------------------
    payload = _hook_common.read_stdin_json()

    # -- Extract session_id from stop-event payload --------------------------
    current_session_id = ""
    if payload.get("session_id"):
        current_session_id = str(payload["session_id"])
    # Fallback: derive UUID from transcript_path filename pattern
    # e.g. .gald3r/logs/20260607_b24090d8-9d3a-4f83_claude_chat.jsonl
    if not current_session_id and payload.get("transcript_path"):
        m = re.search(r"[\\\/]\d{8}_([0-9a-f]{8}-[0-9a-f-]+)",
                      str(payload["transcript_path"]))
        if m:
            current_session_id = m.group(1)

    # -- Locate project root --------------------------------------------------
    project_root = args.project_root
    if not project_root:
        d = SCRIPT_DIR
        found = None
        while True:
            if (d / ".gald3r").exists():
                found = d
                break
            parent = d.parent
            if parent == d:
                break
            d = parent
        project_root = str(found) if found else str(Path.cwd())
    project_root = Path(project_root)

    logs_dir = project_root / ".gald3r" / "logs"
    state_file = logs_dir / "ggo_run_state.json"
    diag_log = logs_dir / "hook_diag.log"

    def write_diag(msg):
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(diag_log, "a", encoding="utf-8") as fh:
                fh.write("%s ggo-stop-detect [%s]: %s\n"
                         % (stamp, current_platform, msg))
        except OSError:
            pass

    def emit_allow_exit(context):
        """Allow-exit response: run is not being held open by this hook."""
        print(json.dumps({
            "continue": True,
            "additional_context": context,
        }, separators=(",", ":")))
        sys.exit(0)

    # Case 0: no active run marker -> this stop is unrelated to g-go-go.
    if not state_file.exists():
        emit_allow_exit("[ggo-stop-detect] No active g-go-go run; stop allowed.")

    # Read + parse the run-state marker.
    state = None
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise ValueError("state marker is not a JSON object")
    except (OSError, ValueError):
        write_diag("unreadable/invalid state marker; allowing exit")
        emit_allow_exit(
            "[ggo-stop-detect] Run-state marker unreadable; stop allowed.")

    active = bool(state.get("active", False))
    if not active:
        emit_allow_exit(
            "[ggo-stop-detect] g-go-go run not active; stop allowed.")

    # -- Case 1: Platform mismatch -- a different agent owns this run. --------
    stored_platform = str(state.get("platform") or "")
    if stored_platform and stored_platform != current_platform:
        write_diag("platform mismatch (stored=%s current=%s); allowing exit"
                   % (stored_platform, current_platform))
        emit_allow_exit(
            "[ggo-stop-detect] Platform mismatch: '%s' owns this run, '%s' "
            "is stopping — stop allowed."
            % (stored_platform, current_platform))

    # -- Case 2: Session mismatch -- a different chat instance. ---------------
    stored_session_id = str(state.get("session_id") or "")
    if (stored_session_id and current_session_id
            and stored_session_id != current_session_id):
        write_diag("session_id mismatch (stored=%s current=%s); allowing exit"
                   % (stored_session_id, current_session_id))
        emit_allow_exit(
            "[ggo-stop-detect] Session mismatch: run owned by session '%s', "
            "stopping session is '%s' — stop allowed."
            % (stored_session_id, current_session_id))

    # -- First-touch session registration (no session_id stored yet) ----------
    # The g-go-go INIT write does not have the session_id; the first stop
    # captures it.
    if not stored_session_id and current_session_id:
        try:
            state["session_id"] = current_session_id
            # Also backfill platform if INIT did not write it.
            if not stored_platform:
                state["platform"] = current_platform
            state["updated_at"] = _utc_stamp()
            state_file.write_text(json.dumps(state, indent=2),
                                  encoding="utf-8")
            write_diag("first-touch: registered session_id=%s platform=%s"
                       % (current_session_id, current_platform))
        except (OSError, TypeError, ValueError) as exc:
            write_diag("first-touch registration failed (non-fatal): %s" % exc)

    def _as_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    iteration = _as_int(state.get("iter")) if state.get("iter") is not None else 0
    budget_remaining = (_as_int(state.get("budget_remaining"))
                        if state.get("budget_remaining") is not None else 0)
    reinvoke_count = (_as_int(state.get("reinvoke_count"))
                      if state.get("reinvoke_count") is not None else 0)
    hard_stop = str(state.get("authorized_hard_stop") or "")

    def _clear_marker():
        try:
            state_file.unlink()
        except OSError:
            pass

    # Case 3: a genuine, authorized hard stop was recorded. Never re-invoke.
    if hard_stop.strip():
        write_diag('authorized hard stop recorded ("%s"); allowing exit and '
                   "clearing marker" % hard_stop)
        _clear_marker()
        emit_allow_exit(
            "[ggo-stop-detect] Authorized hard stop (%s); stop allowed."
            % hard_stop)

    # Case 4: budget exhausted -> the budget cap itself is a hard stop.
    if budget_remaining <= 0:
        write_diag("budget exhausted (budget_remaining=%d); allowing exit "
                   "and clearing marker" % budget_remaining)
        _clear_marker()
        emit_allow_exit(
            "[ggo-stop-detect] Run budget exhausted; stop allowed.")

    # Case 5: re-invoke ceiling reached -> anti-infinite-loop fail-safe.
    reinvoke_cap = min(budget_remaining, GGO_REINVOKE_CEILING)
    if reinvoke_count >= reinvoke_cap:
        write_diag("re-invoke cap reached (reinvoke_count=%d cap=%d); "
                   "allowing exit and clearing marker"
                   % (reinvoke_count, reinvoke_cap))
        _clear_marker()
        emit_allow_exit(
            "[ggo-stop-detect] Re-invoke cap reached (%d/%d); stop allowed "
            "(treat as hard stop)." % (reinvoke_count, reinvoke_cap))

    # Case 6: unauthorized mid-loop stop -> re-invoke with reminder.
    new_count = reinvoke_count + 1
    try:
        state["reinvoke_count"] = new_count
        state["updated_at"] = _utc_stamp()
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except (OSError, TypeError, ValueError):
        write_diag("failed to persist incremented reinvoke_count; "
                   "re-invoking anyway")

    write_diag("unauthorized mid-loop stop detected; re-invoking "
               "(reinvoke_count=%d/%d, iter=%d)"
               % (new_count, reinvoke_cap, iteration))

    reminder = (
        "[ggo-stop-detect / BUG-107] This g-go-go autopilot run is NOT "
        "authorized to stop.\n"
        "You halted mid-loop without quoting an authorizing hard-stop row. "
        "Per the g-go-go\n"
        "contract, a 'session checkpoint', 'handing off cleanly', 'natural "
        "stopping point',\n"
        "'good progress so far', or any context/complexity/subagent-count "
        "concern is the\n"
        "FORBIDDEN CONTEXT WINDOW PANIC stop wearing a gentler name -- it is "
        "not a valid exit.\n"
        "\n"
        "Resume the loop now. There are exactly two valid moves:\n"
        "  (a) run the next lowest-ID eligible iteration anyway (at N=1 "
        "bucket if needed), or\n"
        "  (b) if and only if a genuine hard-stop table row applies, write "
        "that verbatim row\n"
        "      into .gald3r/logs/ggo_run_state.json (field "
        "authorized_hard_stop) and THEN stop.\n"
        "If --context-aware is active, REDUCE the bucket count N (never "
        "below 1) instead of\n"
        "stopping. Re-invoke %d of %d. Continue." % (new_count, reinvoke_cap)
    )

    print(json.dumps({
        # Claude Code Stop-hook continuation contract.
        "decision": "block",
        "reason": reminder,
        # Cursor stop-hook continuation contract.
        "continue": False,
        "followup": reminder,
        "additional_context": reminder,
    }, separators=(",", ":")))
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
        # Fail-soft: never hold the host session open on an internal error.
        try:
            print(json.dumps({
                "continue": True,
                "additional_context":
                    "[ggo-stop-detect] Hook error; stop allowed.",
            }, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
