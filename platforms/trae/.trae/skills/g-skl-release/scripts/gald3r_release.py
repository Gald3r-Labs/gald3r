#!/usr/bin/env python3
"""Python port of gald3r_release.ps1 (T1585).

gald3r Maintainer Release Tool - syncs and tags a release across gald3r's
three template repositories. <gald3r_source> only - NOT shipped to user
projects.

For user project releases, use @g-ship /
.claude/skills/g-skl-release/scripts/gald3r_semver.py.

Two-track release model:
  Track A (<gald3r_source>):  version managed in <gald3r_source>
                              CHANGELOG.md / VERSION
  Track B (template repos):   version managed in each template repo's
                              CHANGELOG.md / VERSION

This script handles Track B - promoting template CHANGELOGs and tagging.

Task: T1210. <gald3r_source> maintainer-only. See root_only_manifest.yaml.
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
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

# Cross-script call within this batch: import the gald3r_semver.py sibling.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
import gald3r_semver  # noqa: E402

_ANSI = {"cyan": "36", "green": "32", "yellow": "33", "red": "31",
         "gray": "37", "darkgray": "90", "white": "97"}
_ansi_ready = False

TEMPLATE_REPO_NAMES = ("<template_slim>", "<template_full>", "<template_adv>")


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


def _git(repo: Path, *git_args: str, quiet: bool = True) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(
        ["git", "-C", str(repo), *git_args],
        capture_output=quiet, text=True, encoding="utf-8", errors="replace")


def _powershell_exe() -> Optional[str]:
    return shutil.which("pwsh") or shutil.which("powershell")


def _run_repo_semver(repo: Path, theme: str) -> None:
    """Run the repo's own semver script: prefer .py sibling, else pwsh the .ps1."""
    repo_semver_py = repo / "scripts" / "gald3r_semver.py"
    repo_semver_ps1 = repo / "scripts" / "gald3r_semver.ps1"
    if repo_semver_py.exists():
        subprocess.run([sys.executable, str(repo_semver_py),
                        "-ProjectRoot", str(repo),
                        "-BumpType", "patch",
                        "-Theme", theme,
                        "-Apply"])
        return
    if repo_semver_ps1.exists():
        shell = _powershell_exe()
        if shell:
            subprocess.run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", str(repo_semver_ps1),
                            "-ProjectRoot", str(repo),
                            "-BumpType", "patch",
                            "-Theme", theme,
                            "-Apply"])
            return
    raise FileNotFoundError("no repo semver script")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r Maintainer Release Tool - syncs and tags a "
                    "release across the three template repositories (T1210).")
    parser.add_argument("-TemplateVersion", "--template-version",
                        dest="template_version", default="",
                        help='Version to release in the template repos '
                             '(e.g. "1.5.0"); default: <template_adv>/VERSION')
    parser.add_argument("-Theme", "--theme", dest="theme", default="",
                        help="Short theme name for the release")
    parser.add_argument("-Apply", "--apply", dest="apply",
                        action="store_true",
                        help="Actually apply changes (default: dry-run)")
    parser.add_argument("-GitHub", "--github", dest="github",
                        action="store_true",
                        help="Create GitHub releases after tagging")
    parser.add_argument("-NoGitHub", "--no-github", dest="no_github",
                        action="store_true",
                        help="Skip GitHub release creation")
    parser.add_argument("-RepoRoot", "--repo-root", dest="repo_root",
                        default="<workspace>",
                        help="Override the ecosystem root")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    repos = [repo_root / name for name in TEMPLATE_REPO_NAMES]
    theme = args.theme

    def fail(msg: str) -> int:
        _say(f"ERROR: {msg}", "red")
        return 1

    # -- Validate repo existence --------------------------------------------
    for repo in repos:
        if not repo.exists():
            return fail(f"Template repo not found: {repo}")

    # -- Determine template version ------------------------------------------
    template_version = args.template_version
    if not template_version:
        version_file = repo_root / "<template_adv>" / "VERSION"
        if version_file.exists():
            template_version = version_file.read_text(
                encoding="utf-8-sig").strip()
            _say("Auto-detected version from <template_adv>/VERSION: "
                 f"{template_version}", "cyan")
        else:
            return fail("TemplateVersion not specified and VERSION file not "
                        f"found at {version_file}")

    # -- Pre-flight: check each repo is clean enough ---------------------------
    _say("")
    _say("gald3r Maintainer Release Tool", "cyan")
    _say("─" * 60, "darkgray")
    _say(f"  Template version : {template_version}", "cyan")
    _say(f"  Theme            : {theme if theme else '(none)'}", "cyan")
    _say(f"  Mode             : {'APPLY' if args.apply else 'DRY-RUN'}",
         "yellow" if args.apply else "darkgray")
    _say("")

    _say("── Pre-flight checks ────────────────────────", "darkgray")
    all_clean = True
    for repo in repos:
        repo_name = repo.name
        dirty = _git(repo, "status", "--short").stdout.strip()
        if dirty:
            _say(f"  ⚠  {repo_name} has uncommitted changes:", "yellow")
            for line in dirty.splitlines():
                _say(f"       {line}", "gray")
            all_clean = False
        else:
            _say(f"  ✓  {repo_name} is clean", "green")
    _say("")

    if not all_clean and args.apply:
        _say("")
        response = input("WARNING: Some repos have uncommitted changes. "
                         "Continue anyway? [y/N] ")
        if not response.lower().startswith("y"):
            _say("Aborted. Commit or stash changes in each repo first.",
                 "yellow")
            return 0

    # -- Process each template repo --------------------------------------------
    _say("── Processing template repos ────────────────", "darkgray")

    for repo in repos:
        repo_name = repo.name
        _say("")
        _say(f"  [{repo_name}]", "white")

        version_path = repo / "VERSION"

        current_version = "0.0.0"
        if version_path.exists():
            current_version = version_path.read_text(
                encoding="utf-8-sig").strip()

        _say(f"    Current: {current_version}  →  Target: {template_version}",
             "gray")

        if current_version == template_version:
            _say(f"    Already at {template_version} — checking if tag "
                 "exists...", "darkgray")
            tag_exists = _git(repo, "tag", "-l",
                              f"v{template_version}").stdout.strip()
            if tag_exists:
                _say(f"    Tag v{template_version} already exists — skipping",
                     "darkgray")
                continue

        if not args.apply:
            _say("    DRY-RUN: Would promote CHANGELOG + bump VERSION + tag "
                 f"v{template_version}", "darkgray")
            continue

        try:
            # Use the repo's own semver script when present (parity sync)
            _run_repo_semver(repo, theme)
        except FileNotFoundError:
            # Fallback: do it manually
            _say(f"    gald3r_semver script not found in {repo_name} — "
                 "promoting manually", "yellow")

            version_path.write_text(template_version, encoding="utf-8",
                                    newline="")
            _say(f"    ✓ VERSION → {template_version}", "green")

            # Promote CHANGELOG via the imported semver sibling
            gald3r_semver.main(["-ProjectRoot", str(repo),
                                "-BumpType", "patch",
                                "-Theme", theme,
                                "-Apply"])

        _say(f"    ✓ {repo_name} released at v{template_version}", "green")

    # -- GitHub releases ---------------------------------------------------------
    if args.github and not args.no_github and args.apply:
        _say("")
        _say("── Creating GitHub releases ─────────────────", "darkgray")
        for repo in repos:
            repo_name = repo.name
            _say(f"  Creating GitHub release for {repo_name}...", "gray")

            # Push tags first
            _git(repo, "push", "origin", f"v{template_version}")

            # Extract release notes from CHANGELOG
            changelog = repo / "CHANGELOG.md"
            in_section = False
            notes: List[str] = []
            cl_lines = changelog.read_text(
                encoding="utf-8-sig", errors="replace").splitlines() \
                if changelog.exists() else []
            for line in cl_lines:
                if re.match(r"^## \[" + re.escape(template_version) + r"\]",
                            line):
                    in_section = True
                    continue
                if in_section and re.match(r"^## \[", line):
                    break
                if in_section:
                    notes.append(line)
            notes_content = "\n".join(notes).strip()
            notes_file = Path(tempfile.gettempdir()) / \
                f"gald3r_release_notes_{repo_name}.md"
            notes_file.write_text(notes_content + "\n", encoding="utf-8")

            title = (f"v{template_version} — {theme}" if theme
                     else f"v{template_version}")
            gh = shutil.which("gh")
            if gh:
                subprocess.run([gh, "release", "create",
                                f"v{template_version}",
                                "--title", title,
                                "--notes-file", str(notes_file),
                                "--repo", f"wrm3/{repo_name}"])
            else:
                _say("  gh CLI not found — skipping GitHub release creation",
                     "yellow")

            _say(f"  ✓ GitHub release created for {repo_name}", "green")

    _say("")
    _say(f"── Release v{template_version} complete ─────────────────", "green")
    _say("")
    _say("Next steps:", "cyan")
    _say("  Push all template repos:  git push origin main --tags (in each)",
         "gray")
    _say("  Update <gald3r_source> CHANGELOG if needed", "gray")
    _say("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
