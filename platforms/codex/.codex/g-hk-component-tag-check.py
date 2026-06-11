#!/usr/bin/env python3
"""Python port of g-hk-component-tag-check.ps1 (T1584).

Git pre-commit hook: enforce subsystem tagging on .gald3r_sys components.
Blocks commits that add new component files to .gald3r_sys/ without subsystem
tagging.

Run modes:
  - git pre-commit hook (via core.hooksPath): called with no arguments, no stdin
  - Direct check:  python g-hk-component-tag-check.py [-WarnOnly] [-Staged]

Exit codes: 0 = pass (allow commit), 1 = fail (block commit)
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; pure-stdlib path used here)

MARKDOWN_DIRS = ["skills", "commands", "agents", "rules"]
SCRIPT_DIRS = ["hooks", "scripts"]

VALID_GROUPS_TEXT = """
Each .gald3r_sys component needs:
  Markdown (.md):  'subsystem_memberships: [GROUP]' in YAML frontmatter
  PowerShell (.ps1): '# @subsystems: GROUP' in first 15 lines

Valid groups: LOGGING_SYSTEM | MEMORY_AND_KNOWLEDGE | TASK_MANAGEMENT |
  BUG_AND_QUALITY | WORKSPACE_COORDINATION | PROJECT_IDENTITY_SETUP |
  PLATFORM_INTEGRATION | AGENT_ORCHESTRATION | RELEASE_AND_VERSIONING |
  VAULT_AND_RESEARCH | UI_AND_OUTPUT | SECURITY_AND_COMPLIANCE | UNGROUPED

Run @g-skill-new / @g-command-new / @g-rule-new to scaffold with tags pre-filled.
Or add tags manually and re-stage the files.
"""


def _git(args: list) -> str:
    """Run a git command and return stdout, or '' on any failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except OSError:
        return ""


def _in_taggable_dir(rel_path: str, dirs: list) -> bool:
    for d in dirs:
        if f".gald3r_sys/{d}/" in rel_path or f".gald3r_sys\\{d}\\" in rel_path:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enforce subsystem tagging on staged .gald3r_sys components."
    )
    parser.add_argument(
        "-WarnOnly", "--warn-only", dest="warn_only", action="store_true",
        help="Print findings but do not block (exit 0 always)",
    )
    parser.add_argument(
        "-Staged", "--staged", dest="staged", action="store_true",
        help="Explicit staged mode (default when called from git)",
    )
    args = parser.parse_args()

    # Determine repo root
    repo_root = _git(["rev-parse", "--show-toplevel"])
    if not repo_root:
        print("[tag-check] Not inside a git repo — skipping.")
        return 0
    repo_root_path = Path(repo_root)

    # Get staged files (ACM: Added, Copied, Modified)
    staged_files = _git(["diff", "--cached", "--name-only", "--diff-filter=ACM"])
    if not staged_files:
        return 0

    violations = []

    for rel_path in staged_files.splitlines():
        rel_path = rel_path.strip()
        if not rel_path:
            continue
        full_path = repo_root_path / rel_path.replace("/", "\\" if sys.platform == "win32" else "/")
        if not full_path.is_file():
            continue

        # Only check files under .gald3r_sys
        if not (rel_path.startswith(".gald3r_sys/") or rel_path.startswith(".gald3r_sys\\")):
            continue

        ext = full_path.suffix.lower()

        if ext == ".md":
            if not _in_taggable_dir(rel_path, MARKDOWN_DIRS):
                continue
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not re.search(r"subsystem_memberships\s*:", content):
                violations.append(f"MISSING subsystem_memberships: in {rel_path}")
        elif ext == ".ps1":
            if not _in_taggable_dir(rel_path, SCRIPT_DIRS):
                continue
            try:
                lines = full_path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()[:15]
            except OSError:
                continue
            has_tag = any(re.match(r"^#\s*@subsystems\s*:", ln) for ln in lines)
            if not has_tag:
                violations.append(
                    f"MISSING '# @subsystems:' comment in first 15 lines: {rel_path}"
                )

    if not violations:
        return 0

    # Report violations
    print("")
    print("=== [g-hk-component-tag-check] SUBSYSTEM TAGGING VIOLATIONS ===")
    print("")
    for v in violations:
        print(f"  !! {v}")
    print(VALID_GROUPS_TEXT)

    if args.warn_only:
        return 0
    return 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Never crash the session on unexpected errors — fail open.
        sys.exit(0)
