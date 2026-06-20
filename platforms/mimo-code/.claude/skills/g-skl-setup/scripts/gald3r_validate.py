#!/usr/bin/env python3
"""Python port of gald3r_validate.ps1 (T1585).

Zero-dependency gald3r structure integrity check (T1012).
Exit 0 = PASS, Exit 1 = FAIL (violations listed).

Usage: python gald3r_validate.py [--fix] [--json] [--project-root <path>] [--report]
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, TextIO


# UTF-8-safe stdio on Windows consoles (the PS1 originals emit Unicode glyphs)
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _bootstrap_engine() -> bool:
    """Make ``gald3r.utils`` importable; fall back to the bundled engine source."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for parent in here.parents:
        engine_src = parent / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()
try:
    from gald3r.utils import console as _console
except ImportError:
    _console = None  # graceful stdlib fallback

_ANSI = {"green": "32", "yellow": "33", "red": "31"}
_ansi_ready = False

REQUIRED_FILES = ("TASKS.md", "PROJECT.md", "CONSTRAINTS.md", "BUGS.md",
                  "SUBSYSTEMS.md")
REQUIRED_FIELDS = ("id:", "title:", "status:", "type:")
TASK_SUBDIRS = ("open", "in-progress", "awaiting-verification", "completed")


def _supports_color(stream: TextIO) -> bool:
    if _console is not None:
        return bool(_console.color_enabled(stream))
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def _say(msg: str = "", color: Optional[str] = None) -> None:
    global _ansi_ready
    code = _ANSI.get((color or "").lower())
    if code and _supports_color(sys.stdout):
        if os.name == "nt" and not _ansi_ready:
            os.system("")
            _ansi_ready = True
        print(f"\x1b[{code}m{msg}\x1b[0m")
    else:
        print(msg)


def find_gald_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Auto-discover the project root (walk up max 8 levels)."""
    current = (start_path or Path.cwd()).resolve()
    for _ in range(8):
        if (current / ".gald3r").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Zero-dependency gald3r structure integrity check (T1012).")
    parser.add_argument("-Fix", "--fix", dest="fix", action="store_true",
                        help="Create missing directories where fixable")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit machine-readable JSON result")
    parser.add_argument("-Report", "--report", dest="report",
                        action="store_true",
                        help="Verbose report output including warnings")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default="", help="Project root (default: auto-discover)")
    args = parser.parse_args(argv)

    violations: List[str] = []
    warnings: List[str] = []

    if args.project_root == "":
        root = find_gald_root()
        if root is None:
            print("gald3r validate: FAIL - .gald3r/ not found in current dir "
                  "or any parent")
            return 1
        project_root = root
    else:
        project_root = Path(args.project_root)

    gald_dir = project_root / ".gald3r"
    tasks_dir = gald_dir / "tasks"

    # -- CHECK 1: .gald3r/ exists ---------------------------------------------
    if not gald_dir.exists():
        violations.append("MISSING: .gald3r/ directory")
        if args.fix:
            gald_dir.mkdir(parents=True, exist_ok=True)
            violations[-1] += " [FIXED: created]"

    # -- CHECK 2: Required root files -----------------------------------------
    for name in REQUIRED_FILES:
        if not (gald_dir / name).exists():
            violations.append(f"MISSING: .gald3r/{name}")

    # -- CHECK 3: tasks/ directory --------------------------------------------
    if not tasks_dir.exists():
        violations.append("MISSING: .gald3r/tasks/ directory")
        if args.fix:
            for sub in TASK_SUBDIRS:
                (tasks_dir / sub).mkdir(parents=True, exist_ok=True)
            violations[-1] += " [FIXED: created with subdirs]"

    # -- CHECK 4: Task file YAML frontmatter -----------------------------------
    if tasks_dir.exists():
        for task_file in sorted(tasks_dir.rglob("*.md")):
            content = _read_text(task_file)
            for field in REQUIRED_FIELDS:
                if not content.startswith(field) and f"\n{field}" not in content:
                    violations.append(
                        f"MISSING_FIELD: {task_file.name} missing '{field}'")

    # -- CHECK 5: Phantom detection (TASKS.md refs non-existent task files) ----
    tasks_index_path = gald_dir / "TASKS.md"
    if tasks_index_path.exists():
        tasks_index = _read_text(tasks_index_path)
        for ref in re.findall(r"tasks/[^)]+\.md", tasks_index):
            if not (gald_dir / ref).exists():
                violations.append(
                    f"PHANTOM: TASKS.md references missing file: {ref}")

    # -- CHECK 6: Orphan detection (task files not in TASKS.md) ----------------
    if tasks_dir.exists() and tasks_index_path.exists():
        tasks_index = _read_text(tasks_index_path)
        for task_file in sorted(tasks_dir.rglob("task*.md")):
            rel_path = task_file.relative_to(gald_dir).as_posix()
            if not re.search(re.escape(task_file.stem), tasks_index):
                warnings.append(f"ORPHAN: {rel_path} not referenced in TASKS.md")

    # -- CHECK 7: Subsystem spec files have locations: --------------------------
    subsystems_dir = gald_dir / "subsystems"
    if subsystems_dir.exists():
        for spec in sorted(subsystems_dir.glob("*.md")):
            if "locations:" not in _read_text(spec):
                warnings.append(
                    f"INCOMPLETE: subsystems/{spec.name} missing 'locations:' "
                    "in frontmatter")

    # -- REPORT ----------------------------------------------------------------
    total_violations = len(violations)
    total_warnings = len(warnings)

    if args.json:
        print(json.dumps({
            "pass": total_violations == 0,
            "violations": violations,
            "warnings": warnings,
            "project_root": str(project_root),
        }, indent=2))
    elif args.report:
        if total_violations == 0 and total_warnings == 0:
            _say("gald3r validate: PASS", "green")
            _say(f"  Project root: {project_root}")
            _say("  All structural checks passed.")
        else:
            if total_violations > 0:
                _say(f"gald3r validate: FAIL ({total_violations} violations, "
                     f"{total_warnings} warnings)", "red")
            else:
                _say(f"gald3r validate: PASS with warnings "
                     f"({total_warnings} warnings)", "yellow")
            _say(f"  Project root: {project_root}")
            for violation in violations:
                _say(f"  ❌ {violation}", "red")
            for warning in warnings:
                _say(f"  ⚠️  {warning}", "yellow")
    else:
        # Default: simple output
        if total_violations == 0:
            _say("gald3r validate: PASS")
        else:
            _say(f"gald3r validate: FAIL ({total_violations} violations)")
            for violation in violations:
                _say(f"  {violation}")

    return 1 if total_violations > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
