#!/usr/bin/env python3
"""Generate the "Download" block that heads every gald3r release note.

This repo carries release NOTES; the engine repo (Gald3r-Labs/gald3r_core) carries
the FILES. Before this existed, anyone who clicked a release here found notes and
nothing to download -- the assets were one repo away with no signpost.

The block is built from the matching gald3r_core release's ACTUAL asset list, so it
can never link to a file that is not on that release. A tag with no matching engine
release (everything before the Go rewrite) gets a pointer to the newest release
instead of a dead link.

Two callers share this one generator (do not fork the logic):
  - .github/workflows/release.yml, which prepends it at cut time
  - scripts/backfill_release_downloads.py, which fills it in on past releases

Usage:
    python scripts/release_download_block.py v5.0.0-beta.51 [--out header.md]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

CORE = "Gald3r-Labs/gald3r_core"
MARKER = "<!-- gald3r:downloads-block -->"
TAG_URL = f"https://github.com/{CORE}/releases/tag/{{tag}}"
DL_URL = f"https://github.com/{CORE}/releases/download/{{tag}}/{{asset}}"
LATEST_URL = f"https://github.com/{CORE}/releases/latest"


def core_assets(tag: str) -> list[str] | None:
    """Asset names on the gald3r_core release for `tag`, or None if there is none."""
    r = subprocess.run(
        ["gh", "release", "view", tag, "--repo", CORE, "--json", "assets"],
        capture_output=True,
    )
    if r.returncode != 0:
        return None
    try:
        return [a["name"] for a in json.loads(r.stdout.decode("utf-8", "replace"))["assets"]]
    except (ValueError, KeyError):
        return None


def _pick(assets: list[str], *needles: str, exclude: tuple[str, ...] = ()) -> str | None:
    """First asset containing every needle and none of `exclude` (case-insensitive)."""
    for name in assets:
        low = name.lower()
        if all(n in low for n in needles) and not any(x in low for x in exclude):
            return name
    return None


def _link(tag: str, asset: str, label: str | None = None) -> str:
    return f"[{label or asset}]({DL_URL.format(tag=tag, asset=asset)})"


def build_block(tag: str, assets: list[str] | None) -> str:
    """The markdown block to prepend to `tag`'s release notes."""
    if assets is None:
        return (
            f"{MARKER}\n"
            "## Download\n\n"
            f"`{tag}` predates the current engine repo, so it has no matching build.\n"
            f"For a version you can actually install, get the newest release: "
            f"**[Download gald3r]({LATEST_URL})**.\n\n"
            "---\n\n"
        )

    # `exclude` keeps the desktop apps out of the engine rows -- gald3r_ide and
    # Throne ship on the same release and share several of these substrings.
    apps = ("throne", "_ide")
    win_installer = _pick(assets, "windows", ".msi") or _pick(assets, "windows", ".exe", exclude=apps)
    win_portable = _pick(assets, "windows", ".zip")
    mac_arm = _pick(assets, "macos", "arm64", ".pkg") or _pick(
        assets, "macos", "arm64", ".tar.gz", exclude=apps + ("unsigned",))
    mac_intel = _pick(assets, "macos", "x86_64", ".pkg") or _pick(assets, "macos", "x86_64", ".tar.gz")
    linux = _pick(assets, "linux", ".tar.gz", exclude=apps) or _pick(assets, "linux", ".appimage")
    sums = _pick(assets, "sha256sums")

    out = [
        MARKER,
        "## Download",
        "",
        "This repo carries the release notes. The installers live on the engine repo:",
        "",
        f"### **[Download gald3r {tag} — all files]({TAG_URL.format(tag=tag)})**",
        "",
    ]

    rows: list[tuple[str, str]] = []
    if win_installer or win_portable:
        cells = [
            _link(tag, win_installer, "installer (.msi)") if win_installer else "",
            _link(tag, win_portable, "portable (.zip)") if win_portable else "",
        ]
        rows.append(("**Windows**", " · ".join(c for c in cells if c)))
    if mac_arm:
        rows.append(("**macOS** (Apple Silicon)", _link(tag, mac_arm)))
    if mac_intel:
        rows.append(("**macOS** (Intel)", _link(tag, mac_intel)))
    if linux:
        rows.append(("**Linux**", _link(tag, linux)))
    if rows:
        out += ["| OS | gald3r engine |", "|---|---|"]
        out += [f"| {os_} | {cell} |" for os_, cell in rows]
        out.append("")

    desktop: list[str] = []
    for label, token in (("Throne", "throne"), ("gald3r_ide", "_ide")):
        parts = [
            _link(tag, asset, os_name)
            for os_name, asset in (
                ("Windows", _pick(assets, token, "windows")),
                ("macOS", _pick(assets, token, "macos")),
                ("Linux", _pick(assets, token, "linux")),
            )
            if asset
        ]
        if parts:
            desktop.append(f"- **{label}** — " + " · ".join(parts))
    if desktop:
        out += ["**Desktop apps** (same version, same release):", ""] + desktop + [""]

    if sums:
        out += [f"Verify your download against {_link(tag, sums)}.", ""]

    out += ["---", ""]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tag", help="Release tag, e.g. v5.0.0-beta.51")
    ap.add_argument("--out", help="Write the block here instead of stdout.")
    args = ap.parse_args(argv)

    block = build_block(args.tag, core_assets(args.tag))
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(block)
        print(f"wrote download block for {args.tag} -> {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
