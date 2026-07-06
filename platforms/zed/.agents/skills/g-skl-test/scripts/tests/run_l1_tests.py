#!/usr/bin/env python3
"""Python port of run_l1_tests.ps1 (T1585).

gald3r_templates framework test-harness runner (T1532). Discovers framework
tests from ``tests_manifest.psd1`` (the test-plan manifest), filters them by
verification level, runs each via its declared runner (PowerShell or Python),
and reports a pass/fail summary with a proper process exit code (0 = all
green, non-zero = one or more failures or harness errors).

By default runs the **L1** plan (fast / daily). Use -Level L2 / L3 / All for
the broader plans. Test selection is manifest-backed: a test belongs to a
level when its ``Level`` field matches OR the requested level appears in its
optional ``AlsoLevels`` list.

Runner resolution: for 'pwsh' entries a sibling .py port is preferred when it
exists next to the resolved test path; otherwise the .ps1 is dispatched via
pwsh/powershell -NoProfile -ExecutionPolicy Bypass -File.
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
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


def _color_enabled() -> bool:
    if _HAS_UTILS:
        from gald3r.utils import console
        return console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "gray": "90"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


SCRIPT_DIR = Path(__file__).resolve().parent


def find_repo_root() -> Path:
    """Search upward from the harness for the .gald3r marker (depth-robust)."""
    d = SCRIPT_DIR
    while not (d / ".gald3r").exists():
        if d.parent == d:
            break
        d = d.parent
    return d


def _strip_psd1_comments(text: str) -> str:
    """Remove # comments (line-based; the manifest has no '#' inside strings
    other than in comments, and quoted '#' is preserved by the quote scan)."""
    out_lines = []
    for line in text.splitlines():
        in_sq = False
        cut = None
        for i, ch in enumerate(line):
            if ch == "'":
                in_sq = not in_sq
            elif ch == "#" and not in_sq:
                cut = i
                break
        out_lines.append(line if cut is None else line[:cut])
    return "\n".join(out_lines)


def parse_tests_manifest(path: Path) -> List[Dict[str, Any]]:
    """Parse tests_manifest.psd1 (Import-PowerShellDataFile equivalent for the
    known structure: Tests = @( @{ Name=..; Level=..; Runner=..; Path=..;
    Desc=..; AlsoLevels=@(..) }, ... ))."""
    text = _strip_psd1_comments(path.read_text(encoding="utf-8-sig", errors="replace"))
    tests: List[Dict[str, Any]] = []
    # Inner hashtables contain no nested braces; the outer file hashtable does,
    # so [^{}]* matches exactly the per-test blocks.
    for block_m in re.finditer(r"@\{([^{}]*)\}", text, flags=re.DOTALL):
        block = block_m.group(1)
        entry: Dict[str, Any] = {}
        for kv in re.finditer(r"(\w+)\s*=\s*'([^']*)'", block):
            entry[kv.group(1)] = kv.group(2)
        also = re.search(r"AlsoLevels\s*=\s*@\(([^)]*)\)", block)
        if also:
            entry["AlsoLevels"] = re.findall(r"'([^']*)'", also.group(1))
        if "Name" in entry and "Path" in entry:
            tests.append(entry)
    return tests


def matches_level(test: Dict[str, Any], want: str) -> bool:
    """Manifest level filter: Level match, AlsoLevels match, or All."""
    if want == "All":
        return True
    if test.get("Level") == want:
        return True
    if want in test.get("AlsoLevels", []):
        return True
    return False


def find_powershell() -> Optional[str]:
    """Locate a PowerShell host (prefer pwsh, fall back to Windows PowerShell)."""
    for cand in ("pwsh", "powershell"):
        exe = shutil.which(cand)
        if exe:
            return exe
    return None


def resolve_test_path(repo_root: Path, manifest_path_field: str) -> Path:
    """Tests live beside this harness; resolve by leaf there, else repo-root-relative."""
    leaf = Path(manifest_path_field.replace("\\", "/")).name
    local_path = SCRIPT_DIR / leaf
    if local_path.exists():
        return local_path
    return repo_root / manifest_path_field.replace("/", os.sep)


def run_one(test: Dict[str, Any], repo_root: Path,
            ps_host: Optional[str]) -> Dict[str, Any]:
    """Dispatch one manifest entry; returns the result row."""
    name = test.get("Name", "?")
    runner = test.get("Runner", "?")
    level = test.get("Level", "?")
    test_path = resolve_test_path(repo_root, test["Path"])

    row: Dict[str, Any] = {"name": name, "level": level, "runner": runner,
                           "status": "fail", "exit": None, "note": ""}

    if not test_path.exists():
        row["status"] = "error"
        row["note"] = f"test file not found: {test['Path']}"
        return row

    try:
        if runner == "pwsh":
            py_sibling = test_path.with_suffix(".py")
            if py_sibling.exists():
                proc = subprocess.run([sys.executable, str(py_sibling)])
            elif ps_host:
                proc = subprocess.run([ps_host, "-NoProfile", "-ExecutionPolicy",
                                       "Bypass", "-File", str(test_path)])
            else:
                row["status"] = "error"
                row["note"] = "no PowerShell host on PATH and no .py sibling"
                return row
            exit_code = proc.returncode
        elif runner == "python":
            proc = subprocess.run([sys.executable, str(test_path)])
            exit_code = proc.returncode
        else:
            row["status"] = "error"
            row["note"] = f"unknown runner '{runner}'"
            return row
    except OSError as exc:
        row["status"] = "error"
        row["note"] = str(exc)
        return row

    row["exit"] = exit_code
    row["status"] = "pass" if exit_code == 0 else "fail"
    return row


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="gald3r_templates framework test-harness runner (T1532)."
    )
    p.add_argument("-Level", "--level", dest="level", default="L1",
                   choices=("L1", "L2", "L3", "All"))
    p.add_argument("-Json", "--json", dest="json", action="store_true")
    p.add_argument("-ListOnly", "--list-only", dest="list_only", action="store_true")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: discover -> filter -> dispatch -> summarize."""
    args = build_parser().parse_args(argv)

    repo_root = find_repo_root()
    manifest_path = SCRIPT_DIR / "tests_manifest.psd1"

    if not manifest_path.is_file():
        cprint(f"[HARNESS ERROR] test manifest not found: {manifest_path}", "red")
        return 2

    all_tests = parse_tests_manifest(manifest_path)
    selected = [t for t in all_tests if matches_level(t, args.level)]

    if args.list_only:
        cprint(f"Test plan '{args.level}' ({len(selected)} test(s)):", "cyan")
        for t in selected:
            cprint(f"  [{t.get('Level')}] {t.get('Name')} ({t.get('Runner')}) "
                   f"-> {t.get('Path')}", "gray")
        return 0

    ps_host = find_powershell()
    run_results = [run_one(t, repo_root, ps_host) for t in selected]

    total = len(run_results)
    passed = sum(1 for r in run_results if r["status"] == "pass")
    failed = sum(1 for r in run_results if r["status"] != "pass")

    if args.json:
        print(json.dumps({
            "suite": "gald3r_templates framework harness",
            "level": args.level,
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": run_results,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        }, indent=2))
    else:
        print("")
        cprint("================================================", "cyan")
        cprint(f"  gald3r_templates harness - plan {args.level:<4}          ", "cyan")
        cprint("================================================", "cyan")
        for r in run_results:
            icon = {"pass": "PASS", "fail": "FAIL"}.get(r["status"], "ERR ")
            color = {"pass": "green", "fail": "red"}.get(r["status"], "yellow")
            line = f"  [{icon}] {r['name']} ({r['level']}/{r['runner']})"
            if r["note"]:
                line += f"  -- {r['note']}"
            cprint(line, color)
        print("")
        cprint(f"Summary: {passed}/{total} test suites passed, {failed} failed "
               f"(plan {args.level})", "green" if failed == 0 else "red")
        print("")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
