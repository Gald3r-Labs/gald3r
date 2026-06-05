"""Task schema — the canonical vocabulary, status→folder / status→marker maps,
and validation. Mirrors `.gald3r_sys/schemas/task_file.v1.schema.yaml` so engine
output validates against the existing system.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

SCHEMA_VERSION = "task-file-v1"

TYPES = ["feature", "bug_fix", "refactor", "chore", "documentation"]
PRIORITIES = ["critical", "high", "medium", "low"]

# current (v1) lifecycle — exactly what the markdown system writes
STATUSES = [
    "pending", "speccing", "in-progress", "awaiting-verification",
    "verification-in-progress", "completed", "failed", "paused", "cancelled",
]
# accepted legacy/alias values (valid, but not written by new files)
LEGACY_STATUSES = ["waiting", "resource-gated", "requires-user-attention", "verified", "closed"]
ALL_STATUSES = STATUSES + LEGACY_STATUSES

REQUIRED = ["id", "title", "type", "status", "priority", "created_date"]

# status -> tasks/<folder>/  (canonical: awaiting-verification/ for the review states)
STATUS_FOLDER = {
    "pending": "open", "speccing": "open",
    "in-progress": "in-progress",
    "awaiting-verification": "awaiting-verification",
    "verification-in-progress": "awaiting-verification",
    "completed": "completed", "failed": "failed",
    "paused": "paused", "cancelled": "cancelled",
    # legacy
    "waiting": "open", "resource-gated": "open", "requires-user-attention": "open",
    "verified": "completed", "closed": "completed",
}

# status -> TASKS.md marker emoji (matches the .gald3r/TASKS.md legend)
STATUS_MARKER = {
    "pending": "📋", "speccing": "📝", "in-progress": "🔄",
    "awaiting-verification": "🔍", "verification-in-progress": "🕵️",
    "completed": "✅", "failed": "❌", "cancelled": "❌", "paused": "⏸️",
    "resource-gated": "⏳", "waiting": "⏳", "requires-user-attention": "🚨",
    "verified": "✅", "closed": "✅",
}

TERMINAL = {"completed", "failed", "cancelled", "verified", "closed"}

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
    return errs
