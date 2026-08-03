#!/usr/bin/env python3
"""Goal quit-condition stop hook (BUG-645).

Fires under the "stop" event, mirroring `g-hk-ggo-stop-detect.py`'s proven
state-machine pattern (T1444/BUG-107) but scoped to gald3r's OWN persistent
session-goal mechanism (`@g-goal`, `.gald3r/config/ACTIVE_GOAL.md`) instead
of the g-go-go autopilot run marker.

Why this exists
----------------
BUG-645 is a live incident (2026-08-03, ~70 minutes): a goal-locked session
kept re-blocking Stop with IDENTICAL feedback after the goal's underlying
work was genuinely complete, because gald3r's goal machinery (`g-goal.md`)
was documented ENTIRELY as agent self-discipline prose -- "when turn_budget
is exhausted, the loop surfaces a notice and pauses" -- with no mechanical
enforcement anywhere. An agent that (for whatever reason) keeps re-blocking
itself has no sanctioned, mechanical release valve. `g-hk-ggo-stop-detect.py`
already solved this exact class of problem for g-go-go (an
`authorized_hard_stop` terminal marker + `min(budget, ceiling)` re-invoke
cap); this hook brings the SAME two safety valves to the goal mechanism:

1. **Terminal-state clause** -- an EXPLICIT `condition_discharged` frontmatter
   flag (mirrors `authorized_hard_stop` semantics -- a documented, sanctioned
   terminal state, not silence) OR an AUTOMATIC no-runnable-work detection
   (open task/bug queue is empty across >= 2 consecutive sweeps) both allow
   the stop and stop re-blocking.
2. **Re-invoke ceiling** -- `min(turn_budget - turns_consumed,
   GOAL_REINVOKE_CEILING)`, the same shape as g-hk-ggo-stop-detect's
   `min(budget_remaining, 25)`.
3. **Escalation over repetition** -- if the underlying "remaining work" count
   is UNCHANGED across `STAGNATION_ESCALATION_THRESHOLD` consecutive checks
   (the actual livelock signature: re-blocking with zero forward progress),
   escalate (allow stop + notify) BEFORE the numeric ceiling is even reached.

Genuinely additive: `.gald3r/config/ACTIVE_GOAL.md` not existing (the
overwhelming majority of sessions, since `@g-goal` is opt-in) is a pure
no-op allow-exit, identical to `g-hk-ggo-stop-detect.py`'s own "no active
run" case 0. This hook never WEAKENS goal enforcement for a genuinely
in-progress, satisfiable goal -- case 6 (the default) still re-blocks with a
reminder exactly as `g-goal.md`'s own documented contract describes, it just
now ALSO guarantees a bounded number of re-blocks rather than an unbounded
one.

The pure decision core (`decide()`) takes no I/O beyond an optional injected
`remaining_work_resolver` -- see its own docstring -- so it is directly
unit-testable without stdin/subprocess plumbing (mirrors the
`outer_loop_progress_snapshot.record_*` convention: pure function in,
dict out, caller owns all I/O).
"""
# @subsystems: PROJECT_IDENTITY_SETUP
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
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

#: BUG-645 item 3 -- hard cap on identical-feedback re-blocks, mirroring
#: g-hk-ggo-stop-detect.py's GGO_REINVOKE_CEILING (25) but deliberately
#: smaller: the reported incident (~25 identical "standing by" turns) is
#: EXACTLY GGO's own ceiling value, so a goal-scoped ceiling that small would
#: still allow the full incident to replay. BUG-645's own suggested value.
GOAL_REINVOKE_CEILING = 5

#: BUG-645 item 4 -- "the same feedback re-fires N times with no state
#: delta" escalates BEFORE the numeric re-invoke ceiling above, since a
#: stuck run may still be within budget/ceiling while making zero progress.
STAGNATION_ESCALATION_THRESHOLD = 3

#: BUG-645 item 2 -- consecutive zero-remaining-work sweeps required before
#: the AUTOMATIC terminal-state clause fires (mirrors T579's own
#: BLOCKER_REPEAT_THRESHOLD=2 "quickly, but not on a single noisy reading"
#: rationale in outer_loop_progress_snapshot.py).
NO_RUNNABLE_WORK_STREAK_REQUIRED = 2

SCRIPT_DIR = Path(__file__).resolve().parent

_TASK_TERMINAL_STATUSES = frozenset({"completed", "verified", "closed", "cancelled"})
_BUG_TERMINAL_STATUSES = frozenset({"resolved", "wont-fix", "closed", "cancelled"})

_FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(?P<body>.*?)\r?\n---", re.S)
_KV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")


