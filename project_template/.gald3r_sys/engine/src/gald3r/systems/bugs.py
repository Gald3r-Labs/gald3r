"""BugSystem — bug lifecycle over `.gald3r/bugs/` + `BUGS.md`. Cloned from the
folder-backed pattern (`_base.FolderSystem`). Mirrors `g-skl-bugs` / `g-bug-*`.
"""
from __future__ import annotations

import re
from typing import List

from gald3r.config import Config
from gald3r.ids import new_uuid
from gald3r.run_state import is_agent_run_active
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

    def create(self, title, severity="medium", kind="code", status=None, body="",
               route_inbox=None, **fields):
        fields.setdefault("uuid", new_uuid())  # stable cross-project primary key (T522)
        # T585: route to bugs/inbox/ as an id-less draft during an active agent
        # run; the hot-inbox intake assigns the real id. intake forces False.
        if route_inbox is None:
            route_inbox = is_agent_run_active(self.cfg.gald3r_dir)
        if route_inbox:
            return self._queue_inbox_draft(title=title, severity=severity,
                                           kind=kind, status=status, body=body,
                                           fields=fields)
        return super().create(title=title, severity=severity, kind=kind,
                               status=status, body=body, **fields)

    def _queue_inbox_draft(self, *, title, severity, kind, status, body, fields) -> Item:
        """Write an id-less bug draft to ``bugs/inbox/`` (T585).

        Returns a sentinel ``Item`` (``id="BUG-0"``, ``inbox_queued=True``) — NOT
        a live tracked bug. No id assigned, index untouched; the next
        ``InboxSystem.intake()`` assigns the id. The draft uses ``priority:`` for
        the severity (the field intake's ``_read_draft`` maps to severity), and a
        uuid-suffixed filename so concurrent same-titled bugs never collide.
        """
        from datetime import date
        uid = fields.get("uuid") or new_uuid()
        fields["uuid"] = uid
        cdate = fields.get("created_date") or date.today().isoformat()
        inbox = self.cfg.gald3r_dir / "bugs" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        slug = (re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "bug")[:40]
        fm = {
            "title": title, "priority": severity, "kind": kind,
            "status": status or self.spec.default_status,
            "created_date": cdate, "uuid": uid,
            "source": fields.get("source", "agent_run"),
        }
        subs = fields.get("subsystems")
        if subs:
            fm["subsystems"] = subs
        path = inbox / f"draft_{slug}_{uid.split('-')[0]}.md"
        self.store.write_doc(path, fm, body or "")
        return Item(fm={"id": "BUG-0", "title": title, "severity": severity,
                        "kind": kind, "status": fm["status"], "uuid": uid,
                        "inbox_queued": True, "inbox_path": str(path)},
                    body=body, path=path)

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
        as the source of truth; it refuses to clobber a curated index with its compact table,
        but ADOPTS orphan rows (file present, index missing) by appending them — it does not
        rewrite or drop the curated rows (BUG-169/BUG-174-A). Reports phantom either way."""
        if not self._index_is_curated():
            return super().sync()
        items = self._all()
        ids = {self._num(it.id) for it in items}
        old = self.store.read_text(self.index_path)
        referenced = self._index_ref_ids(old)
        phantom = sorted(referenced - ids)
        orphan = sorted(ids - referenced)
        adopted: List[int] = []
        if orphan:
            by_num = {self._num(it.id): it for it in items}
            self.store.write_text(
                self.index_path,
                self._append_orphan_rows(old, [by_num[n] for n in orphan]),
            )
            adopted = orphan
            orphan = []  # adopted now; index references them
        return {
            "count": len(ids),
            "phantom": phantom,
            "orphan": orphan,
            "adopted": adopted,
            "index_preserved": True,
            "warning": ("BUGS.md is hand-curated (resolution prose + file-less historical "
                        "rows); engine appended missing rows non-destructively (T521) but did "
                        "NOT rewrite curated rows. Edit BUGS.md by hand, or run gald3r validate "
                        "to see drift."),
        }

    def _append_orphan_rows(self, old: str, orphans: List[Item]) -> str:
        """Append curated-table-compatible rows for orphan bugs to a hand-curated BUGS.md
        (BUG-169/BUG-174-A). Non-destructive: existing rows + resolution prose are preserved
        verbatim; new rows go under an engine-adopted marker. Idempotent — the caller only
        passes ids absent from the index, and a re-run finds them referenced."""
        rows = "\n".join(
            f"| {it.id} | {it.fm.get('title','')} | {it.fm.get('severity','—')} "
            f"| {it.status} | {it.fm.get('created_date','—')} |"
            for it in sorted(orphans, key=lambda x: self._num(x.id))
        )
        marker = "<!-- gald3r-engine-adopted-orphans (hand-curated index; edit rows above by hand) -->"
        base = old if old.endswith("\n") else old + "\n"
        if marker in base:
            return base.replace(marker + "\n", marker + "\n" + rows + "\n", 1)
        return base + f"\n{marker}\n{rows}\n"
