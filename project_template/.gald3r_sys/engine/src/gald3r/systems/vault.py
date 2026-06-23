"""VaultSystem — the file-first knowledge vault under `.gald3r/vault/`.

The deterministic half of `g-skl-vault` / `g-vault-*`, in code: route a note to its
folder by `type`, write it with correct frontmatter, append the operations log, and
regenerate the machine catalog (`_index.yaml`) + human home page (`index.md`). The
*judgment* half (entity/concept extraction, classification, LLM enrichment) stays in
prompts — this module makes NO LLM calls.

It bakes in the two fixes the vault review (`reviews/REVIEW_vault_system.md`) called
out as the system's signature breakage:
  * **`tags:` is the canonical label key (D021)** — the engine emits/reads `tags:`
    only, and silently migrates an incoming `topics:` to `tags:`, so the index can
    never again be born with the label field dropped (defect C1);
  * the reindexer reads frontmatter the same way every producer writes it, so there
    is one contract, not the SKILL-vs-hook drift the review found (M4).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from gald3r.config import Config
from gald3r.store import Store

# note `type` -> destination folder (relative to vault root). Mirrors VAULT_SCHEMA.md routing.
TYPE_FOLDER: Dict[str, str] = {
    "article": "research/articles",
    "github": "research/github",
    "repo": "research/github",
    "harvest": "research/harvests",
    "paper": "research/papers",
    "platform_doc": "research/platforms",
    "platform": "research/platforms",
    "video": "research/videos",
    "card": "knowledge/cards",
    "comparison": "knowledge/comparisons",
    "concept": "knowledge/concepts",
    "entity": "knowledge/entities",
    "session": "projects/{project}/sessions",
    "decision": "projects/{project}/decisions",
}
_DEFAULT_FOLDER = "research/articles"
REQUIRED = ["date", "type", "ingestion_type", "source", "title", "tags"]
# vault-root files that are contracts/indexes, never treated as notes
_ROOT_FILES = {"VAULT_SCHEMA.md", "index.md", "log.md", "obsidian_setup.md", "MOC.md"}


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(title).lower()).strip("-")
    return (s or "note")[:60]


@dataclass
class Note:
    fm: Dict[str, Any]
    body: str = ""
    path: Optional[Path] = None
    rel: str = ""        # path relative to the vault root, posix-style

    @property
    def title(self) -> str:
        return str(self.fm.get("title", ""))

    @property
    def type(self) -> str:
        return str(self.fm.get("type", ""))

    @property
    def tags(self) -> List[str]:
        t = self.fm.get("tags")
        return list(t) if isinstance(t, (list, tuple)) else ([t] if t else [])

    def to_dict(self) -> Dict[str, Any]:
        return {"rel": self.rel, "title": self.title, "type": self.type,
                "tags": self.tags, "source": self.fm.get("source", ""),
                "date": str(self.fm.get("date", ""))}


class VaultSystem:
    def __init__(self, config: Config):
        self.cfg = config
        self.store = Store(config.gald3r_dir)
        self.dir = config.gald3r_dir / "vault"

    # ---- routing ----
    def _folder_for(self, note_type: str, folder: Optional[str] = None) -> str:
        if folder:
            return folder.strip("/")
        tmpl = TYPE_FOLDER.get(note_type, _DEFAULT_FOLDER)
        return tmpl.replace("{project}", self.cfg.project_name)

    # ---- notes scan ----
    def _note_files(self) -> List[Path]:
        if not self.dir.exists():
            return []
        out = []
        for p in sorted(self.dir.rglob("*.md")):
            rel = p.relative_to(self.dir).as_posix()
            if "/.obsidian/" in f"/{rel}" or rel in _ROOT_FILES:
                continue
            out.append(p)
        return out

    def _load(self, path: Path) -> Optional[Note]:
        fm, body = self.store.read_doc(path)
        fm = self._normalize_fm(fm)
        if "title" not in fm:
            return None
        return Note(fm=fm, body=body.strip(), path=path,
                    rel=path.relative_to(self.dir).as_posix())

    @staticmethod
    def _normalize_fm(fm: Dict[str, Any]) -> Dict[str, Any]:
        """Canonical-key normalization: migrate the legacy `topics:` label key to
        `tags:` (D021). Done on read AND write so the schism can't reappear. If both
        are present, `tags:` wins; an empty `tags:` is filled from `topics:`."""
        fm = dict(fm)
        if "topics" in fm:
            legacy = fm.pop("topics")
            if not fm.get("tags"):
                fm["tags"] = legacy
        return fm

    def list(self, type: Optional[str] = None) -> List[Note]:
        notes = [n for n in (self._load(p) for p in self._note_files()) if n]
        if type:
            notes = [n for n in notes if n.type == type]
        return sorted(notes, key=lambda n: n.rel)

    def get(self, rel_or_slug: str) -> Optional[Note]:
        key = rel_or_slug.strip().removesuffix(".md")
        for n in self.list():
            if n.rel == rel_or_slug or n.rel.removesuffix(".md").endswith(key):
                return n
        return None

    def search(self, query: str, limit: int = 20) -> List[Note]:
        """Keyword search over note title/body/tags — case-insensitive substring,
        ranked by total match count (T609 local half). Pure/offline; the semantic
        (embedding) search is the cloud RAG layer (paused cloud epic)."""
        q = (query or "").strip().lower()
        if not q:
            return []
        scored: List[tuple] = []
        for n in self.list():
            hay = f"{n.title}\n{n.body}\n{' '.join(n.tags)}".lower()
            score = hay.count(q)
            if score:
                scored.append((score, n))
        scored.sort(key=lambda sn: (-sn[0], sn[1].rel))
        return [n for _, n in scored[:limit]]

    # ---- structured note fetch / backlinks / context (T609 remaining ACs) ----
    def note_get(self, rel_or_slug: str) -> Optional[Dict[str, Any]]:
        """Fetch a single note as structured JSON: parsed `metadata` (full frontmatter),
        `body`, and convenience top-level fields. Returns None when no note matches.
        Agents call this instead of reading the raw .md file — no parsing in context."""
        note = self.get(rel_or_slug)
        if note is None:
            return None
        return {
            "rel": note.rel,
            "title": note.title,
            "type": note.type,
            "tags": note.tags,
            "metadata": dict(note.fm),
            "body": note.body,
        }

    @staticmethod
    def _link_targets(body: str) -> List[str]:
        """Extract `[[wikilink]]` targets from a note body, dropping the `|alias` and
        `#heading` parts and the optional `.md` suffix — the same link shape the
        index writer emits (`[[<rel-without-.md>|<title>]]`)."""
        out: List[str] = []
        for raw in re.findall(r"\[\[([^\]]+)\]\]", body or ""):
            target = raw.split("|", 1)[0].split("#", 1)[0].strip().removesuffix(".md")
            if target:
                out.append(target)
        return out

    def backlinks(self, rel_or_slug: str) -> List[Note]:
        """List notes whose body `[[wikilink]]`-references the given note. A link
        matches on the target's full vault-relative path (sans `.md`) or its bare
        slug/basename, so both `[[research/articles/foo|Foo]]` and `[[foo]]` resolve."""
        note = self.get(rel_or_slug)
        if note is None:
            return []
        target_rel = note.rel.removesuffix(".md")
        target_slug = Path(target_rel).name
        out: List[Note] = []
        for n in self.list():
            if n.rel == note.rel:
                continue  # a note does not back-link to itself
            for link in self._link_targets(n.body):
                if link == target_rel or Path(link).name == target_slug:
                    out.append(n)
                    break
        return out

    def context(self, budget: int = 8000) -> Dict[str, Any]:
        """Assemble a token-budgeted, project-specific context block from the vault —
        the `memory_context` pattern, vault-scoped. Newest notes first (by frontmatter
        `date`, then rel), each rendered as a titled excerpt, accumulated until the
        token budget is hit. Token cost is approximated at ~4 chars/token (the
        memory_context convention); offline, no model call."""
        budget = max(0, int(budget))
        notes = sorted(self.list(), key=lambda n: (str(n.fm.get("date", "")), n.rel),
                       reverse=True)
        blocks: List[str] = []
        included: List[Dict[str, Any]] = []
        used_tokens = 0
        for n in notes:
            tags = f" [{', '.join(n.tags)}]" if n.tags else ""
            block = f"## {n.title} ({n.rel}){tags}\n{n.body}".strip()
            cost = self._approx_tokens(block)
            if used_tokens + cost > budget:
                continue  # skip; a later, smaller note may still fit
            blocks.append(block)
            included.append(n.to_dict())
            used_tokens += cost
        return {
            "budget": budget,
            "used_tokens": used_tokens,
            "note_count": len(included),
            "notes": included,
            "context": "\n\n".join(blocks),
        }

    @staticmethod
    def _approx_tokens(text: str) -> int:
        """Approximate token count at ~4 chars/token (memory_context convention)."""
        return (len(text) + 3) // 4

    # ---- ingest ----
    def ingest(self, title: str, type: str, source: str, tags: Optional[List[str]] = None,
               ingestion_type: str = "manual", body: str = "", date_: Optional[str] = None,
               folder: Optional[str] = None, reason: str = "", reindex: bool = True,
               **extra: Any) -> Note:
        """Route a note to its folder by `type`, write it with full frontmatter, append
        the log, and (by default) reindex. `tags` is canonical (never `topics`)."""
        if len(title.strip()) < 3:
            raise ValueError("note title too short")
        fm: Dict[str, Any] = {
            "date": date_ or date.today().isoformat(),
            "type": type,
            "ingestion_type": ingestion_type,
            "source": source,
            "title": title.strip(),
            "tags": list(tags or []),
        }
        fm.update({k: v for k, v in extra.items() if v is not None})
        fm = self._normalize_fm(fm)
        missing = [k for k in REQUIRED if not fm.get(k) and k != "tags"]
        if missing:
            raise ValueError(f"note missing required frontmatter: {', '.join(missing)}")

        rel_folder = self._folder_for(type, folder)
        path = self.dir / rel_folder / f"{slugify(title)}.md"
        self.store.write_doc(path, fm, body or f"# {title}\n")
        note = Note(fm=fm, body=(body or f"# {title}\n").strip(), path=path,
                    rel=path.relative_to(self.dir).as_posix())
        self.log_append("ingest", note.rel, reason or f"ingest {type}", "ready")
        if reindex:
            self.reindex()
        return note

    # ---- log (append-only) ----
    def log_append(self, action: str, target: str, reason: str = "", status: str = "ready",
                   when: Optional[str] = None) -> None:
        log_path = self.dir / "log.md"
        existing = self.store.read_text(log_path) or self._log_scaffold()
        stamp = when or f"{date.today().isoformat()} 00:00 UTC"
        block = (f"\n## {stamp} | {action} | {target}\n"
                 f"- reason: {reason}\n- status: {status}\n")
        self.store.write_text(log_path, existing.rstrip() + "\n" + block)

    def _log_scaffold(self) -> str:
        return (f'---\ngald3r_rel_version: "{self.cfg.gald3r_rel_version}"\n'
                f'schema_version: "generic-v1"\n---\n# Vault Log\n')

    # ---- reindex (regenerate _index.yaml + index.md) ----
    def reindex(self) -> Dict[str, Any]:
        notes = self.list()
        self._write_index_yaml(notes)
        self._write_index_md(notes)
        return {"count": len(notes), "tags": sorted({t for n in notes for t in n.tags})}

    def _write_index_yaml(self, notes: List[Note]) -> None:
        v = self.cfg.gald3r_rel_version
        header = (f"# gald3r_rel_version: {v}\n"
                  f"# schema_version: generic-v1\n"
                  f"# Vault Index - auto-generated by gald3r.systems.vault\n"
                  f"# Last updated: {date.today().isoformat()} 00:00:00 UTC\n"
                  f"# Total notes: {len(notes)}\n")
        if not notes:
            self.store.write_text(self.dir / "_index.yaml", header + "notes:\n")
            return
        entries = [{
            "path": n.rel, "title": n.title, "type": n.type,
            "date": str(n.fm.get("date", "")), "ingestion_type": n.fm.get("ingestion_type", ""),
            "source": n.fm.get("source", ""), "tags": n.tags,
            "next_refresh": n.fm.get("next_refresh"),
        } for n in notes]
        body = yaml.safe_dump({"notes": entries}, sort_keys=False, allow_unicode=True,
                              default_flow_style=False)
        self.store.write_text(self.dir / "_index.yaml", header + body)

    def _write_index_md(self, notes: List[Note]) -> None:
        groups: Dict[str, List[Note]] = {}
        for n in notes:
            groups.setdefault(str(Path(n.rel).parent.as_posix()), []).append(n)
        sections = []
        for folder in sorted(groups):
            lines = [f"- [[{n.rel.removesuffix('.md')}|{n.title}]]"
                     for n in sorted(groups[folder], key=lambda x: x.title)]
            sections.append(f"### {folder}\n" + "\n".join(lines))
        notes_block = "\n\n".join(sections) if sections else "*(no notes yet)*"
        self.store.write_text(self.dir / "index.md", f"""---
gald3r_rel_version: "{self.cfg.gald3r_rel_version}"
schema_version: "generic-v1"
---
# Vault Index

Generated vault home page.

## Summary

- Total notes: {len(notes)}

## Notes by Folder

{notes_block}
""")

    # ---- lint (deterministic structural checks only) ----
    def lint(self) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for path in self._note_files():
            raw_fm, _ = self.store.read_doc(path)
            rel = path.relative_to(self.dir).as_posix()
            if "topics" in raw_fm:
                issues.append({"note": rel, "issue": "uses legacy 'topics:' key (use 'tags:')",
                               "severity": "high"})
            fm = self._normalize_fm(raw_fm)
            for k in REQUIRED:
                if k == "tags":
                    continue
                if not fm.get(k):
                    issues.append({"note": rel, "issue": f"missing required field: {k}",
                                   "severity": "high"})
            if not fm.get("tags"):
                issues.append({"note": rel, "issue": "empty tags (not searchable in Obsidian)",
                               "severity": "medium"})
            if fm.get("type") and fm["type"] not in TYPE_FOLDER:
                issues.append({"note": rel, "issue": f"unknown type '{fm['type']}'",
                               "severity": "low"})
        return issues
