#!/usr/bin/env python3
"""Python port of g-hk-vault-reindex.ps1 (T1584); dual-index regen (T1627).

ONE generator, TWO derived artifacts (T1627 / WS-A-4, OKF amendment):
  - `_index.yaml` (vault root): machine-readable note registry (path, title,
    type, ingestion_type, date, tags, source, project_id, refresh metadata).
    UTF-8, no BOM. This stays the machine SOURCE OF TRUTH — it drives search
    and staleness tracking and is never replaced by index.md.
  - OKF-style `index.md` per directory (vault root + every directory holding
    notes): `# Section` headings with `* [Title](relative-url) - one-line
    description` bullets, no frontmatter. A derived, regenerated view for
    progressive disclosure (an agent reads one small index.md instead of
    globbing the whole vault). Stale generated per-directory index.md files
    (identified by their auto-generated marker line) are removed on regen.

Registered on the canonical `stop` event (T1627): `g_hk_core.py`
CONCERN_CHAIN["stop"], Claude `settings.json` `hooks.Stop`, and Cursor
`hooks.json` `stop`. DEBOUNCED: the regen is skipped when both artifacts
exist, the indexed note count matches, and no note is newer than
`_index.yaml` — rapid successive Stops do not trigger redundant regens.
`-ForceRun` bypasses both the debounce and the session guard.

Scans `*.md` recursively, excluding hidden directories (any path component
below the vault root starting with `.` — `.obsidian/`, `.git/`, `.cursor/`,
`.gald3r_sys/`, `.backups/`, ... hold framework infrastructure, never vault
notes; T1632 / WS-B-9) and the index/log schema files themselves (reserved
names matched case-insensitively). Legacy per-subdir `_INDEX.md` MOC views —
produced by the retired `gen_vault_moc.py` script — are index artifacts, not
notes: they are never indexed, and marker-carrying copies are removed on
regen so the per-subdir index function is unified into this ONE generator's
per-directory `index.md` views (T1632 / WS-B-9). Frontmatter fields are
parsed leniently; title falls
back to the first `# ` heading or the filename, date falls back to the file's
UTC mtime. Session-idempotent via GALD3R_HK_VAULT_REINDEX_APPLIED (override
with -ForceRun). Vault location comes from -VaultOverride or the
g-hk-vault-resolve sibling (the .py is imported; the .ps1 is invoked via
PowerShell as a fallback). Never crashes the session: errors exit 0.
"""
# @subsystems: VAULT_AND_RESEARCH
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402,F401

_HOOK_DIR = Path(__file__).resolve().parent


def _powershell_exe() -> str:
    if os.name == "nt":
        return shutil.which("powershell.exe") or shutil.which("pwsh") or "powershell.exe"
    return shutil.which("pwsh") or "pwsh"


def load_resolve_context() -> Dict[str, Any]:
    """Load vault paths from the g-hk-vault-resolve sibling.

    Prefers the .py sibling (imported in-process); falls back to dot-sourcing
    the .ps1 via PowerShell and reading the exported variables as JSON.
    """
    py_sibling = _HOOK_DIR / "g-hk-vault-resolve.py"
    if py_sibling.is_file():
        spec = importlib.util.spec_from_file_location("g_hk_vault_resolve", str(py_sibling))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.resolve()
    ps_sibling = _HOOK_DIR / "g-hk-vault-resolve.ps1"
    cmd = [
        _powershell_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        f". '{ps_sibling}'; @{{"
        "VaultPath=$VaultPath; ReposPath=$ReposPath;"
        "VaultLocalPath=$VaultLocalPath; ReposLocalPath=$ReposLocalPath;"
        "VaultUsingFallback=$VaultUsingFallback;"
        "VaultMigrationCandidate=$VaultMigrationCandidate;"
        "VaultMessages=@($VaultMessages)"
        "} | ConvertTo-Json -Compress",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout.strip())


