"""Stable UUID identity for tasks & bugs (T522).

The display id (`T###` / `BUG-###`) is repo-local and collides on cross-project merge; a
`uuid` is the durable primary key that makes merge/absorb/split key on identity, not number.

Decision (T522 AC1): **UUIDv4** via stdlib `uuid.uuid4()`. The engine is a pure-core package
with a single runtime dependency (pyyaml); `uuid.uuid7()` is not in the stdlib (would need a
hand-rolled impl), and the merge key requires uniqueness + stability, not sortability —
chronology already lives in the display id. Reconsider v7 only if the merge tooling (AC5)
needs time-ordered keys.

The backfill is a SURGICAL line insertion (one `uuid:` line added after the id line),
NOT a frontmatter reserialization — so it never reorders/reformats curated files, and a
malformed-YAML file is skipped (reported), not corrupted.
"""
from __future__ import annotations

import re
import uuid as _uuid
from pathlib import Path
from typing import Any, Dict, List

from gald3r.store import split_doc

# RFC-4122 (any version) — validation accepts existing uuids regardless of version.
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                     r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_ID_LINE = re.compile(r"^(id|bug_id)\s*:", re.IGNORECASE)
_UUID_LINE = re.compile(r"^uuid\s*:\s*(.*?)\s*$", re.IGNORECASE)


def new_uuid() -> str:
    """A fresh stable primary key (RFC-4122 UUIDv4)."""
    return str(_uuid.uuid4())


def has_valid_uuid(fm: Dict[str, Any]) -> bool:
    v = fm.get("uuid")
    return isinstance(v, str) and bool(UUID_RE.match(v.strip()))


def _frontmatter_bounds(lines: List[str]):
    """Return (open_idx, close_idx) of the leading `---` … `---` fence, or None."""
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return 0, i
    return None


def backfill_file(path: Path) -> str:
    """Ensure one valid `uuid:` line exists in a file's frontmatter. Returns the outcome:
    'added' | 'filled' (empty/invalid → new) | 'present' | 'skipped' (no frontmatter / no id line).
    Surgical: preserves every other byte; never reserializes."""
    raw = path.read_text(encoding="utf-8-sig")
    try:
        fm, _ = split_doc(raw)
    except Exception:
        return "skipped"  # malformed YAML — leave for repair (gald3r validate reports it)
    if has_valid_uuid(fm):
        return "present"

    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(newline)
    bounds = _frontmatter_bounds(lines)
    if bounds is None:
        return "skipped"
    open_i, close_i = bounds

    # replace an empty/invalid existing `uuid:` line in place, else insert after the id line
    for i in range(open_i + 1, close_i):
        if _UUID_LINE.match(lines[i]):
            lines[i] = f"uuid: {new_uuid()}"
            path.write_text(newline.join(lines), encoding="utf-8")
            return "filled"
    anchor = next((i for i in range(open_i + 1, close_i) if _ID_LINE.match(lines[i])), None)
    if anchor is None:
        return "skipped"
    lines.insert(anchor + 1, f"uuid: {new_uuid()}")
    path.write_text(newline.join(lines), encoding="utf-8")
    return "added"


def backfill_dir(gald3r_dir: Path) -> Dict[str, Any]:
    """Idempotent one-time backfill across .gald3r/tasks + .gald3r/bugs (T522 AC3)."""
    gd = Path(gald3r_dir)
    targets: List[Path] = []
    for sub, prefix in (("tasks", "task"), ("bugs", "bug")):
        d = gd / sub
        if d.exists():
            targets += sorted(d.rglob(f"{prefix}*.md"))
    tally: Dict[str, int] = {"added": 0, "filled": 0, "present": 0, "skipped": 0}
    skipped: List[str] = []
    for p in targets:
        outcome = backfill_file(p)
        tally[outcome] += 1
        if outcome == "skipped":
            skipped.append(str(p.relative_to(gd)).replace("\\", "/"))
    return {"checked": len(targets), **tally, "skipped_files": skipped}
