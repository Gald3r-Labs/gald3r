#!/usr/bin/env python3
"""Python port of gald3r_system_test.ps1 (T1585).

gald3r systems functional test harness (T1540). Exercises each major gald3r
system independently and emits a per-system PASS / PARTIAL / FAIL result plus
an overall functionality percentage: "gald3r is N% functional on this install".

Tests are NON-DESTRUCTIVE: read-only structural/presence checks where
possible; any write (Task / Bug create-read-update) happens in a throwaway
temp dir and NEVER touches the real .gald3r/ tree. The check implementations
live in the sibling module ``gald3r_system_checks.py`` (decomposed per the
T1585 size guidance).

DRY reuse: the Platform Parity and PLATFORM_SPEC checks shell out to the
existing custom_scripts/platform_parity_sync script (preferring a .py sibling
when present) rather than re-implementing parity logic.

Exit codes: 0 OK, 1 -FailBelow gate tripped, 2 invalid -Systems selection.
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def _bootstrap_engine_utils() -> bool:
    """Make gald3r.utils importable: installed package, else walk up to .gald3r_sys/engine/src."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        cand = parent / ".gald3r_sys" / "engine" / "src"
        if (cand / "gald3r" / "utils" / "__init__.py").is_file():
            sys.path.insert(0, str(cand))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_UTILS = _bootstrap_engine_utils()

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from gald3r_system_checks import (  # noqa: E402  (sibling import after bootstrap)
    CHECK_REGISTRY,
    CheckContext,
    find_powershell,
)


def _color_enabled() -> bool:
    if _HAS_UTILS:
        from gald3r.utils import console
        return console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36",
         "gray": "90", "darkyellow": "33"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


def read_identity(dot_gald3r: Path) -> Dict[str, str]:
    """Read project_name + gald3r_version from .gald3r/.identity (best effort)."""
    info = {"project_name": "unknown", "gald3r_version": "unknown"}
    identity_path = dot_gald3r / ".identity"
    if identity_path.is_file():
        try:
            for line in identity_path.read_text(encoding="utf-8",
                                                errors="replace").splitlines():
                m = re.match(r"^\s*project_name\s*=\s*(.+?)\s*$", line)
                if m:
                    info["project_name"] = m.group(1)
                m = re.match(r"^\s*gald3r_version\s*=\s*(.+?)\s*$", line)
                if m:
                    info["gald3r_version"] = m.group(1)
        except OSError:
            pass
    return info


def get_system_status(r: Dict[str, Any]) -> str:
    """PASS / PARTIAL / FAIL / SKIP from pass/fail counters."""
    denom = r["passed"] + r["failed"]
    if denom == 0:
        return "SKIP"
    if r["failed"] == 0:
        return "PASS"
    if r["passed"] == 0:
        return "FAIL"
    return "PARTIAL"


def get_system_score(r: Dict[str, Any]) -> Optional[int]:
    """0-100 score, or None for skipped (excluded from the average)."""
    denom = r["passed"] + r["failed"]
    if denom == 0:
        return None
    return int(round((r["passed"] / denom) * 100, 0))


def get_status_glyph(status: str) -> str:
    return {"PASS": "[PASS]", "PARTIAL": "[PARTIAL]",
            "FAIL": "[FAIL]", "SKIP": "[SKIP]"}.get(status, "[?]")


