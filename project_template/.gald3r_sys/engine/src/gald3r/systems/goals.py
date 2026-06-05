"""GoalSystem — project goals (the `## Goals` section of PROJECT.md).

Goals are `- **G-NN**: text` bullets inside PROJECT.md (not separate files), so this
is a single-file *section* system rather than a folder+index one. Pure Mode-A:
edits only the Goals section, preserving the rest of the document.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gald3r.config import Config
from gald3r.store import Store

_BULLET = re.compile(r"^- \*\*(G-\d+)\*\*:\s*(.*)$")
_SECTION = re.compile(r"(^##\s+Goals\s*\n)(.*?)(?=^\#\#\s|\Z)", re.S | re.M)


@dataclass
class Goal:
    id: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "text": self.text}


class GoalSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)
        self.path = config.gald3r_dir / "PROJECT.md"

    def _text(self) -> str:
        return self.store.read_text(self.path)

    def list(self) -> List[Goal]:
        text = self._text()
        m = _SECTION.search(text)
        body = m.group(2) if m else text
        out: List[Goal] = []
        for line in body.splitlines():
            bm = _BULLET.match(line.strip())
            if bm:
                out.append(Goal(id=bm.group(1), text=bm.group(2).strip()))
        return out

    def get(self, goal_id: str) -> Optional[Goal]:
        gid = self._norm(goal_id)
        return next((g for g in self.list() if g.id == gid), None)

    def _next_id(self) -> str:
        nums = [int(g.id.split("-")[1]) for g in self.list()]
        return f"G-{(max(nums) + 1) if nums else 1:02d}"

    @staticmethod
    def _norm(goal_id: str) -> str:
        s = str(goal_id).upper()
        if s.startswith("G-"):
            return f"G-{int(s[2:]):02d}"
        return f"G-{int(s):02d}"

    def add(self, text: str) -> Goal:
        if not text or len(text.strip()) < 3:
            raise ValueError("goal text too short")
        g = Goal(id=self._next_id(), text=text.strip())
        self._save(self.list() + [g])
        return g

    def update(self, goal_id: str, text: str) -> Goal:
        gid = self._norm(goal_id)
        goals = self.list()
        for g in goals:
            if g.id == gid:
                g.text = text.strip()
                self._save(goals)
                return g
        raise KeyError(f"goal {gid} not found")

    def remove(self, goal_id: str) -> bool:
        gid = self._norm(goal_id)
        goals = self.list()
        kept = [g for g in goals if g.id != gid]
        if len(kept) == len(goals):
            return False
        self._save(kept)
        return True

    def _save(self, goals: List[Goal]) -> None:
        bullets = "\n".join(f"- **{g.id}**: {g.text}" for g in goals) or "*(no goals yet)*"
        text = self._text()
        if _SECTION.search(text):
            new = _SECTION.sub(lambda m: m.group(1) + "\n" + bullets + "\n\n", text)
        elif text.strip():
            new = text.rstrip() + "\n\n## Goals\n\n" + bullets + "\n"
        else:
            name = self.cfg.project_name
            new = (f'---\ngald3r_rel_version: "{self.cfg.gald3r_rel_version}"\n'
                   f'schema_version: "PROJECT-md-v1"\n---\n# PROJECT.md — {name}\n\n'
                   f"## Goals\n\n{bullets}\n")
        self.store.write_text(self.path, new)
