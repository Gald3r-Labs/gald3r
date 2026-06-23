"""Shared base for folder-backed item systems (bugs, features, prds, …).

This IS the cloned pattern, factored out: sequential/prefixed IDs, item files
(optionally in status subfolders), generic CRUD with folder moves, and index (.md)
regeneration. A new system = an `ItemSpec` + an `render_index` callable + the
fields it cares about. Pure Mode-A: deterministic file ops, no LLM calls.

(tasks.py predates this base and stays standalone as the reference implementation;
it can be refactored onto this base later without changing behavior.)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from gald3r.config import Config
from gald3r.store import Store


def slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", str(title).lower()).strip("_")
    return (s or "item")[:40]


@dataclass
class ItemSpec:
    name: str                          # singular, e.g. "bug"
    dir_name: str                      # ".gald3r/<dir_name>/"
    index_name: str                    # ".gald3r/<index_name>"
    file_prefix: str                   # filename prefix, e.g. "bug" -> bug007_slug.md
    id_kind: str                       # "int" (id=int) | "prefix" (id="PREFIX-NNN")
    statuses: List[str]
    status_folder: Dict[str, str]      # status -> subfolder ("" = flat in dir)
    status_marker: Dict[str, str]
    terminal: set
    required: List[str]                # required frontmatter fields
    default_status: str
    id_prefix: str = ""                # e.g. "BUG-"
    id_pad: int = 3
    # field name -> enum of allowed values (validation)
    enums: Dict[str, List[str]] = field(default_factory=dict)
    frozen_statuses: set = field(default_factory=set)  # immutable once in these


@dataclass
class Item:
    fm: Dict[str, Any]
    body: str = ""
    path: Optional[Path] = None

    @property
    def id(self) -> Any:
        return self.fm.get("id")

    @property
    def status(self) -> str:
        return str(self.fm.get("status", ""))

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.fm)


class FolderSystem:
    def __init__(self, config: Config, spec: ItemSpec,
                 render_index: Callable[["FolderSystem", List[Item]], str]):
        self.cfg = config
        self.spec = spec
        self._render_index = render_index
        self.store = Store(config.gald3r_dir)
        self.base_dir = config.gald3r_dir / spec.dir_name
        self.index_path = config.gald3r_dir / spec.index_name

    # ---- ids ----
    def _num(self, item_id: Any) -> int:
        if isinstance(item_id, int):
            return item_id
        m = re.search(r"(\d+)\s*$", str(item_id))
        return int(m.group(1)) if m else 0

    def _format_id(self, n: int) -> Any:
        if self.spec.id_kind == "int":
            return n
        return f"{self.spec.id_prefix}{n:0{self.spec.id_pad}d}"

    def _next_id(self) -> Any:
        # BUG-169/BUG-174-B: allocate over the UNION of on-disk file ids AND ids
        # referenced in the index (.md). An item whose file was archived/moved leaves its
        # id only in the index; allocating from files alone would re-issue it (observed:
        # `bug new` re-issued BUG-173). _index_ref_ids() already tolerates both formats.
        file_nums = {self._num(it.id) for it in self._all()}
        index_nums = self._index_ref_ids(self.store.read_text(self.index_path))
        known = file_nums | index_nums
        n = (max(known) + 1) if known else 1
        # Defense in depth: max()+1 over the full known set cannot collide, but fail loudly
        # rather than silently duplicate if that invariant is ever broken.
        if n in known:
            raise RuntimeError(
                f"{self.spec.name} id allocation collision: computed {n} already exists "
                f"(file ids + index ids = {sorted(known)})"
            )
        return self._format_id(n)

    # ---- files ----
    def _files(self) -> List[Path]:
        return sorted(self.base_dir.rglob(f"{self.spec.file_prefix}*.md")) if self.base_dir.exists() else []

    def _load(self, path: Path) -> Optional[Item]:
        try:
            fm, body = self.store.read_doc(path)
        except Exception:
            # Malformed YAML frontmatter must not crash `bug list` (etc.) for the whole
            # store (T521). Skip here; `gald3r validate` reports it as a violation to repair.
            return None
        if "id" not in fm:
            return None
        return Item(fm=fm, body=body.strip(), path=path)

    def _all(self) -> List[Item]:
        items = [it for it in (self._load(p) for p in self._files()) if it]
        return sorted(items, key=lambda it: self._num(it.id))

    def _folder(self, status: str) -> str:
        return self.spec.status_folder.get(status, self.spec.status_folder.get(self.spec.default_status, ""))

    def _path_for(self, it: Item) -> Path:
        sub = self._folder(it.status)
        fn = f"{self.spec.file_prefix}{self._num(it.id):0{self.spec.id_pad}d}_{slug(it.fm.get('title', it.id))}.md"
        return (self.base_dir / sub / fn) if sub else (self.base_dir / fn)

    def marker(self, status: str) -> str:
        return self.spec.status_marker.get(status, " ")

    # ---- validation ----
    def _validate(self, fm: Dict[str, Any]) -> List[str]:
        errs: List[str] = []
        for k in self.spec.required:
            if k not in fm or fm[k] in (None, ""):
                errs.append(f"missing required field: {k}")
        if "title" in fm and isinstance(fm["title"], str) and len(fm["title"]) < 5:
            errs.append("title must be at least 5 characters")
        if "status" in fm and fm["status"] not in self.spec.statuses:
            errs.append(f"status '{fm.get('status')}' not in vocabulary")
        for fld, allowed in self.spec.enums.items():
            if fld in fm and fm[fld] not in allowed:
                errs.append(f"{fld} must be one of {allowed}")
        return errs

    # ---- CRUD ----
    def create(self, title: str, status: Optional[str] = None, body: str = "",
               created_date: Optional[str] = None, **fields: Any) -> Item:
        fm: Dict[str, Any] = {"id": self._next_id(), "title": title,
                              "status": status or self.spec.default_status}
        fm.update({k: v for k, v in fields.items() if v is not None})
        fm.setdefault("created_date", created_date or date.today().isoformat())
        fm.setdefault("schema_version", f"{self.spec.name}-file-v1")
        errs = self._validate(fm)
        if errs:
            raise ValueError(f"invalid {self.spec.name}: " + "; ".join(errs))
        it = Item(fm=fm, body=body)
        self._write(it)
        self.sync()
        return it

    def get(self, item_id: Any) -> Optional[Item]:
        n = self._num(item_id)
        return next((it for it in self._all() if self._num(it.id) == n), None)

    def list(self, status: Optional[str] = None) -> List[Item]:
        items = self._all()
        return [it for it in items if it.status == status] if status else items

    def update(self, item_id: Any, **changes: Any) -> Item:
        it = self.get(item_id)
        if not it:
            raise KeyError(f"{self.spec.name} {item_id} not found")
        if it.status in self.spec.frozen_statuses:
            raise PermissionError(f"{self.spec.name} {it.id} is frozen (status={it.status}); immutable")
        for k, v in changes.items():
            if v is not None:
                it.fm[k] = v
        errs = self._validate(it.fm)
        if errs:
            raise ValueError(f"invalid {self.spec.name}: " + "; ".join(errs))
        self._write(it)
        self.sync()
        return it

    def delete(self, item_id: Any) -> bool:
        it = self.get(item_id)
        if not it:
            return False
        self.store.remove(it.path)
        self.sync()
        return True

    def _write(self, it: Item) -> Item:
        new_path = self._path_for(it)
        if it.path and Path(it.path) != new_path:
            self.store.remove(it.path)
        self.store.write_doc(new_path, it.fm, it.body or self._default_body(it))
        it.path = new_path
        return it

    def _default_body(self, it: Item) -> str:
        return f"## Description\n{it.fm.get('title', it.id)}\n"

    # ---- index ----
    def sync(self) -> Dict[str, Any]:
        items = self._all()
        ids = {self._num(it.id) for it in items}
        referenced = self._index_ref_ids(self.store.read_text(self.index_path))
        phantom = sorted(referenced - ids)        # in index, no file
        orphan = sorted(ids - referenced)         # file, not in (pre-regen) index
        # The engine render below includes every item file, so orphans are ADOPTED
        # into the regenerated index (BUG-169/BUG-174-A), not merely reported.
        self.store.write_text(self.index_path, self._render_index(self, items))
        return {"count": len(ids), "phantom": phantom, "orphan": orphan, "adopted": orphan}

    def _index_ref_ids(self, text: str) -> set:
        if not text:
            return set()
        # Ignore the "Next <X> ID:" counter line — it names the NOT-yet-created id, so it must
        # never be counted as an existing id (critical now that _next_id reads this set: bugs
        # render it as a `## Next Bug ID:` heading, features/prds as a `**Next feat ID**:` bold
        # line — BUG-174-B regression). Anchored to line-start with an optional `#`/`*`/`-`
        # marker prefix so a table row / title that merely contains "Next Bug ID" (e.g. a bug
        # titled "...mis-parses 'Next Bug ID'...") is still counted.
        body = "\n".join(ln for ln in text.splitlines()
                         if not re.match(r"\s*(?:#+|\*+|-)\s*\**Next\b.*\bID\b", ln))
        if self.spec.id_kind == "int":
            return {int(m) for m in re.findall(r"\bT(\d+)\b", body)}
        pref = re.escape(self.spec.id_prefix.rstrip("-"))
        return {int(m) for m in re.findall(pref + r"-?(\d+)", body)}
