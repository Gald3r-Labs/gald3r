#!/usr/bin/env python3
"""Python port of check_platform_status.ps1 (T1585).

Read and report the gald3r cross-platform capability index. Entry point for
@g-platform-check; CHECK delegate for g-skl-platform-monitor.

Reads .gald3r/PLATFORM_STATUS.md and reports the current capability state for
one platform (-Platform <name>) or all 23 (default). T1460 SKELETON: parses
and reports the status table today; deep per-platform gap analysis and
doc-diff are placeholder calls to the future g-skl-platform-monitor
operations (CHECK / SCAN_DOCS), completed by T1461-T1483.

-GenerateMatrix (T1543): reads all 23 canonical PLATFORM_SPEC.md files,
derives each capability cell (Hooks / Rules / Skills / Commands / MCP /
Docs Fresh), and (re)writes .gald3r/PLATFORM_CAPABILITY_MATRIX.md. Reads
PLATFORM_STATUS.md read-only to cross-check (warns on disagreement; NEVER
overwrites PLATFORM_STATUS.md).
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _bootstrap_engine() -> bool:
    """Make gald3r.utils importable; fall back to stdlib when unavailable."""
    try:
        import gald3r.utils  # noqa: F401

        return True
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for d in here.parents:
        engine_src = d / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401

                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()


def _color_enabled() -> bool:
    if _HAS_ENGINE:
        from gald3r.utils import console

        return console.color_enabled()
    return bool(getattr(sys.stdout, "isatty", lambda: False)()) and not os.environ.get("NO_COLOR")


# Console color codes mirroring the PS1 -ForegroundColor usage.
_COLORS = {
    "cyan": "36", "red": "31", "yellow": "33", "green": "32",
    "darkgray": "90", "darkyellow": "33", "gray": "37",
}


def say(msg: str, color: Optional[str] = None) -> None:
    """Write-Host equivalent — same text, ANSI color when supported."""
    if color and _color_enabled():
        print(f"\x1b[{_COLORS[color]}m{msg}\x1b[0m")
    else:
        print(msg)


# The 23 supported platforms (matches PLATFORM_STATUS.md rows and T1461-T1483).
KNOWN_PLATFORMS = [
    "cursor", "claude", "copilot", "codex", "antigravity", "windsurf", "gemini",
    "cline", "roo", "opencode", "openhands", "kiro", "aider", "augment", "goose",
    "junie", "kiro-cli", "mistral", "openclaw", "qwen", "replit", "subq", "warp",
]

VALID_CELLS = ["✅", "⚠️", "❌", "❓"]  # ✅ ⚠️ ❌ ❓
_OK, _WARN, _NO, _UNK = VALID_CELLS


def get_spec_folder_name(platform_name: str) -> str:
    """Platform name -> canonical PLATFORM_SPEC.md folder (leading-dot)."""
    if platform_name == "replit":
        return ".replit-gald3r"
    return f".{platform_name}"


def split_table_row(line: str) -> Optional[List[str]]:
    """Split a markdown table row into trimmed cells (None for non-rows)."""
    if not re.match(r"^\s*\|", line):
        return None
    inner = re.sub(r"^\s*\|", "", line)
    inner = re.sub(r"\|\s*$", "", inner)
    return [c.strip() for c in inner.split("|")]


def parse_status_rows(status_path: Path) -> List[Dict[str, str]]:
    """Parse the PLATFORM_STATUS.md capability table into row dicts."""
    rows: List[Dict[str, str]] = []
    text = status_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        cells = split_table_row(line)
        if cells is None or len(cells) < 9:
            continue
        if cells[0] == "Platform" or re.match(r"^[-: ]+$", cells[0]):
            continue
        if cells[0] not in KNOWN_PLATFORMS:
            continue
        rows.append({
            "Platform": cells[0], "Status": cells[1], "LastDocScan": cells[2],
            "Hooks": cells[3], "Rules": cells[4], "Skills": cells[5],
            "Commands": cells[6], "MCP": cells[7], "Notes": cells[8],
        })
    return rows


def get_frontmatter_field(content: str, field: str) -> Optional[str]:
    """Read a single scalar frontmatter field (between the first two '---' fences)."""
    fm_match = re.match(r"(?s)^\s*---\s*\r?\n(.*?)\r?\n---\s*\r?\n", content)
    if not fm_match:
        return None
    for line in fm_match.group(1).split("\n"):
        m = re.match(rf"^\s*{re.escape(field)}\s*:\s*(.+?)\s*(#.*)?$", line)
        if m:
            val = m.group(1).strip()
            val = val.strip('"')   # strip surrounding double quotes
            val = val.strip("'")   # strip surrounding single quotes
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
    """AC2 Hooks cross-read: return '❌' when prose clearly says no hook system."""
    section = _section_after_heading(
        content, r"^##\s+(?:\d+\.\s+)?Hooks?\s+(?:System|Support).*$")
    if section is None:
        return None
    if (re.search(r"(?i)no\s+(?:native\s+)?hook", section)
            or re.search(r"(?i)no\s+hook\s*/\s*lifecycle", section)
            or re.search(rf"(?i){_NO}\s*none", section)):
        return _NO
    return None


def get_docs_fresh_cell(last_doc_scan: Optional[str], threshold: int) -> str:
    """Compute the 'Docs Fresh' cell from last_doc_scan vs the threshold (AC2)."""
    if last_doc_scan is None or not last_doc_scan.strip():
        return _UNK
    v = last_doc_scan.strip().lower()
    if v == "never" or v == "":
        return _UNK
    try:
        parsed = datetime.strptime(last_doc_scan.strip(), "%Y-%m-%d")
    except ValueError:
        return _UNK
    age_days = (datetime.now(timezone.utc).date() - parsed.date()).days
    return _OK if age_days <= threshold else _WARN


def generate_matrix(repo_root: Path, status_path: Path, crawl_max_age_days: int) -> int:
    """T1543: -GenerateMatrix — compute 6 capability cells per platform and
    (re)write .gald3r/PLATFORM_CAPABILITY_MATRIX.md."""
    specs_root = repo_root / ".gald3r_sys" / "platforms"
    matrix_path = repo_root / ".gald3r" / "PLATFORM_CAPABILITY_MATRIX.md"

    say("\n=== check_platform_status -GenerateMatrix (T1543) ===", "cyan")
    say(f"  specs : {specs_root}", "darkgray")
    say(f"  output: {matrix_path}", "darkgray")
    say("")

    if not specs_root.exists():
        say(f"  ERROR: canonical platforms spec root not found at {specs_root}", "red")
        return 1

    # ---- Cross-check source: PLATFORM_STATUS.md (READ ONLY; never overwritten). ----
    status_by_platform: Dict[str, Dict[str, str]] = {}
    if status_path.exists():
        for row in parse_status_rows(status_path):
            status_by_platform[row["Platform"]] = row
    else:
        say("  WARN: PLATFORM_STATUS.md not found — skipping cross-check (AC5).", "yellow")

    matrix_rows: List[Dict[str, str]] = []
    missing_spec_folders: List[str] = []
    tally: Dict[str, int] = {_OK: 0, _WARN: 0, _NO: 0, _UNK: 0}

    for p in KNOWN_PLATFORMS:
        spec_path = specs_root / get_spec_folder_name(p) / "PLATFORM_SPEC.md"

        if not spec_path.exists():
            missing_spec_folders.append(p)
            matrix_rows.append({
                "Platform": p, "Hooks": _UNK, "Rules": _UNK, "Skills": _UNK,
                "Commands": _UNK, "MCP": _UNK, "DocsFresh": _UNK,
            })
            # Parity with the PS1: `5 | ForEach-Object { $tally['❓']++ }` pipes the
            # scalar 5 so the block runs ONCE (not 5 times). The PS1 intent was +5
            # for the capability cells but the actual behavior is +1; mirrored
            # exactly here so .py and .ps1 tallies match (pre-existing PS1 quirk).
            tally[_UNK] += 1   # capability cells (DocsFresh counted below)
            tally[_UNK] += 1   # DocsFresh
            continue

        content = spec_path.read_text(encoding="utf-8")

        summary = get_capability_summary_row(content)
        if not summary:
            # No structured capability table -> honest all-❓ for the 5 capability cells.
            summary = {"Hooks": _UNK, "Rules": _UNK, "Skills": _UNK,
                       "Commands": _UNK, "MCP": _UNK}

        # Hooks: prefer the structured Capability Summary cell; if non-committal (❓)
        # and the narrative clearly says "no hooks", honor the explicit ❌ (AC2 intent).
        hooks = summary["Hooks"]
        if hooks == _UNK or not hooks.strip():
            narr = get_hooks_from_narrative(content)
            if narr:
                hooks = narr

        # Normalize any unexpected token to ❓ (honest default).
        cell_hooks = hooks if hooks in VALID_CELLS else _UNK
        cell_rules = summary["Rules"] if summary["Rules"] in VALID_CELLS else _UNK
        cell_skills = summary["Skills"] if summary["Skills"] in VALID_CELLS else _UNK
        cell_commands = summary["Commands"] if summary["Commands"] in VALID_CELLS else _UNK
        cell_mcp = summary["MCP"] if summary["MCP"] in VALID_CELLS else _UNK

        # Docs Fresh (AC2): last_doc_scan vs per-spec crawl_max_age_days (fallback to CLI).
        last_scan_fm = get_frontmatter_field(content, "last_doc_scan")
        thr_fm = get_frontmatter_field(content, "crawl_max_age_days")
        threshold = crawl_max_age_days
        if thr_fm and re.match(r"^\d+$", thr_fm):
            threshold = int(thr_fm)
        # Prefer the PLATFORM_STATUS.md row's Last Doc Scan when the spec frontmatter
        # is "never" but STATUS records a real date (STATUS is the scan ledger).
        last_scan = last_scan_fm
        if (last_scan is None or last_scan.strip().lower() == "never") and p in status_by_platform:
            status_scan = status_by_platform[p]["LastDocScan"]
            if status_scan and status_scan.strip().lower() != "never":
                last_scan = status_scan
        cell_docs_fresh = get_docs_fresh_cell(last_scan, threshold)

        matrix_rows.append({
            "Platform": p, "Hooks": cell_hooks, "Rules": cell_rules,
            "Skills": cell_skills, "Commands": cell_commands, "MCP": cell_mcp,
            "DocsFresh": cell_docs_fresh,
        })

        for cv in (cell_hooks, cell_rules, cell_skills, cell_commands, cell_mcp,
                   cell_docs_fresh):
            if cv in tally:
                tally[cv] += 1
            else:
                tally[_UNK] += 1

        # ---- AC5 cross-check vs PLATFORM_STATUS.md (warn only; never write STATUS) ----
        if p in status_by_platform:
            s = status_by_platform[p]
            pairs = [
                ("Hooks", cell_hooks, s["Hooks"]),
                ("Rules", cell_rules, s["Rules"]),
                ("Skills", cell_skills, s["Skills"]),
                ("Commands", cell_commands, s["Commands"]),
                ("MCP", cell_mcp, s["MCP"]),
            ]
            emdash = "—"
            for cap, mine, theirs in pairs:
                if theirs in VALID_CELLS and mine != theirs:
                    say(f"  Matrix says {mine} but STATUS says {theirs} for {p} "
                        f"{cap} {emdash} verify PLATFORM_SPEC.md or PLATFORM_STATUS.md",
                        "yellow")

    if missing_spec_folders:
        say("  NOTE: {0} platform(s) had no canonical PLATFORM_SPEC.md (cells left {1}): {2}".format(
            len(missing_spec_folders), _UNK, ", ".join(missing_spec_folders)), "darkyellow")

    # ---- Write the matrix file, preserving the existing column layout/order. ----
    lines: List[str] = []
    lines.append("# PLATFORM_CAPABILITY_MATRIX.md — Feature Comparison Across Platforms")
    lines.append("")
    lines.append("**Generated by** `check_platform_status.py --generate-matrix` (T1543). "
                 "Owned by `g-agnt-platformer`.")
    lines.append("23 platforms × 6 capability columns. Cells sourced from each "
                 "platform's canonical `PLATFORM_SPEC.md`")
    lines.append("(`## Capability Summary` table + frontmatter `last_doc_scan`). "
                 "Cross-checked against `PLATFORM_STATUS.md`.")
    lines.append("")
    lines.append(f"Legend: {_OK} verified working · {_WARN} partial / Cursor-generic "
                 f"· {_NO} not supported · {_UNK} untested.")
    lines.append("")
    lines.append("| Platform | Hooks | Rules | Skills | Commands | MCP | Docs Fresh |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in matrix_rows:
        lines.append("| {0} | {1} | {2} | {3} | {4} | {5} | {6} |".format(
            r["Platform"], r["Hooks"], r["Rules"], r["Skills"], r["Commands"],
            r["MCP"], r["DocsFresh"]))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Capability columns**")
    lines.append("")
    lines.append("| Column | Meaning |")
    lines.append("|---|---|")
    lines.append("| Hooks | Native lifecycle hook system + gald3r hook wiring |")
    lines.append("| Rules | Persistent always-apply rules / memory injection |")
    lines.append("| Skills | `g-skl-*/SKILL.md` discovery + invocation |")
    lines.append("| Commands | `@g-*` slash commands / workflow equivalents |")
    lines.append("| MCP | Model Context Protocol server support |")
    lines.append("| Docs Fresh | Last doc scan within `crawl_max_age_days` |")
    lines.append("")
    lines.append("Cells are derived from each platform's `## Capability Summary` table "
                 "in its canonical `PLATFORM_SPEC.md`; `Docs Fresh` is computed from "
                 "frontmatter `last_doc_scan` vs `crawl_max_age_days` "
                 f"(default {crawl_max_age_days}). Regenerate with "
                 "`check_platform_status.py --generate-matrix`.")

    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    total_cells = len(matrix_rows) * 6
    say("")
    say("  Updated {0} cells ({1} {5}, {2} {6}, {3} {7}, {4} {8})".format(
        total_cells, tally[_OK], tally[_WARN], tally[_NO], tally[_UNK],
        _OK, _WARN, _NO, _UNK), "green")
    return 0


def status_report(status_path: Path, platform: str) -> int:
    """Default mode: parse and report the PLATFORM_STATUS.md capability table."""
    say("\n=== check_platform_status (T1460 skeleton) ===", "cyan")

    if not status_path.exists():
        say(f"  ERROR: PLATFORM_STATUS.md not found at {status_path}", "red")
        say("  Run T1460 setup or @g-platform-check to (re)generate it.", "darkgray")
        return 1

    rows = parse_status_rows(status_path)

    if platform != "all":
        target = platform.lower()
        if target not in KNOWN_PLATFORMS:
            say(f"  ERROR: unknown platform '{platform}'. "
                f"Known: {', '.join(KNOWN_PLATFORMS)}", "red")
            return 1
        rows = [r for r in rows if r["Platform"] == target]

    if not rows:
        say("  No matching platform rows found in PLATFORM_STATUS.md.", "yellow")
        return 1

    # Report (Format-Table equivalent: auto-sized aligned columns).
    cols = ["Platform", "Status", "LastDocScan", "Hooks", "Rules", "Skills",
            "Commands", "MCP"]
    widths = {c: max(len(c), max(len(r[c]) for r in rows)) for c in cols}
    say("")
    say("  ".join(c.ljust(widths[c]) for c in cols))
    say("  ".join(("-" * len(c)).ljust(widths[c]) for c in cols))
    for r in rows:
        say("  ".join(r[c].ljust(widths[c]) for c in cols))
    say("")

    healthy = sum(1 for r in rows if r["Status"] == _OK)
    attention = sum(1 for r in rows if r["Status"] == _WARN)
    rework = sum(1 for r in rows if r["Status"] == _NO)
    unknown = sum(1 for r in rows if r["Status"] == _UNK)

    say("  Summary: {0} healthy, {1} need attention, {2} need rework, {3} unknown (of {4})".format(
        healthy, attention, rework, unknown, len(rows)), "green")

    # Placeholder delegation to future g-skl-platform-monitor operations (T1461-T1483).
    # TODO[TASK-1460->T1461-T1483]: wire CHECK gap-analysis + SCAN_DOCS diff here once the
    # per-platform monitor operations are implemented. Scaffolding by design per T1460 spec.
    say("  (deep gap analysis / doc-scan: g-skl-platform-monitor CHECK|SCAN_DOCS -- T1461-T1483)",
        "darkgray")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Read and report the gald3r cross-platform capability index "
                    "(Python port of check_platform_status.ps1, T1460/T1543).",
        allow_abbrev=False)
    parser.add_argument("-Platform", "--platform", dest="platform", default="all",
                        help="Platform name (e.g. cursor, claude, windsurf). "
                             "Default 'all' reports every platform.")
    parser.add_argument("-GenerateMatrix", "--generate-matrix", dest="generate_matrix",
                        action="store_true",
                        help="T1543: derive capability cells from PLATFORM_SPEC.md "
                             "files and (re)write PLATFORM_CAPABILITY_MATRIX.md.")
    parser.add_argument("-CrawlMaxAgeDays", "--crawl-max-age-days",
                        dest="crawl_max_age_days", type=int, default=7,
                        help="Docs-freshness threshold in days (default 7).")
    args = parser.parse_args(argv)

    # Resolve the project root (parent of the scripts/ folder, matching the PS1's
    # `(Get-Item $PSScriptRoot).Parent` — originally custom_scripts/ at repo root).
    repo_root = Path(__file__).resolve().parent.parent
    status_path = repo_root / ".gald3r" / "PLATFORM_STATUS.md"

    if args.generate_matrix:
        return generate_matrix(repo_root, status_path, args.crawl_max_age_days)
    return status_report(status_path, args.platform)


if __name__ == "__main__":
    sys.exit(main())