def write_report(report_path: Path, scored: List[Dict[str, Any]],
                 overall: int, systems_passing: int, systems_tested: int,
                 project_name: str, gald3r_version: str, now_utc: datetime) -> None:
    """Write the markdown report (UTF-8 without BOM, like the PS1)."""
    lines: List[str] = []
    lines.append("# gald3r System Test Report")
    lines.append("Generated: {0} UTC".format(now_utc.strftime("%Y-%m-%d %H:%M")))
    lines.append(f"Project: {project_name}")
    lines.append(f"gald3r version: {gald3r_version}")
    lines.append("")
    lines.append("## Overall Score: {0}% functional ({1}/{2} systems passing)".format(
        overall, systems_passing, systems_tested))
    lines.append("")
    lines.append("| System | Score | Status | Notes |")
    lines.append("|--------|-------|--------|-------|")
    for s in scored:
        score_text = f"{s['score']}%" if s["score"] is not None else "-"
        detail = "{0}/{1} tests".format(s["passed"], s["passed"] + s["failed"])
        if s["status"] == "SKIP":
            detail = "skipped"
        if s["notes"]:
            detail = f"{detail}; {s['notes']}"
        lines.append("| {0} | {1} | {2} {3} | {4} |".format(
            s["name"], score_text, get_status_glyph(s["status"]), s["status"], detail))
    lines.append("")
    any_fail = [s for s in scored if s["failures"]]
    lines.append("## Failed Tests")
    if any_fail:
        for s in any_fail:
            lines.append(f"### {s['name']}")
            for f in s["failures"]:
                lines.append(f"- {f}")
            lines.append("")
    else:
        lines.append("None. All tested systems passed.")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_human_summary(scored: List[Dict[str, Any]], overall: int,
                        systems_passing: int, systems_tested: int,
                        project_name: str, gald3r_version: str,
                        report_path: Optional[Path]) -> None:
    """The human-readable console table (mirrors the PS1 output shape)."""
    print("")
    cprint("==================================================================", "cyan")
    cprint("  gald3r System Test Harness (T1540)", "cyan")
    cprint(f"  Project: {project_name}   gald3r version: {gald3r_version}", "gray")
    cprint("==================================================================", "cyan")
    fmt = "  {0:<20} {1:>6}  {2:<9} {3}"
    cprint(fmt.format("System", "Score", "Status", "Notes"), "gray")
    cprint("  " + "-" * 62, "gray")
    for s in scored:
        score_text = f"{s['score']}%" if s["score"] is not None else "-"
        color = {"PASS": "green", "PARTIAL": "yellow", "FAIL": "red"}.get(
            s["status"], "gray")
        cprint(fmt.format(s["name"], score_text, s["status"], s["notes"]), color)
    cprint("  " + "-" * 62, "gray")
    ov_color = "green" if overall >= 90 else ("yellow" if overall >= 70 else "red")
    cprint("  OVERALL: {0}% functional  ({1}/{2} systems passing)".format(
        overall, systems_passing, systems_tested), ov_color)
    if report_path:
        cprint(f"  Report: {report_path}", "gray")
    any_fail = [s for s in scored if s["failures"]]
    if any_fail:
        print("")
        cprint("  Failed Tests:", "red")
        for s in any_fail:
            cprint(f"    {s['name']}:", "yellow")
            for f in s["failures"]:
                cprint(f"      - {f}", "darkyellow")
    print("")


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="gald3r systems functional test harness (T1540)."
    )
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", default="",
                   help="The gald3r install root to test (default: parent of the "
                        "directory containing this script).")
    p.add_argument("-FailBelow", "--fail-below", dest="fail_below", type=int, default=0,
                   help="CI gate: exit non-zero when overall score is below this "
                        "percentage (0-100). Default 0 (never gate on score).")
    p.add_argument("-Json", "--json", dest="json", action="store_true",
                   help="Emit a machine-readable JSON summary instead of the table.")
    p.add_argument("-NoReport", "--no-report", dest="no_report", action="store_true",
                   help="Do not write the markdown report file.")
    p.add_argument("-Systems", "--systems", dest="systems", default="",
                   help="Comma-separated subset of system keys to run. Keys: "
                        + ",".join(CHECK_REGISTRY.keys()))
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: run selected checks -> score -> report -> output -> gate."""
    args = build_parser().parse_args(argv)
    if not (0 <= args.fail_below <= 100):
        print("ERROR: -FailBelow must be in 0..100", file=sys.stderr)
        return 2

    # Resolve roots (PS1: script dir -> repo root is one level up).
    if args.project_root.strip():
        repo_root = Path(args.project_root).resolve()
    else:
        repo_root = _SCRIPT_DIR.parent.resolve()
    ctx = CheckContext(repo_root=repo_root, ps_host=find_powershell())

    identity = read_identity(ctx.dot_gald3r)
    project_name = identity["project_name"]
    gald3r_version = identity["gald3r_version"]

    # Subset selection
    selected_keys = list(CHECK_REGISTRY.keys())
    if args.systems.strip():
        want = [s.strip().lower() for s in args.systems.split(",") if s.strip()]
        selected_keys = [k for k in CHECK_REGISTRY if k in want]
        if not selected_keys:
            cprint("ERROR: -Systems matched no known keys. Valid: "
                   + ", ".join(CHECK_REGISTRY.keys()), "red")
            return 2

    # Run
    results = [CHECK_REGISTRY[key](ctx) for key in selected_keys]

    # Score each system + overall
    scored: List[Dict[str, Any]] = []
    for r in results:
        scored.append({
            "name": r["name"],
            "key": r["key"],
            "status": get_system_status(r),
            "score": get_system_score(r),
            "passed": r["passed"],
            "failed": r["failed"],
            "skipped": r["skipped"],
            "failures": list(r["failures"]),
            "notes": r["notes"],
        })

    active_scores = [s["score"] for s in scored if s["score"] is not None]
    overall = int(round(sum(active_scores) / len(active_scores), 0)) if active_scores else 0
    systems_passing = sum(1 for s in scored if s["status"] == "PASS")
    systems_tested = sum(1 for s in scored if s["status"] != "SKIP")

    # Write markdown report to .gald3r/reports/
    now_utc = datetime.now(timezone.utc)
    stamp = now_utc.strftime("%Y%m%d_%H%M%S")
    report_path: Optional[Path] = None
    reports_dir = ctx.dot_gald3r / "reports"
    if not args.no_report and ctx.dot_gald3r.is_dir():
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"system_test_{stamp}.md"
        write_report(report_path, scored, overall, systems_passing, systems_tested,
                     project_name, gald3r_version, now_utc)

    # Output
    if args.json:
        print(json.dumps({
            "suite": "gald3r system test harness",
            "project": project_name,
            "gald3r_version": gald3r_version,
            "overall_score": overall,
            "systems_passing": systems_passing,
            "systems_tested": systems_tested,
            "report": str(report_path) if report_path else None,
            "timestamp": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "systems": scored,
        }, indent=2))
    else:
        print_human_summary(scored, overall, systems_passing, systems_tested,
                            project_name, gald3r_version, report_path)

    # CI gate
    if args.fail_below > 0 and overall < args.fail_below:
        if not args.json:
            cprint("FAIL GATE: overall score {0}% is below -FailBelow {1}%".format(
                overall, args.fail_below), "red")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
