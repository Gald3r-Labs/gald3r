#!/usr/bin/env python3
"""generate_status.py — GAP B generator (T515): PLATFORM_STATUS.md from specs + ledger.

Closes the second broken link of the T513 freshness loop. ``check_platform_status.py``
reads ``PLATFORM_STATUS.md`` READ-ONLY and explicitly never writes it; the
CHECK/SCAN_DOCS auto-refresh was a documented ``TODO[TASK-1460->T1461-T1483]``
skeleton, so STATUS was maintained by hand and silently rotted (the 2026-06-02
baseline under-counted hook-capable platforms — see T512). This is the generator
that skeleton promised.

SOURCE-OF-TRUTH DECISION (T515 — Option 2, the task's recommended option):
the curated **Status verdict + Notes** columns are HAND-AUTHORED human judgement and
are PRESERVED by merge from the existing ``PLATFORM_STATUS.md``. Only the
*mechanical* cells are regenerated:

  * the 5 capability cells (Hooks/Rules/Skills/Commands/MCP) are re-derived from
    each platform's ``PLATFORM_SPEC.md`` ``## Capability Summary`` EXACTLY the way
    ``--generate-matrix`` derives them (shared via ``platform_spec_io``), so a
    regen on unchanged inputs leaves ZERO STATUS-vs-matrix cross-check warnings; and
  * ``Last Doc Scan`` is taken from the crawl ledger (``--crawl-ledger`` snapshot of
    ``platform_docs_crawl_registry``) when present — the REAL registry completion
    date — else from the spec frontmatter ``last_doc_scan`` (NOT "now" blindly).

A platform with no resolvable spec keeps its existing STATUS row untouched (rows
are never silently dropped), and an all-❓ capability set is written honestly.

C-001 parity: this is a host-side repo-file writer; it reads the crawl ledger from
a JSON export, never from a per-request backend tenant session, and requires NO DB
connection and NO new table.

Idempotent: re-running with no input change reproduces a byte-identical file modulo
the single generated ``_Generated <UTC>_`` timestamp line (suppress it with
``--no-timestamp`` for byte-for-byte diffs in tests/CI).

OUT OF SCOPE: reading crawled docs into the specs (that is T514 / spec_refresh.py).

Usage::

    python generate_status.py                       # dry-run: print the regen plan
    python generate_status.py --apply               # rewrite PLATFORM_STATUS.md
    python generate_status.py --apply --crawl-ledger registry.json
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import platform_spec_io as psio  # noqa: E402
from platform_spec_io import UNK  # noqa: E402

try:
    from check_platform_status import (  # noqa: E402
        KNOWN_PLATFORMS,
        parse_status_rows,
        resolve_spec_path,
        _find_root,
    )
except ImportError:  # pragma: no cover - defensive
    KNOWN_PLATFORMS = []  # type: ignore
    parse_status_rows = None  # type: ignore
    resolve_spec_path = None  # type: ignore
    _find_root = None  # type: ignore

# Marker line for the single generated timestamp (the only non-deterministic byte).
_GENERATED_RX = re.compile(r"(?m)^_Generated .*?_\s*$")


def _existing_rows_by_platform(status_path: Path) -> Dict[str, Dict[str, str]]:
    """Parse the existing STATUS table into {platform: row} for the merge."""
    if not status_path.exists() or parse_status_rows is None:
        return {}
    return {r["Platform"]: r for r in parse_status_rows(status_path)}


def _split_preamble_and_tail(text: str) -> tuple:
    """Split the existing STATUS file into (preamble, tail).

    preamble = everything up to and including the table's separator row
    (``|---|...|``); tail = everything from the first ``## `` heading AFTER the
    table onward (Summary / Platform-Specific sections). Both are PRESERVED
    verbatim so this generator only rewrites the data rows, never the banner,
    legend, or trailing curated prose.
    """
    lines = text.splitlines(keepends=True)
    sep_idx = None
    for i, line in enumerate(lines):
        cells = psio.split_table_row(line.rstrip("\n"))
        if cells and cells and re.match(r"^[-: ]+$", cells[0]):
            sep_idx = i
            break
    if sep_idx is None:
        return text, ""
    preamble = "".join(lines[: sep_idx + 1])
    # Tail = the first '## ' heading after the table (skipping the data rows + a
    # possible '---' divider line).
    tail_idx = None
    for j in range(sep_idx + 1, len(lines)):
        if lines[j].startswith("## "):
            tail_idx = j
            break
    tail = "".join(lines[tail_idx:]) if tail_idx is not None else ""
    return preamble, tail


def build_rows(
    repo_root: Path,
    existing: Dict[str, Dict[str, str]],
    ledger: Dict[str, Dict[str, object]],
) -> List[Dict[str, str]]:
    """Build the regenerated STATUS data rows for the full registry roster.

    Capability cells + Last Doc Scan are regenerated; Status + Notes are merged
    from ``existing``. A platform whose spec cannot be resolved keeps its prior
    row verbatim (rows are never dropped).
    """
    specs_root = repo_root / ".gald3r_sys" / "platforms"
    rows: List[Dict[str, str]] = []
    for platform in KNOWN_PLATFORMS:
        prior = existing.get(platform, {})
        spec_path = resolve_spec_path(repo_root, specs_root, platform) if resolve_spec_path else None
        if spec_path is None:
            # No spec to regenerate from: preserve the existing row untouched, or
            # write an honest all-❓ stub if the platform is brand-new to STATUS.
            rows.append({
                "Platform": platform,
                "Status": prior.get("Status", UNK),
                "LastDocScan": prior.get("LastDocScan", "never"),
                "Hooks": prior.get("Hooks", UNK),
                "Rules": prior.get("Rules", UNK),
                "Skills": prior.get("Skills", UNK),
                "Commands": prior.get("Commands", UNK),
                "MCP": prior.get("MCP", UNK),
                "Notes": prior.get("Notes", ""),
            })
            continue
        content = spec_path.read_text(encoding="utf-8")
        cells = psio.capability_cells(content)
        last_scan = psio.resolve_last_doc_scan(content, platform, ledger)
        rows.append({
            "Platform": platform,
            # Status verdict + Notes are curated human judgement -> preserved by merge.
            "Status": prior.get("Status", psio.get_frontmatter_field(content, "status") or UNK),
            "LastDocScan": last_scan or prior.get("LastDocScan", "never"),
            "Hooks": cells["Hooks"],
            "Rules": cells["Rules"],
            "Skills": cells["Skills"],
            "Commands": cells["Commands"],
            "MCP": cells["MCP"],
            "Notes": prior.get("Notes", ""),
        })
    return rows


def render_status(
    preamble: str,
    rows: List[Dict[str, str]],
    tail: str,
    timestamp: bool,
) -> str:
    """Assemble the full STATUS file: preserved preamble + regenerated data rows +
    a regenerated Summary + the preserved curated tail sections."""
    parts: List[str] = [preamble.rstrip("\n"), "\n"]
    for r in rows:
        parts.append(
            "| {Platform} | {Status} | {LastDocScan} | {Hooks} | {Rules} | "
            "{Skills} | {Commands} | {MCP} | {Notes} |\n".format(**r)
        )
    parts.append("---\n\n")

    # Regenerated Summary block (deterministic counts by Status verdict).
    healthy = sum(1 for r in rows if r["Status"] == "✅")
    attention = sum(1 for r in rows if r["Status"] == "⚠️")
    rework = sum(1 for r in rows if r["Status"] == "❌")
    unknown = sum(1 for r in rows if r["Status"] == "❓")
    parts.append("## Summary\n\n")
    parts.append("_Generated by `generate_status.py` (T515) from the per-platform "
                 "`PLATFORM_SPEC.md` `## Capability Summary` tables + the crawl ledger. "
                 "Capability cells + Last Doc Scan are regenerated; Status verdict + "
                 "Notes are preserved (Option 2 merge)._\n\n")
    if timestamp:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        parts.append(f"_Generated {now}_\n\n")
    parts.append(f"- **Total platforms**: {len(rows)}\n")
    parts.append(f"- **Healthy (✅)**: {healthy}\n")
    parts.append(f"- **Need attention (⚠️)**: {attention}\n")
    parts.append(f"- **Need rework (❌)**: {rework}\n")
    parts.append(f"- **Unknown (❓)**: {unknown}\n")

    # Preserve any curated tail sections that come AFTER the generated Summary
    # (e.g. "## Platform-Specific vs. Cursor-Copy"), but drop the OLD hand-written
    # "## Summary" so it is not duplicated.
    extra = _strip_old_summary(tail)
    if extra.strip():
        parts.append("\n")
        parts.append(extra)
    return "".join(parts)


def _strip_old_summary(tail: str) -> str:
    """Remove a leading '## Summary' section from the preserved tail (the generator
    writes its own), keeping every other curated '## ' section verbatim."""
    if not tail.strip():
        return ""
    lines = tail.splitlines(keepends=True)
    out: List[str] = []
    skipping = False
    for line in lines:
        if line.startswith("## "):
            skipping = line.strip().lower() == "## summary"
        if not skipping:
            out.append(line)
    return "".join(out)


def normalize_for_compare(text: str) -> str:
    """Strip the single generated timestamp line for idempotency comparisons."""
    return _GENERATED_RX.sub("", text)


def run(
    repo_root: Path,
    ledger_path: Optional[Path],
    apply: bool,
    timestamp: bool = True,
) -> dict:
    """Regenerate PLATFORM_STATUS.md (dry-run by default). Returns a report dict
    including the rendered text and whether it changed."""
    status_path = repo_root / ".gald3r" / "PLATFORM_STATUS.md"
    existing_text = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
    existing = _existing_rows_by_platform(status_path)
    ledger = psio.load_crawl_ledger(ledger_path)

    preamble, tail = _split_preamble_and_tail(existing_text)
    rows = build_rows(repo_root, existing, ledger)
    rendered = render_status(preamble, rows, tail, timestamp)

    changed = normalize_for_compare(rendered) != normalize_for_compare(existing_text)
    if apply:
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(rendered, encoding="utf-8")

    return {
        "status_path": str(status_path),
        "rows": rows,
        "rendered": rendered,
        "changed": changed,
        "applied": apply,
    }


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="GAP B (T515): regenerate PLATFORM_STATUS.md from the specs + "
                    "crawl ledger (Option 2: preserve Status + Notes, regenerate "
                    "capability cells + Last Doc Scan).",
        allow_abbrev=False)
    parser.add_argument("--apply", dest="apply", action="store_true",
                        help="Rewrite PLATFORM_STATUS.md. Default is dry-run "
                             "(print the regen plan, change nothing).")
    parser.add_argument("--crawl-ledger", dest="ledger", default=None,
                        help="Optional crawl-ledger JSON snapshot "
                             "(platform_crawl_status registry) for the real "
                             "Last Doc Scan completion date.")
    parser.add_argument("--no-timestamp", dest="timestamp", action="store_false",
                        help="Omit the generated timestamp line (byte-for-byte "
                             "deterministic output for tests/CI).")
    args = parser.parse_args(argv)

    if _find_root is None or not KNOWN_PLATFORMS:
        print("ERROR: check_platform_status unavailable — cannot resolve roster/root.")
        return 1
    repo_root = _find_root()
    ledger_path = Path(args.ledger) if args.ledger else None

    report = run(repo_root, ledger_path, apply=args.apply, timestamp=args.timestamp)

    print("\n=== generate_status (T515, GAP B) ===")
    print(f"  output : {report['status_path']}")
    print(f"  rows   : {len(report['rows'])} platforms")
    print(f"  changed: {report['changed']}")
    if args.apply:
        print("  APPLIED: PLATFORM_STATUS.md regenerated from specs + ledger.")
    else:
        print("  DRY-RUN: re-run with --apply to rewrite PLATFORM_STATUS.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
