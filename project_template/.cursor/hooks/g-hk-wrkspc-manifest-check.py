#!/usr/bin/env python3
"""Python port of g-hk-wrkspc-manifest-check.ps1 (T1584).

Read-only Workspace-Control manifest preflight for g-wrkspc commands.
Validates that the canonical manifest exists and can be parsed as basic
YAML-like text. Deep schema validation belongs to g-skl-workspace VALIDATE.

Exit codes: 0 = pass / inactive, 2 = preflight failure (missing-with
-RequireManifest, empty manifest, or missing top-level keys).
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; pure-stdlib path used here)

REQUIRED_KEYS = [
    "schema:",
    "workspace:",
    "repositories:",
    "controlled_members:",
    "routing_policy:",
    "wpac_relationship:",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Workspace-Control manifest preflight for g-wrkspc commands."
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root",
        default=os.getcwd(),
        help="Project root (default: current directory)",
    )
    parser.add_argument(
        "-RequireManifest", "--require-manifest", dest="require_manifest",
        action="store_true",
        help="Exit 2 when the manifest is missing instead of reporting inactive",
    )
    parser.add_argument(
        "-ForceRun", "--force-run", dest="force_run", action="store_true",
        help="Override the per-session idempotency guard",
    )
    args = parser.parse_args()

    # -- Idempotency guard -----------------------------------------------------
    if not args.force_run and os.environ.get("GALD3R_HK_WRKSPC_MANIFEST_CHECK_APPLIED") == "1":
        print("[SKIP] g-hk-wrkspc-manifest-check already applied this session. Pass -ForceRun to override.")
        return 0
    os.environ["GALD3R_HK_WRKSPC_MANIFEST_CHECK_APPLIED"] = "1"

    manifest_path = Path(args.project_root) / ".gald3r" / "linking" / "workspace_manifest.yaml"

    if not manifest_path.exists():
        if args.require_manifest:
            print("Workspace-Control: inactive (missing .gald3r/linking/workspace_manifest.yaml)")
            return 2
        print("Workspace-Control: inactive")
        return 0

    try:
        content = manifest_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        content = ""
    if not content.strip():
        print("Workspace-Control: manifest is empty")
        return 2

    missing = []
    for key in REQUIRED_KEYS:
        if not re.search(r"(?m)^" + re.escape(key), content):
            missing.append(key)

    if missing:
        print("Workspace-Control: manifest missing top-level key(s): " + ", ".join(missing))
        return 2

    print("Workspace-Control: manifest preflight passed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
