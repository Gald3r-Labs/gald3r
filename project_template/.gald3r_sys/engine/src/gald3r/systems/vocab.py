"""VocabSystem — project abbreviations (`.gald3r/vocab.md` Active Vocabulary table),
keyed by abbreviation (no numeric id). Mirrors `g-vocab-*`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gald3r.config import Config
from gald3r.store import Store
from gald3r.systems import _table

_HEADER = "| Abbreviation |"


@dataclass
class Term:
    abbr: str
    expansion: str
    context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"abbr": self.abbr, "expansion": self.expansion, "context": self.context}


def _unwrap(cell: str) -> str:
    return cell.strip().strip("`").replace("**", "").strip()


class VocabSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)
        self.path = config.gald3r_dir / "vocab.md"

    def _text(self) -> str:
        t = self.store.read_text(self.path)
        return t if t.strip() else self._scaffold()

    def list(self) -> List[Term]:
        found = _table.parse_rows(self._text(), _HEADER)
        out: List[Term] = []
        if found:
            for cells in found[2]:
                if len(cells) >= 3 and _unwrap(cells[0]):
                    out.append(Term(abbr=_unwrap(cells[0]), expansion=cells[1].strip(),
                                    context=cells[2].strip()))
        return out

    def get(self, abbr: str) -> Optional[Term]:
        a = abbr.strip().upper()
        return next((t for t in self.list() if t.abbr.upper() == a), None)

    def add(self, abbr: str, expansion: str, context: str = "") -> Term:
        abbr = abbr.strip()
        if not abbr or not expansion.strip():
            raise ValueError("abbr and expansion are required")
        terms = [t for t in self.list() if t.abbr.upper() != abbr.upper()]  # upsert
        term = Term(abbr=abbr, expansion=expansion.strip(), context=context.strip())
        self._save(terms + [term])
        return term

    def remove(self, abbr: str) -> bool:
        terms = self.list()
        kept = [t for t in terms if t.abbr.upper() != abbr.strip().upper()]
        if len(kept) == len(terms):
            return False
        self._save(kept)
        return True

    def _save(self, terms: List[Term]) -> None:
        rows = [f"| `{t.abbr}` | {t.expansion} | {t.context} |"
                for t in sorted(terms, key=lambda x: x.abbr.upper())]
        self.store.write_text(self.path, _table.replace_rows(self._text(), _HEADER, rows))

    def _scaffold(self) -> str:
        return f"""---
gald3r_rel_version: "{self.cfg.gald3r_rel_version}"
schema_version: "generic-v1"
---
# gald3r Vocabulary & Abbreviations

User-defined shorthand that all agents expand silently.

## Active Vocabulary

| Abbreviation | Full Expansion | Context |
|---|---|---|
"""