def parse_frontmatter(text: str) -> Dict[str, str]:
    """Scalar-only ``key: value`` frontmatter reader for ACTIVE_GOAL.md.

    Deliberately NOT a full YAML parser -- ACTIVE_GOAL.md's own schema
    (`g-goal.md`) is documented as flat scalar fields only, mirroring the
    same lightweight regex convention
    ``coordination.workspace.preflight.read_manifest_repositories`` already
    uses for workspace_manifest.yaml rather than adding a YAML dependency to
    a hook script."""
    m = _FRONTMATTER_RE.match(text) or _FRONTMATTER_RE.search(text)
    if not m:
        return {}
    out: Dict[str, str] = {}
    for line in re.split(r"\r?\n", m.group("body")):
        km = _KV_LINE_RE.match(line)
        if not km:
            continue
        key, value = km.group(1), km.group(2).strip()
        value = value.strip().strip('"').strip("'")
        out[key] = value
    return out


def patch_frontmatter_fields(text: str, updates: Dict[str, str]) -> str:
    """Return *text* with each ``updates`` key set inside the frontmatter
    block, preserving every other line untouched. A key not already present
    is appended just before the closing ``---``. Never raises; returns
    *text* unchanged when no frontmatter block is found (defensive -- the
    caller already checked the file exists and parsed once)."""
    if not updates:
        return text
    m = _FRONTMATTER_RE.match(text) or _FRONTMATTER_RE.search(text)
    if not m:
        return text
    body_lines = re.split(r"\r?\n", m.group("body"))
    remaining = dict(updates)
    new_lines = []
    for line in body_lines:
        km = _KV_LINE_RE.match(line)
        if km and km.group(1) in remaining:
            new_lines.append(f"{km.group(1)}: {remaining.pop(km.group(1))}")
        else:
            new_lines.append(line)
    for key, value in remaining.items():
        new_lines.append(f"{key}: {value}")
    new_body = "\n".join(new_lines)
    start, end = m.span("body")
    return text[: start] + new_body + text[end:]


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _as_optional_int(value: Any) -> Optional[int]:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def count_runnable_work(project_root: Path) -> Optional[int]:
    """Best-effort count of ALL still-open task/bug rows (no value/severity
    floor -- every non-terminal row counts) via the project's own
    ``.gald3r/gald3r.db``. Returns ``None`` (never raises, never guesses)
    when no DB exists yet or the read fails -- an honest "cannot determine"
    is required here because guessing zero would wrongly auto-discharge a
    goal that is actually still open.

    Deliberately a small, dependency-light raw ``sqlite3`` (stdlib) query
    rather than importing ``gald3r_core.project.gald3r_integration.queries``
    -- this script ships verbatim under ``neutral_source/`` to every
    supported platform's generated install (BUG-356/BUG-531's IP-leak
    audit), so a hook script here must never carry a literal
    ``from gald3r_core ...`` import, even a guarded one. Mirrors
    ``drift_score.py``'s own documented precedent for exactly this
    situation (``KNOWN_ENGINE_IMPORT_EXCEPTIONS``'s "falls back to a small
    dependency-light reimplemented parser" note) -- implemented as the
    dependency-light path from the start instead of via a guarded import
    + fallback.
    """
    db_path = project_root / ".gald3r" / "gald3r.db"
    if not db_path.is_file():
        return None
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            task_rows = conn.execute("SELECT status FROM tasks").fetchall()
            bug_rows = conn.execute("SELECT status FROM bugs").fetchall()
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    open_tasks = sum(
        1
        for (status,) in task_rows
        if (status or "").strip().lower() not in _TASK_TERMINAL_STATUSES
    )
    open_bugs = sum(
        1
        for (status,) in bug_rows
        if (status or "").strip().lower() not in _BUG_TERMINAL_STATUSES
    )
    return open_tasks + open_bugs


