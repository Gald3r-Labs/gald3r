"""PrdSystem — PRD governance lifecycle over `.gald3r/prds/` + `PRDS.md`. Flat files.
Enforces the C-019 freeze: `released`/`superseded` PRDs are immutable (base
`frozen_statuses`). Cloned via _base.
"""
from __future__ import annotations

from typing import List

from gald3r.config import Config
from gald3r.systems._base import FolderSystem, Item, ItemSpec

_STATUSES = ["draft", "review", "approved", "in-implementation",
             "released", "superseded", "archived"]

SPEC = ItemSpec(
    name="prd", dir_name="prds", index_name="PRDS.md", file_prefix="prd",
    id_kind="prefix", id_prefix="PRD-", id_pad=3,
    statuses=_STATUSES,
    status_folder={s: "" for s in _STATUSES},      # flat: prds/prdNNN_*.md
    status_marker={"draft": "✏️", "review": "🔍", "approved": "👍",
                   "in-implementation": "🔨", "released": "🔒",
                   "superseded": "♻️", "archived": "🗄️"},
    terminal={"released", "superseded", "archived"},
    frozen_statuses={"released", "superseded"},     # C-019 immutability
    default_status="draft",
    required=["id", "title", "status"],
)


def render_index(fs: FolderSystem, items: List[Item]) -> str:
    name = fs.cfg.project_name
    rows = "\n".join(
        f"| {fs.marker(it.status)} {it.status} | {it.id} | {it.fm.get('title','')} | "
        f"{it.fm.get('supersedes','—')} | {it.fm.get('superseded_by','—')} |"
        for it in items
    )
    return f"""---
gald3r_rel_version: "{fs.cfg.gald3r_rel_version}"
schema_version: "PRDS-md-v1"
---
# PRDS.md — {name}

PRDs in status `released` or `superseded` are **immutable** (C-019). Use a revise
flow to supersede a frozen PRD.

## PRD Index

| Status | ID | Title | Supersedes | Superseded by |
|--------|----|-------|-----------|---------------|
{rows}

---

**Next PRD ID**: {fs._next_id()}
"""


class PrdSystem(FolderSystem):
    def __init__(self, config: Config):
        super().__init__(config, SPEC, render_index)
