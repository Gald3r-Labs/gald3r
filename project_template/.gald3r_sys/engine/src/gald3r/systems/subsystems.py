"""SubsystemSystem — the subsystem registry (`.gald3r/subsystems/<name>.md` specs +
`SUBSYSTEMS.md` index). Name-keyed (no numeric id), each spec carries `locations:`.
Mirrors `g-skl-subsystems` / `g-subsystem-*`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.config import Config
from gald3r.store import Store


def _fname(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name.strip()).strip("_")


@dataclass
class Subsystem:
    name: str
    locations: List[str] = field(default_factory=list)
    status: str = "active"
    owner: str = ""
    dependencies: List[str] = field(default_factory=list)
    body: str = ""
    path: Optional[Path] = None

    def to_frontmatter(self) -> Dict[str, Any]:
        fm: Dict[str, Any] = {"name": self.name, "status": self.status,
                              "locations": list(self.locations)}
        if self.owner:
            fm["owner"] = self.owner
        if self.dependencies:
            fm["dependencies"] = list(self.dependencies)
        fm["schema_version"] = "subsystem-file-v1"
        return fm

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "status": self.status, "locations": self.locations,
                "owner": self.owner, "dependencies": self.dependencies}


class SubsystemSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)
        self.dir = config.gald3r_dir / "subsystems"
        self.index_path = config.gald3r_dir / "SUBSYSTEMS.md"

    def _files(self) -> List[Path]:
        return sorted(p for p in self.dir.glob("*.md")) if self.dir.exists() else []

    def _load(self, path: Path) -> Optional[Subsystem]:
        fm, body = self.store.read_doc(path)
        if "name" not in fm:
            return None
        return Subsystem(
            name=str(fm["name"]), status=str(fm.get("status", "active")),
            locations=list(fm.get("locations") or []), owner=str(fm.get("owner", "")),
            dependencies=list(fm.get("dependencies") or []), body=body.strip(), path=path,
        )

    def list(self) -> List[Subsystem]:
        items = [s for s in (self._load(p) for p in self._files()) if s]
        return sorted(items, key=lambda s: s.name.upper())

    def get(self, name: str) -> Optional[Subsystem]:
        key = name.strip().upper()
        return next((s for s in self.list() if s.name.upper() == key), None)

    def register(self, name: str, locations: Optional[List[str]] = None, owner: str = "",
                 dependencies: Optional[List[str]] = None, body: str = "", status: str = "active") -> Subsystem:
        if len(name.strip()) < 2:
            raise ValueError("subsystem name too short")
        if not locations:
            raise ValueError("at least one location is required")
        s = Subsystem(name=name.strip(), locations=list(locations), owner=owner,
                      dependencies=list(dependencies or []), status=status, body=body)
        self._write(s)
        self.sync()
        return s

    def update(self, name: str, **changes: Any) -> Subsystem:
        s = self.get(name)
        if not s:
            raise KeyError(f"subsystem {name} not found")
        for k, v in changes.items():
            if v is not None and hasattr(s, k):
                setattr(s, k, v)
        self._write(s)
        self.sync()
        return s

    def remove(self, name: str) -> bool:
        s = self.get(name)
        if not s:
            return False
        self.store.remove(s.path)
        self.sync()
        return True

    def _write(self, s: Subsystem) -> Subsystem:
        path = self.dir / f"{_fname(s.name)}.md"
        body = s.body or (f"## {s.name}\n\n**Locations**:\n"
                          + "\n".join(f"- `{loc}`" for loc in s.locations) + "\n")
        self.store.write_doc(path, s.to_frontmatter(), body)
        s.path = path
        return s

    def sync(self) -> Dict[str, Any]:
        subs = self.list()
        rows = "\n".join(
            f"| {s.name} | {s.status} | `subsystems/{_fname(s.name)}.md` | "
            f"{', '.join(s.locations) if s.locations else '—'} |"
            for s in subs
        )
        self.store.write_text(self.index_path, f"""---
gald3r_rel_version: "{self.cfg.gald3r_rel_version}"
schema_version: "SUBSYSTEMS-md-v1"
---
# SUBSYSTEMS.md — {self.cfg.project_name}

## Overview

Master registry of subsystems present in this repository. Each has a spec in
`.gald3r/subsystems/{{name}}.md` — read it before changing that area.

## Subsystem Index

| Subsystem | Status | Spec File | What's In Code |
|-----------|--------|-----------|----------------|
{rows}
""")
        return {"count": len(subs)}
