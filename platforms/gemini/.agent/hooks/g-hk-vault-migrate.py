#!/usr/bin/env python3
"""Python port of g-hk-vault-migrate.ps1 (T1584).

Migrates vault notes from a source vault (default: the local
`.gald3r/vault/`) into a destination vault (default: the resolved shared
vault), then triggers a reindex of the destination:

- `log.md` files are merged block-wise (split on `## ` headings, dedup,
  destination blocks first).
- Other files are copied when missing at the destination, skipped when the
  SHA256 hashes match, and otherwise resolved by frontmatter `date:` (or
  file mtime): newer-or-equal source wins; older source is kept at the
  destination and reported as a conflict. -Force always overwrites.

Registered on the canonical `session-start` event with `--if-diverged`
(T1627 / WS-A-4): in that mode the hook consults g-hk-vault-resolve's
divergence signal (`VaultMigrationCandidate` — the local `.gald3r/vault/`
holds markdown notes while a DIFFERENT shared vault_location is configured
and writable) and no-ops unless it is set, so the migration fires only on
actual vault_location divergence. Wired in `g_hk_core.py`
CONCERN_CHAIN["session-start"], Claude `settings.json` `hooks.SessionStart`,
and Cursor `hooks.json` `sessionStart`.

Session-idempotent via GALD3R_HK_VAULT_MIGRATE_APPLIED (override with
-ForceRun). Cross-script calls use the .py siblings only
(g-hk-vault-resolve.py / g-hk-vault-reindex.py) — the .ps1 fallback
branches were removed once .ps1-only installs went EOL (T1600). Exit
codes: 0 on success/no-op, 1 when the source path does not exist
(preserved from the original .ps1).
"""
# @subsystems: VAULT_AND_RESEARCH
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402,F401

_HOOK_DIR = Path(__file__).resolve().parent


def load_resolve_context() -> Dict[str, Any]:
    """Load vault paths from the g-hk-vault-resolve sibling (.py, imported in-process)."""
    py_sibling = _HOOK_DIR / "g-hk-vault-resolve.py"
    spec = importlib.util.spec_from_file_location("g_hk_vault_resolve", str(py_sibling))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.resolve()


def run_reindex(destination: str) -> None:
    """Invoke the g-hk-vault-reindex sibling (.py) for the destination vault.

    Output is suppressed (matches `| Out-Null`).
    """
    py_sibling = _HOOK_DIR / "g-hk-vault-reindex.py"
    cmd = [sys.executable, str(py_sibling), "-VaultOverride", destination]
    subprocess.run(cmd, capture_output=True, timeout=600)


