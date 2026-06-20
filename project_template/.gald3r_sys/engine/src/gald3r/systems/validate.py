"""Validation gate — `gald3r validate [--fix]`. The engine ENFORCES the `.gald3r`
contract that the `g-rl-*` rules only advise (T520, epic T518).

For every task/bug file it:
  * validates frontmatter against the schema (required fields, enums, types);
  * normalizes status case/aliases to the canonical T519 token (`Open` -> `open`,
    `wont-fix` -> `wont_fix`); an un-normalizable status is an error;
  * verifies the file lives in the folder its status requires;
  * reports frontmatter <-> index (TASKS.md / BUGS.md) agreement.

Read-only by default. ``--fix`` performs ONLY safe, reversible normalizations (status
canonicalization in-place) and folder moves — it never edits the curated index, and it is
idempotent (a second run finds nothing to fix). Non-zero exit on any unresolved violation so
a pre-commit hook can fail closed.

Pure Mode-A: deterministic file ops, no LLM calls.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r import ids as _ids
from gald3r.schema import status as _status
from gald3r.schema import task as _task
from gald3r.store import Store

ERROR = "error"      # schema violation / un-normalizable status -> always blocks
FIXABLE = "fixable"  # wrong case-alias status, wrong folder -> --fix resolves
WARN = "warn"        # frontmatter/index disagreement -> reported, never auto-rewritten


@dataclass
class Violation:
    file: str
    item: str        # "task" | "bug"
    kind: str        # ERROR | FIXABLE | WARN
    field: str
    message: str
    fixed: bool = False


# tasks/awaiting/ is an accepted alias of tasks/awaiting-verification/ (both spellings ship)
_TASK_FOLDER_ALIASES = {"awaiting-verification": {"awaiting-verification", "awaiting"}}


class ValidateSystem:
    def __init__(self, g):
        self.g = g
        self.cfg = g.config
        self.store = Store(self.cfg.gald3r_dir)
        self._tasks_dir = self.cfg.tasks_dir
        self._bugs_dir = self.cfg.gald3r_dir / "bugs"

    # ---- file discovery ----------------------------------------------------
    def _select(self, paths: Optional[List[str]]) -> Dict[str, List[Path]]:
        """Group target files into {'task': [...], 'bug': [...]}. With no paths, scan
        the whole tasks/ and bugs/ trees; with paths, filter to the ones that belong."""
        out: Dict[str, List[Path]] = {"task": [], "bug": []}
        if paths:
            for raw in paths:
                p = Path(raw)
                if not p.is_absolute():
                    p = (self.cfg.root / raw).resolve()
                if not p.is_file():
                    continue
                kind = self._classify(p)
                if kind:
                    out[kind].append(p)
        else:
            if self._tasks_dir.exists():
                out["task"] = sorted(self._tasks_dir.rglob("task*.md"))
            if self._bugs_dir.exists():
                out["bug"] = sorted(self._bugs_dir.rglob("bug*.md"))
        return out

    @staticmethod
    def _classify(p: Path) -> Optional[str]:
        parts = {part.lower() for part in p.parts}
        if "tasks" in parts and p.name.lower().startswith("task"):
            return "task"
        if "bugs" in parts and p.name.lower().startswith("bug"):
            return "bug"
        return None

    # ---- index membership (report-only) ------------------------------------
    def _index_ids(self, index_path: Path, patterns: List[str]) -> set:
        """Collect referenced ids from an index, tolerant of BOTH index formats: the
        engine's `T123` / `BUG-123` and the regenerate_tasks_md.ps1 markdown-link
        `[123](tasks/...)` (T521 will unify these; until then, accept either)."""
        text = self.store.read_text(index_path) if index_path.exists() else ""
        if not text:
            return set()
        body = "\n".join(ln for ln in text.splitlines()
                         if not re.match(r"\s*#+\s*Next\b.*\bID\b", ln))
        ids: set = set()
        for pat in patterns:
            ids |= {int(m) for m in re.findall(pat, body)}
        return ids

    @staticmethod
    def _num(v: Any) -> Optional[int]:
        m = re.search(r"\d+", str(v))
        return int(m.group()) if m else None

    def _safe_read(self, path: Path):
        """Read a doc, never raising — a file the gate exists to catch (malformed YAML,
        unquoted colon, double fence) must surface as a violation, not crash the run."""
        try:
            fm, body = self.store.read_doc(path)
            return fm, body, None
        except Exception as e:  # malformed frontmatter is itself a finding
            return None, "", f"unparseable frontmatter ({e.__class__.__name__}): {e}"

    # ---- per-item validation -----------------------------------------------
    def _validate_task(self, path: Path, fix: bool, index_ids: set) -> List[Violation]:
        rel = str(path.relative_to(self.cfg.root)).replace("\\", "/")
        fm, body, err = self._safe_read(path)
        if err:
            return [Violation(rel, "task", ERROR, "frontmatter", err)]
        vs: List[Violation] = []
        if not fm:
            return [Violation(rel, "task", ERROR, "frontmatter", "no YAML frontmatter")]

        # schema errors (status handled separately via normalization, below)
        for e in _task.validate(fm):
            if "status" not in e.lower():
                vs.append(Violation(rel, "task", ERROR, "frontmatter", e))

        raw = fm.get("status")
        eff = None
        if raw not in (None, ""):
            norm = _status.normalize_task_status(raw)
            if norm is None:
                vs.append(Violation(rel, "task", ERROR, "status",
                                    f"status '{raw}' is not in the task vocabulary"))
            else:
                eff = norm
                if norm != raw:
                    vs.append(self._fix_status(path, fm, body, raw, norm, "task", fix))

        if eff:
            vs.extend(self._check_folder(path, fm, body, eff, _task.folder_for(eff), "task", fix))

        n = self._num(fm.get("id"))
        if n is not None and index_ids and n not in index_ids:
            vs.append(Violation(rel, "task", WARN, "index",
                                f"T{n} has a file but is not referenced in TASKS.md"))
        if not _ids.has_valid_uuid(fm):
            vs.append(Violation(rel, "task", WARN, "uuid",
                                "missing stable uuid (T522) — run the uuid backfill; "
                                "new tasks are auto-stamped"))
        return vs

    def _validate_bug(self, path: Path, fix: bool, index_ids: set) -> List[Violation]:
        rel = str(path.relative_to(self.cfg.root)).replace("\\", "/")
        fm, body, err = self._safe_read(path)
        if err:
            return [Violation(rel, "bug", ERROR, "frontmatter", err)]
        vs: List[Violation] = []
        if not fm:
            return [Violation(rel, "bug", ERROR, "frontmatter",
                              "no YAML frontmatter (status/severity likely live in the body)")]

        bugs = self.g.bugs
        for e in bugs._validate(fm):
            if "status" not in e.lower():
                vs.append(Violation(rel, "bug", ERROR, "frontmatter", e))

        raw = fm.get("status")
        eff = None
        if raw not in (None, ""):
            norm = _status.normalize_bug_status(raw)
            if norm is None:
                vs.append(Violation(rel, "bug", ERROR, "status",
                                    f"status '{raw}' is not in the bug vocabulary"))
            else:
                eff = norm
                if norm != raw:
                    vs.append(self._fix_status(path, fm, body, raw, norm, "bug", fix))

        if eff:
            vs.extend(self._check_folder(path, fm, body, eff, bugs._folder(eff), "bug", fix))

        n = self._num(fm.get("id"))
        if n is not None and index_ids and n not in index_ids:
            vs.append(Violation(rel, "bug", WARN, "index",
                                f"BUG-{n} has a file but is not referenced in BUGS.md"))
        if not _ids.has_valid_uuid(fm):
            vs.append(Violation(rel, "bug", WARN, "uuid",
                                "missing stable uuid (T522) — run the uuid backfill; "
                                "new bugs are auto-stamped"))
        return vs

    # ---- fixers (safe, reversible) -----------------------------------------
    def _fix_status(self, path: Path, fm: Dict[str, Any], body: str,
                    raw: Any, norm: str, item: str, fix: bool) -> Violation:
        rel = str(path.relative_to(self.cfg.root)).replace("\\", "/")
        v = Violation(rel, item, FIXABLE, "status",
                      f"status '{raw}' should be canonical '{norm}'")
        if fix:
            fm["status"] = norm
            self.store.write_doc(path, fm, body)
            v.fixed = True
        return v

    def _check_folder(self, path: Path, fm: Dict[str, Any], body: str,
                      eff_status: str, expected: str, item: str, fix: bool) -> List[Violation]:
        base = self._tasks_dir if item == "task" else self._bugs_dir
        try:
            rel_parts = path.relative_to(base).parts
        except ValueError:
            rel_parts = ()
        # top = the status subfolder directly under base; "" when the file is flat in base.
        # Deeper nesting is allowed (e.g. completed/2026/05/) so the archive convention is
        # not flagged — only the top-level status bucket must match.
        top = rel_parts[0] if len(rel_parts) > 1 else ""
        ok_names = _TASK_FOLDER_ALIASES.get(expected, {expected}) if item == "task" else {expected}
        ok = (top == "" and expected == "") or (top in ok_names)
        if ok:
            return []
        rel = str(path.relative_to(self.cfg.root)).replace("\\", "/")
        target_dir = (base / expected) if expected else base
        v = Violation(rel, item, FIXABLE, "folder",
                      f"status '{eff_status}' requires {item}s/{expected or '.'}/, "
                      f"found {item}s/{top or '.'}/")
        if fix:
            target_dir.mkdir(parents=True, exist_ok=True)
            new_path = target_dir / path.name
            if new_path.resolve() != path.resolve():
                # byte-preserving move — never reserialize/reorder a file's frontmatter just
                # to relocate it (a status fix, if any, already rewrote it in place first)
                path.replace(new_path)
            v.fixed = True
        return [v]

    # ---- public API --------------------------------------------------------
    def run(self, paths: Optional[List[str]] = None, fix: bool = False) -> Dict[str, Any]:
        targets = self._select(paths)
        task_ids = self._index_ids(self.cfg.tasks_md, [r"\bT(\d+)\b", r"\[(\d+)\]\(tasks/"])
        bug_ids = self._index_ids(self.cfg.gald3r_dir / "BUGS.md",
                                  [r"\bBUG-(\d+)\b", r"\[(?:BUG-)?(\d+)\]\(bugs/"])

        violations: List[Violation] = []
        for p in targets["task"]:
            violations.extend(self._validate_task(p, fix, task_ids))
        for p in targets["bug"]:
            violations.extend(self._validate_bug(p, fix, bug_ids))

        errors = sum(1 for v in violations if v.kind == ERROR)
        fixable_unresolved = sum(1 for v in violations if v.kind == FIXABLE and not v.fixed)
        fixed = sum(1 for v in violations if v.fixed)
        return {
            "checked": len(targets["task"]) + len(targets["bug"]),
            "tasks_checked": len(targets["task"]),
            "bugs_checked": len(targets["bug"]),
            "violations": [asdict(v) for v in violations],
            "errors": errors,
            "fixable": sum(1 for v in violations if v.kind == FIXABLE),
            "fixed": fixed,
            "warnings": sum(1 for v in violations if v.kind == WARN),
            # ok = nothing blocks a commit: no schema errors and no unresolved fixables
            "ok": errors == 0 and fixable_unresolved == 0,
        }
