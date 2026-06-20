"""BugSystem — bug lifecycle over `.gald3r/bugs/` + `BUGS.md`. Cloned from the
folder-backed pattern (`_base.FolderSystem`). Mirrors `g-skl-bugs` / `g-bug-*`.
"""
from __future__ import annotations

import re
from typing import List

from gald3r.config import Config
from gald3r.ids import new_uuid
from gald3r.schema import status as _status
from gald3r.systems._base import FolderSystem, Item, ItemSpec

# Status vocabulary is owned by gald3r.schema.status (the BugStatus enum + alias map) — the
# single source of truth shared with bug_file.v1.schema.yaml (T519). Do not re-inline it here;
# tests/test_status_vocab.py fails if these and the YAML schema ever drift apart.
_STATUSES = _status.BUG_STATUSES
_FOLDER = _status.BUG_FOLDER
_MARKER = _status.BUG_MARKER
_TERMINAL = _status.BUG_TERMINAL

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


# Signatures that mark a BUGS.md as engine-generated (the render_index() output above).
# A hand-curated BUGS.md (rich resolution prose in the Status column, file-less historical
# rows, a `| ID | Title | Severity | Status | Created |` layout) has NEITHER.
_ENGINE_INDEX_MARKERS = ('schema_version: "BUGS-md-v1"', "## Next Bug ID:")


class BugSystem(FolderSystem):
    def __init__(self, config: Config):
        super().__init__(config, SPEC, render_index)

    def create(self, title, severity="medium", kind="code", status=None, body="", **fields):
        fields.setdefault("uuid", new_uuid())  # stable cross-project primary key (T522)
        return super().create(title=title, severity=severity, kind=kind,
                               status=status, body=body, **fields)

    def _index_is_curated(self) -> bool:
        """True when BUGS.md holds hand-curated bug rows the engine table can't reproduce
        (rich resolution prose, file-less historical entries) — it MUST NOT be overwritten
        (T521). Requires a POSITIVE signal (an actual `| BUG-NNN |` row) so a fresh/stub or
        engine-generated index is still regenerated normally."""
        text = self.store.read_text(self.index_path)
        if not text.strip():
            return False  # absent/empty -> the engine may create its own index
        if any(marker in text for marker in _ENGINE_INDEX_MARKERS):
            return False  # engine-generated -> safe to regenerate
        return bool(re.search(r"\|\s*BUG-\d+\s*\|", text))  # curated table rows present

    def sync(self):  # type: ignore[override]
        """Non-destructive over a curated BUGS.md (T521). The engine still reads bug *files*
        as the source of truth; it just refuses to clobber a curated index with its compact
        table. Reports phantom/orphan either way so drift is still visible."""
        if not self._index_is_curated():
            return super().sync()
        items = self._all()
        ids = {self._num(it.id) for it in items}
        referenced = self._index_ref_ids(self.store.read_text(self.index_path))
        return {
            "count": len(ids),
            "phantom": sorted(referenced - ids),
            "orphan": sorted(ids - referenced),
            "index_preserved": True,
            "warning": ("BUGS.md is hand-curated (resolution prose + file-less historical "
                        "rows); engine left it untouched to prevent data loss (T521). "
                        "Edit BUGS.md by hand, or run gald3r validate to see drift."),
        }