def decide(
    goal_fields: Dict[str, str],
    *,
    project_root: Path,
    remaining_work_resolver: Callable[[Path], Optional[int]] = count_runnable_work,
) -> Dict[str, Any]:
    """Pure BUG-645 decision core: given ACTIVE_GOAL.md's parsed frontmatter
    fields, decide whether to allow this stop or re-block it.

    Returns a dict with:
      - ``action``: ``"allow"`` | ``"block"``
      - ``reason``: short machine-readable reason (also the human reminder
        text on ``"block"``)
      - ``updates``: frontmatter fields to persist back (may be empty)
      - ``notify``: an operator-facing message when a QUIT CONDITION (not
        genuine goal satisfaction) is why the stop is being allowed, else
        ``None``

    Order mirrors g-hk-ggo-stop-detect.py's case ordering: explicit terminal
    state, then automatic terminal state, then the pre-existing turn-budget
    contract, then the numeric re-invoke ceiling, then stagnation
    escalation, and only then the default re-block.
    """
    turn_budget = _as_int(goal_fields.get("turn_budget"), 50)
    turns_consumed = _as_int(goal_fields.get("turns_consumed"), 0)
    reinvoke_count = _as_int(goal_fields.get("reinvoke_count"), 0)
    condition_discharged = _as_bool(goal_fields.get("condition_discharged"))
    zero_remaining_streak = _as_int(goal_fields.get("zero_remaining_work_streak"), 0)
    last_remaining = _as_optional_int(goal_fields.get("last_remaining_work_count"))
    stagnant_checks = _as_int(goal_fields.get("stagnant_checks"), 0)
    description = str(goal_fields.get("description") or "(no description)")

    # 0. Vestigial-template guard (BUG-654, found on this hook's FIRST live
    #    firing): a scaffolded-but-never-set ACTIVE_GOAL.md carries
    #    ``id: null`` / ``description: ""`` / ``set_at: null``. File-exists
    #    alone is NOT goal-active -- a goal with no id, no description, and
    #    no set_at was never actually set by @g-goal/@g-mission, and blocking
    #    every stop against "(no description)" is a livelock on a phantom.
    #    Deliberately conservative, two ways: any ONE real signal (id,
    #    non-empty description, or set_at) keeps the goal enforceable, AND
    #    all three keys must actually be PRESENT in the frontmatter -- a
    #    minimal hand-authored goal file that omits them entirely is not the
    #    scaffold-template shape and stays enforced.
    def _is_null(v: Any) -> bool:
        return v is None or str(v).strip().lower() in ("", "null", "~", "none")

    if (
        all(k in goal_fields for k in ("id", "description", "set_at"))
        and _is_null(goal_fields.get("id"))
        and _is_null(goal_fields.get("description"))
        and _is_null(goal_fields.get("set_at"))
    ):
        return {
            "action": "allow",
            "reason": "vestigial goal template (id/description/set_at all null) -- no goal was ever set; stop allowed",
            "updates": {},
            "notify": None,
        }

    # 1. Explicit terminal-state clause (BUG-645 item 2, human/agent-set
    #    half) -- mirrors authorized_hard_stop: a documented, sanctioned
    #    terminal state, never silence.
    if condition_discharged:
        return {
            "action": "allow",
            "reason": "condition_discharged set -- goal terminal state recognized",
            "updates": {},
            "notify": None,
        }

    remaining = remaining_work_resolver(project_root)

    # 2. Automatic terminal-state clause (BUG-645 item 2, machine-derived
    #    half): the open task/bug queue is empty across >= 2 consecutive
    #    sweeps. A SINGLE zero reading is not trusted alone (a transient DB
    #    read race is possible) -- requires the same repeat-before-trust
    #    discipline T579's own blocker tracking uses.
    zero_remaining_streak = zero_remaining_streak + 1 if remaining == 0 else 0
    if remaining == 0 and zero_remaining_streak >= NO_RUNNABLE_WORK_STREAK_REQUIRED:
        return {
            "action": "allow",
            "reason": (
                f"no runnable work remained across {zero_remaining_streak} "
                "consecutive sweeps -- goal appears unsatisfiable or already satisfied"
            ),
            "updates": {
                "condition_discharged": "true",
                "zero_remaining_work_streak": str(zero_remaining_streak),
            },
            "notify": (
                "[goal-stop-detect] Goal appears unsatisfiable or already satisfied "
                f"(no runnable work across {zero_remaining_streak} consecutive "
                "checks) -- run @g-goal clear."
            ),
        }

    # 3. Turn budget exhausted -- g-goal.md's own pre-existing documented
    #    contract ("pauses for user direction"), now mechanically enforced.
    if turns_consumed >= turn_budget:
        return {
            "action": "allow",
            "reason": f"turn budget exhausted ({turns_consumed}/{turn_budget})",
            "updates": {"zero_remaining_work_streak": str(zero_remaining_streak)},
            "notify": (
                f"[goal-stop-detect] Turn budget exhausted ({turns_consumed}/"
                f"{turn_budget}) -- stop allowed; run @g-goal status for direction."
            ),
        }

    # 4. Re-invoke ceiling (BUG-645 item 3) -- min(remaining budget, cap),
    #    the exact shape g-hk-ggo-stop-detect.py uses.
    reinvoke_cap = min(max(turn_budget - turns_consumed, 0), GOAL_REINVOKE_CEILING)
    if reinvoke_count >= reinvoke_cap:
        return {
            "action": "allow",
            "reason": f"re-invoke ceiling reached ({reinvoke_count}/{reinvoke_cap})",
            "updates": {"zero_remaining_work_streak": str(zero_remaining_streak)},
            "notify": (
                f"[goal-stop-detect] Re-invoke ceiling reached ({reinvoke_count}/"
                f"{reinvoke_cap}) -- stop allowed rather than looping further; "
                "run @g-goal status for direction."
            ),
        }

    # 5. Escalation over repetition (BUG-645 item 4): the remaining-work
    #    count has not moved across STAGNATION_ESCALATION_THRESHOLD
    #    consecutive checks -- the actual reported livelock signature
    #    (identical feedback, zero forward progress) -- fires BEFORE the
    #    numeric ceiling above so a stuck-but-still-in-budget run does not
    #    have to burn its whole ceiling first.
    if remaining is not None and remaining > 0 and remaining == last_remaining:
        stagnant_checks += 1
    else:
        stagnant_checks = 1 if remaining is not None else stagnant_checks
    if stagnant_checks >= STAGNATION_ESCALATION_THRESHOLD:
        return {
            "action": "allow",
            "reason": (
                f"remaining work count stagnant at {remaining} across "
                f"{stagnant_checks} consecutive checks -- escalating instead of "
                "re-blocking"
            ),
            "updates": {
                "last_remaining_work_count": str(remaining),
                "stagnant_checks": str(stagnant_checks),
                "zero_remaining_work_streak": str(zero_remaining_streak),
            },
            "notify": (
                f"[goal-stop-detect] No progress across {stagnant_checks} "
                "consecutive checks (same remaining-work count) -- stop allowed; "
                "run @g-goal status for direction."
            ),
        }

    # 6. Otherwise: still genuinely in progress -- re-block with a reminder,
    #    exactly matching g-goal.md's documented contract, now bounded.
    new_turns_consumed = turns_consumed + 1
    new_reinvoke_count = reinvoke_count + 1
    reminder = (
        "[goal-stop-detect / BUG-645] Active goal not yet complete: "
        f'"{description}"\n'
        f"Turn {new_turns_consumed}/{turn_budget}, re-invoke "
        f"{new_reinvoke_count}/{reinvoke_cap}. Continue working toward the goal. "
        "If the goal is genuinely satisfied or has become permanently "
        "unsatisfiable, run @g-goal clear rather than repeating this stop."
    )
    return {
        "action": "block",
        "reason": reminder,
        "updates": {
            "turns_consumed": str(new_turns_consumed),
            "reinvoke_count": str(new_reinvoke_count),
            "last_remaining_work_count": (
                "" if remaining is None else str(remaining)
            ),
            "stagnant_checks": str(stagnant_checks),
            "zero_remaining_work_streak": str(zero_remaining_streak),
        },
        "notify": None,
    }


