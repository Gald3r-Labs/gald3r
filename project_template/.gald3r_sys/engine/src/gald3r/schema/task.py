"""Task schema — vocabulary helpers + validation. The status vocabulary itself
(`STATUSES`, `LEGACY_STATUSES`, the folder/marker/terminal maps) is owned by
`gald3r.schema.status` (the single source of truth shared with the YAML schemas, T519);
this module re-exports it under the historical names and keeps the task-specific
validation (`TYPES`, `PRIORITIES`, `RELEASE_HOLD_VALUES`, `REQUIRED`).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from gald3r.schema import status as _status

SCHEMA_VERSION = "task-file-v1"

TYPES = ["feature", "bug_fix", "refactor", "chore", "documentation"]
PRIORITIES = ["critical", "high", "medium", "low"]
# release-staging hold (T419): omitted/none = g-ship picks it up; manual/sync_required hold it back
RELEASE_HOLD_VALUES = ["none", "manual", "sync_required"]

# current (v1) lifecycle + accepted legacy values — sourced from the TaskStatus enum (T519)
STATUSES = _status.TASK_STATUSES
LEGACY_STATUSES = _status.TASK_LEGACY
ALL_STATUSES = _status.TASK_ALL_STATUSES

REQUIRED = ["id", "title", "type", "status", "priority", "created_date"]

# status -> tasks/<folder>/ and status -> TASKS.md marker emoji (derived from the enum)
STATUS_FOLDER = _status.TASK_FOLDER
STATUS_MARKER = _status.TASK_MARKER
TERMINAL = _status.TASK_TERMINAL

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def folder_for(status: str) -> str:
    return STATUS_FOLDER.get(status, "open")


def marker_for(status: str) -> str:
    return STATUS_MARKER.get(status, " ")


def validate(fm: Dict[str, Any]) -> List[str]:
    """Return a list of human-readable validation errors (empty = valid)."""
    errs: List[str] = []
    for k in REQUIRED:
        if k not in fm or fm[k] in (None, ""):
            errs.append(f"missing required field: {k}")
    if "id" in fm and not isinstance(fm["id"], int):
        errs.append("id must be an integer")
    if "title" in fm and isinstance(fm["title"], str) and len(fm["title"]) < 5:
        errs.append("title must be at least 5 characters")
    if fm.get("type") not in TYPES and "type" in fm:
        errs.append(f"type must be one of {TYPES}")
    if fm.get("priority") not in PRIORITIES and "priority" in fm:
        errs.append(f"priority must be one of {PRIORITIES}")
    if "status" in fm and fm["status"] not in ALL_STATUSES:
        errs.append(f"status '{fm.get('status')}' not in vocabulary")
    if "created_date" in fm and not _DATE.match(str(fm["created_date"])):
        errs.append("created_date must be YYYY-MM-DD")
    if fm.get("release_hold") not in (None, "") and fm.get("release_hold") not in RELEASE_HOLD_VALUES:
        errs.append(f"release_hold must be one of {RELEASE_HOLD_VALUES}")
    return errs
