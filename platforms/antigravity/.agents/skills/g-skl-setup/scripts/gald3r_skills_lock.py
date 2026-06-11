#!/usr/bin/env python3
"""Python port of gald3r_skills_lock.ps1 (T1585).

Read/write/verify gald3r-skills-lock.json (T1043).

Lock-file management for installed gald3r projects. Operations:

  WRITE   - scan installed platform skill copies, compute SHA-256 hashes,
            write gald3r-skills-lock.json.
  VERIFY  - recompute hashes against current files, classify each skill
            as unchanged | tampered | missing. Exits 1 on tampered/missing.
  UPGRADE - recompute hashes; for each entry, compare against the
            canonical source under --source-root. Classify each skill as
            unchanged | local-modified | upstream-changed | both-changed
            | new (in source, not in lock) | removed (in lock, missing in source).
  READ    - print the parsed lock JSON to stdout.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO


# UTF-8-safe stdio on Windows consoles (the PS1 originals emit Unicode glyphs)
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _bootstrap_engine() -> bool:
    """Make ``gald3r.utils`` importable; fall back to the bundled engine source."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for parent in here.parents:
        engine_src = parent / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()
try:
    from gald3r.utils import console as _console
except ImportError:
    _console = None  # graceful stdlib fallback

_ANSI = {"cyan": "36", "green": "32", "yellow": "33", "red": "31"}
_ansi_ready = False

LOCK_VERSION = 1

# Platform skill directories to scan (in install priority order)
PLATFORM_DIRS = (".cursor/skills", ".claude/skills", ".agent/skills",
                 ".codex/skills", ".opencode/skills")


def _supports_color(stream: TextIO) -> bool:
    if _console is not None:
        return bool(_console.color_enabled(stream))
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def _say(msg: str = "", color: Optional[str] = None) -> None:
    global _ansi_ready
    code = _ANSI.get((color or "").lower())
    if code and _supports_color(sys.stdout):
        if os.name == "nt" and not _ansi_ready:
            os.system("")
            _ansi_ready = True
        print(f"\x1b[{code}m{msg}\x1b[0m")
    else:
        print(msg)


def get_gald3r_version(root: Path) -> str:
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return "unknown"
    content = changelog.read_text(encoding="utf-8-sig", errors="replace")
    match = re.search(r"(?m)^## \[(\d+\.\d+\.\d+[^\]]*)\]", content)
    if match:
        return match.group(1)
    return "unreleased"


def get_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def find_installed_skills(root: Path) -> Dict[str, Dict[str, Any]]:
    """First platform dir wins per slug (install priority order)."""
    found: Dict[str, Dict[str, Any]] = {}
    root_resolved = root.resolve()
    for rel_dir in PLATFORM_DIRS:
        base = root / Path(rel_dir)
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if not child.is_dir():
                continue
            skill_file = child / "SKILL.md"
            if skill_file.exists() and child.name not in found:
                rel_norm = skill_file.resolve().relative_to(
                    root_resolved).as_posix()
                found[child.name] = {
                    "slug": child.name,
                    "abs": skill_file,
                    "rel": rel_norm,
                }
    return found


def action_write(root: Path, lock_path: Path, tier_tag: str,
                 as_json: bool) -> int:
    skills = find_installed_skills(root)
    if not skills:
        _say("WARNING: No installed skills found under platform dirs: "
             + ", ".join(PLATFORM_DIRS), "yellow")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lock: Dict[str, Any] = {
        "version": LOCK_VERSION,
        "gald3r_version": get_gald3r_version(root),
        "installed_date": now,
        "tier": tier_tag,
        "skills": {},
    }

    for slug in sorted(skills):
        s = skills[slug]
        lock["skills"][slug] = {
            "source": "github:gald3r/gald3r",
            "path": s["rel"],
            "sha256_hash": get_file_sha256(s["abs"]),
            "tier": tier_tag,
            "installed_at": now,
        }

    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")

    if as_json:
        print(json.dumps({
            "action": "WRITE",
            "lock_path": str(lock_path),
            "skills_count": len(skills),
            "gald3r_version": lock["gald3r_version"],
            "tier": tier_tag,
        }, indent=2))
    else:
        _say(f"Wrote {lock_path}")
        _say(f"  gald3r_version : {lock['gald3r_version']}")
        _say(f"  tier           : {tier_tag}")
        _say(f"  skills hashed  : {len(skills)}")
    return 0


def _load_lock(lock_path: Path) -> Dict[str, Any]:
    if not lock_path.exists():
        raise FileNotFoundError(
            f"Lock file not found: {lock_path}. Run -Action WRITE first.")
    return json.loads(lock_path.read_text(encoding="utf-8-sig"))


