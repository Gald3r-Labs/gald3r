#!/usr/bin/env python3
"""Python port of release.ps1 (T1585).

Orchestrate a gald3r slim template release - version injection, parity gate,
export, and handoff.

Drives the full release pipeline from <gald3r_source> to the public gald3r
repo:
  1. Run platform parity check (unless -Force or -SkipParityCheck)
  2. Inject version string into all version locations in
     <ECOSYSTEM_ROOT>/<template_full>
  3. Validate CHANGELOG.md contains a heading for the target version
  4. Run export_slim_template_repo to mirror <ECOSYSTEM_ROOT>/<template_full>
     to -Destination
  5. Print the suggested git commit, tag, and push commands

Default is DRY-RUN. Use -Apply to write files. This script does NOT commit
or push - review the diff in -Destination before committing.
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO


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


def _say(msg: str = "", color: Optional[str] = None,
         stream: Optional[TextIO] = None) -> None:
    global _ansi_ready
    stream = stream or sys.stdout
    code = _ANSI.get((color or "").lower())
    if code and _supports_color(stream):
        if os.name == "nt" and not _ansi_ready:
            os.system("")
            _ansi_ready = True
        print(f"\x1b[{code}m{msg}\x1b[0m", file=stream)
    else:
        print(msg, file=stream)


def _warn(msg: str) -> None:
    _say(f"WARNING: {msg}", "yellow", sys.stderr)


def _resolve_script_cmd(base_no_suffix: Path) -> Optional[List[str]]:
    """Cross-skill script resolver: prefer a .py sibling at runtime, else
    run the .ps1 via pwsh/powershell."""
    py = base_no_suffix.with_suffix(".py")
    if py.is_file():
        return [sys.executable, str(py)]
    ps1 = base_no_suffix.with_suffix(".ps1")
    if ps1.is_file():
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell:
            return [shell, "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(ps1)]
    return None


def _script_exists(base_no_suffix: Path) -> bool:
    return (base_no_suffix.with_suffix(".py").is_file()
            or base_no_suffix.with_suffix(".ps1").is_file())


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Orchestrate a gald3r slim template release - version "
                    "injection, parity gate, export, and handoff.")
    parser.add_argument("-Version", "--version-string", dest="version",
                        required=True,
                        help='Version string (e.g. "1.1.0" - no "v" prefix)')
    parser.add_argument("-Destination", "--destination", dest="destination",
                        required=True,
                        help="Target directory (local clone of the public "
                             "gald3r repo)")
    parser.add_argument("-Apply", "--apply", dest="apply",
                        action="store_true",
                        help="Actually write files (default: dry-run)")
    parser.add_argument("-Force", "--force", dest="force",
                        action="store_true",
                        help="Skip the parity gate (warns but proceeds)")
    parser.add_argument("-SkipParityCheck", "--skip-parity-check",
                        dest="skip_parity_check", action="store_true",
                        help="Do not invoke platform_parity_sync")
    args = parser.parse_args(argv)

    version = args.version
    destination = args.destination

    scripts_dir = Path(__file__).resolve().parent
    skill_root = scripts_dir.parent
    # Resolve <gald3r_source> repo root (walk up looking for custom_scripts)
    repo_root = skill_root
    for _ in range(6):
        if _script_exists(repo_root / "custom_scripts"
                          / "platform_parity_sync"):
            break
        parent = repo_root.parent
        if parent == repo_root:
            break
        repo_root = parent
    ecosystem_root = repo_root.parent
    template_src = ecosystem_root / "<template_full>"

    _say("")
    _say("gald3r release pipeline", "cyan")
    _say(f"  Version     : {version}", "cyan")
    _say(f"  Destination : {destination}", "cyan")
    _say(f"  Mode        : {'APPLY' if args.apply else 'DRY-RUN'}",
         "green" if args.apply else "yellow")
    _say("")

    # --- Step 1: Parity gate ---
    parity_base = repo_root / "custom_scripts" / "platform_parity_sync"
    if not args.skip_parity_check and not args.force:
        parity_cmd = _resolve_script_cmd(parity_base)
        if parity_cmd is None:
            _warn(f"Parity check script not found at {parity_base}.ps1 — "
                  "skipping (use -Force to suppress this warning)")
        else:
            _say("Step 1: Running platform parity check (report-only)...",
                 "cyan")
            proc = subprocess.run(parity_cmd)
            if proc.returncode != 0:
                _say("")
                _say("ERROR: Parity gaps detected. Fix with:\n"
                     "  .\\custom_scripts\\platform_parity_sync.ps1 -Sync\n"
                     "Then re-run, or use -Force to override.", "red",
                     sys.stderr)
                return 1
            _say("  Parity: CLEAN", "green")
    elif args.force:
        _warn("Step 1: -Force specified — parity gate skipped. Not "
              "recommended for release exports.")

    # --- Step 2: Version injection ---
    _say(f"Step 2: Version injection ({version})...", "cyan")

    version_targets: List[Dict[str, Any]] = [
        {
            "file": template_src / "README.md",
            "pattern": r"version-[\d.]+-green\.svg",
            "replace": f"version-{version}-green.svg",
            "desc": "README.md badge",
        },
        {
            "file": template_src / "AGENTS.md",
            "pattern": r"\*\*gald3r version\*\*: [\d.]+",
            "replace": f"**gald3r version**: {version}",
            "desc": "AGENTS.md",
        },
        {
            "file": template_src / "CLAUDE.md",
            "pattern": r"\*\*gald3r version\*\*: [\d.]+",
            "replace": f"**gald3r version**: {version}",
            "desc": "CLAUDE.md",
        },
        {
            "file": template_src / ".agent" / "agent_instructions.md",
            "pattern": r"\*\*gald3r Version\*\*: [\d.]+",
            "replace": f"**gald3r Version**: {version}",
            "desc": ".agent/agent_instructions.md",
        },
        {
            "file": template_src / ".gald3r" / ".identity",
            "pattern": r"gald3r_version=[\d.]+",
            "replace": f"gald3r_version={version}",
            "desc": ".gald3r/.identity",
        },
        {
            "file": template_src / "VERSION",
            "is_simple_overwrite": True,
            "replace": f"{version}\n",
            "desc": "VERSION",
        },
    ]

    version_errors: List[str] = []
    for target in version_targets:
        file_path: Path = target["file"]
        if not file_path.exists():
            _warn(f"  SKIP (not found): {target['desc']}")
            continue

        if target.get("is_simple_overwrite"):
            if args.apply:
                file_path.write_text(str(target["replace"]), encoding="utf-8",
                                     newline="")
            _say(f"  {'Updated' if args.apply else 'Would update'}: "
                 f"{target['desc']} -> {version}",
                 "green" if args.apply else "darkgray")
            continue

        content = file_path.read_text(encoding="utf-8-sig", errors="replace")
        if not re.search(str(target["pattern"]), content):
            _warn(f"  No match found in {target['desc']} — pattern may be "
                  f"stale: {target['pattern']}")
            version_errors.append(str(target["desc"]))
            continue
        new_content = re.sub(str(target["pattern"]), str(target["replace"]),
                             content)
        if args.apply and content != new_content:
            file_path.write_text(new_content, encoding="utf-8", newline="")
        already_current = content == new_content
        if args.apply and not already_current:
            _say(f"  Updated: {target['desc']}", "green")
        elif already_current:
            _say(f"  Already current: {target['desc']}", "darkgray")
        else:
            _say(f"  Would update: {target['desc']}", "darkgray")

    if version_errors:
        _warn(f"Version injection had {len(version_errors)} unmatched "
              f"location(s): {', '.join(version_errors)}")

    # --- Step 3: CHANGELOG validation ---
    _say("Step 3: Validating CHANGELOG.md heading...", "cyan")
    changelog_path = template_src / "CHANGELOG.md"
    if not changelog_path.exists():
        _say(f"ERROR: CHANGELOG.md not found at {changelog_path}", "red",
             sys.stderr)
        return 1
    changelog_content = changelog_path.read_text(encoding="utf-8-sig",
                                                 errors="replace")
    heading_pattern = r"## \[" + re.escape(version) + r"\]"
    if not re.search(heading_pattern, changelog_content):
        today = date.today().strftime("%Y-%m-%d")
        _say(f"ERROR: CHANGELOG.md does not contain a heading for version "
             f"[{version}].\nAdd the release entries under "
             f"'## [{version}] - {today}' before running this script.",
             "red", sys.stderr)
        return 1
    _say(f"  CHANGELOG.md: heading [[{version}]] found", "green")

    # --- Step 4: Export ---
    _say("Step 4: Running export_slim_template_repo...", "cyan")
    export_base = repo_root / "custom_scripts" / "export_slim_template_repo"
    export_cmd = _resolve_script_cmd(export_base)
    if export_cmd is None:
        _say(f"ERROR: Export script not found: {export_base}.ps1", "red",
             sys.stderr)
        return 1

    export_args = ["-Destination", destination, "-SkipParityCheck"]
    if args.apply:
        export_args.append("-Apply")
    if args.force:
        export_args.append("-Force")

    proc = subprocess.run(export_cmd + export_args)
    if proc.returncode >= 8:
        _say(f"ERROR: Export script failed with exit code {proc.returncode}",
             "red", sys.stderr)
        return 1

    # --- Step 5: Print git handoff commands ---
    dest_full = Path(destination).resolve()
    _say("")
    _say("Release pipeline complete.", "green")
    if not args.apply:
        _say("(Dry-run — no files written. Re-run with -Apply to execute.)",
             "yellow")
        return 0

    _say("")
    _say(f"Next steps — run these in {dest_full} :", "cyan")
    _say("")
    _say(f'  cd "{dest_full}"')
    _say("  git add .")
    _say("  git status   # Review what changed")
    _say("  git diff --stat HEAD")
    _say("")
    _say(f'  git commit -m "release: v{version}"')
    _say(f'  git tag -a "v{version}" -m "gald3r v{version}"')
    _say("  git push origin main --tags")
    _say("")
    _say("After push, GitHub Actions will automatically create a GitHub "
         "Release with:", "darkgray")
    _say(f"  - Release notes extracted from CHANGELOG.md [[{version}]] "
         "section", "darkgray")
    _say(f"  - gald3r-template-v{version}.zip download archive", "darkgray")
    _say("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
