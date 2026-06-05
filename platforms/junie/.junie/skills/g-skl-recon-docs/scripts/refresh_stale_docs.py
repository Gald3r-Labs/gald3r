#!/usr/bin/env python3
"""
refresh_stale_docs.py — gald3r stale docs refresher.
Scans research/platforms/_index.yaml and re-fetches all stale entries.

Usage:
    python refresh_stale_docs.py --vault-path PATH [--dry-run] [--no-js] [--count-only]
"""

import argparse
import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("SETUP_REQUIRED: PyYAML not installed — run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


INDEX_FILE = "_index.yaml"


def _load_ingest_doc():
    """Load sibling ingest_doc.py for shared write_note / platform tagging."""
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("ingest_doc_mod", here / "ingest_doc.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def find_crawl_script():
    current = Path(__file__).resolve()
    for _ in range(8):
        candidate = current / ".cursor" / "skills" / "g-skl-crawl" / "scripts" / "crawl_url.py"
        if candidate.exists():
            return str(candidate)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return str(Path(__file__).parent.parent.parent.parent / ".cursor" / "skills" / "g-skl-crawl" / "scripts" / "crawl_url.py")


def load_index(platforms_dir: Path) -> list:
    index_path = platforms_dir / INDEX_FILE
    if not index_path.exists():
        return []
    with open(index_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def save_index(platforms_dir: Path, index: list):
    index_path = platforms_dir / INDEX_FILE
    with open(index_path, "w", encoding="utf-8") as f:
        yaml.dump(index, f, default_flow_style=False, allow_unicode=True)


def is_stale(entry: dict) -> bool:
    nr = entry.get("next_refresh", "")
    if not nr:
        return True
    try:
        return datetime.today().date() >= datetime.strptime(nr, "%Y-%m-%d").date()
    except ValueError:
        return True


def crawl_and_update(entry: dict, vault_path: str, no_js: bool, crawl_script: str, ingest_mod):
    url = entry["url"]
    out_rel = entry.get("vault_path", "")
    out_path = Path(vault_path) / out_rel if out_rel else Path(vault_path) / "research" / "platforms" / f"{entry['slug']}.md"

    cmd = [sys.executable, crawl_script, "--url", url, "--output", str(out_path)]
    if no_js:
        cmd.append("--no-js")
    result = subprocess.run(cmd, capture_output=True, text=True)

    today = datetime.today().strftime("%Y-%m-%d")
    refresh_days = entry.get("refresh_days", 30)
    next_refresh = (datetime.today() + timedelta(days=refresh_days)).strftime("%Y-%m-%d")

    if result.returncode == 0:
        raw_markdown = out_path.read_text(encoding="utf-8")
        plat = entry.get("platform")  # optional future index field
        ingest_mod.write_note(
            out_path,
            url,
            entry.get("name", entry.get("slug", "docs")),
            refresh_days,
            raw_markdown,
            platform=plat,
        )
        entry["last_fetched"] = today
        entry["next_refresh"] = next_refresh
        entry["status"] = "fresh"
        return True
    else:
        entry["status"] = "error"
        return False


def main():
    parser = argparse.ArgumentParser(description="Refresh stale documentation entries in the vault")
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--dry-run", action="store_true", help="List stale URLs without fetching")
    parser.add_argument("--no-js", action="store_true")
    parser.add_argument("--count-only", action="store_true", help="Print stale count only (for session hooks)")
    args = parser.parse_args()

    platforms_dir = Path(args.vault_path) / "research" / "platforms"
    if not platforms_dir.exists():
        if args.count_only:
            print("0")
        else:
            print("No research/platforms/ directory found — nothing to refresh")
        return

    index = load_index(platforms_dir)
    stale = [e for e in index if is_stale(e)]

    if args.count_only:
        print(str(len(stale)))
        return

    if not stale:
        print("All docs are fresh.")
        return

    print(f"Stale docs: {len(stale)} / {len(index)}")

    if args.dry_run:
        for e in stale:
            print(f"  STALE  {e['url']}  (last: {e.get('last_fetched', 'never')})")
        return

    crawl_script = find_crawl_script()
    ingest_mod = _load_ingest_doc()
    ok, fail = 0, 0
    for entry in stale:
        print(f"  Refreshing: {entry['url']}", end=" ", flush=True)
        if crawl_and_update(entry, args.vault_path, args.no_js, crawl_script, ingest_mod):
            print("OK")
            ok += 1
        else:
            print("FAIL")
            fail += 1

    save_index(platforms_dir, index)
    print(f"\nRefreshed {ok} / {len(stale)} stale docs ({fail} failed)")

    # After batch refresh, regenerate MOC hubs (T045 / g-platform-crawl)
    if ok > 0:
        moc_script = None
        here = Path(__file__).resolve()
        for depth in range(2, 12):
            if depth >= len(here.parents):
                break
            cand = here.parents[depth] / "scripts" / "gen_vault_moc.py"
            if cand.is_file():
                moc_script = cand
                break
        if moc_script and moc_script.exists():
            r = subprocess.run(
                [sys.executable, str(moc_script), "--vault-path", args.vault_path, "--auto"],
                capture_output=True,
                text=True,
            )
            if r.returncode == 0:
                print(r.stdout.strip())
            else:
                print("MOC_GEN_WARNING:", r.stderr or r.stdout, file=sys.stderr)

    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
