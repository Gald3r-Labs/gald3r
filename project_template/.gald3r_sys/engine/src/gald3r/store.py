"""All `.gald3r/` file I/O — the ONE place that touches disk.

Reads tolerantly (any valid YAML frontmatter, BOM-safe) and writes deterministically
(controlled key order, LF endings, no BOM) so that what the engine writes is
format-compatible with what the markdown system + humans hand-author. This module
makes no LLM calls and knows nothing about tasks specifically.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

# canonical frontmatter key order (task files); unknown keys follow, stable-sorted
_FM_ORDER = [
    "id", "title", "type", "status", "priority", "created_date",
    "dependencies", "workspace_repos", "release_hold",
    "status_changed", "worktree_owner",
    "gald3r_rel_version", "schema_version",
]

_NEEDS_QUOTE = re.compile(r'[:#\[\]{}",\n]|^\s|\s$|^[&*!|>%@`?-]')


def split_doc(text: str) -> Tuple[Dict[str, Any], str]:
    """Split a markdown doc into (frontmatter dict, body str). Tolerant; BOM-safe."""
    m = re.match(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, m.group(2)


def _scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_scalar(x) for x in v) + "]"
    s = "" if v is None else str(v)
    if s == "" or _NEEDS_QUOTE.search(s):
        return json.dumps(s, ensure_ascii=False)  # valid YAML double-quoted scalar
    return s


def emit_frontmatter(fm: Dict[str, Any]) -> str:
    keys = [k for k in _FM_ORDER if k in fm] + sorted(k for k in fm if k not in _FM_ORDER)
    lines = ["---"]
    for k in keys:
        lines.append(f"{k}: {_scalar(fm[k])}")
    lines.append("---")
    return "\n".join(lines)


class Store:
    """Low-level reader/writer for documents under `.gald3r/`."""

    def __init__(self, gald3r_dir: Path):
        self.dir = Path(gald3r_dir)

    # ---- documents (frontmatter + body) ----
    def read_doc(self, path: Path) -> Tuple[Dict[str, Any], str]:
        return split_doc(Path(path).read_text(encoding="utf-8-sig"))

    def write_doc(self, path: Path, fm: Dict[str, Any], body: str = "") -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        content = emit_frontmatter(fm) + "\n\n" + (body or "").strip() + "\n"
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)

    # ---- plain text ----
    def read_text(self, path: Path) -> str:
        p = Path(path)
        return p.read_text(encoding="utf-8-sig") if p.exists() else ""

    def write_text(self, path: Path, text: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def remove(self, path: Path) -> None:
        p = Path(path)
        if p.exists():
            p.unlink()
