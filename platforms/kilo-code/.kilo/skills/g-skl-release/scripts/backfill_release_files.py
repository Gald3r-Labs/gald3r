#!/usr/bin/env python3
"""Python port of backfill_release_files.ps1 (T1585).

gald3r Release File Backfill (BUG-104 / C-023).

Scans a project's CHANGELOG.md for versioned headers (## [X.Y.Z]) and creates
a matching release file under .gald3r/releases/ for any version that does not
already have one. This silences the session-start C-023 warning:
    "N CHANGELOG version(s) missing release file - run @g-release-sync"

Backfilled release files are named release{NNN}_v{X}-{Y}-{Z}.md so they
satisfy both the canonical release{NNN}_{slug}.md naming and the g-rl-25
Step 2b "filename contains the version" check. They are written with
status: released and the date parsed from the CHANGELOG header (when present).

Invoked by @g-update on the upgrade path and by @g-release-sync /
g-medic --heal-c023.

Task: T1438  Bug: BUG-104. Ships in g-skl-release skill (full + adv tiers).
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, TextIO


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

_ANSI = {"cyan": "36", "green": "32", "yellow": "33", "red": "31",
         "gray": "37", "darkgray": "90"}
_ansi_ready = False


def _supports_color(stream: TextIO) -> bool:
    if _console is not None:
        return bool(_console.color_enabled(stream))
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def _release_body(next_id: int, version: str, rel_date: str) -> str:
    return (
        f"---\n"
        f"id: {next_id}\n"
        f"name: 'v{version}'\n"
        f"version: '{version}'\n"
        f"target_date: '{rel_date}'\n"
        f"status: released\n"
        f"cadence_days: 14\n"
        f"features: []\n"
        f"tasks: []\n"
        f"notes: 'Backfilled from CHANGELOG by backfill_release_files.ps1 "
        f"(BUG-104 / C-023).'\n"
        f"created_date: '{rel_date}'\n"
        f"released_date: '{rel_date}'\n"
        f"---\n"
        f"# Release {next_id}: v{version}\n"
        f"\n"
        f"## Release Notes\n"
        f"\n"
        f"See CHANGELOG.md section [{version}] for the full notes.\n"
        f"\n"
        f"## Blockers\n"
        f"\n"
        f"- None (backfilled record).\n"
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r Release File Backfill (BUG-104 / C-023). Creates "
                    "missing .gald3r/releases/ files from CHANGELOG headers.")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=os.getcwd(),
                        help="Root directory of the target project "
                             "(default: cwd)")
    parser.add_argument("-Apply", "--apply", dest="apply",
                        action="store_true",
                        help="Actually write files (default: dry-run)")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit a JSON result object")
    args = parser.parse_args(argv)
    as_json = args.json

    global _ansi_ready

    def status(msg: str = "", color: str = "cyan") -> None:
        global _ansi_ready
        if as_json:
            return
        code = _ANSI.get(color.lower())
        if code and _supports_color(sys.stdout):
            if os.name == "nt" and not _ansi_ready:
                os.system("")
                _ansi_ready = True
            print(f"\x1b[{code}m{msg}\x1b[0m")
        else:
            print(msg)

    project_root = Path(args.project_root)
    changelog_path = project_root / "CHANGELOG.md"
    releases_dir = project_root / ".gald3r" / "releases"

    if not changelog_path.exists():
        if as_json:
            print(json.dumps({
                "success": False,
                "error": f"CHANGELOG.md not found at {changelog_path}",
            }))
        else:
            status(f"ERROR: CHANGELOG.md not found at {changelog_path}", "red")
        return 1

    # Parse CHANGELOG versions: version + optional date from
    # "## [X.Y.Z] - YYYY-MM-DD"
    versions: List[Dict[str, str]] = []
    for line in changelog_path.read_text(
            encoding="utf-8-sig", errors="replace").splitlines():
        m = re.match(r"^##\s*\[(\d+\.\d+\.\d+)\]\s*-?\s*(\d{4}-\d{2}-\d{2})?",
                     line)
        if m:
            versions.append({
                "version": m.group(1),
                "date": m.group(2) or date.today().strftime("%Y-%m-%d"),
            })

    if not versions:
        status("No versioned CHANGELOG headers found - nothing to backfill.",
               "darkgray")
        if as_json:
            print(json.dumps({"success": True, "created": [], "skipped": [],
                              "dry_run": not args.apply}))
        return 0

    # Collect existing release-file versions (frontmatter version: + filenames)
    existing_versions: List[str] = []
    existing_max_id = 0
    if releases_dir.is_dir():
        for rel_file in sorted(releases_dir.glob("release*.md")):
            if not rel_file.is_file():
                continue
            try:
                raw = rel_file.read_text(encoding="utf-8-sig",
                                         errors="replace")
            except OSError:
                raw = ""
            m = re.search(r"(?m)^\s*version:\s*'?\"?(\d+\.\d+\.\d+)", raw)
            if m:
                existing_versions.append(m.group(1))
            m = re.match(r"^release(\d+)_", rel_file.name)
            if m:
                id_num = int(m.group(1))
                if id_num > existing_max_id:
                    existing_max_id = id_num

    created: List[str] = []
    skipped: List[str] = []
    next_id = existing_max_id

    if not releases_dir.is_dir() and args.apply:
        releases_dir.mkdir(parents=True, exist_ok=True)

    status("")
    status("gald3r Release File Backfill (C-023)", "cyan")
    status("-" * 50, "darkgray")
    status(f"  Project root : {project_root}")
    status(f"  Mode         : {'APPLY' if args.apply else 'DRY-RUN'}",
           "yellow" if args.apply else "darkgray")
    status("")

    for v in versions:
        if v["version"] in existing_versions:
            skipped.append(v["version"])
            status(f"  skip: [{v['version']}] already has a release file",
                   "darkgray")
            continue

        next_id += 1
        id_str = f"{next_id:03d}"
        ver_slug = "v" + v["version"].replace(".", "-")
        file_name = f"release{id_str}_{ver_slug}.md"
        file_path = releases_dir / file_name

        if args.apply:
            file_path.write_text(_release_body(next_id, v["version"],
                                               v["date"]),
                                 encoding="utf-8", newline="\n")
            status(f"  created: {file_name}  ([{v['version']}] released "
                   f"{v['date']})", "green")
        else:
            status(f"  would create: {file_name}  ([{v['version']}] released "
                   f"{v['date']})", "gray")
        created.append(v["version"])

    status("")
    status(f"Backfill summary: {len(created)} created, {len(skipped)} "
           "already present.", "cyan")
    if not args.apply and created:
        status("DRY-RUN: no files written. Re-run with -Apply to create them.",
               "darkgray")

    if as_json:
        print(json.dumps({
            "success": True,
            "dry_run": not args.apply,
            "created": created,
            "skipped": skipped,
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
