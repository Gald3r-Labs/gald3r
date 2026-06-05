"""FeatureSystem — feature staging lifecycle over `.gald3r/features/` + `FEATURES.md`.
Flat files (no status subfolders); the index groups by status. Cloned via _base.
"""
from __future__ import annotations

from typing import List

from gald3r.config import Config
from gald3r.systems._base import FolderSystem, Item, ItemSpec

_STATUSES = ["staging", "specced", "committed", "shipped"]

SPEC = ItemSpec(
    name="feature", dir_name="features", index_name="FEATURES.md", file_prefix="feat",
    id_kind="prefix", id_prefix="feat-", id_pad=3,
    statuses=_STATUSES,
    status_folder={s: "" for s in _STATUSES},     # flat: features/featNNN_*.md
    status_marker={"staging": "🌱", "specced": "📝", "committed": "🔨", "shipped": "✅"},
    terminal={"shipped"}, default_status="staging",
    required=["id", "title", "status"],
    enums={"priority": ["critical", "high", "medium", "low"]},
)

_GROUPS = [("shipped", "Shipped"), ("committed", "Committed"),
           ("specced", "Specced"), ("staging", "Staging")]


def render_index(fs: FolderSystem, items: List[Item]) -> str:
    name = fs.cfg.project_name
    secs = []
    for st, label in _GROUPS:
        rows = [f"- **{it.id}** {it.fm.get('title','')}"
                + (f" ({it.fm['priority']})" if it.fm.get("priority") else "")
                for it in items if it.status == st]
        secs.append(f"### {label}\n" + ("\n".join(rows) if rows else "*(none yet)*"))
    return f"""---
gald3r_rel_version: "{fs.cfg.gald3r_rel_version}"
schema_version: "FEATURES-md-v1"
---
# FEATURES.md — {name} Feature Registry

## Overview

Features are user-visible capabilities moving through the staging pipeline.
Individual feature files live in `features/featNNN_name.md`.

| Status | Meaning |
|--------|---------|
| staging | Research phase — collecting approaches |
| specced | Formal requirements written |
| committed | Active tasks created in TASKS.md |
| shipped | Fully implemented and verified |

## Features Index

{chr(10).join(secs)}

---

**Next feat ID**: {fs._next_id()}
"""


class FeatureSystem(FolderSystem):
    def __init__(self, config: Config):
        super().__init__(config, SPEC, render_index)