def get_file_hash_safe(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest().upper()
    except OSError:
        return None


def _parse_date_loose(text: str) -> Optional[datetime.datetime]:
    text = text.strip()
    try:
        parsed = datetime.datetime.fromisoformat(text)
        return parsed.replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def get_note_date(path: Path) -> datetime.datetime:
    """Frontmatter `date:` when parseable, else the file's UTC mtime.

    Missing files return datetime.min (matches [datetime]::MinValue)."""
    if not path.is_file():
        return datetime.datetime.min
    try:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        fm = re.match(r"^---\r?\n(.+?)\r?\n---", raw, re.DOTALL)
        if fm:
            dm = re.search(r"^date:\s*(.+)$", fm.group(1), re.MULTILINE)
            if dm:
                parsed = _parse_date_loose(dm.group(1))
                if parsed is not None:
                    return parsed
    except OSError:
        pass
    return datetime.datetime.utcfromtimestamp(path.stat().st_mtime)


def merge_log_file(source_log: Path, destination_log: Path) -> None:
    """Merge `## `-headed blocks from destination + source, dedup, rewrite."""
    blocks: List[str] = []
    for path in (destination_log, source_log):
        if path.is_file():
            try:
                raw = path.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            if raw:
                for chunk in re.split(r"(?m)(?=^## )", raw):
                    block = chunk.strip()
                    if block:
                        blocks.append(block)

    merged = list(dict.fromkeys(blocks))  # unique, first occurrence wins
    if merged:
        with destination_log.open("w", encoding="utf-8", newline="") as fh:
            fh.write("\r\n\r\n".join(merged) + "\r\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate vault notes from a source vault into the destination vault."
    )
    parser.add_argument(
        "-SourcePath", "--source-path", dest="source_path", default="",
        help="Source vault path (default: local .gald3r/vault/).",
    )
    parser.add_argument(
        "-DestinationPath", "--destination-path", dest="destination_path", default="",
        help="Destination vault path (default: resolved shared vault).",
    )
    parser.add_argument(
        "-Force", "--force", dest="force", action="store_true",
        help="Always overwrite destination files on hash mismatch.",
    )
    parser.add_argument(
        "-ForceRun", "--force-run", dest="force_run", action="store_true",
        help="Bypass the once-per-session idempotency guard.",
    )
    parser.add_argument(
        "-IfDiverged", "--if-diverged", dest="if_diverged", action="store_true",
        help=(
            "Lifecycle-hook mode (T1627): only migrate when g-hk-vault-resolve"
            " reports vault_location divergence (VaultMigrationCandidate);"
            " otherwise no-op. Used by the session-start registration."
        ),
    )
    args = parser.parse_args(argv)

    # -- Idempotency guard -----------------------------------------------------
    if not args.force_run and os.environ.get("GALD3R_HK_VAULT_MIGRATE_APPLIED") == "1":
        print("[SKIP] g-hk-vault-migrate already applied this session. Pass -ForceRun to override.")
        return 0
    os.environ["GALD3R_HK_VAULT_MIGRATE_APPLIED"] = "1"

    source_path = args.source_path
    destination_path = args.destination_path
    ctx: Dict[str, Any] = {}
    if args.if_diverged or not source_path or not destination_path:
        ctx = load_resolve_context()

    # -- Divergence gate (T1627 / WS-A-4) ---------------------------------------
    # At session-start the migration must fire ONLY when the local vault has
    # content while a different shared vault is configured and writable.
    if args.if_diverged and not ctx.get("VaultMigrationCandidate"):
        print(
            "[SKIP] g-hk-vault-migrate: no vault_location divergence"
            " (nothing to migrate)."
        )
        return 0

    if not source_path:
        source_path = ctx["VaultLocalPath"]
    if not destination_path:
        destination_path = ctx["VaultPath"]

    if source_path == destination_path:
        print("Source and destination are the same. Nothing to migrate.")
        return 0

    source = Path(source_path)
    destination = Path(destination_path)

    if not source.exists():
        print(f"Source path does not exist: {source_path}")
        return 1

    destination.mkdir(parents=True, exist_ok=True)

    copied = 0
    updated = 0
    skipped = 0
    conflicts: List[str] = []

    source_files = sorted(
        (f for f in source.rglob("*") if f.is_file() and ".obsidian" not in f.parts),
        key=lambda f: str(f),
    )

    for file in source_files:
        relative_path = str(file)[len(str(source)):].lstrip("\\/")
        target_path = destination / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if file.name == "log.md":
            merge_log_file(file, target_path)
            continue

        source_hash = get_file_hash_safe(file)
        target_hash = get_file_hash_safe(target_path)

        if not target_hash:
            shutil.copy2(str(file), str(target_path))
            copied += 1
            continue

        if source_hash == target_hash:
            skipped += 1
            continue

        source_date = get_note_date(file)
        target_date = get_note_date(target_path)

        if args.force or source_date >= target_date:
            shutil.copy2(str(file), str(target_path))
            updated += 1
        else:
            skipped += 1
            conflicts.append(relative_path)

    run_reindex(str(destination))

    print("Vault migration summary")
    print(f"  source: {source_path}")
    print(f"  destination: {destination_path}")
    print(f"  copied: {copied}")
    print(f"  updated: {updated}")
    print(f"  skipped: {skipped}")
    if conflicts:
        print("  conflicts kept at destination:")
        for conflict in conflicts:
            print(f"    - {conflict}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        sys.exit(0)
