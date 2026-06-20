"""
gen_vault_moc.py — Generate or update _INDEX.md MOC (Map of Content) files

Creates hub notes containing [[wikilinks]] to all .md files in a directory.
These links make the Obsidian graph view show connections instead of isolated dots.

Vault root discovery (in priority order):
    1. --vault-path CLI argument
    2. GALD3R_VAULT_ROOT environment variable

Usage:
    python gen_vault_moc.py [--vault-path PATH] --target-path PATH [--dry-run] [--verbose]
    python gen_vault_moc.py [--vault-path PATH] --auto [--dry-run] [--verbose]

Options:
    --vault-path   Root of the Obsidian vault (falls back to $GALD3R_VAULT_ROOT)
    --target-path  Directory to generate _INDEX.md for (can be specified multiple times)
    --auto         Auto-discover all directories with >= MIN_FILES .md files
    --min-files    Minimum file count to trigger auto-generation (default: 10)
    --dry-run      Preview without writing files
    --verbose      Print each file processed

Examples:
    # Generate for all platform dirs automatically (vault from env):
    GALD3R_VAULT_ROOT=<vault-root> python gen_vault_moc.py --auto

    # Generate for one specific dir:
    python gen_vault_moc.py --vault-path <vault-root> \\
        --target-path <vault-root>/research/platforms/cursor

    # Dry run to preview:
    python gen_vault_moc.py --vault-path <vault-root> --auto --dry-run
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

MIN_FILES_DEFAULT = 10
INDEX_FILENAME = "_INDEX.md"
# Tags that identify MOC files in the vault's own index
MOC_TAGS_BASE = ["moc"]


def resolve_vault_root(cli_value: str | None) -> Path | None:
    """Resolve vault root from CLI arg or GALD3R_VAULT_ROOT env var."""
    raw = cli_value or os.environ.get("GALD3R_VAULT_ROOT")
    return Path(raw) if raw else None


def read_frontmatter_title(path: Path) -> str:
    """Extract title: from YAML frontmatter, fall back to stem."""
    try:
        content = path.read_text(encoding="utf-8-sig")
        if content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                fm = content[3:end]
                m = re.search(r'(?m)^title:\s*["\']?(.+?)["\']?\s*$', fm)
                if m:
                    return m.group(1).strip().strip('"\'')
    except Exception:
        pass
    return path.stem.replace("_", " ").replace("-", " ").title()


def relative_wikilink(vault_root: Path, target: Path) -> str:
    """Return Obsidian-style wikilink path relative to vault root, no .md extension."""
    try:
        rel = target.relative_to(vault_root)
        # Forward slashes, no .md
        return str(rel.with_suffix("")).replace("\\", "/")
    except ValueError:
        return str(target.with_suffix("")).replace("\\", "/")


def generate_moc(vault_root: Path, target_dir: Path, dry_run: bool, verbose: bool) -> bool:
    """
    Generate or update _INDEX.md in target_dir.
    Returns True if file was created/updated.
    """
    index_path = target_dir / INDEX_FILENAME

    # Collect subdirectory index files (links to sub-MOCs)
    subdir_entries: list[tuple[str, str, int]] = []  # (name, wikilink, count)
    for sub in sorted(target_dir.iterdir()):
        if sub.is_dir():
            sub_index = sub / INDEX_FILENAME
            note_count = len([f for f in sub.rglob("*.md") if f.name != INDEX_FILENAME])
            if note_count == 0:
                continue
            if sub_index.exists():
                wl = relative_wikilink(vault_root, sub_index)
                subdir_entries.append((sub.name, wl, note_count))
            else:
                # Include subdir even without _INDEX.md — show it as a plain entry
                subdir_entries.append((sub.name, sub.name, note_count))

    # Collect .md files in this directory only (non-recursive, skip _INDEX.md)
    note_files = sorted(
        [f for f in target_dir.iterdir() if f.is_file() and f.suffix == ".md" and f.name != INDEX_FILENAME],
        key=lambda f: f.name,
    )

    if not note_files and not subdir_entries:
        return False

    today = date.today().isoformat()
    note_count = len(note_files)
    dir_name = target_dir.name.replace("-", " ").replace("_", " ").title()

    # Derive platform tag from directory hierarchy
    platform_tags: list[str] = []
    known_platforms = {"cursor", "claude-code", "gemini", "openai", "opencode", "claude"}
    for part in target_dir.parts:
        if part.lower() in known_platforms:
            platform_tags.append(part.lower())

    tags = MOC_TAGS_BASE + platform_tags
    tags_yaml = "[" + ", ".join(tags) + "]"

    # Build frontmatter
    frontmatter = (
        f"---\n"
        f'title: "{dir_name} — Index"\n'
        f"date: {today}\n"
        f"type: moc\n"
        f"tags: {tags_yaml}\n"
        f"auto_generated: true\n"
        f"last_updated: {today}\n"
        f"note_count: {note_count}\n"
        f"---\n"
    )

    # Build body
    lines = [
        f"# {dir_name} — Index",
        "",
        f"> Auto-generated index. Do not edit manually — regenerated by `scripts/gen_vault_moc.py`.",
        "",
    ]

    if subdir_entries:
        lines += ["## Subdirectories", ""]
        for (name, wl, count) in subdir_entries:
            label = name.replace("-", " ").replace("_", " ").title()
            lines.append(f"- [[{wl}|{label}/]] ({count} notes)")
        lines.append("")

    if note_files:
        lines += ["## Notes", ""]
        for f in note_files:
            title = read_frontmatter_title(f)
            wl = relative_wikilink(vault_root, f)
            lines.append(f"- [[{wl}|{title}]]")

    body = "\n".join(lines) + "\n"
    new_content = frontmatter + "\n" + body

    # Check if update needed (idempotent)
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        if existing == new_content:
            if verbose:
                print(f"  UNCHANGED: {index_path}")
            return False

    if verbose:
        prefix = "[DRY-RUN] " if dry_run else ""
        print(f"  {prefix}{'UPDATE' if index_path.exists() else 'CREATE'}: {index_path} ({note_count} notes)")

    if not dry_run:
        index_path.write_text(new_content, encoding="utf-8")

    return True


def find_auto_targets(vault_root: Path, min_files: int) -> list[Path]:
    """Find all directories with >= min_files .md files (direct or via subdirs, excluding _INDEX.md)."""
    targets: list[Path] = []
    for d in sorted(vault_root.rglob("*")):
        if not d.is_dir():
            continue
        # Skip hidden dirs
        if any(part.startswith(".") for part in d.parts):
            continue
        # Count direct .md files
        direct_count = len([f for f in d.iterdir() if f.is_file() and f.suffix == ".md" and f.name != INDEX_FILENAME])
        # Count recursive (for dirs that aggregate subdirectory content)
        recursive_count = len([f for f in d.rglob("*.md") if f.name != INDEX_FILENAME])
        if direct_count >= min_files or recursive_count >= min_files:
            targets.append(d)
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate _INDEX.md MOC files for vault directories")
    parser.add_argument("--vault-path", default=None, help="Vault root path (falls back to $GALD3R_VAULT_ROOT)")
    parser.add_argument("--target-path", "--path", action="append", dest="targets", default=[], help="Directory to index (repeatable)")
    parser.add_argument("--auto", action="store_true", help="Auto-discover dirs with >= min-files notes")
    parser.add_argument("--min-files", type=int, default=MIN_FILES_DEFAULT, help=f"Min files for auto mode (default: {MIN_FILES_DEFAULT})")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    vault_root = resolve_vault_root(args.vault_path)
    if vault_root is None:
        print("ERROR: no vault path. Pass --vault-path or set GALD3R_VAULT_ROOT.")
        return 1
    if not vault_root.exists():
        print(f"ERROR: vault path not found: {vault_root}")
        return 1

    target_dirs: list[Path] = []

    if args.auto:
        target_dirs = find_auto_targets(vault_root, args.min_files)
        # Sort deepest-first so child MOCs are created before parent MOCs reference them
        target_dirs = sorted(target_dirs, key=lambda p: len(p.parts), reverse=True)
        if args.verbose:
            print(f"Auto-discovered {len(target_dirs)} directories with >= {args.min_files} notes")
    else:
        for t in args.targets:
            p = Path(t)
            if not p.exists():
                print(f"WARNING: target not found, skipping: {p}")
                continue
            target_dirs.append(p)

    if not target_dirs:
        print("No target directories found. Use --target-path or --auto.")
        return 1

    if args.dry_run:
        print("DRY-RUN — no files written")

    created = 0
    unchanged = 0
    for d in target_dirs:
        changed = generate_moc(vault_root, d, dry_run=args.dry_run, verbose=args.verbose)
        if changed:
            created += 1
        else:
            unchanged += 1

    label = "Would create/update" if args.dry_run else "Created/updated"
    print(f"\ngen_vault_moc.py complete:\n  {label}: {created}\n  Unchanged: {unchanged}\n")
    if args.dry_run and created > 0:
        print("Run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
