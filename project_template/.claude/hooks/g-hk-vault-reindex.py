#!/usr/bin/env python3
"""Python port of g-hk-vault-reindex.ps1 (T1584).

Rebuilds the vault index pair from the resolved vault directory:
  - `_index.yaml`: machine-readable note registry (path, title, type,
    ingestion_type, date, tags, source, project_id, refresh metadata)
  - `index.md`: human-readable summary grouped by type plus the 10 most
    recent updates

Scans `*.md` recursively, excluding `.obsidian/` contents and the index/log
schema files themselves. Frontmatter fields are parsed leniently; title falls
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
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

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

    excluded_names = {"_index.yaml", "index.md", "log.md", "VAULT_SCHEMA.md"}
    files = sorted(
        (
            f for f in vault_path.rglob("*.md")
            if f.is_file()
            and ".obsidian" not in f.parts
            and f.name not in excluded_names
        ),
        key=lambda f: str(f),
    )

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
            "tags": tags,
            "source": source,
            "project_id": project_id,
            "refresh_policy": refresh_policy,
            "next_refresh": refresh_after,
            "expires_after": expires_after,
        })

    yaml_header = [
        "# Vault Index - auto-generated by g-hk-vault-reindex.ps1",
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

    type_names = sorted({e["type"] for e in entries})
    recent_entries = sorted(entries, key=lambda e: e["date"], reverse=True)[:10]

    index_md: List[str] = []
    index_md.append("# Vault Index")
    index_md.append("")
    index_md.append(f"Generated: {timestamp}")
    index_md.append("")
    index_md.append("## Summary")
    index_md.append("")
    index_md.append(f"- Total notes: {len(entries)}")
    index_md.append("")

    for type_name in type_names:
        index_md.append(f"## {type_name}")
        index_md.append("")
        group = sorted(
            (e for e in entries if e["type"] == type_name), key=lambda e: e["title"]
        )
        for entry in group:
            # Porting note: the .ps1 used `${($entry.path -replace ...)}` which
            # PowerShell treats as an (empty) braced variable name; the Python
            # port emits the intended `[[path|title]]` wikilink instead.
            link_target = re.sub(r"\.md$", "", entry["path"])
            index_md.append(f"- [[{link_target}|{entry['title']}]]")
        index_md.append("")

    index_md.append("## Recent Updates")
    index_md.append("")
    for entry in recent_entries:
        link_target = re.sub(r"\.md$", "", entry["path"])
        index_md.append(f"- {entry['date']} - [[{link_target}|{entry['title']}]]")
    index_md.append("")

    with index_md_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("\r\n".join(index_md))

    print(f"Vault index updated at {vault_path} ({len(entries)} notes)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        sys.exit(0)
