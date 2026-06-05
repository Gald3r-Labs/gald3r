"""IdeaSystem — the idea board (`.gald3r/IDEA_BOARD.md`), a single-file table of
ideas with status markers. Mirrors `g-skl-ideas` / `g-idea-*`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from gald3r.config import Config
from gald3r.store import Store
from gald3r.systems import _table

_HEADER = "| ID | Status | Title |"
_MARKER = {"new": "💡", "review": "🔍", "promoted": "📋", "shelved": "❌", "implemented": "✅"}
_STATUSES = list(_MARKER)
_ROW = re.compile(r"^\|\s*(I-\d+)\s*\|")


@dataclass
class Idea:
    id: str
    status: str
    title: str
    category: str = "general"
    added: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "status": self.status, "title": self.title,
                "category": self.category, "added": self.added}


class IdeaSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)
        self.path = config.gald3r_dir / "IDEA_BOARD.md"

    def _text(self) -> str:
        t = self.store.read_text(self.path)
        return t if t.strip() else self._scaffold()

    def list(self) -> List[Idea]:
        found = _table.parse_rows(self._text(), _HEADER)
        out: List[Idea] = []
        if found:
            for cells in found[2]:
                if len(cells) >= 5 and cells[0].startswith("I-"):
                    out.append(Idea(id=cells[0], status=self._status_from_marker(cells[1]),
                                    title=cells[2], category=cells[3], added=cells[4]))
        return out

    @staticmethod
    def _status_from_marker(cell: str) -> str:
        for st, mk in _MARKER.items():
            if mk in cell:
                return st
        return "new"

    def get(self, idea_id: str) -> Optional[Idea]:
        iid = self._norm(idea_id)
        return next((i for i in self.list() if i.id == iid), None)

    @staticmethod
    def _norm(idea_id: str) -> str:
        s = str(idea_id).upper().replace("IDEA-", "I-")
        n = int(s[2:]) if s.startswith("I-") else int(s)
        return f"I-{n:03d}"

    def _next_id(self) -> str:
        nums = [int(i.id.split("-")[1]) for i in self.list()]
        return f"I-{(max(nums) + 1) if nums else 1:03d}"

    def capture(self, title: str, category: str = "general", status: str = "new") -> Idea:
        if len(title.strip()) < 3:
            raise ValueError("idea title too short")
        if status not in _STATUSES:
            raise ValueError(f"status must be one of {_STATUSES}")
        idea = Idea(id=self._next_id(), status=status, title=title.strip(),
                    category=category, added=date.today().isoformat())
        self._save(self.list() + [idea])
        return idea

    def update(self, idea_id: str, status: Optional[str] = None, title: Optional[str] = None) -> Idea:
        iid = self._norm(idea_id)
        ideas = self.list()
        for i in ideas:
            if i.id == iid:
                if status is not None:
                    if status not in _STATUSES:
                        raise ValueError(f"status must be one of {_STATUSES}")
                    i.status = status
                if title is not None:
                    i.title = title.strip()
                self._save(ideas)
                return i
        raise KeyError(f"idea {iid} not found")

    def _save(self, ideas: List[Idea]) -> None:
        rows = [f"| {i.id} | [{_MARKER[i.status]}] | {i.title} | {i.category} | {i.added} |"
                for i in sorted(ideas, key=lambda x: x.id)]
        self.store.write_text(self.path, _table.replace_rows(self._text(), _HEADER, rows))

    def _scaffold(self) -> str:
        return f"""---
gald3r_rel_version: "{self.cfg.gald3r_rel_version}"
schema_version: "generic-v1"
---
# IDEA_BOARD.md — {self.cfg.project_name}

## Status Indicators
- `[💡]` = New idea (not yet reviewed)
- `[🔍]` = Under review
- `[📋]` = Promoted to task
- `[❌]` = Shelved
- `[✅]` = Implemented

## Ideas

| ID | Status | Title | Category | Added |
|----|--------|-------|----------|-------|
"""
