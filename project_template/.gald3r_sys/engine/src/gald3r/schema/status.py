"""status.py — the single source of truth for bug & task status vocabularies (T519).

One enum per item type. From these enums the engine derives EVERYTHING else:
the `bugs.py` `_STATUSES`/`_FOLDER`/`_MARKER`/`_TERMINAL` maps, the `schema/task.py`
`STATUSES`/`LEGACY_STATUSES`/`STATUS_FOLDER`/`STATUS_MARKER`/`TERMINAL` maps, and the
status enums declared in the YAML schemas
(`.gald3r_sys/schemas/{bug,task}_file.v1.schema.yaml`).

Why this module exists
-----------------------
`bugs.py` carried an inline 17-value `_STATUSES` while `bug_file.v1.schema.yaml` declared
only 7, so engine-valid statuses (``resolved``, ``pending``, ``completed``, ``documented``,
``paused`` ...) were schema-INVALID — the literal source of "previously unknown but valid
statuses". Deriving both sides from one enum makes that divergence impossible. A test
(`tests/test_status_vocab.py`) fails if the enum, the engine maps, and the two YAML schema
enums ever drift apart again.

Design note (T519 AC: "a Pydantic `StrEnum` (or equivalent)")
-------------------------------------------------------------
The engine is a pure-core package with a single runtime dependency (``pyyaml``). Adding
``pydantic`` for one enum would violate that minimalism (g-rl-38 Simplicity First) and the
engine's stated "Mode A pure core" contract. We use the stdlib ``(str, Enum)`` — the
documented *equivalent*. It is value-comparable to plain strings (``BugStatus.OPEN ==
"open"``), works on ``requires-python >= 3.10`` (``enum.StrEnum`` is 3.11+), and needs no
new dependency.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set

# ----------------------------------------------------------------------------------------
# Bug status
# ----------------------------------------------------------------------------------------


class BugStatus(str, Enum):
    """Canonical bug lifecycle vocabulary — the values new bug files are written with."""

    OPEN = "open"
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    AWAITING_VERIFICATION = "awaiting-verification"
    VERIFICATION_IN_PROGRESS = "verification-in-progress"
    REQUIRES_USER_ATTENTION = "requires-user-attention"
    RESOLVED = "resolved"
    FIXED = "fixed"
    COMPLETED = "completed"
    DOCUMENTED = "documented"
    VERIFIED = "verified"
    CLOSED = "closed"
    ARCHIVED = "archived"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    WONT_FIX = "wont_fix"


# Bucket each canonical status into a folder (.gald3r/bugs/<folder>/) and a TASKS-style marker.
_BUG_FOLDER: Dict[BugStatus, str] = {
    BugStatus.OPEN: "open",
    BugStatus.PENDING: "open",
    BugStatus.IN_PROGRESS: "open",
    BugStatus.AWAITING_VERIFICATION: "open",
    BugStatus.VERIFICATION_IN_PROGRESS: "open",
    BugStatus.REQUIRES_USER_ATTENTION: "open",
    BugStatus.RESOLVED: "done",
    BugStatus.FIXED: "done",
    BugStatus.COMPLETED: "done",
    BugStatus.DOCUMENTED: "done",
    BugStatus.VERIFIED: "done",
    BugStatus.CLOSED: "done",
    BugStatus.ARCHIVED: "done",
    BugStatus.PAUSED: "paused",
    BugStatus.CANCELLED: "cancelled",
    BugStatus.WONT_FIX: "cancelled",
}
_BUG_MARKER: Dict[BugStatus, str] = {
    BugStatus.OPEN: "📋",
    BugStatus.PENDING: "📋",
    BugStatus.IN_PROGRESS: "🔄",
    BugStatus.AWAITING_VERIFICATION: "🔍",
    BugStatus.VERIFICATION_IN_PROGRESS: "🕵️",
    BugStatus.REQUIRES_USER_ATTENTION: "🚨",
    BugStatus.RESOLVED: "✅",
    BugStatus.FIXED: "✅",
    BugStatus.COMPLETED: "✅",
    BugStatus.DOCUMENTED: "✅",
    BugStatus.VERIFIED: "✅",
    BugStatus.CLOSED: "✅",
    BugStatus.ARCHIVED: "❌",
    BugStatus.PAUSED: "⏸️",
    BugStatus.CANCELLED: "❌",
    BugStatus.WONT_FIX: "❌",
}
_BUG_TERMINAL: Set[BugStatus] = {
    BugStatus.RESOLVED,
    BugStatus.FIXED,
    BugStatus.COMPLETED,
    BugStatus.DOCUMENTED,
    BugStatus.VERIFIED,
    BugStatus.CLOSED,
    BugStatus.CANCELLED,
    BugStatus.WONT_FIX,
    BugStatus.ARCHIVED,
}

# Accepted non-canonical aliases -> canonical enum member. These keep already-valid legacy
# tokens working (AC6: no behavior change to valid files) while ``wont_fix`` stays canonical.
# Case variants (``Open``, ``Resolved``) are handled by ``.lower()`` in ``normalize_*``.
BUG_ALIASES: Dict[str, BugStatus] = {
    "wont-fix": BugStatus.WONT_FIX,
}

# ----------------------------------------------------------------------------------------
# Task status
# ----------------------------------------------------------------------------------------


class TaskStatus(str, Enum):
    """Current task lifecycle — exactly what new task files are written with."""

    PENDING = "pending"
    SPECCING = "speccing"
    IN_PROGRESS = "in-progress"
    AWAITING_VERIFICATION = "awaiting-verification"
    VERIFICATION_IN_PROGRESS = "verification-in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


_TASK_FOLDER: Dict[TaskStatus, str] = {
    TaskStatus.PENDING: "open",
    TaskStatus.SPECCING: "open",
    TaskStatus.IN_PROGRESS: "in-progress",
    TaskStatus.AWAITING_VERIFICATION: "awaiting-verification",
    TaskStatus.VERIFICATION_IN_PROGRESS: "awaiting-verification",
    TaskStatus.COMPLETED: "completed",
    TaskStatus.FAILED: "failed",
    TaskStatus.PAUSED: "paused",
    TaskStatus.CANCELLED: "cancelled",
}
_TASK_MARKER: Dict[TaskStatus, str] = {
    TaskStatus.PENDING: "📋",
    TaskStatus.SPECCING: "📝",
    TaskStatus.IN_PROGRESS: "🔄",
    TaskStatus.AWAITING_VERIFICATION: "🔍",
    TaskStatus.VERIFICATION_IN_PROGRESS: "🕵️",
    TaskStatus.COMPLETED: "✅",
    TaskStatus.FAILED: "❌",
    TaskStatus.PAUSED: "⏸️",
    TaskStatus.CANCELLED: "❌",
}
_TASK_TERMINAL: Set[TaskStatus] = {
    TaskStatus.COMPLETED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
}

# Legacy task statuses: still VALID (back-compat) but not written by new files. Each maps to
# a folder + marker so the engine can place/render existing files that still use them.
TASK_LEGACY: List[str] = ["waiting", "resource-gated", "requires-user-attention", "verified", "closed"]
_TASK_LEGACY_FOLDER: Dict[str, str] = {
    "waiting": "open",
    "resource-gated": "open",
    "requires-user-attention": "open",
    "verified": "completed",
    "closed": "completed",
}
_TASK_LEGACY_MARKER: Dict[str, str] = {
    "waiting": "⏳",
    "resource-gated": "⏳",
    "requires-user-attention": "🚨",
    "verified": "✅",
    "closed": "✅",
}
# verified / closed are terminal-equivalent (folder=completed) for back-compat.
_TASK_LEGACY_TERMINAL: Set[str] = {"verified", "closed"}

# ----------------------------------------------------------------------------------------
# Derived, string-keyed maps (what bugs.py / schema/task.py actually consume)
# ----------------------------------------------------------------------------------------


def _expand(by_member: Dict, aliases: Dict[str, object]) -> Dict[str, str]:
    """Flatten an enum-keyed map to a {string_value: x} map, then graft alias keys on."""
    out: Dict[str, str] = {member.value: val for member, val in by_member.items()}
    for alias, canon in aliases.items():
        out[alias] = by_member[canon]
    return out


# --- bug (canonical members + aliases) ---
BUG_STATUSES: List[str] = [m.value for m in BugStatus] + list(BUG_ALIASES)
BUG_FOLDER: Dict[str, str] = _expand(_BUG_FOLDER, BUG_ALIASES)
BUG_MARKER: Dict[str, str] = _expand(_BUG_MARKER, BUG_ALIASES)
BUG_TERMINAL: Set[str] = {m.value for m in _BUG_TERMINAL} | {
    a for a, c in BUG_ALIASES.items() if c in _BUG_TERMINAL
}

# --- task (current members + legacy) ---
TASK_STATUSES: List[str] = [m.value for m in TaskStatus]
TASK_ALL_STATUSES: List[str] = TASK_STATUSES + TASK_LEGACY
TASK_FOLDER: Dict[str, str] = {m.value: f for m, f in _TASK_FOLDER.items()}
TASK_FOLDER.update(_TASK_LEGACY_FOLDER)
TASK_MARKER: Dict[str, str] = {m.value: mk for m, mk in _TASK_MARKER.items()}
TASK_MARKER.update(_TASK_LEGACY_MARKER)
TASK_TERMINAL: Set[str] = {m.value for m in _TASK_TERMINAL} | _TASK_LEGACY_TERMINAL

# The exact value lists the YAML schema status enums must contain (AC3/AC5). Order matters
# for a stable, readable schema diff: canonical first, then aliases/legacy.
BUG_SCHEMA_ENUM: List[str] = [m.value for m in BugStatus] + list(BUG_ALIASES)
TASK_SCHEMA_ENUM_CURRENT: List[str] = [m.value for m in TaskStatus]
TASK_SCHEMA_ENUM_LEGACY: List[str] = list(TASK_LEGACY)

# ----------------------------------------------------------------------------------------
# Normalization (AC4) — case + alias canonicalization, never silent-drop
# ----------------------------------------------------------------------------------------


def normalize_bug_status(raw: Optional[str]) -> Optional[str]:
    """Canonicalize a raw bug-status token to a ``BugStatus`` value, or ``None`` if unknown.

    Handles case (``Open`` -> ``open``, ``Resolved`` -> ``resolved``) and hyphen/underscore
    aliases (``wont-fix`` -> ``wont_fix``). Returns ``None`` for genuinely unknown tokens so
    callers can surface a validation error rather than silently coercing.
    """
    if raw is None:
        return None
    key = str(raw).strip().lower()
    if not key:
        return None
    if key in BUG_ALIASES:
        return BUG_ALIASES[key].value
    try:
        return BugStatus(key).value
    except ValueError:
        return None


def normalize_task_status(raw: Optional[str]) -> Optional[str]:
    """Canonicalize a raw task-status token to a current or legacy task status, or ``None``.

    Lower-cases (``Pending`` -> ``pending``); legacy values pass through unchanged (still
    valid). Returns ``None`` for unknown tokens.
    """
    if raw is None:
        return None
    key = str(raw).strip().lower()
    if not key:
        return None
    if key in TASK_ALL_STATUSES:
        return key
    return None