def action_verify(root: Path, lock_path: Path, as_json: bool) -> int:
    lock = _load_lock(lock_path)

    report: Dict[str, List[str]] = {"unchanged": [], "tampered": [], "missing": []}

    for slug, entry in (lock.get("skills") or {}).items():
        abs_path = root / Path(str(entry.get("path", "")))
        if not abs_path.exists():
            report["missing"].append(slug)
            continue
        cur = get_file_sha256(abs_path)
        if cur == entry.get("sha256_hash"):
            report["unchanged"].append(slug)
        else:
            report["tampered"].append(slug)

    if as_json:
        print(json.dumps({
            "action": "VERIFY",
            "lock_path": str(lock_path),
            "counts": {
                "unchanged": len(report["unchanged"]),
                "tampered": len(report["tampered"]),
                "missing": len(report["missing"]),
            },
            "tampered": report["tampered"],
            "missing": report["missing"],
        }, indent=2))
    else:
        _say(f"VERIFY against {lock_path}")
        _say(f"  unchanged : {len(report['unchanged'])}")
        _say(f"  tampered  : {len(report['tampered'])}")
        _say(f"  missing   : {len(report['missing'])}")
        if report["tampered"]:
            _say("")
            _say("Tampered skills (local hash != lock hash):", "yellow")
            for slug in report["tampered"]:
                _say(f"  - {slug}")
        if report["missing"]:
            _say("")
            _say("Missing skills (in lock, not on disk):", "yellow")
            for slug in report["missing"]:
                _say(f"  - {slug}")

    if report["tampered"] or report["missing"]:
        return 1
    return 0


def action_upgrade(root: Path, source: Path, lock_path: Path,
                   as_json: bool) -> int:
    lock = _load_lock(lock_path)

    local = find_installed_skills(root)
    src = find_installed_skills(source)

    report: Dict[str, List[str]] = {
        "unchanged": [],          # local AND source both match lock
        "local_modified": [],     # tampered locally; source matches lock
        "upstream_changed": [],   # source moved on; local still matches lock
        "both_changed": [],       # local AND source both differ from lock
        "new": [],                # in source, not in lock
        "removed": [],            # in lock, no longer in source
    }

    lock_slugs: Dict[str, Any] = dict((lock.get("skills") or {}).items())

    for slug, entry in lock_slugs.items():
        lock_hash = entry.get("sha256_hash")
        local_cur = (get_file_sha256(local[slug]["abs"])
                     if slug in local else None)
        source_cur = (get_file_sha256(src[slug]["abs"])
                      if slug in src else None)

        if not source_cur:
            report["removed"].append(slug)
        elif local_cur == lock_hash and source_cur == lock_hash:
            report["unchanged"].append(slug)
        elif local_cur != lock_hash and source_cur == lock_hash:
            report["local_modified"].append(slug)
        elif local_cur == lock_hash and source_cur != lock_hash:
            report["upstream_changed"].append(slug)
        else:
            report["both_changed"].append(slug)

    for slug in src:
        if slug not in lock_slugs:
            report["new"].append(slug)

    if as_json:
        print(json.dumps({
            "action": "UPGRADE",
            "lock_path": str(lock_path),
            "source": str(source),
            "counts": {key: len(val) for key, val in report.items()},
            "local_modified": report["local_modified"],
            "upstream_changed": report["upstream_changed"],
            "both_changed": report["both_changed"],
            "new": report["new"],
            "removed": report["removed"],
        }, indent=2))
    else:
        _say(f"UPGRADE classification (lock vs local vs {source})")
        _say(f"  unchanged        : {len(report['unchanged'])}")
        _say(f"  local-modified   : {len(report['local_modified'])}")
        _say(f"  upstream-changed : {len(report['upstream_changed'])}")
        _say(f"  both-changed     : {len(report['both_changed'])}")
        _say(f"  new (in source)  : {len(report['new'])}")
        _say(f"  removed          : {len(report['removed'])}")
        for cat in ("local_modified", "upstream_changed", "both_changed",
                    "new", "removed"):
            items = report[cat]
            if items:
                _say("")
                _say(f"{cat.replace('_', '-')}:", "cyan")
                for slug in items:
                    _say(f"  - {slug}")
    return 0


def action_read(lock_path: Path) -> int:
    if not lock_path.exists():
        raise FileNotFoundError(f"Lock file not found: {lock_path}")
    sys.stdout.write(lock_path.read_text(encoding="utf-8-sig"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    default_source = str(Path(__file__).resolve().parent.parent)
    parser = argparse.ArgumentParser(
        description="Read/write/verify gald3r-skills-lock.json (T1043).")
    parser.add_argument("-Action", "--action", dest="action", required=True,
                        type=str.upper,
                        choices=["WRITE", "VERIFY", "UPGRADE", "READ"],
                        help="Lock-file operation")
    parser.add_argument("-ProjectPath", "--project-path", dest="project_path",
                        default=os.getcwd(),
                        help="Installed project root (default: cwd)")
    parser.add_argument("-SourceRoot", "--source-root", dest="source_root",
                        default=default_source,
                        help="Canonical gald3r source (for UPGRADE)")
    parser.add_argument("-LockFile", "--lock-file", dest="lock_file",
                        default="gald3r-skills-lock.json",
                        help="Lock file relative path")
    parser.add_argument("-Tier", "--tier", dest="tier", default="unknown",
                        type=str.lower,
                        choices=["full", "slim", "adv", "unknown"],
                        help="Tier tag for WRITE")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit machine-readable JSON")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    project_path = Path(args.project_path).resolve()
    lock_path = project_path / args.lock_file

    try:
        if args.action == "WRITE":
            return action_write(project_path, lock_path, args.tier, args.json)
        if args.action == "VERIFY":
            return action_verify(project_path, lock_path, args.json)
        if args.action == "UPGRADE":
            return action_upgrade(project_path, Path(args.source_root),
                                  lock_path, args.json)
        return action_read(lock_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        _say(f"ERROR: {exc}", "red")
        return 1


if __name__ == "__main__":
    sys.exit(main())
