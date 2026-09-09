"""Workflow-local read-only metadata check; full asset/hash validation is upstream.

The unified private release pipeline is the single release writer. This public
check neither publishes a draft nor changes its notes, assets or release flags.
"""

import argparse
import json
import re
import subprocess
import sys

REPOSITORY = "Gald3r-Labs/gald3r"
MIRROR_START = (5, 0, 54)


def version_tuple(tag):
    match = re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[A-Za-z0-9.-]+)?", tag)
    if not match:
        raise ValueError("Expected a release tag such as v5.0.54")
    return tuple(int(part) for part in match.groups())


def check_metadata(tag, pages):
    version = version_tuple(tag)
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise ValueError("Malformed release-list response")
    matches = [release for page in pages for release in page
               if isinstance(release, dict) and release.get("tag_name") == tag]
    if len(matches) != 1:
        raise ValueError("Expected one existing release; stage it upstream, then rerun this check")
    release = matches[0]
    if type(release.get("draft")) is not bool:
        raise ValueError("Existing release has invalid draft state")
    body = release.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("Existing release has no notes")
    if version >= MIRROR_START:
        assets = release.get("assets")
        if not isinstance(assets, list) or not any(
            isinstance(asset, dict) and asset.get("name") == "SHA256SUMS.txt"
            and asset.get("state") == "uploaded" and type(asset.get("size")) is int
            and asset["size"] > 0 for asset in assets
        ):
            raise ValueError("Mirrored release is missing uploaded checksum metadata")
        if f"https://github.com/{REPOSITORY}/releases/download/{tag}/" not in body:
            raise ValueError("Mirrored release notes lack same-repository, same-tag download links")
    return "draft" if release.get("draft") is True else "published"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args(argv)
    try:
        version_tuple(args.tag)
        # Authenticated pagination can include this repository's drafts; the
        # by-tag API endpoint can hide a draft. No write method is ever used.
        result = subprocess.run(
            ["gh", "api", "--hostname", "github.com", "--method", "GET",
             f"repos/{REPOSITORY}/releases?per_page=100", "--paginate", "--slurp"],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        if result.returncode:
            raise ValueError("Release metadata is unavailable; verify read permission and retry")
        state = check_metadata(args.tag, json.loads(result.stdout))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Release metadata check failed: {exc}", file=sys.stderr)
        return 1
    print(f"{args.tag}: {state} metadata checked; no release was changed. Full inventory and hashes remain the upstream gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
