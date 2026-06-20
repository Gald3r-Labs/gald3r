"""
normalize_vault_tags.py — Normalize vault note tag taxonomy

Non-destructive: only modifies the YAML frontmatter, never the body.
Idempotent: safe to re-run.

Actions performed within frontmatter ONLY:
0. (folded from fix_platform_doc_tags.py) Repair the tags key itself BEFORE normalizing:
   - frontmatter has `topics:` but NOT `tags:`  → rename `topics:` to `tags:`
   - frontmatter has NEITHER `tags:` nor `topics:` → add `tags: []`
   - frontmatter already has `tags:`            → leave the key as-is
   (Disable this pre-pass with --no-fix-tags-key.)
1. Lowercase all tag values
2. Replace underscores with hyphens in tag values
3. Add missing category tag if type: is present but the category tag is absent:
   platform_doc / documentation → ensure 'platform-doc' in tags
   video                        → ensure 'video' in tags
   article                      → ensure 'article' in tags
   github                       → ensure 'github' in tags
   session                      → ensure 'session' in tags
   decision                     → ensure 'decision' in tags
   harvest                      → ensure 'harvest' in tags
   concept                      → ensure 'concept' in tags
   moc                          → ensure 'moc' in tags
4. Write back UTF-8 without BOM

Vault root discovery (in priority order):
    1. --vault-path CLI argument
    2. GALD3R_VAULT_ROOT environment variable

Usage:
    python normalize_vault_tags.py [--vault-path PATH] [--dry-run] [--verbose] [--no-fix-tags-key]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

TYPE_TO_CATEGORY = {
    "platform_doc":   "platform-doc",
    "documentation":  "platform-doc",
    "video":          "video",
    "video_analysis": "video",
    "article":        "article",
    "github":         "github",
    "session":        "session",
    "decision":       "decision",
    "harvest":        "harvest",
    "concept":        "concept",
    "moc":            "moc",
}

# Matches `tags: [...]` or `tags:\n  - item` patterns in frontmatter
TAGS_INLINE_RE = re.compile(r"(?m)^(tags:\s*\[)([^\]]*?)(\])")
TAGS_BLOCK_RE  = re.compile(r"(?m)^(tags:\s*\n)((?:[ \t]*-[^\n]*\n)*)")
TYPE_RE        = re.compile(r"(?m)^type:\s*(.+?)\s*$")

# Folded from fix_platform_doc_tags.py — repair the tags key itself
HAS_TAGS_RE    = re.compile(r"(?m)^tags:")
HAS_TOPICS_RE  = re.compile(r"(?m)^topics:")


def resolve_vault_root(cli_value: str | None) -> Path | None:
    """Resolve vault root from CLI arg or GALD3R_VAULT_ROOT env var."""
    raw = cli_value or os.environ.get("GALD3R_VAULT_ROOT")
    return Path(raw) if raw else None


def normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace("_", "-").strip('"\'')


def parse_inline_tags(raw: str) -> list[str]:
    """Parse `[tag1, tag2, "tag3"]` into a list."""
    items = [t.strip().strip('"\'') for t in raw.split(",") if t.strip()]
    return [t for t in items if t]


def parse_block_tags(raw: str) -> list[str]:
    """Parse YAML block list `  - tag` lines into a list."""
    items = []
    for line in raw.splitlines():
        m = re.match(r"[ \t]*-\s*(.+)", line)
        if m:
            items.append(m.group(1).strip().strip('"\''))
    return items


def split_frontmatter(content: str):
    if not content.startswith("---"):
        return None, content
    rest = content[3:]
    idx = rest.find("\n---")
    if idx == -1:
        return None, content
    return rest[:idx], rest[idx + 4:]


def fix_tags_key(frontmatter: str) -> tuple[str, bool]:
    """
    Folded from fix_platform_doc_tags.py: ensure a `tags:` key exists in the
    frontmatter so the normalization steps below have something to act on.

    - `topics:` present, `tags:` absent → rename `topics:` → `tags:`
    - neither present                   → append `tags: []`
    - `tags:` already present           → no change

    Returns (new_frontmatter, changed).
    """
    has_tags = bool(HAS_TAGS_RE.search(frontmatter))
    if has_tags:
        return frontmatter, False

    has_topics = bool(HAS_TOPICS_RE.search(frontmatter))
    if has_topics:
        return HAS_TOPICS_RE.sub("tags:", frontmatter, count=1), True

    # Insert `tags: []` at end of frontmatter
    return frontmatter.rstrip() + "\ntags: []\n", True


def normalize_file(path: Path, dry_run: bool, verbose: bool, fix_tags_key_enabled: bool) -> str:
    """Returns: changed | already_correct | skipped | error"""
    try:
        content = path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        if verbose:
            print(f"  ERROR {path}: {exc}")
        return "error"

    # Skip files without frontmatter
    if not content.startswith("---"):
        return "skipped"

    frontmatter, body = split_frontmatter(content)
    if frontmatter is None:
        return "skipped"

    new_fm = frontmatter
    changed = False

    # ── Step 0: repair tags key (folded fix_platform_doc_tags.py) ──────────────
    if fix_tags_key_enabled:
        new_fm, key_changed = fix_tags_key(new_fm)
        changed = changed or key_changed

    # ── Step 1 & 2: normalize existing tags ───────────────────────────────────
    inline_match = TAGS_INLINE_RE.search(new_fm)
    block_match  = TAGS_BLOCK_RE.search(new_fm)

    current_tags: list[str] = []
    if inline_match:
        current_tags = parse_inline_tags(inline_match.group(2))
        normalized = [normalize_tag(t) for t in current_tags if t]
        if normalized != current_tags:
            new_raw = ", ".join(normalized)
            new_fm = new_fm[:inline_match.start()] + f"{inline_match.group(1)}{new_raw}{inline_match.group(3)}" + new_fm[inline_match.end():]
            current_tags = normalized
            changed = True
        else:
            current_tags = normalized
    elif block_match:
        current_tags = parse_block_tags(block_match.group(2))
        normalized = [normalize_tag(t) for t in current_tags if t]
        if normalized != current_tags:
            new_lines = "\n".join(f"  - {t}" for t in normalized) + "\n"
            new_fm = new_fm[:block_match.start()] + f"tags:\n{new_lines}" + new_fm[block_match.end():]
            current_tags = normalized
            changed = True
        else:
            current_tags = normalized

    # ── Step 3: add missing category tag ──────────────────────────────────────
    type_match = TYPE_RE.search(new_fm)
    if type_match:
        type_val = type_match.group(1).strip().strip('"\'').lower()
        category = TYPE_TO_CATEGORY.get(type_val)
        if category and category not in current_tags:
            # Add category tag to the inline tag list
            inline_m = TAGS_INLINE_RE.search(new_fm)
            if inline_m:
                existing_raw = inline_m.group(2).strip()
                if existing_raw:
                    new_raw = existing_raw + ", " + category
                else:
                    new_raw = category
                new_fm = new_fm[:inline_m.start()] + f"{inline_m.group(1)}{new_raw}{inline_m.group(3)}" + new_fm[inline_m.end():]
                current_tags.append(category)
                changed = True
            elif TAGS_BLOCK_RE.search(new_fm):
                # Append to block
                block_m = TAGS_BLOCK_RE.search(new_fm)
                new_block = block_m.group(0).rstrip("\n") + f"\n  - {category}\n"
                new_fm = new_fm[:block_m.start()] + new_block + new_fm[block_m.end():]
                current_tags.append(category)
                changed = True

    if not changed:
        return "already_correct"

    new_content = "---" + new_fm + "\n---" + body
    if verbose:
        prefix = "[DRY-RUN] " if dry_run else ""
        print(f"  {prefix}CHANGED: {path.name}")

    if not dry_run:
        path.write_text(new_content, encoding="utf-8")

    return "changed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize vault tag taxonomy")
    parser.add_argument("--vault-path", default=None, help="Vault root path (falls back to $GALD3R_VAULT_ROOT)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--no-fix-tags-key",
        action="store_true",
        help="Disable the folded fix_platform_doc_tags pre-pass (topics:→tags: / add tags: [])",
    )
    args = parser.parse_args()

    vault_root = resolve_vault_root(args.vault_path)
    if vault_root is None:
        print("ERROR: no vault path. Pass --vault-path or set GALD3R_VAULT_ROOT.")
        return 1
    if not vault_root.exists():
        print(f"ERROR: path not found: {vault_root}")
        return 1

    counts = {"changed": 0, "already_correct": 0, "skipped": 0, "error": 0}
    files = sorted(vault_root.rglob("*.md"))

    if args.verbose:
        print(f"Scanning {len(files)} .md files under {vault_root}")
        if args.dry_run:
            print("DRY-RUN — no files written")

    for f in files:
        result = normalize_file(
            f,
            dry_run=args.dry_run,
            verbose=args.verbose,
            fix_tags_key_enabled=not args.no_fix_tags_key,
        )
        counts[result] += 1

    label = "Would change" if args.dry_run else "Changed"
    print(
        f"\nnormalize_vault_tags.py complete:\n"
        f"  {label}: {counts['changed']}\n"
        f"  Already correct: {counts['already_correct']}\n"
        f"  Skipped (no FM): {counts['skipped']}\n"
        f"  Errors: {counts['error']}\n"
    )
    if args.dry_run and counts["changed"] > 0:
        print("Run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