def _find_project_root() -> Path:
    d = SCRIPT_DIR
    while True:
        if (d / ".gald3r").exists():
            return d
        parent = d.parent
        if parent == d:
            return Path.cwd()
        d = parent


def main() -> int:
    # Read (and discard) the stop-event stdin payload -- this hook needs
    # nothing from it (unlike g-hk-ggo-stop-detect.py's session/platform
    # pinning, a goal has no owning-session concept: ACTIVE_GOAL.md is a
    # single project-wide file, not a per-run marker), but reading it keeps
    # this hook's stdin contract identical to every sibling stop concern.
    _hook_common.read_stdin_json()

    project_root = _find_project_root()
    goal_file = project_root / ".gald3r" / "config" / "ACTIVE_GOAL.md"

    def emit_allow(context: str) -> int:
        print(json.dumps({"continue": True, "additional_context": context},
                          separators=(",", ":")))
        return 0

    if not goal_file.is_file():
        return emit_allow("[goal-stop-detect] No active goal; stop allowed.")

    try:
        text = goal_file.read_text(encoding="utf-8-sig")
    except OSError:
        return emit_allow("[goal-stop-detect] ACTIVE_GOAL.md unreadable; stop allowed.")

    fields = parse_frontmatter(text)
    if not fields:
        return emit_allow(
            "[goal-stop-detect] ACTIVE_GOAL.md has no parseable frontmatter; "
            "stop allowed."
        )

    result = decide(fields, project_root=project_root)

    if result["updates"]:
        try:
            goal_file.write_text(
                patch_frontmatter_fields(text, result["updates"]), encoding="utf-8"
            )
        except OSError:
            pass  # non-fatal -- the decision below still applies this pass

    if result["action"] == "allow":
        context = result["reason"]
        if result.get("notify"):
            context = result["notify"]
        return emit_allow(f"[goal-stop-detect] {context}")

    reminder = result["reason"]
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
                    "[goal-stop-detect] Hook error; stop allowed.",
            }, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
