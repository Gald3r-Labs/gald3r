#!/usr/bin/env python3
"""Python port of check_platform_status.ps1 (T1585).

Read and report the gald3r cross-platform capability index. Entry point for
@g-platform-check; CHECK delegate for g-skl-platform-monitor.

Reads .gald3r/PLATFORM_STATUS.md and reports the current capability state for
one platform (-Platform <name>) or every registry platform (default). The roster
is registry-driven (PLATFORM_REGISTRY.yaml, T516) — see platform_registry.py.
T1460 SKELETON: parses and reports the status table today; deep per-platform gap
analysis and doc-diff are placeholder calls to the future g-skl-platform-monitor
operations (CHECK / SCAN_DOCS), completed by T1461-T1483.

-GenerateMatrix (T1543): reads each registry platform's canonical PLATFORM_SPEC.md,
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

# Shared spec/cell parsing (the single home of the base+curated capability-cell merge,
# used by both -GenerateMatrix here and generate_status.py — T515 AC2). Script-adjacent.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import platform_spec_io as psio  # noqa: E402


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


# The supported platforms — derived from the single source of truth,
# PLATFORM_REGISTRY.yaml (T516), via the shared platform_registry reader. No hardcoded
# roster lives here anymore. If the registry file is missing, the reader returns a
# baked-in fallback roster so this tool still runs (AC2 safe fallback).
def _load_known_platforms() -> List[str]:
    try:
        from platform_registry import known_platforms  # script-adjacent import
    except ImportError:
        # Make this script's own folder importable (covers odd invocation cwds).
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from platform_registry import known_platforms
        except ImportError:
            # Last-resort fallback if the shared reader is unavailable: the original
            # 23-platform list, so the tool degrades gracefully rather than crashing.
            return [
                "cursor", "claude", "copilot", "codex", "antigravity", "windsurf",
                "gemini", "cline", "roo", "opencode", "openhands", "kiro", "aider",
                "augment", "goose", "junie", "kiro-cli", "mistral", "openclaw",
                "qwen", "replit", "subq", "warp",
            ]
    return list(known_platforms())


KNOWN_PLATFORMS = _load_known_platforms()

VALID_CELLS = ["✅", "⚠️", "❌", "❓"]  # ✅ ⚠️ ❌ ❓
_OK, _WARN, _NO, _UNK = VALID_CELLS


def get_spec_folder_name(platform_name: str) -> str:
    """Platform name -> legacy override-tree PLATFORM_SPEC.md folder (leading-dot)."""
    if platform_name == "replit":
        return ".replit-gald3r"
    return f".{platform_name}"


# Skill trees (relative to repo root) where canonical PLATFORM_SPEC.md files live in the
# absorbed layout. Probed in order; first hit wins.
_REL_SPEC_TREES = (
    Path("gald3r_templates") / "gald3r_core" / "project_template" / ".claude" / "skills",
    Path("gald3r_templates") / "gald3r_core" / "project_template" / ".cursor" / "skills",
    Path(".claude") / "skills",
    Path(".cursor") / "skills",
)


def _registry_spec_suffixes(platform_name: str) -> List[str]:
    """Candidate g-skl-platform-<suffix> names for a platform, sourced from the registry
    `spec_path` when available, else derived (name + -code-stripped short name)."""
    suffixes: List[str] = []
    try:
        from platform_registry import all_entries
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from platform_registry import all_entries
        except ImportError:
            all_entries = None  # type: ignore
    if all_entries is not None:
        for e in all_entries():
            if str(e.get("name")) == platform_name:
                sp = e.get("spec_path")
                if sp:
                    suffixes.append(str(sp).split("/")[0].replace("g-skl-platform-", ""))
                break
    suffixes.append(platform_name)
    if platform_name.endswith("-code"):
        suffixes.append(platform_name[:-5])
    # de-dup, preserve order
    seen: set = set()
    return [s for s in suffixes if s and not (s in seen or seen.add(s))]


def resolve_spec_path(repo_root: Path, specs_root: Path, platform_name: str) -> Optional[Path]:
    """Resolve a platform's PLATFORM_SPEC.md. Prefer the legacy override tree
    (.gald3r_sys/platforms/.<x>/) when present; otherwise resolve from the registry
    spec_path against the skill trees (the absorbed layout). Returns None if not found."""
    legacy = specs_root / get_spec_folder_name(platform_name) / "PLATFORM_SPEC.md"
    if legacy.exists():
        return legacy
    for suffix in _registry_spec_suffixes(platform_name):
        for rel in _REL_SPEC_TREES:
            cand = repo_root / rel / f"g-skl-platform-{suffix}" / "PLATFORM_SPEC.md"
            if cand.exists():
                return cand
    return None


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


def load_matrix_data() -> Dict[str, Dict[str, str]]:
    """Curated rich-cell data (base capabilities + Engine tier + Rules ext), keyed by
    PLATFORM_REGISTRY.yaml platform name (T653). Harvested from the canonical matrix and
    used by -GenerateMatrix as the AUTHORITATIVE cell source; platforms absent here fall
    back to PLATFORM_SPEC.md-derived base cells with ❓/— for the engine columns.
    Script-adjacent platform_matrix_data.json; returns {} when absent (generator still runs)."""
    import json
    data_path = Path(__file__).resolve().parent / "platform_matrix_data.json"
    if not data_path.is_file():
        return {}
    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    plats = raw.get("platforms") if isinstance(raw, dict) else None
    return plats if isinstance(plats, dict) else {}


def generate_matrix(repo_root: Path, status_path: Path, crawl_max_age_days: int) -> int:
    """T1543/T653: -GenerateMatrix — build the rich 8-column capability matrix (Hooks /
    Rules / Skills / Commands / MCP / Engine tier / Rules ext) for the full registry roster
    and (re)write .gald3r/PLATFORM_CAPABILITY_MATRIX.md. The roster stays registry-driven
    (KNOWN_PLATFORMS, T516). Base cells derive from each platform's PLATFORM_SPEC.md, then
    the curated platform_matrix_data.json overrides them with authoritative values; Engine
    tier + Rules ext come from the curated data. PLATFORM_STATUS.md is a read-only
    cross-check (warns; never overwritten)."""
    specs_root = repo_root / ".gald3r_sys" / "platforms"
    matrix_path = repo_root / ".gald3r" / "PLATFORM_CAPABILITY_MATRIX.md"

    curated = load_matrix_data()

    say("\n=== check_platform_status -GenerateMatrix (T1543/T653) ===", "cyan")
    say(f"  specs : {specs_root}", "darkgray")
    say(f"  output: {matrix_path}", "darkgray")
    say("")

    # The row set is registry-driven (KNOWN_PLATFORMS, T516). Spec files are resolved per
    # platform via resolve_spec_path, which prefers the legacy override tree and falls back
    # to the registry spec_path against the skill trees (absorbed layout). Only error out
    # when NEITHER source can supply a single spec.
    if not specs_root.exists():
        any_spec = any(resolve_spec_path(repo_root, specs_root, p) for p in KNOWN_PLATFORMS)
        if not any_spec and not curated:
            say(f"  ERROR: no PLATFORM_SPEC.md found via legacy {specs_root} or the registry "
                f"skill trees, and no curated platform_matrix_data.json — cannot build the "
                f"matrix.", "red")
            return 1
        if not any_spec:
            say("  NOTE: no PLATFORM_SPEC.md resolved — building from curated "
                "platform_matrix_data.json only.", "darkyellow")
        else:
            say(f"  NOTE: legacy {specs_root} absent — resolving specs from the registry "
                f"(PLATFORM_REGISTRY.yaml) against the skill trees.", "darkyellow")

    # ---- Cross-check source: PLATFORM_STATUS.md (READ ONLY; never overwritten). ----
    status_by_platform: Dict[str, Dict[str, str]] = {}
    if status_path.exists():
        for row in parse_status_rows(status_path):
            status_by_platform[row["Platform"]] = row
    else:
        say("  WARN: PLATFORM_STATUS.md not found — skipping cross-check (AC5).", "yellow")

    matrix_rows: List[Dict[str, str]] = []
    missing_data: List[str] = []
    tally: Dict[str, int] = {_OK: 0, _WARN: 0, _NO: 0, _UNK: 0}

    for p in KNOWN_PLATFORMS:
        cur = curated.get(p, {})
        engine_tier = cur.get("engine_tier", _UNK)
        rules_ext = cur.get("rules_ext", "—")

        # Base cells: derive from PLATFORM_SPEC.md (registry-driven generator logic), then
        # let the curated data override with the authoritative values (T653). This base +
        # curated merge is shared with generate_status.py (T515 AC2) via
        # platform_spec_io.matrix_capability_cells, so the matrix and STATUS can never
        # disagree on a capability cell.
        spec_path = resolve_spec_path(repo_root, specs_root, p)
        content = spec_path.read_text(encoding="utf-8") if spec_path is not None else None
        cells = psio.matrix_capability_cells(content, cur)
        cell_hooks = cells["Hooks"]
        cell_rules = cells["Rules"]
        cell_skills = cells["Skills"]
        cell_commands = cells["Commands"]
        cell_mcp = cells["MCP"]

        if spec_path is None and not cur:
            missing_data.append(p)

        matrix_rows.append({
            "Platform": p, "Hooks": cell_hooks, "Rules": cell_rules,
            "Skills": cell_skills, "Commands": cell_commands, "MCP": cell_mcp,
            "EngineTier": engine_tier, "RulesExt": rules_ext,
        })

        for cv in (cell_hooks, cell_rules, cell_skills, cell_commands, cell_mcp):
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
                        f"{cap} {emdash} verify PLATFORM_SPEC.md / curated data / STATUS",
                        "yellow")

    if missing_data:
        say("  NOTE: {0} platform(s) had neither PLATFORM_SPEC.md nor curated data "
            "(cells left {1}): {2}".format(
                len(missing_data), _UNK, ", ".join(missing_data)), "darkyellow")

    # ---- Write the matrix file (rich 8-column schema; T653). ----
    lines: List[str] = []
    lines.append("# PLATFORM_CAPABILITY_MATRIX.md — Feature Comparison Across Platforms")
    lines.append("")
    lines.append("**Generated by** `check_platform_status.py --generate-matrix` (T1543/T653). "
                 "Owned by `g-agnt-platformer`.")
    lines.append(f"Registry-driven: {len(matrix_rows)} platforms (roster from "
                 "`PLATFORM_REGISTRY.yaml`, T516). Base capability cells (Hooks / Rules / "
                 "Skills / Commands / MCP) derive from each platform's canonical "
                 "`PLATFORM_SPEC.md`")
    lines.append("(`## Capability Summary`), overridden by curated `platform_matrix_data.json` "
                 "(authoritative). `Engine tier` and `Rules ext` come from the curated data. "
                 "Cross-checked against `PLATFORM_STATUS.md`.")
    lines.append("")
    lines.append(f"Legend: {_OK} verified · {_WARN} partial · {_NO} not supported "
                 f"· {_UNK} untested.")
    lines.append("")
    lines.append("| Platform | Hooks | Rules | Skills | Commands | MCP | Engine tier | "
                 "Rules ext |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in matrix_rows:
        lines.append("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} |".format(
            r["Platform"], r["Hooks"], r["Rules"], r["Skills"], r["Commands"],
            r["MCP"], r["EngineTier"], r["RulesExt"]))
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
    lines.append("| Engine tier | How the bundled gald3r engine reaches the platform — "
                 "L2 MCP, L1 CLI (`uv run … gald3r`), L0 files-only (`SKILL.full.md`) |")
    lines.append("| Rules ext | Per-platform rule file extension "
                 "(`.md` / `.mdc` / single-file) |")
    lines.append("")
    lines.append("Base cells derive from each platform's `## Capability Summary` in its "
                 "canonical `PLATFORM_SPEC.md`, overridden by curated "
                 "`platform_matrix_data.json` (which also supplies `Engine tier` + "
                 "`Rules ext`). Regenerate with `check_platform_status.py --generate-matrix`.")

    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    total_cells = len(matrix_rows) * 5
    say("")
    say("  Updated {0} base cells ({1} {5}, {2} {6}, {3} {7}, {4} {8}) across "
        "{9} platforms".format(
            total_cells, tally[_OK], tally[_WARN], tally[_NO], tally[_UNK],
            _OK, _WARN, _NO, _UNK, len(matrix_rows)), "green")
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

    # STATUS auto-refresh (the T1460 skeleton's promise) is now BUILT — the freshness
    # loop is closed by the host-side generators, NOT by an inline placeholder here:
    #   * generate_status.py (T515, GAP B) regenerates PLATFORM_STATUS.md from each
    #     PLATFORM_SPEC.md ## Capability Summary + the curated matrix data + the crawl
    #     ledger (capability cells match -GenerateMatrix; Status + Notes preserved); and
    #   * spec_refresh.py (T514, GAP A) proposes PLATFORM_SPEC.md edits from crawled docs.
    # This default mode stays a READ-ONLY reporter by design; deep per-platform gap
    # analysis / doc-scan remains the g-skl-platform-monitor CHECK|SCAN_DOCS scope
    # (T1461-T1483), now feeding the generators above rather than an empty stub.
    say("  (regenerate STATUS: generate_status.py --apply; refresh specs: spec_refresh.py "
        "-- GAP A/B closed, T514/T515)", "darkgray")
    return 0


def _find_root(start: Optional[Path] = None) -> Path:
    """Resolve the project root by walking up from this script (BUG-161 fix).

    The script moved from the legacy ``custom_scripts/`` (one level under the repo
    root) into ``…/skills/g-skl-platform-monitor/scripts/``, so the old
    ``Path(__file__).resolve().parent.parent`` resolved to the skill folder — and every
    ``.gald3r/PLATFORM_STATUS.md`` / ``.gald3r_sys`` probe missed, making the status
    report and ``-GenerateMatrix`` exit early. Prefer the ancestor that actually holds
    ``.gald3r/PLATFORM_STATUS.md`` (the exact file this tool reads); then any ``.gald3r``
    project marker; else fall back to the identical legacy expression so no
    previously-working layout can regress.
    """
    here = (start or Path(__file__)).resolve()
    for root in here.parents:
        if (root / ".gald3r" / "PLATFORM_STATUS.md").is_file():
            return root
    for root in here.parents:
        if (root / ".gald3r").is_dir():
            return root
    return here.parent.parent  # legacy fallback — identical to pre-BUG-161 behavior


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

    # Resolve the project root via an anchored walk-up (BUG-161 fix). The script lives in
    # the skill tree now, not the legacy custom_scripts/ one level under the repo root, so
    # the old Path(__file__).parent.parent resolved to the skill folder and every probe missed.
    repo_root = _find_root()
    status_path = repo_root / ".gald3r" / "PLATFORM_STATUS.md"

    if args.generate_matrix:
        return generate_matrix(repo_root, status_path, args.crawl_max_age_days)
    return status_report(status_path, args.platform)


if __name__ == "__main__":
    sys.exit(main())