def _parse_frontmatter(raw: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    m = re.match(r"^---\r?\n(.+?)\r?\n---", raw, re.DOTALL)
    if not m:
        return fields
    frontmatter = m.group(1)

    def field(pattern: str):
        fm = re.search(pattern, frontmatter, re.MULTILINE)
        return fm.group(1).strip() if fm else ""

    title = field(r"^title:\s*['\"]?(.+?)['\"]?\s*$")
    if title:
        fields["title"] = title.strip("\"'")
    for key, pattern in (
        ("type", r"^type:\s*(.+)$"),
        ("date", r"^date:\s*(.+)$"),
        ("description", r"^description:\s*(.+)$"),
        ("source", r"^source:\s*(.+)$"),
        ("ingestion_type", r"^ingestion_type:\s*(.+)$"),
        ("project_id", r"^project_id:\s*(.+)$"),
        ("refresh_policy", r"^refresh_policy:\s*(.+)$"),
        ("next_refresh", r"^next_refresh:\s*(.+)$"),
        ("expires_after", r"^expires_after:\s*(.+)$"),
    ):
        value = field(pattern)
        if value:
            fields[key] = value
    tags_match = re.search(r"^tags:\s*\[(.+?)\]", frontmatter, re.MULTILINE)
    if tags_match:
        fields["tags"] = [t.strip().strip("\"'") for t in re.split(r",\s*", tags_match.group(1))]
    return fields


# ── OKF-style index.md derivation (T1627 / WS-A-4, OKF amendment) ────────────
# Format contract (consumed by the WS-B-11 vault lint): no frontmatter,
# `# Section` headings, `* [Title](relative-url) - one-line description`
# bullets. index.md is a DERIVED view of _index.yaml — never the reverse.

# Marker line stamped into every generated index.md. The stale-view cleanup
# only ever deletes index.md files carrying this marker, so hand-written
# index.md files are never touched.
GENERATED_MARKER = "Auto-generated by g-hk-vault-reindex"

# Reserved index/log names, matched case-insensitively (T1632). `_index.md`
# is the legacy per-subdir MOC view emitted by the retired gen_vault_moc.py —
# an index artifact, never a note.
EXCLUDED_INDEX_NAMES = {"_index.yaml", "index.md", "_index.md", "log.md", "vault_schema.md"}

# Markers identifying a legacy gen_vault_moc.py `_INDEX.md` view (T1632 /
# WS-B-9). Only `_INDEX.md`-named files carrying one of these (or
# GENERATED_MARKER) in their head are removed on regen — anything else named
# `_INDEX.md` is left alone (just never indexed as a note).
LEGACY_MOC_MARKERS = ("gen_vault_moc", "auto_generated: true")


def _in_hidden_dir(vault_path: Path, candidate: Path) -> bool:
    """True when a directory component BELOW the vault root starts with '.'.

    Hidden directories (`.obsidian/`, `.git/`, `.cursor/`, `.gald3r_sys/`,
    `.backups/`, ...) hold framework infrastructure, never vault notes
    (T1632 / WS-B-9). Only components below the vault root count, so a vault
    that itself lives under a dot-directory (the default `.gald3r/vault`
    fallback) is not excluded. Fails toward exclusion on unrelatable paths.
    """
    try:
        rel_parts = candidate.relative_to(vault_path).parts
    except ValueError:
        return True
    return any(part.startswith(".") for part in rel_parts[:-1])


def scan_note_files(vault_path: Path) -> List[Path]:
    """List indexable vault notes (recursive, minus hidden dirs + reserved files)."""
    return sorted(
        (
            f for f in vault_path.rglob("*.md")
            if f.is_file()
            and not _in_hidden_dir(vault_path, f)
            and f.name.lower() not in EXCLUDED_INDEX_NAMES
        ),
        key=lambda f: str(f),
    )


def _legacy_moc_views(vault_path: Path) -> List[Path]:
    """Marker-carrying legacy `_INDEX.md` MOC views awaiting cleanup (T1632).

    Only `_INDEX.md`-named files (outside hidden dirs) whose head carries a
    generated marker qualify — hand-written files of the same name are never
    returned. Their presence makes the index stale (the regen unifies them
    into the per-directory index.md views and removes them).
    """
    views: List[Path] = []
    for candidate in vault_path.rglob("*.md"):
        if candidate.name.lower() != "_index.md":
            continue
        if not candidate.is_file() or _in_hidden_dir(vault_path, candidate):
            continue
        try:
            head = candidate.read_text(encoding="utf-8-sig", errors="replace")[:800]
        except OSError:
            continue
        if any(m in head for m in (GENERATED_MARKER,) + LEGACY_MOC_MARKERS):
            views.append(candidate)
    return views


def index_is_fresh(index_yaml_path: Path, index_md_path: Path, files: List[Path]) -> bool:
    """Debounce check (T1627): True when a regen would be redundant.

    Fresh = both artifacts exist, the note count recorded in _index.yaml
    matches the current scan, no legacy `_INDEX.md` MOC views are awaiting
    unification (T1632), and no note's mtime is >= _index.yaml's mtime.
    Any parse/stat failure counts as stale (fail toward regenerating).
    """
    if not index_yaml_path.is_file() or not index_md_path.is_file():
        return False
    try:
        index_mtime = index_yaml_path.stat().st_mtime
        header = index_yaml_path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False
    m = re.search(r"^# Total notes:\s*(\d+)\s*$", header, re.MULTILINE)
    if not m or int(m.group(1)) != len(files):
        return False
    if _legacy_moc_views(index_yaml_path.parent):
        return False
    try:
        return all(f.stat().st_mtime < index_mtime for f in files)
    except OSError:
        return False


def _link_url(relative_path: str) -> str:
    """Percent-encode a vault-relative path for a markdown link target."""
    return quote(relative_path, safe="/")


def _one_line_description(entry: Dict[str, Any]) -> str:
    """Derive the OKF bullet's one-line description for a note entry."""
    desc = str(entry.get("description") or "").strip().strip("\"'")
    if not desc:
        kind = entry.get("ingestion_type") or entry.get("type") or "note"
        desc = f"{kind} ({entry['date']})" if entry.get("date") else str(kind)
    desc = re.sub(r"\s+", " ", desc)
    if len(desc) > 160:
        desc = desc[:157].rstrip() + "..."
    return desc


def relative_dirs_with_notes(entries: List[Dict[str, Any]]) -> Set[str]:
    """Vault-relative dirs (posix, '' = root) needing an index.md view.

    Includes every directory holding a note directly PLUS all of its
    ancestors, so intermediate directories link down to their children
    (progressive disclosure). The root is always included.
    """
    all_dirs: Set[str] = {""}
    for entry in entries:
        d = posixpath.dirname(entry["path"])
        while d:
            all_dirs.add(d)
            d = posixpath.dirname(d)
    return all_dirs


def build_okf_index_lines(
    rel_dir: str,
    entries: List[Dict[str, Any]],
    timestamp: str,
    all_dirs: Set[str],
) -> List[str]:
    """Build one directory's OKF-style index.md lines (no trailing newline)."""
    prefix = rel_dir + "/" if rel_dir else ""
    subtree = [e for e in entries if e["path"].startswith(prefix)] if rel_dir else entries
    direct = [e for e in subtree if posixpath.dirname(e["path"]) == rel_dir]
    children = sorted(d for d in all_dirs if d and posixpath.dirname(d) == rel_dir)

    lines: List[str] = []
    lines.append("# Vault Index" if not rel_dir else f"# {rel_dir}")
    lines.append("")
    lines.append(
        f"{GENERATED_MARKER} on {timestamp}. Derived view of `_index.yaml`"
        " (the machine source of truth) - do not edit by hand."
        f" Notes in this section: {len(subtree)}."
    )
    lines.append("")

    if children:
        lines.append("# Sections")
        lines.append("")
        for child in children:
            child_name = posixpath.basename(child)
            count = sum(1 for e in entries if e["path"].startswith(child + "/"))
            noun = "note" if count == 1 else "notes"
            lines.append(
                f"* [{child_name}/]({_link_url(child_name + '/index.md')})"
                f" - {count} {noun}"
            )
        lines.append("")

    if direct:
        lines.append("# Notes")
        lines.append("")
        for entry in sorted(direct, key=lambda e: str(e["title"]).lower()):
            name = posixpath.basename(entry["path"])
            lines.append(
                f"* [{entry['title']}]({_link_url(name)})"
                f" - {_one_line_description(entry)}"
            )
        lines.append("")

    if not rel_dir and entries:
        lines.append("# Recent Updates")
        lines.append("")
        for entry in sorted(entries, key=lambda e: e["date"], reverse=True)[:10]:
            lines.append(
                f"* [{entry['title']}]({_link_url(entry['path'])})"
                f" - updated {entry['date']}"
            )
        lines.append("")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild the vault _index.yaml and index.md from vault notes."
    )
    parser.add_argument(
        "-VaultOverride", "--vault-override", dest="vault_override", default="",
        help="Explicit vault path (skips g-hk-vault-resolve).",
    )
    parser.add_argument(
        "-ForceRun", "--force-run", dest="force_run", action="store_true",
        help="Bypass the once-per-session idempotency guard.",
    )
    args = parser.parse_args(argv)

    # -- Idempotency guard -----------------------------------------------------
    if not args.force_run and os.environ.get("GALD3R_HK_VAULT_REINDEX_APPLIED") == "1":
        print("[SKIP] g-hk-vault-reindex already applied this session. Pass -ForceRun to override.")
        return 0
    os.environ["GALD3R_HK_VAULT_REINDEX_APPLIED"] = "1"

    if args.vault_override:
        vault_path = Path(args.vault_override)
    else:
        vault_path = Path(load_resolve_context()["VaultPath"])

    vault_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    index_yaml_path = vault_path / "_index.yaml"
    index_md_path = vault_path / "index.md"

    files = scan_note_files(vault_path)

    # -- Debounce (T1627): skip redundant regens on rapid successive Stops ------
    if not args.force_run and index_is_fresh(index_yaml_path, index_md_path, files):
        print(
            "[SKIP] g-hk-vault-reindex: vault index up to date (debounced)."
            " Pass -ForceRun to rebuild."
        )
        return 0

    entries: List[Dict[str, Any]] = []
    for file in files:
        try:
            raw = file.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if not raw:
            continue

        relative_path = str(file)[len(str(vault_path)):].lstrip("\\/").replace("\\", "/")
        fm = _parse_frontmatter(raw)
        title = fm.get("title", "")
        note_type = fm.get("type", "")
        description = fm.get("description", "").strip("\"'")
        date = fm.get("date", "")
        tags = fm.get("tags", [])
        source = fm.get("source", "")
        ingestion_type = fm.get("ingestion_type", "")
        project_id = fm.get("project_id", "null")
        refresh_policy = fm.get("refresh_policy", "")
        refresh_after = fm.get("next_refresh", "")
        expires_after = fm.get("expires_after", "")

        if not title:
            heading = next(
                (line for line in raw.split("\n") if re.match(r"^#\s+", line)), None
            )
            if heading:
                title = re.sub(r"^#+\s*", "", heading).strip()
            else:
                title = file.stem

        if not date:
            mtime = datetime.datetime.fromtimestamp(
                file.stat().st_mtime, tz=datetime.timezone.utc
            )
            date = mtime.strftime("%Y-%m-%d")

        if not ingestion_type and note_type:
            ingestion_type = note_type

        entries.append({
            "path": relative_path,
            "title": title,
            "type": note_type,
            "ingestion_type": ingestion_type,
            "date": date,
            "description": description,
            "tags": tags,
            "source": source,
            "project_id": project_id,
            "refresh_policy": refresh_policy,
            "next_refresh": refresh_after,
            "expires_after": expires_after,
        })

    yaml_header = [
        "# Vault Index - auto-generated by g-hk-vault-reindex",
        f"# Last updated: {timestamp}",
        f"# Total notes: {len(entries)}",
        "notes:",
    ]

    yaml_lines: List[str] = []
    for entry in entries:
        tags_string = "[" + ", ".join(entry["tags"]) + "]"
        escaped_title = entry["title"].replace('"', '\\"')
        yaml_lines.append(f"  - path: {entry['path']}")
        yaml_lines.append(f"    title: \"{escaped_title}\"")
        yaml_lines.append(f"    type: {entry['type']}")
        yaml_lines.append(f"    ingestion_type: {entry['ingestion_type']}")
        yaml_lines.append(f"    date: {entry['date']}")
        yaml_lines.append(f"    tags: {tags_string}")
        yaml_lines.append(f"    source: {entry['source']}")
        yaml_lines.append(f"    project_id: {entry['project_id']}")
        if entry["refresh_policy"]:
            yaml_lines.append(f"    refresh_policy: {entry['refresh_policy']}")
        if entry["next_refresh"]:
            yaml_lines.append(f"    next_refresh: {entry['next_refresh']}")
        if entry["expires_after"]:
            yaml_lines.append(f"    expires_after: {entry['expires_after']}")

    with index_yaml_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\r\n".join(yaml_header + yaml_lines))

    # -- OKF-style index.md views: one per directory holding notes (T1627) ------
    all_dirs = relative_dirs_with_notes(entries)
    generated: Set[Path] = set()
    for rel_dir in sorted(all_dirs):
        lines = build_okf_index_lines(rel_dir, entries, timestamp, all_dirs)
        target = index_md_path if not rel_dir else vault_path / rel_dir / "index.md"
        with target.open("w", encoding="utf-8", newline="") as fh:
            fh.write("\r\n".join(lines))
        generated.add(target.resolve())

    # Remove stale generated views (directories that no longer hold notes).
    # Only files carrying GENERATED_MARKER are ever deleted — hand-written
    # index.md files are left alone. Hidden directories are never touched
    # (they are outside the scan, so any views there are not ours; T1632).
    for stale in vault_path.rglob("*.md"):
        if stale.name.lower() != "index.md" or _in_hidden_dir(vault_path, stale):
            continue
        try:
            resolved = stale.resolve()
        except OSError:
            continue
        if resolved in generated:
            continue
        try:
            head = stale.read_text(encoding="utf-8-sig", errors="replace")[:800]
        except OSError:
            continue
        if GENERATED_MARKER in head:
            try:
                stale.unlink()
            except OSError:
                pass

    # Unify legacy per-subdir `_INDEX.md` MOC views into this regen (T1632 /
    # WS-B-9): the retired gen_vault_moc.py per-subdir indexes are replaced
    # by the per-directory index.md views above, so marker-carrying copies
    # are removed. Hand-written `_INDEX.md` files are never touched.
    for legacy in _legacy_moc_views(vault_path):
        try:
            legacy.unlink()
        except OSError:
            pass

    print(
        f"Vault index updated at {vault_path}"
        f" ({len(entries)} notes, {len(generated)} index.md views)"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        sys.exit(0)
