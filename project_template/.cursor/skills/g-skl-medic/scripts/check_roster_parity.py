#!/usr/bin/env python3
"""Roster-parity gate (T516) — assert the platform roster agrees across every source.

The single source of truth is PLATFORM_REGISTRY.yaml. This gate asserts that the four
rosters agree:

    overlays  == registry == specs == STATUS rows

and fails loudly (exit 2) on any HARD mismatch:
  * an overlay dir with no registry entry (or vice versa)
  * a non-redundant registry platform with NO PLATFORM_SPEC.md anywhere
  * a STATUS row whose platform is neither a registry name nor a registered alias

KNOWN/intended residual drift is reported as a WARNING (exit 0), because the registry
documents it deliberately:
  * a registry platform with no STATUS row yet (e.g. mimo-code) — soft
  * a registered alias (e.g. vibe -> mistral) that has a STATUS row but no overlay — soft

Wired into g-medic L1-J (Platform Doc Freshness neighbourhood). Read-only; never writes.

Usage:
    python check_roster_parity.py [--root <repo_root>] [--json]

Exit codes: 0 = parity OK (warnings allowed) · 2 = HARD drift · 1 = usage/IO error.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set


# Registry locations to probe under the repo root (first hit wins).
_REL_REGISTRY_PATHS = (
    Path("gald3r_templates") / "gald3r_core" / "platforms" / "PLATFORM_REGISTRY.yaml",
    Path("gald3r_core") / "platforms" / "PLATFORM_REGISTRY.yaml",
    Path(".gald3r_sys") / "platforms" / "PLATFORM_REGISTRY.yaml",
    Path("platforms") / "PLATFORM_REGISTRY.yaml",
)

# Overlay roots to probe (first existing wins).
_REL_OVERLAY_ROOTS = (
    Path("gald3r_templates") / "gald3r_core" / "platforms",
    Path("gald3r_core") / "platforms",
    Path(".gald3r_sys") / "platforms",
)

# Skill trees to probe for PLATFORM_SPEC.md coverage (any hit = covered).
_REL_SPEC_TREES = (
    Path("gald3r_templates") / "gald3r_core" / "project_template" / ".claude" / "skills",
    Path("gald3r_templates") / "gald3r_core" / "project_template" / ".cursor" / "skills",
    Path(".claude") / "skills",
    Path(".cursor") / "skills",
)

_REL_STATUS = Path(".gald3r") / "PLATFORM_STATUS.md"


def _find_root(start: Optional[Path] = None) -> Path:
    """Find the project root by walking up the tree.

    Prefer a root where BOTH a registry candidate AND the ``.gald3r/PLATFORM_STATUS.md``
    anchor resolve. That distinguishes the true project root from an interior build
    directory such as ``gald3r_templates/gald3r_core`` — which also contains
    ``platforms/PLATFORM_REGISTRY.yaml`` and would otherwise be returned greedily,
    making every overlay/spec/STATUS probe resolve to nothing (false HARD DRIFT).
    """
    here = (start or Path(__file__)).resolve()
    for root in here.parents:
        has_registry = any((root / rel).is_file() for rel in _REL_REGISTRY_PATHS)
        if has_registry and (root / _REL_STATUS).is_file():
            return root
    # Fallbacks: any registry candidate, then the .gald3r project marker, else CWD.
    for root in here.parents:
        for rel in _REL_REGISTRY_PATHS:
            if (root / rel).is_file():
                return root
    for root in here.parents:
        if (root / ".gald3r").is_dir():
            return root
    return Path.cwd()


def _load_registry(root: Path) -> Optional[Path]:
    for rel in _REL_REGISTRY_PATHS:
        p = root / rel
        if p.is_file():
            return p
    return None


def _parse_registry(path: Path) -> List[Dict[str, object]]:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return list(data.get("platforms") or [])
    except ImportError:
        # Reuse the monitor's minimal parser if PyYAML is unavailable.
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from platform_registry import all_entries  # type: ignore

            return all_entries(start=path)
        except ImportError:
            return []


def _overlay_dirs(root: Path) -> Set[str]:
    for rel in _REL_OVERLAY_ROOTS:
        base = root / rel
        if base.is_dir():
            return {
                d.name for d in base.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            }
    return set()


def _spec_exists(root: Path, spec_suffixes: Set[str]) -> bool:
    """Any tree contains g-skl-platform-<suffix>/PLATFORM_SPEC.md for any suffix."""
    for rel in _REL_SPEC_TREES:
        base = root / rel
        if not base.is_dir():
            continue
        for suffix in spec_suffixes:
            if (base / f"g-skl-platform-{suffix}" / "PLATFORM_SPEC.md").is_file():
                return True
    return False


def _status_rows(root: Path) -> Set[str]:
    path = root / _REL_STATUS
    if not path.is_file():
        return set()
    rows: Set[str] = set()
    import re

    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([a-z0-9][a-z0-9-]*)\s*\|", line)
        if not m:
            continue
        name = m.group(1)
        if name in ("Platform",) or re.match(r"^[-:]+$", name):
            continue
        rows.add(name)
    return rows


def _spec_suffix_for(entry: Dict[str, object]) -> Set[str]:
    """Candidate spec-folder suffixes for a registry entry. spec_path takes priority;
    fall back to name and the -code-stripped short name (mimo-code -> mimo)."""
    out: Set[str] = set()
    sp = entry.get("spec_path")
    if sp:
        # spec_path is like "g-skl-platform-<suffix>/PLATFORM_SPEC.md"
        first = str(sp).split("/")[0]
        out.add(first.replace("g-skl-platform-", ""))
    name = str(entry.get("name") or "")
    if name:
        out.add(name)
        if name.endswith("-code"):
            out.add(name[:-5])
    return {s for s in out if s}


def run(root: Path) -> Dict[str, object]:
    reg_path = _load_registry(root)
    if reg_path is None:
        return {"ok": False, "hard": True,
                "errors": [f"PLATFORM_REGISTRY.yaml not found under {root}"],
                "warnings": [], "counts": {}}

    entries = _parse_registry(reg_path)
    canonical = [e for e in entries if not e.get("alias_of")]
    aliases = [e for e in entries if e.get("alias_of")]
    registry_names = {str(e["name"]) for e in canonical if e.get("name")}
    registry_overlay_dirs = {str(e["overlay_dir"]) for e in canonical if e.get("overlay_dir")}
    alias_names = {str(e["name"]) for e in aliases if e.get("name")}

    overlays = _overlay_dirs(root)
    status = _status_rows(root)

    errors: List[str] = []
    warnings: List[str] = []

    # 1) overlays == registry overlay_dirs
    ov_only = sorted(overlays - registry_overlay_dirs)
    reg_only = sorted(registry_overlay_dirs - overlays)
    for o in ov_only:
        errors.append(f"overlay '{o}' has NO registry entry (add it to PLATFORM_REGISTRY.yaml)")
    for r in reg_only:
        errors.append(f"registry overlay_dir '{r}' has NO platforms/<dir> overlay")

    # 2) every non-redundant registry platform has a PLATFORM_SPEC.md somewhere
    spec_missing: List[str] = []
    for e in canonical:
        if e.get("lifecycle") == "redundant":
            continue
        suffixes = _spec_suffix_for(e)
        if not _spec_exists(root, suffixes):
            spec_missing.append(str(e.get("name")))
    for s in sorted(spec_missing):
        errors.append(f"platform '{s}' has NO PLATFORM_SPEC.md in any skill tree")

    # 3) STATUS rows must be a registry name or a registered alias
    valid_status = registry_names | alias_names
    status_unknown = sorted(status - valid_status)
    for s in status_unknown:
        errors.append(f"PLATFORM_STATUS.md row '{s}' is neither a registry platform nor a "
                      f"registered alias (drop it or register it)")

    # SOFT: registry platforms with no STATUS row (documented drift)
    no_status = sorted(registry_names - status)
    for s in no_status:
        warnings.append(f"registry platform '{s}' has no PLATFORM_STATUS.md row yet "
                        f"(run @g-platform-check {s})")

    # SOFT: aliases present in STATUS without an overlay (expected by design)
    alias_in_status = sorted(alias_names & status)
    for s in alias_in_status:
        warnings.append(f"alias '{s}' has a STATUS row (resolved via alias_of in the registry — "
                        f"not double-counted)")

    counts = {
        "overlays": len(overlays),
        "registry_canonical": len(registry_names),
        "registry_aliases": len(alias_names),
        "status_rows": len(status),
        "specs_covered": len(registry_names) - len(spec_missing),
    }
    hard = len(errors) > 0
    return {"ok": not hard, "hard": hard, "errors": errors, "warnings": warnings,
            "counts": counts, "registry_path": str(reg_path)}


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Platform roster-parity gate (T516).")
    parser.add_argument("--root", default=None, help="Repo root (default: auto-detect).")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else _find_root()
    result = run(root)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2 if result.get("hard") else 0

    print("\n=== platform roster-parity (T516) ===")
    print(f"  registry: {result.get('registry_path', 'NOT FOUND')}")
    c = result.get("counts", {})
    if c:
        print(f"  overlays={c.get('overlays')}  registry={c.get('registry_canonical')} "
              f"(+{c.get('registry_aliases')} alias)  specs_covered={c.get('specs_covered')} "
              f"status_rows={c.get('status_rows')}")
    for e in result.get("errors", []):
        print(f"  ERROR: {e}")
    for w in result.get("warnings", []):
        print(f"  warn : {w}")
    if result.get("hard"):
        print("  RESULT: HARD DRIFT — roster sources disagree. Fix before shipping.")
        return 2
    if result.get("warnings"):
        print("  RESULT: OK (with documented soft drift).")
    else:
        print("  RESULT: OK — overlays == registry == specs == STATUS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
