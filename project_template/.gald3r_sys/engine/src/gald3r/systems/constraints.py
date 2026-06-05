"""ConstraintSystem — project constraints index (`.gald3r/CONSTRAINTS.md`
Constraint Index table). Mirrors `g-skl-constraints` / `g-constraint-*`.

Note: the governance/approval prose in CONSTRAINTS.md is preserved untouched; this
system manages the Constraint Index rows. Definition blocks remain a human/agent
concern for now (a future refinement can manage them too).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gald3r.config import Config
from gald3r.store import Store
from gald3r.systems import _table

_HEADER = "| ID | Status | Name |"
_STATUSES = ["active", "archived"]


@dataclass
class Constraint:
    id: str
    status: str
    name: str
    scope: str = "project"
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "status": self.status, "name": self.name,
                "scope": self.scope, "summary": self.summary}


class ConstraintSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)
        self.path = config.gald3r_dir / "CONSTRAINTS.md"

    def _text(self) -> str:
        t = self.store.read_text(self.path)
        return t if t.strip() else self._scaffold()

    def list(self) -> List[Constraint]:
        found = _table.parse_rows(self._text(), _HEADER)
        out: List[Constraint] = []
        if found:
            for c in found[2]:
                if len(c) >= 5 and c[0].startswith("C-"):
                    out.append(Constraint(id=c[0], status=c[1], name=c[2], scope=c[3], summary=c[4]))
        return out

    def get(self, cid: str) -> Optional[Constraint]:
        n = self._norm(cid)
        return next((c for c in self.list() if c.id == n), None)

    @staticmethod
    def _norm(cid: str) -> str:
        s = str(cid).upper()
        n = int(s[2:]) if s.startswith("C-") else int(s)
        return f"C-{n:03d}"

    def _next_id(self) -> str:
        nums = [int(c.id.split("-")[1]) for c in self.list()]
        return f"C-{(max(nums) + 1) if nums else 1:03d}"

    def add(self, name: str, scope: str = "project", summary: str = "") -> Constraint:
        if len(name.strip()) < 3:
            raise ValueError("constraint name too short")
        c = Constraint(id=self._next_id(), status="active", name=name.strip(),
                       scope=scope, summary=summary.strip())
        self._save(self.list() + [c])
        return c

    def update(self, cid: str, status: Optional[str] = None, name: Optional[str] = None,
               scope: Optional[str] = None, summary: Optional[str] = None) -> Constraint:
        n = self._norm(cid)
        cons = self.list()
        for c in cons:
            if c.id == n:
                if status is not None:
                    if status not in _STATUSES:
                        raise ValueError(f"status must be one of {_STATUSES}")
                    c.status = status
                if name is not None:
                    c.name = name.strip()
                if scope is not None:
                    c.scope = scope
                if summary is not None:
                    c.summary = summary.strip()
                self._save(cons)
                return c
        raise KeyError(f"constraint {n} not found")

    def archive(self, cid: str) -> Constraint:
        return self.update(cid, status="archived")

    def _save(self, cons: List[Constraint]) -> None:
        rows = [f"| {c.id} | {c.status} | {c.name} | {c.scope} | {c.summary} |"
                for c in sorted(cons, key=lambda x: x.id)]
        self.store.write_text(self.path, _table.replace_rows(self._text(), _HEADER, rows))

    def _scaffold(self) -> str:
        return f"""---
gald3r_rel_version: "{self.cfg.gald3r_rel_version}"
schema_version: "CONSTRAINTS-md-v1"
---
# CONSTRAINTS.md — {self.cfg.project_name}

## Constraint Index

| ID | Status | Name | Scope | One-line summary |
|----|--------|------|-------|-----------------|

## Constraint Definitions

*(Constraint definitions appear here as constraints are added)*
"""
