"""
migrate_topics_to_tags.py — gald3r vault frontmatter migration

Renames `topics:` to `tags:` in all vault note YAML frontmatter.
Non-destructive: values are copied unchanged, only the key name changes.
Idempotent: files already using `tags:` are reported as already correct.

Usage:
    python migrate_topics_to_tags.py --vault-path PATH [--dry-run] [--verbose]

Examples:
    # Check what would change (no writes):
    python migrate_topics_to_tags.py --vault-path G:/gald3r_ecosystem/gald3r_vault --dry-run

    # Apply the migration:
    python migrate_topics_to_tags.py --vault-path G:/gald3r_ecosystem/gald3r_vault

    # Apply with verbose output:
    python migrate_topics_to_tags.py --vault-path G:/gald3r_ecosystem/gald3r_vault --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Matches `topics:` key at the start of a line within YAML frontmatter.
# Only renames the KEY — does not alter values.
TOPICS_PATTERN = re.compile(r"(?m)^topics:", re.MULTILINE)

# Frontmatter delimiter
FRONTMATTER_OPEN = re.compile(r"^---\s*$", re.MULTILINE)


def has_frontmatter(content: str) -> bool:
    """Return True if the file starts with a YAML frontmatter block."""
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return False
    # Find the closing ---
    lines = stripped.split("\n")
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return True
    return False


def migrate_file(path: Path, dry_run: bool, verbose: bool) -> str:
    """
    Migrate a single file.

    Returns one of: "changed" | "already_correct" | "skipped" | "error"
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        if verbose:
            print(f"  ERROR reading {path}: {exc}")
        return "error"

    if not has_frontmatter(content):
        return "skipped"

    if "tags:" in content and "topics:" not in content:
        return "already_correct"

    if "topics:" not in content:
        return "skipped"

    new_content = TOPICS_PATTERN.sub("tags:", content, count=1)

    if new_content == content:
        return "skipped"

    if verbose:
        print(f"  {'[DRY-RUN] ' if dry_run else ''}CHANGED: {path}")

    if not dry_run:
        path.write_text(new_content, encoding="utf-8")

    return "changed"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rename topics: → tags: in vault note YAML frontmatter"
    )
    parser.add_argument("--vault-path", required=True, help="Path to vault root folder")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing changes")
    parser.add_argument("--verbose", action="store_true", help="Print each file processed")
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"ERROR: vault path not found: {vault_path}")
        return 1

    counts: dict[str, int] = {"changed": 0, "already_correct": 0, "skipped": 0, "error": 0}

    md_files = list(vault_path.rglob("*.md"))
    if args.verbose:
        print(f"Scanning {len(md_files)} markdown files under {vault_path}")
        if args.dry_run:
            print("DRY-RUN MODE: no files will be modified")

    for md_file in md_files:
        result = migrate_file(md_file, dry_run=args.dry_run, verbose=args.verbose)
        counts[result] += 1

    label = "Would change" if args.dry_run else "Changed"
    print(
        f"\nmigrate_topics_to_tags.py complete:\n"
        f"  {label}: {counts['changed']}\n"
        f"  Already correct (tags:): {counts['already_correct']}\n"
        f"  Skipped (no frontmatter / no topics:): {counts['skipped']}\n"
        f"  Errors: {counts['error']}\n"
    )
    if args.dry_run and counts["changed"] > 0:
        print("Run without --dry-run to apply the migration.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
