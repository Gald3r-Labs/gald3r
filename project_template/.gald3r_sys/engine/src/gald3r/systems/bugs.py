"""BugSystem — bug lifecycle over `.gald3r/bugs/` + `BUGS.md`. Cloned from the
folder-backed pattern (`_base.FolderSystem`). Mirrors `g-skl-bugs` / `g-bug-*`.
"""
from __future__ import annotations

from typing import List

from gald3r.config import Config
from gald3r.systems._base import FolderSystem, Item, ItemSpec

_STATUSES = [
    "open", "pending", "in-progress", "awaiting-verification", "verification-in-progress",
    "resolved", "fixed", "completed", "documented", "paused", "cancelled", "requires-user-attention",
    "verified", "closed", "wont-fix", "wont_fix", "archived",
]
_FOLDER = {
    "open": "open", "pending": "open", "in-progress": "open",
    "awaiting-verification": "open", "verification-in-progress": "open",
    "requires-user-attention": "open",
    "resolved": "done", "fixed": "done", "completed": "done", "documented": "done",
    "verified": "done", "closed": "done", "archived": "done",
    "paused": "paused",
    "cancelled": "cancelled", "wont-fix": "cancelled", "wont_fix": "cancelled",
}
_MARKER = {
    "open": "📋", "pending": "📋", "in-progress": "🔄",
    "awaiting-verification": "🔍", "verification-in-progress": "🕵️",
    "resolved": "✅", "fixed": "✅", "completed": "✅", "documented": "✅",
    "verified": "✅", "closed": "✅", "cancelled": "❌", "wont-fix": "❌",
    "wont_fix": "❌", "archived": "❌", "paused": "⏸️", "requires-user-attention": "🚨",
}
_TERMINAL = {"resolved", "fixed", "completed", "documented", "verified",
             "closed", "cancelled", "wont-fix", "wont_fix", "archived"}

SPEC = ItemSpec(
    name="bug", dir_name="bugs", index_name="BUGS.md", file_prefix="bug",
    id_kind="prefix", id_prefix="BUG-", id_pad=3,
    statuses=_STATUSES, status_folder=_FOLDER, status_marker=_MARKER,
    terminal=_TERMINAL, default_status="open",
    required=["id", "title", "severity", "status", "kind"],
    enums={
        "severity": ["critical", "high", "medium", "low"],
        "kind": ["code", "spec_defect", "policy_incongruity", "design_gap"],
    },
)


def render_index(fs: FolderSystem, items: List[Item]) -> str:
    name = fs.cfg.project_name
    rows = "\n".join(
        f"| [{fs.marker(it.status)}] | {it.id} | {it.fm.get('title','')} | "
        f"{it.fm.get('severity','—')} | {it.fm.get('subsystems','—')} |"
        for it in items
    ) or ""
    next_id = fs._next_id()
    return f"""---
gald3r_rel_version: "{fs.cfg.gald3r_rel_version}"
schema_version: "BUGS-md-v1"
---
# BUGS.md — {name} Bug Tracker

## Status Indicators
<!-- DO NOT REMOVE THIS SECTION — agents depend on it for status parsing -->
- `[ ]` = Open (no bug file yet)
- `[📋]` = Documented (bug file created)
- `[🔄]` = Fix in progress
- `[🔍]` = Awaiting Verification
- `[🕵️]` = Verification In Progress
- `[✅]` = Resolved
- `[❌]` = Won't fix

## Bug Summary

| Status | ID | Bug | Severity | Subsystems |
|--------|----|-----|----------|------------|
{rows}

## Next Bug ID: {next_id}
"""


class BugSystem(FolderSystem):
    def __init__(self, config: Config):
        super().__init__(config, SPEC, render_index)

    def create(self, title, severity="medium", kind="code", status=None, body="", **fields):
        return super().create(title=title, severity=severity, kind=kind,
                               status=status, body=body, **fields)
