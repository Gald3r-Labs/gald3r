"""Inbox intake — absorb staged task/bug drafts from the gitignored inbox folders
into live tracked state. Replaces custom_scripts/hot_inbox_intake.ps1 (T1573).

The original 273-line script re-implemented ID assignment, frontmatter writing, and
TASKS.md/BUGS.md row insertion by hand. The engine already does all three correctly via
TaskSystem/BugSystem.create() (+ sync()), so intake collapses to: parse each draft ->
create() -> remove the draft. Pure Mode-A: no git, no network, no LLM — the caller
(the g-go-go housekeeping gate / a hook) owns committing the result.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.config import Config
from gald3r.systems.tasks import TaskSystem
from gald3r.systems.bugs import BugSystem


def _read_draft(path: Path) -> Dict[str, Any]:
    """Tolerant parse of an inbox draft: loose frontmatter + body notes.

    Mirrors the original script's field extraction so existing drafts intake identically.
    """
    raw = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

    def field(pattern: str, default: str) -> str:
        m = re.search(pattern, raw, re.MULTILINE)
        return m.group(1).strip() if m else default

    title = field(r"^title:\s*['\"]?(.+?)['\"]?\s*$",
                  path.stem.replace("-", " ").replace("_", " "))
    priority = field(r"^priority:\s*(\w+)", "medium")
    type_ = field(r"^type:\s*(\w+)", "feature")
    subsys_raw = field(r"^subsystems:\s*(.+)", "[]")

    # body = everything after a leading frontmatter block (--- ... ---)
    body = re.sub(r"(?ms)\A﻿?---.*?---\s*", "", raw).strip()

    return {"title": title, "priority": priority, "type": type_,
            "subsystems": _parse_list(subsys_raw), "body": body}


def _parse_list(s: str) -> List[str]:
    s = s.strip()
    if not s or s == "[]":
        return []
    inner = s[1:-1] if s.startswith("[") and s.endswith("]") else s
    return [p.strip().strip("'\"") for p in inner.split(",") if p.strip()]


class InboxSystem:
    """Scans `.gald3r/tasks/inbox/` and `.gald3r/bugs/inbox/`, ingesting drafts."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.tasks = TaskSystem(cfg)
        self.bugs = BugSystem(cfg)

    @property
    def task_inbox(self) -> Path:
        return self.cfg.tasks_dir / "inbox"

    @property
    def bug_inbox(self) -> Path:
        return self.cfg.gald3r_dir / "bugs" / "inbox"

    def intake(self, dry_run: bool = False) -> Dict[str, Any]:
        created: List[Dict[str, Any]] = []
        removed: List[str] = []

        for path in sorted(self.task_inbox.glob("*.md")) if self.task_inbox.is_dir() else []:
            d = _read_draft(path)
            if not dry_run:
                t = self.tasks.create(title=d["title"], type=d["type"], priority=d["priority"],
                                      status="pending", body=d["body"],
                                      subsystems=d["subsystems"], source="inbox_intake")
                created.append({"kind": "task", "id": f"T{t.id}", "title": t.title,
                                "from": f"tasks/inbox/{path.name}"})
                path.unlink()
                removed.append(str(path))
            else:
                created.append({"kind": "task", "id": "T?", "title": d["title"],
                                "from": f"tasks/inbox/{path.name}"})

        for path in sorted(self.bug_inbox.glob("*.md")) if self.bug_inbox.is_dir() else []:
            d = _read_draft(path)
            if not dry_run:
                b = self.bugs.create(title=d["title"], severity=d["priority"], status="open",
                                     body=d["body"], subsystems=d["subsystems"],
                                     source="inbox_intake")
                created.append({"kind": "bug", "id": str(b.id), "title": b.fm.get("title", d["title"]),
                                "from": f"bugs/inbox/{path.name}"})
                path.unlink()
                removed.append(str(path))
            else:
                created.append({"kind": "bug", "id": "BUG-?", "title": d["title"],
                                "from": f"bugs/inbox/{path.name}"})

        tasks_n = sum(1 for c in created if c["kind"] == "task")
        bugs_n = sum(1 for c in created if c["kind"] == "bug")
        return {"tasks_ingested": tasks_n, "bugs_ingested": bugs_n,
                "total": tasks_n + bugs_n, "created": created,
                "removed_drafts": removed, "dry_run": dry_run}
