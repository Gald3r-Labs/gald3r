#!/usr/bin/env python3
"""Shared PLATFORM_SPEC.md parsing + crawl-ledger reading helpers (T514 / T515).

This is the ONE place the platform freshness-loop consumers parse a curated
``PLATFORM_SPEC.md`` and read the host-side crawl ledger. It factors the spec
parsing that ``check_platform_status.py`` already does (``split_table_row``,
``get_frontmatter_field``, ``get_capability_summary_row``, the Docs-Fresh
computation, the narrative-Hooks cross-read) into a reusable module so that:

  * spec_refresh.py (T514, GAP A) — crawled docs (DB snapshot) -> PLATFORM_SPEC.md
    change proposals — and
  * generate_status.py (T515, GAP B) — PLATFORM_SPEC.md + crawl ledger ->
    PLATFORM_STATUS.md

both derive cells the SAME way the matrix generator does (so a regen produces
zero cross-check warnings on unchanged inputs). ``check_platform_status.py``
keeps its own copies of these functions (it predates this work and the matrix
generator is surgically left untouched); this module is the single home the two
NEW consumers import, keeping the parse logic at exactly two copies rather than
fanning a third out across the consumers.

CRAWL LEDGER (host-side, C-001 parity): the crawl freshness window lives in the
backend ``platform_ext.platform_docs_crawl_registry`` table, reachable only via
MCP (``platform_crawl_status`` / ``update_crawl_registry``). The backend never
writes repo files in a per-request tenant session, so these consumers run
host-side and read the ledger from a JSON snapshot the host crawl runner exports
(``--crawl-ledger <path>``), shaped like the ``platform_crawl_status`` registry
list. When no ledger snapshot is supplied, the spec frontmatter ``last_doc_scan``
is the authoritative Last-Doc-Scan source (it is itself stamped from the registry
by the spec-refresh consumer). No DB connection and no new table are required.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Capability cell vocabulary — must match check_platform_status.VALID_CELLS.
OK, WARN, NO, UNK = "✅", "⚠️", "❌", "❓"
VALID_CELLS = [OK, WARN, NO, UNK]

# The five capability columns carried in a spec's ## Capability Summary table,
# in canonical order (Docs Fresh is computed separately from the ledger).
CAPABILITY_COLUMNS = ["Hooks", "Rules", "Skills", "Commands", "MCP"]

# Platforms can name their crawl registry differently from their gald3r roster id
# (the backend registry uses 'claude_code' for the 'claude' platform). Map roster
# id -> registry platform key so a ledger snapshot resolves correctly. Unmapped
# names pass through unchanged.
_LEDGER_PLATFORM_ALIASES = {"claude": "claude_code"}


# --------------------------------------------------------------------------- #
# Markdown table + frontmatter parsing (shared with check_platform_status.py)  #
# --------------------------------------------------------------------------- #
def split_table_row(line: str) -> Optional[List[str]]:
    """Split a markdown table row into trimmed cells (None for non-rows)."""
    if not re.match(r"^\s*\|", line):
        return None
    inner = re.sub(r"^\s*\|", "", line)
    inner = re.sub(r"\|\s*$", "", inner)
    return [c.strip() for c in inner.split("|")]


def get_frontmatter_field(content: str, field: str) -> Optional[str]:
    """Read a single scalar frontmatter field (between the first two '---' fences)."""
    fm_match = re.match(r"(?s)^\s*---\s*\r?\n(.*?)\r?\n---\s*\r?\n", content)
    if not fm_match:
        return None
    for line in fm_match.group(1).split("\n"):
        m = re.match(rf"^\s*{re.escape(field)}\s*:\s*(.+?)\s*(#.*)?$", line)
        if m:
            val = m.group(1).strip().strip('"').strip("'")
            return val
    return None


def _section_after_heading(content: str, heading_rx: str) -> Optional[str]:
    """Return the text from a heading to (not including) the next '## ' heading."""
    h = re.search(heading_rx, content, re.MULTILINE)
    if not h:
        return None
    section = content[h.start():]
    hlen = len(h.group(0))
    nxt = re.search(r"(?m)^##\s", section[hlen:])
    if nxt:
        section = section[: hlen + nxt.start()]
    return section


def get_capability_summary_row(content: str) -> Optional[Dict[str, str]]:
    """Extract the single data row from the '## Capability Summary' table."""
    section = _section_after_heading(content, r"^##\s+Capability Summary.*$")
    if section is None:
        return None
    data_row: Optional[List[str]] = None
    for line in section.split("\n"):
        cells = split_table_row(line)
        if cells is None or len(cells) < 6:
            continue
        if re.match(r"^[Hh]ooks$", cells[0]):       # header
            continue
        if re.match(r"^[-: ]+$", cells[0]):          # separator
            continue
        data_row = cells
        break
    if not data_row:
        return None
    return {
        "Hooks": data_row[0], "Rules": data_row[1], "Skills": data_row[2],
        "Commands": data_row[3], "MCP": data_row[4],
    }


def get_hooks_from_narrative(content: str) -> Optional[str]:
    """Return '❌' when the Hooks-section prose clearly says no hook system."""
    section = _section_after_heading(
        content, r"^##\s+(?:\d+\.\s+)?Hooks?\s+(?:System|Support).*$")
    if section is None:
        return None
    if (re.search(r"(?i)no\s+(?:native\s+)?hook", section)
            or re.search(r"(?i)no\s+hook\s*/\s*lifecycle", section)
            or re.search(rf"(?i){NO}\s*none", section)):
        return NO
    return None


def normalize_cell(value: Optional[str]) -> str:
    """Map any token to a valid capability cell (honest ❓ default)."""
    if value and value in VALID_CELLS:
        return value
    return UNK


def capability_cells(content: str) -> Dict[str, str]:
    """Resolve the 5 BASE capability cells for a spec from its ``PLATFORM_SPEC.md``:
    prefer the structured ## Capability Summary row; if Hooks is non-committal
    and the narrative says "no hooks", honor the explicit ❌.

    This is the *spec-only* base. :func:`matrix_capability_cells` layers the curated
    ``platform_matrix_data.json`` override on top — that override is the AUTHORITATIVE
    result ``check_platform_status.py --generate-matrix`` writes, and the one
    ``generate_status.py`` must match (T515 AC2)."""
    summary = get_capability_summary_row(content) or {}
    hooks = summary.get("Hooks", UNK)
    if hooks == UNK or not hooks.strip():
        narr = get_hooks_from_narrative(content)
        if narr:
            hooks = narr
    return {
        "Hooks": normalize_cell(hooks),
        "Rules": normalize_cell(summary.get("Rules")),
        "Skills": normalize_cell(summary.get("Skills")),
        "Commands": normalize_cell(summary.get("Commands")),
        "MCP": normalize_cell(summary.get("MCP")),
    }


# Curated-data key -> capability column name, in canonical column order. The curated
# platform_matrix_data.json uses lowercase keys (hooks/rules/...); the table columns
# are title-case (Hooks/Rules/...).
_CURATED_KEY_TO_COLUMN = (
    ("hooks", "Hooks"),
    ("rules", "Rules"),
    ("skills", "Skills"),
    ("commands", "Commands"),
    ("mcp", "MCP"),
)


def matrix_capability_cells(
    spec_content: Optional[str],
    curated_entry: Optional[Dict[str, object]] = None,
) -> Dict[str, str]:
    """Resolve the 5 AUTHORITATIVE capability cells the way ``--generate-matrix`` does:
    derive the spec base via :func:`capability_cells` (all-❓ when there is no spec),
    then let the curated ``platform_matrix_data.json`` entry override each cell (T653).

    This is the SINGLE home of the base+curated merge so the matrix generator and the
    STATUS generator can never disagree (T515 AC2 — a STATUS regen on unchanged inputs
    leaves zero matrix-vs-STATUS cross-check warnings). Untested-stub specs (all ❓)
    whose researched values live only in the curated data therefore land the SAME cell
    in STATUS as in the matrix, instead of an honest-but-mismatched ❓."""
    if spec_content is not None:
        cells = capability_cells(spec_content)
    else:
        cells = {col: UNK for col in CAPABILITY_COLUMNS}
    cur = curated_entry or {}
    for key, col in _CURATED_KEY_TO_COLUMN:
        if key in cur:
            cells[col] = normalize_cell(str(cur[key]))
    return cells


# --------------------------------------------------------------------------- #
# Docs-Fresh computation (shared with the matrix generator)                    #
# --------------------------------------------------------------------------- #
def _today():
    return datetime.now(timezone.utc).date()


def docs_fresh_cell(last_doc_scan: Optional[str], threshold: int) -> str:
    """Compute the 'Docs Fresh' cell from last_doc_scan vs the threshold."""
    if last_doc_scan is None or not last_doc_scan.strip():
        return UNK
    v = last_doc_scan.strip().lower()
    if v in ("never", ""):
        return UNK
    try:
        parsed = datetime.strptime(last_doc_scan.strip(), "%Y-%m-%d")
    except ValueError:
        return UNK
    age_days = (_today() - parsed.date()).days
    return OK if age_days <= threshold else WARN


def spec_threshold(content: str, default: int = 7) -> int:
    """Resolve the per-spec crawl_max_age_days (fallback to default)."""
    thr_fm = get_frontmatter_field(content, "crawl_max_age_days")
    if thr_fm and re.match(r"^\d+$", thr_fm):
        return int(thr_fm)
    return default


# --------------------------------------------------------------------------- #
# Crawl ledger (host-side JSON snapshot of platform_docs_crawl_registry)       #
# --------------------------------------------------------------------------- #
def load_crawl_ledger(path: Optional[Path]) -> Dict[str, Dict[str, object]]:
    """Load a host-side crawl-ledger JSON snapshot keyed by platform.

    Accepts either shape the host crawl runner / platform_crawl_status emits:
      * ``{"registry": [ {platform, last_crawled_at, pages_count, crawl_status}, ... ]}``
      * a bare ``[ {...}, ... ]`` list of the same rows.

    Returns ``{platform_id: {"last_doc_scan": "YYYY-MM-DD"|None, "pages_count":
    int, "crawl_status": str}}``. ``last_crawled_at`` (ISO timestamp) is reduced
    to a calendar date so it lines up with the spec ``last_doc_scan`` format.
    Returns an empty dict when ``path`` is None or the file is absent/empty.
    """
    if path is None or not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    rows = data.get("registry", []) if isinstance(data, dict) else data
    out: Dict[str, Dict[str, object]] = {}
    for row in rows or []:
        platform = str(row.get("platform", "")).strip().lower()
        if not platform:
            continue
        last = row.get("last_crawled_at")
        scan_date: Optional[str] = None
        if last:
            scan_date = _iso_to_date(str(last))
        out[platform] = {
            "last_doc_scan": scan_date,
            "pages_count": int(row.get("pages_count") or 0),
            "crawl_status": str(row.get("crawl_status") or "never"),
        }
    return out


def _iso_to_date(value: str) -> Optional[str]:
    """Reduce an ISO timestamp (or a bare YYYY-MM-DD) to a YYYY-MM-DD date."""
    v = value.strip()
    if not v:
        return None
    # Already a plain date?
    if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        return v
    try:
        # Tolerate a trailing 'Z' (Python <3.11 fromisoformat rejects it).
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except ValueError:
        # Last resort: take the leading date-looking prefix.
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", v)
        return m.group(1) if m else None


def ledger_last_doc_scan(
    ledger: Dict[str, Dict[str, object]], platform: str
) -> Optional[str]:
    """Last-Doc-Scan date for a platform from the ledger (None if absent).

    Resolves the roster id to its crawl-registry key first (e.g. claude ->
    claude_code), then falls back to the roster id itself.
    """
    for key in (_LEDGER_PLATFORM_ALIASES.get(platform, platform), platform):
        row = ledger.get(key)
        if row and row.get("last_doc_scan"):
            return str(row["last_doc_scan"])
    return None


def resolve_last_doc_scan(
    spec_content: str,
    platform: str,
    ledger: Dict[str, Dict[str, object]],
) -> Optional[str]:
    """The authoritative Last-Doc-Scan for a platform: the crawl-ledger date when
    present (the real registry completion date), else the spec frontmatter
    ``last_doc_scan`` (treating 'never' as absent)."""
    from_ledger = ledger_last_doc_scan(ledger, platform)
    if from_ledger:
        return from_ledger
    fm = get_frontmatter_field(spec_content, "last_doc_scan")
    if fm and fm.strip().lower() != "never":
        return fm.strip()
    return None
