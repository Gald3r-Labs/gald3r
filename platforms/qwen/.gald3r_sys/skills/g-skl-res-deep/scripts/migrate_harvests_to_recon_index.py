"""
migrate_harvests_to_recon_index.py
===================================

T081 AC-7 — Migration helper for existing research/harvests/ folders.

Purpose
-------
Scan existing harvest folders (local `research/harvests/*/` and/or shared
`{vault}/research/recon/*/`), normalize their Obsidian frontmatter per T044, and
seed the `_recon_index.yaml` dedup manifest with one entry per harvest.

The script is **additive only** — it never deletes existing harvest files. It
patches missing frontmatter fields in place and writes/updates a single
`_recon_index.yaml` at the recon base.

Constraints honored
-------------------
- C-001 file-first: no MCP, no Docker required
- C-003 path resolution: reads `.gald3r/.identity` for `vault_location`
- C-005 schema: only adds Obsidian-standard fields listed in VAULT_SCHEMA.md
- C-006 logged: appends a row to `{vault}/log.md` (or `research/log.md`) per run
- Stdlib only: uses pathlib + a minimal hand-rolled YAML parser/writer so the
  script runs on a vanilla UV-managed venv without extra installs.

Invocation
----------
    # From the project root
    uv run python .cursor/skills/g-skl-res-deep/scripts/migrate_harvests_to_recon_index.py

    # Dry-run (shows what would change, writes nothing)
    uv run python .cursor/skills/g-skl-res-deep/scripts/migrate_harvests_to_recon_index.py --dry-run

    # Target only a specific recon base
    uv run python .cursor/skills/g-skl-res-deep/scripts/migrate_harvests_to_recon_index.py --recon-base research/harvests

Idempotent: re-running updates existing entries rather than duplicating them.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Minimal YAML support — frontmatter read/write and _recon_index.yaml parse
# ---------------------------------------------------------------------------

_FRONTMATTER_DELIM = "---"


def _parse_yaml_block(text: str) -> Dict[str, Any]:
    """Parse a small subset of YAML sufficient for frontmatter:

    - scalar ``key: value`` (strings, ints, simple lists inline)
    - inline arrays ``key: [a, b, c]``
    - multi-line block lists are NOT supported (we don't emit them in recon)
    """
    result: Dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not val:
            result[key] = ""
            continue
        # Inline array
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                items = [p.strip().strip("'\"") for p in inner.split(",")]
                result[key] = items
            continue
        # Strip surrounding quotes on scalars
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]
        result[key] = val
    return result


def _emit_yaml_scalar(value: Any) -> str:
    if isinstance(value, list):
        inner = ", ".join(_emit_yaml_scalar(v) for v in value)
        return f"[{inner}]"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return ""
    s = str(value)
    # Quote if contains colons, leading whitespace, or starts with special chars
    if any(ch in s for ch in (":", "#", "\n")) or s.strip() != s:
        s_escaped = s.replace('"', '\\"')
        return f'"{s_escaped}"'
    return s


def _emit_yaml_block(data: Dict[str, Any]) -> str:
    lines: List[str] = []
    for key in data:
        value = data[key]
        lines.append(f"{key}: {_emit_yaml_scalar(value)}")
    return "\n".join(lines)


def split_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str, str]:
    """Return (frontmatter_dict_or_None, raw_frontmatter_block, body)."""
    if not content.startswith(_FRONTMATTER_DELIM):
        return None, "", content
    # Find closing delimiter
    lines = content.splitlines(keepends=True)
    if len(lines) < 3 or lines[0].strip() != _FRONTMATTER_DELIM:
        return None, "", content
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == _FRONTMATTER_DELIM:
            end_idx = i
            break
    if end_idx is None:
        return None, "", content
    block = "".join(lines[1:end_idx])
    body = "".join(lines[end_idx + 1 :])
    # Preserve body leading newline trim
    return _parse_yaml_block(block), block, body


def rebuild_with_frontmatter(fm: Dict[str, Any], body: str) -> str:
    return f"{_FRONTMATTER_DELIM}\n{_emit_yaml_block(fm)}\n{_FRONTMATTER_DELIM}\n{body}"


# ---------------------------------------------------------------------------
# Path resolution — read .gald3r/.identity per C-003
# ---------------------------------------------------------------------------


def find_project_root(start: Path) -> Path:
    """Walk up from ``start`` until a directory containing ``.gald3r/`` is found."""
    cur = start.resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / ".gald3r").is_dir():
            return candidate
    raise RuntimeError(
        f"Could not locate .gald3r/ from {start}. Run from within a gald3r project."
    )


def read_identity(project_root: Path) -> Dict[str, str]:
    """Read .gald3r/.identity as key=value pairs (no quotes)."""
    identity = project_root / ".gald3r" / ".identity"
    result: Dict[str, str] = {}
    if not identity.is_file():
        return result
    for line in identity.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def resolve_recon_base(project_root: Path, override: Optional[str]) -> Tuple[Path, str, Path]:
    """Return (recon_base_path, mode, log_path)."""
    if override:
        base = (project_root / override).resolve()
        return base, "override", project_root / "research" / "log.md"
    identity = read_identity(project_root)
    vault_location = identity.get("vault_location", "{LOCAL}").strip()
    if vault_location in ("", "{LOCAL}"):
        base = (project_root / "research" / "harvests").resolve()
        return base, "local", project_root / "research" / "log.md"
    vault_path = Path(vault_location)
    base = (vault_path / "research" / "recon").resolve()
    log_path = vault_path / "log.md"
    return base, "shared", log_path


# ---------------------------------------------------------------------------
# Migration core
# ---------------------------------------------------------------------------


REQUIRED_FIELDS = ("date", "type", "source", "title", "tags")


def guess_source_from_slug(slug: str) -> str:
    # Example: "user__repo" → "https://github.com/user/repo"
    if "__" in slug:
        user, _, repo = slug.partition("__")
        return f"https://github.com/{user}/{repo}"
    return ""


def default_title_from_slug(slug: str) -> str:
    return f"Recon: {slug.replace('__', '/').replace('-', ' ')}"


def normalize_frontmatter(
    fm: Dict[str, Any], file_path: Path, slug: str
) -> Tuple[Dict[str, Any], List[str]]:
    """Add any missing Obsidian-standard fields with best-effort values.

    Returns (new_fm, list_of_added_keys).
    """
    added: List[str] = []
    new_fm = dict(fm)  # shallow copy preserves order in 3.7+
    # date — use file mtime
    if not new_fm.get("date"):
        mtime = dt.datetime.fromtimestamp(file_path.stat().st_mtime, dt.timezone.utc)
        new_fm["date"] = mtime.strftime("%Y-%m-%d")
        added.append("date")
    # type
    if not new_fm.get("type"):
        new_fm["type"] = "recon"
        added.append("type")
    # source
    if not new_fm.get("source"):
        guessed = (
            new_fm.get("source_url")
            or guess_source_from_slug(slug)
        )
        if guessed:
            new_fm["source"] = guessed
            added.append("source")
    # title
    if not new_fm.get("title"):
        tgt = new_fm.get("target_name") or default_title_from_slug(slug)
        new_fm["title"] = f"Recon: {tgt}" if not str(tgt).lower().startswith("recon") else tgt
        added.append("title")
    # tags (prefer over legacy topics)
    if not new_fm.get("tags"):
        legacy = new_fm.get("topics")
        if isinstance(legacy, list) and legacy:
            new_fm["tags"] = legacy
        else:
            new_fm["tags"] = ["recon"]
        added.append("tags")
    return new_fm, added


def find_feature_files(harvest_dir: Path) -> List[Path]:
    """Return candidate FEATURES-style files in a harvest folder."""
    candidates = []
    for name in ("FEATURES.md", "04_FEATURES.md"):
        p = harvest_dir / name
        if p.is_file():
            candidates.append(p)
    return candidates


def scan_harvest_folders(recon_base: Path) -> List[Path]:
    if not recon_base.is_dir():
        return []
    return sorted(p for p in recon_base.iterdir() if p.is_dir())


def build_index_entry(
    slug: str, frontmatter: Dict[str, Any], output_path: Path, recon_base: Path
) -> Dict[str, Any]:
    # Output path relative to recon_base's parent (vault root or research/)
    try:
        rel = output_path.relative_to(recon_base.parent.parent)
        rel_str = str(rel).replace("\\", "/")
    except ValueError:
        rel_str = str(output_path).replace("\\", "/")
    last_run = frontmatter.get("harvested") or frontmatter.get("date") or dt.date.today().isoformat()
    return {
        "slug": slug,
        "source_url": frontmatter.get("source") or frontmatter.get("source_url") or "",
        "title": frontmatter.get("title") or default_title_from_slug(slug),
        "last_run": last_run,
        "status": "complete" if frontmatter.get("status") == "ready_for_review" or frontmatter.get("passes_completed") else "partial",
        "output_path": rel_str if rel_str.endswith("/") else rel_str + "/",
    }


# ---------------------------------------------------------------------------
# _recon_index.yaml read/write
# ---------------------------------------------------------------------------


def read_index(index_path: Path) -> Dict[str, Any]:
    if not index_path.is_file():
        return {"schema_version": 1, "entries": []}
    text = index_path.read_text(encoding="utf-8")
    entries: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("- "):
            if current is not None:
                entries.append(current)
            current = {}
            after = line.lstrip()[2:]
            if ":" in after:
                k, _, v = after.partition(":")
                current[k.strip()] = v.strip().strip("'\"")
        elif line.startswith("  ") and current is not None and ":" in line:
            k, _, v = line.strip().partition(":")
            current[k.strip()] = v.strip().strip("'\"")
        # Top-level non-entry lines (schema_version, entries:) are ignored for simplicity
    if current is not None:
        entries.append(current)
    return {"schema_version": 1, "entries": entries}


def write_index(index_path: Path, data: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# Auto-managed by g-skl-res-deep / g-skl-res-review / g-skl-res-apply")
    lines.append("# Do not hand-edit unless you know what you're doing.")
    lines.append(f"schema_version: {data.get('schema_version', 1)}")
    lines.append("entries:")
    for entry in data.get("entries", []):
        first = True
        for key in ("slug", "source_url", "title", "last_run", "status", "output_path"):
            if key not in entry:
                continue
            prefix = "  - " if first else "    "
            lines.append(f"{prefix}{key}: {_emit_yaml_scalar(entry[key])}")
            first = False
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def upsert_entry(index_data: Dict[str, Any], entry: Dict[str, Any]) -> str:
    """Return 'added' or 'updated'."""
    for existing in index_data["entries"]:
        if existing.get("slug") == entry["slug"]:
            existing.update(entry)
            return "updated"
    index_data["entries"].append(entry)
    return "added"


# ---------------------------------------------------------------------------
# Vault log append (C-006)
# ---------------------------------------------------------------------------


def append_log(log_path: Path, run_date: str, count: int, note: str, dry_run: bool) -> None:
    row = f"| {run_date} | harvest-migration | {count} notes | {note} |"
    if dry_run:
        print(f"[dry-run] would append to {log_path}: {row}")
        return
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        text += row + "\n"
        log_path.write_text(text, encoding="utf-8")
    else:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Operations Log\n\n"
            "Format: `| YYYY-MM-DD | OPERATION | path/or/context | agent/tool |`\n\n"
            "| Date | Operation | Target | Agent |\n"
            "|------|-----------|--------|-------|\n"
        )
        log_path.write_text(header + row + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change but write nothing.",
    )
    parser.add_argument(
        "--recon-base",
        default=None,
        help=(
            "Override the recon base directory (relative to project root). "
            "Default: resolve from .gald3r/.identity vault_location."
        ),
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Override project root detection.",
    )
    args = parser.parse_args(argv)

    start = Path(args.project_root) if args.project_root else Path.cwd()
    project_root = find_project_root(start)

    recon_base, mode, log_path = resolve_recon_base(project_root, args.recon_base)
    index_path = recon_base / "_recon_index.yaml"

    print(f"Project root: {project_root}")
    print(f"Recon base:   {recon_base} (mode={mode})")
    print(f"Index path:   {index_path}")
    print(f"Log path:     {log_path}")
    print(f"Dry-run:      {args.dry_run}")
    print("---")

    if not recon_base.is_dir():
        print(f"Recon base does not exist yet — nothing to migrate.")
        return 0

    harvests = scan_harvest_folders(recon_base)
    if not harvests:
        print("No harvest folders found.")
        return 0

    index_data = read_index(index_path)
    run_date = dt.date.today().isoformat()
    patched_count = 0
    index_added = 0
    index_updated = 0

    for harvest_dir in harvests:
        slug = harvest_dir.name
        feature_files = find_feature_files(harvest_dir)
        if not feature_files:
            print(f"[skip]  {slug}: no FEATURES.md / 04_FEATURES.md found")
            continue

        # Prefer FEATURES.md; if only 04_FEATURES.md exists, treat it as the canonical
        # synthesis file for this migration.
        source_file = feature_files[0]
        content = source_file.read_text(encoding="utf-8")
        fm, _raw_block, body = split_frontmatter(content)
        if fm is None:
            # Inject a fresh frontmatter
            fm = {}
            body = content
        new_fm, added = normalize_frontmatter(fm, source_file, slug)

        if added:
            print(f"[patch] {slug}: adding missing fields {added}")
            if not args.dry_run:
                source_file.write_text(rebuild_with_frontmatter(new_fm, body), encoding="utf-8")
            patched_count += 1
        else:
            print(f"[ok]    {slug}: frontmatter already complete")

        entry = build_index_entry(slug, new_fm, harvest_dir, recon_base)
        action = upsert_entry(index_data, entry)
        if action == "added":
            index_added += 1
        else:
            index_updated += 1

    # Persist index + log
    if args.dry_run:
        print(f"[dry-run] would write index at {index_path} "
              f"(+{index_added} entries, {index_updated} updated)")
    else:
        write_index(index_path, index_data)
        print(f"[write] {index_path} ({index_added} added, {index_updated} updated)")

    total_touched = patched_count + index_added
    note = (
        f"T081 normalization: {patched_count} frontmatter patches, "
        f"{index_added} new index entries, {index_updated} updated"
    )
    append_log(log_path, run_date, max(total_touched, len(harvests)), note, args.dry_run)

    print("---")
    print(f"Summary: {patched_count} files patched, "
          f"{index_added} index entries added, {index_updated} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
