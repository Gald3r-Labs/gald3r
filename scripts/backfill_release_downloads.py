#!/usr/bin/env python3
"""Prepend the download block to release notes that were published without one.

Release notes cut before the block existed point at nothing downloadable -- the
files are on Gald3r-Labs/gald3r_core and the note never said so. This walks every
release on this repo and prepends the block from release_download_block.py.

Idempotent: a note that already carries the marker is left untouched, so this is
safe to re-run after any future gap.

    python scripts/backfill_release_downloads.py            # dry run
    python scripts/backfill_release_downloads.py --apply
    python scripts/backfill_release_downloads.py --only v5.0.0-beta.51 --apply
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from release_download_block import MARKER, build_block, core_assets  # noqa: E402

LANDING = "Gald3r-Labs/gald3r"


def _gh_json(*args: str):
    r = subprocess.run(["gh", *args], capture_output=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.decode("utf-8", "replace") or "null")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="Write. Without this it is a dry run.")
    ap.add_argument("--limit", type=int, default=200, help="How many releases to walk.")
    ap.add_argument("--only", help="Operate on this tag only.")
    args = ap.parse_args(argv)

    releases = _gh_json("release", "list", "--repo", LANDING, "--limit", str(args.limit), "--json", "tagName")
    if not releases:
        print(f"could not list releases on {LANDING}", file=sys.stderr)
        return 2

    tags = [r["tagName"] for r in releases]
    if args.only:
        tags = [t for t in tags if t == args.only]
        if not tags:
            print(f"no release tagged {args.only}", file=sys.stderr)
            return 2

    changed = skipped = historical = failed = 0
    for tag in tags:
        body = (_gh_json("release", "view", tag, "--repo", LANDING, "--json", "body") or {}).get("body", "")
        if MARKER in body:
            skipped += 1
            continue

        assets = core_assets(tag)
        if assets is None:
            historical += 1
        block = build_block(tag, assets)
        shape = "historical" if assets is None else f"{len(assets)} assets"

        if not args.apply:
            print(f"  {tag:<20} {shape:<12} would prepend {len(block)} chars")
            changed += 1
            continue

        # --notes-file, never --notes: the block carries em dashes and middots,
        # and passing those through argv on Windows mangles them.
        tmp = pathlib.Path(tempfile.gettempdir()) / f"gald3r_relnotes_{tag.replace('/', '_')}.md"
        tmp.write_text(block + (body or ""), encoding="utf-8", newline="\n")
        r = subprocess.run(["gh", "release", "edit", tag, "--repo", LANDING, "--notes-file", str(tmp)],
                           capture_output=True, text=True)
        tmp.unlink(missing_ok=True)
        if r.returncode == 0:
            changed += 1
            print(f"  {tag:<20} {shape:<12} OK")
        else:
            failed += 1
            print(f"  {tag:<20} {shape:<12} FAILED: {r.stderr.strip()[:140]}")

    verb = "APPLIED" if args.apply else "DRY RUN"
    print(f"\n{verb}: {changed} changed, {skipped} already had the block, "
          f"{historical} historical (no matching engine release), {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
