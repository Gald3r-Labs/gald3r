#!/usr/bin/env python3
"""Python port of gald3r_semver.ps1 (T1585).

gald3r Semantic Versioning Engine - core release management for gald3r
projects. Called by @g-ship and gald3r_release.py.

Handles version parsing, CHANGELOG promotion, VERSION file updates,
git tagging, and optional GitHub release hints.

Semver definitions:
  MAJOR (X.0.0) - Breaking changes, complete reframe, new architecture
  MINOR (0.X.0) - New features, additive, nothing breaks
  PATCH (0.0.X) - Bug fixes, small extensions, doc updates

Task: T1210 - part of the g-ship release management system.
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
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

_ANSI = {"cyan": "36", "green": "32", "yellow": "33", "red": "31",
         "gray": "37", "darkgray": "90", "white": "97"}
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


def _read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8-sig", errors="replace").splitlines()


def _git(project_root: Path, *git_args: str) -> int:
    """Run git quietly (parity with the PS1's 2>$null / Out-Null suppression)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(project_root), *git_args],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        return proc.returncode
    except (OSError, FileNotFoundError):
        return 1


# -- Version parsing ----------------------------------------------------------

def get_current_version(version_path: Path, changelog_path: Path) -> str:
    """VERSION file first, then latest CHANGELOG header, else 0.0.0."""
    if version_path.exists():
        v = version_path.read_text(encoding="utf-8-sig").strip()
        if re.match(r"^\d+\.\d+\.\d+$", v):
            return v
    for line in _read_lines(changelog_path):
        m = re.match(r"^## \[(\d+\.\d+\.\d+)\]", line)
        if m:
            return m.group(1)
    return "0.0.0"


def bump_version(current: str, bump_type: str) -> str:
    major, minor, patch = (int(p) for p in current.split("."))
    if bump_type == "major":
        major, minor, patch = major + 1, 0, 0
    elif bump_type == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


# -- [Unreleased] section -----------------------------------------------------

def get_unreleased_content(changelog_path: Path) -> List[str]:
    in_section = False
    content: List[str] = []
    for line in _read_lines(changelog_path):
        if re.match(r"^## \[Unreleased\]", line):
            in_section = True
            continue
        if in_section and re.match(r"^## \[", line):
            break
        if in_section:
            content.append(line)
    # Parity with the PS1 trim quirk: keep non-empty lines; keep empty lines
    # only when the FIRST empty line in the section is not at index 0.
    first_empty = content.index("") if "" in content else -1
    return [line for line in content if line != "" or first_empty > 0]


def unreleased_has_content(changelog_path: Path) -> bool:
    content = get_unreleased_content(changelog_path)
    meaningful = [line for line in content
                  if re.search(r"\S", line) and not line.startswith("###")]
    return len(meaningful) > 0


# -- Promote CHANGELOG --------------------------------------------------------

def promote_changelog(changelog_path: Path, new_version: str, theme: str,
                      rel_date: str) -> List[str]:
    lines = _read_lines(changelog_path)
    result: List[str] = []
    promoted = False
    in_unreleased = False

    header = (f"## [{new_version}] - {rel_date} ({theme})" if theme
              else f"## [{new_version}] - {rel_date}")

    for line in lines:
        if re.match(r"^## \[Unreleased\]", line) and not promoted:
            # Write new empty [Unreleased] + separator
            result.extend(["## [Unreleased]", "", "### Added", "### Changed",
                           "### Fixed", "### Removed", "", "---", ""])
            # Write new version header in place of [Unreleased]
            result.append(header)
            in_unreleased = True
            promoted = True
            continue
        if in_unreleased and re.match(r"^## \[", line):
            in_unreleased = False
        result.append(line)
    return result


# -- Release notes extraction --------------------------------------------------

def get_release_notes(changelog_path: Path, version: str) -> str:
    in_section = False
    notes: List[str] = []
    for line in _read_lines(changelog_path):
        if re.match(r"^## \[" + re.escape(version) + r"\]", line):
            in_section = True
            continue
        if in_section and re.match(r"^## \[", line):
            break
        if in_section:
            notes.append(line)
    return "\n".join(notes).strip()


# -- README badge ---------------------------------------------------------------

def update_readme_badge(readme_path: Path, old_version: str,
                        new_version: str) -> bool:
    if not readme_path.exists():
        return False
    content = readme_path.read_text(encoding="utf-8-sig", errors="replace")
    old_major_minor = ".".join(old_version.split(".")[:2])
    new_major_minor = ".".join(new_version.split(".")[:2])
    pattern = "version-" + re.escape(old_major_minor) + "-"
    if re.search(pattern, content):
        updated = re.sub(pattern, f"version-{new_major_minor}-", content)
        readme_path.write_text(updated, encoding="utf-8", newline="")
        return True
    return False


# -- Main -----------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    as_json = args.json

    def status(msg: str = "", color: str = "cyan") -> None:
        if not as_json:
            _say(msg, color)

    def fail(msg: str) -> int:
        if as_json:
            print(json.dumps({"success": False, "error": msg}))
        else:
            _say(f"ERROR: {msg}", "red")
        return 1

    project_root = Path(args.project_root)
    changelog_path = project_root / "CHANGELOG.md"
    version_path = project_root / "VERSION"
    readme_path = project_root / "README.md"

    if not changelog_path.exists():
        return fail(f"CHANGELOG.md not found at {changelog_path}")
    if not args.bump_type:
        return fail("BumpType is required: major, minor, or patch")

    current_version = get_current_version(version_path, changelog_path)
    new_version = bump_version(current_version, args.bump_type)
    today = date.today().strftime("%Y-%m-%d")
    tag_name = f"v{new_version}"
    theme = args.theme

    status("")
    status("gald3r Semver Release Engine", "cyan")
    status("-" * 50, "darkgray")
    status(f"  Project root : {project_root}")
    status(f"  Current ver  : {current_version}")
    status(f"  Bump type    : {args.bump_type}")
    status(f"  New version  : {new_version}")
    status(f"  Tag          : {tag_name}")
    status(f"  Theme        : {theme if theme else '(none)'}")
    status(f"  Mode         : {'APPLY' if args.apply else 'DRY-RUN'}",
           "yellow" if args.apply else "darkgray")
    status("")

    has_content = unreleased_has_content(changelog_path)
    if not has_content:
        status("WARNING: [Unreleased] section appears empty — release will "
               "have no notes.", "yellow")

    unreleased_content = get_unreleased_content(changelog_path)
    status("── [Unreleased] preview ──────────────────────", "darkgray")
    for line in unreleased_content:
        status(f"  {line}", "gray")
    status("")

    if not args.apply:
        status("DRY-RUN: No changes made. Pass -Apply to execute.", "darkgray")
        if as_json:
            print(json.dumps({
                "success": True,
                "dry_run": True,
                "current": current_version,
                "new_version": new_version,
                "tag": tag_name,
                "has_content": has_content,
            }))
        return 0

    # -- Apply changes ------------------------------------------------------

    status("── Applying changes ──────────────────────────", "yellow")

    # 1. Promote CHANGELOG
    status(f"  [1/5] Promoting CHANGELOG.md [Unreleased] → [{new_version}]...")
    new_lines = promote_changelog(changelog_path, new_version, theme, today)
    changelog_path.write_text("\n".join(new_lines), encoding="utf-8",
                              newline="")
    status("        ✓ CHANGELOG.md updated", "green")

    # 2. Bump VERSION file
    status(f"  [2/7] Writing VERSION file: {new_version}...")
    version_path.write_text(new_version, encoding="utf-8", newline="")
    status("        ✓ VERSION updated", "green")

    # 2b. Update .gald3r/.identity gald3r_version= (T1437 auto-increment)
    identity_path = project_root / ".gald3r" / ".identity"
    if identity_path.exists():
        status("  [2b]  Updating .gald3r/.identity gald3r_version...")
        id_content = identity_path.read_text(encoding="utf-8-sig",
                                             errors="replace")
        if re.search(r"(?m)^gald3r_version=", id_content):
            id_updated = re.sub(r"(?m)^gald3r_version=.*$",
                                f"gald3r_version={new_version}", id_content)
            identity_path.write_text(id_updated, encoding="utf-8", newline="")
            status(f"        ✓ .gald3r/.identity gald3r_version={new_version}",
                   "green")
        else:
            status("        ~ .gald3r/.identity has no gald3r_version= key, "
                   "skipping", "darkgray")
    else:
        status("        ~ No .gald3r/.identity found, skipping", "darkgray")

    # 3. Update README badge
    status("  [3/7] Updating README badge...")
    badge_updated = update_readme_badge(readme_path, current_version,
                                        new_version)
    if badge_updated:
        status("        ✓ README badge updated", "green")
    else:
        status("        ~ README badge not found or already current",
               "darkgray")

    # 3b. Create releases/RELEASE_v{newVersion}.md from CHANGELOG content
    releases_dir = project_root / "releases"
    release_file = releases_dir / f"RELEASE_v{new_version}.md"
    status(f"  [3b]  Creating releases/RELEASE_v{new_version}.md...")
    releases_dir.mkdir(parents=True, exist_ok=True)
    prev_version = current_version
    prev_file = f"RELEASE_v{prev_version}.md"
    release_notes = get_release_notes(changelog_path, new_version)
    release_title = (f"Release v{new_version} — {theme}" if theme
                     else f"Release v{new_version}")
    release_body = (
        f"# {release_title}\n"
        f"\n"
        f"> **Released**: {today}\n"
        f"> **Previous release**: [{prev_version}]({prev_file})\n"
        f"\n"
        f"---\n"
        f"\n"
        f"## Full Changelog\n"
        f"\n"
        f"{release_notes}"
    )
    release_file.write_text(release_body, encoding="utf-8", newline="")
    status(f"        ✓ releases/RELEASE_v{new_version}.md created", "green")

    # 4. Git commit
    status("  [4/7] Creating release commit...")
    commit_msg = (f"release: {tag_name} -- {theme}" if theme
                  else f"release: {tag_name}")
    _git(project_root, "add", "CHANGELOG.md", "VERSION", "README.md")
    _git(project_root, "add", ".gald3r/.identity")
    _git(project_root, "add", f"releases/RELEASE_v{new_version}.md")
    _git(project_root, "commit", "-m", commit_msg)
    status(f"        ✓ Committed: '{commit_msg}'", "green")

    # 5. Git tag
    if not args.no_tag:
        status(f"  [5/7] Creating git tag {tag_name}...")
        tag_msg = (f"Release {tag_name} - {theme}" if theme
                   else f"Release {tag_name}")
        _git(project_root, "tag", "-a", tag_name, "-m", tag_msg)
        status(f"        ✓ Tag created: {tag_name}", "green")
    else:
        status("  [5/7] Skipping tag (--NoTag)", "darkgray")

    status("")
    status(f"── Release {tag_name} complete ─────────────────", "green")
    status("")
    status("Next steps:", "cyan")
    status("  Push:           git push origin main --tags", "gray")
    if not args.no_github:
        status(f"  GitHub release: gh release create {tag_name} --title "
               f"'{tag_name}' --notes-file <(git show HEAD:CHANGELOG.md | ...)",
               "gray")
        status(f"  Or run:         gald3r_semver.py -BumpType ... "
               f"(version {new_version})", "gray")
    status("")

    if as_json:
        print(json.dumps({
            "success": True,
            "dry_run": False,
            "old_version": current_version,
            "new_version": new_version,
            "tag": tag_name,
            "theme": theme,
            "commit_msg": commit_msg,
            "badge_updated": badge_updated,
        }))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="gald3r Semantic Versioning Engine (T1210). Promotes "
                    "CHANGELOG [Unreleased], bumps VERSION, tags the release.")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=os.getcwd(),
                        help="Root directory of the project (default: cwd)")
    parser.add_argument("-BumpType", "--bump-type", dest="bump_type",
                        type=str.lower, choices=["major", "minor", "patch"],
                        default=None, help="Version bump type")
    parser.add_argument("-Theme", "--theme", dest="theme", default="",
                        help="Short theme name for the release")
    parser.add_argument("-Apply", "--apply", dest="apply",
                        action="store_true",
                        help="Actually apply changes (default: dry-run)")
    parser.add_argument("-NoTag", "--no-tag", dest="no_tag",
                        action="store_true", help="Skip git tag creation")
    parser.add_argument("-NoGitHub", "--no-github", dest="no_github",
                        action="store_true",
                        help="Skip GitHub release hints")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Output result as JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
