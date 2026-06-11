#!/usr/bin/env python3
"""Python port of gald3r_feature_hierarchy_sync.ps1 (T1585).

Dry-run validation for feature hierarchy (flat + nested paths under
.gald3r/features/).

Scans all feature markdown files, parses YAML frontmatter for hierarchy
fields, and reports: duplicate feat IDs, missing parents, stale children
references, depth mismatches. Never mutates files. Exit 0 if clean, 1 if
issues found (use -WarnOnly for exit 0).
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


def _bootstrap_engine() -> bool:
    """Make gald3r.utils importable; fall back to stdlib when unavailable."""
    try:
        import gald3r.utils  # noqa: F401

        return True
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for d in here.parents:
        engine_src = d / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401

                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()


def get_frontmatter_block(content: str) -> Optional[str]:
    """Return the YAML frontmatter body between the first two '---' fences."""
    m = re.match(r"(?s)^---\r?\n(.+?)\r?\n---\r?\n", content)
    return m.group(1) if m else None


def get_yaml_scalar(block: str, key: str) -> Optional[str]:
    """Read a scalar frontmatter value (regex fallback — no YAML dependency)."""
    m = re.search(rf"(?m)^{re.escape(key)}\s*:\s*(.+)\s*$", block, re.IGNORECASE)
    if not m:
        return None
    v = m.group(1).strip()
    qm = re.match(r"^['\"](.*)['\"]$", v)
    if qm:
        return qm.group(1)
    return v


def get_yaml_string_list(block: str, key: str) -> List[str]:
    """Read a frontmatter list — inline [a, b] or dash-item form."""
    in_list = False
    items: List[str] = []
    for line in re.split(r"\r?\n", block):
        if re.match(r"^\s*$", line):
            continue
        if not in_list:
            if re.match(rf"^{re.escape(key)}\s*:\s*$", line, re.IGNORECASE):
                in_list = True
                continue
            m = re.match(rf"^{re.escape(key)}\s*:\s*\[\s*(.*?)\s*\]\s*$", line,
                         re.IGNORECASE)
            if m:
                inner = m.group(1).strip()
                if not inner:
                    return []
                return [p.strip().strip("'\"") for p in inner.split(",")]
        else:
            if re.match(r"^(\w+)\s*:", line):
                break
            m = re.match(r"^\-\s+(.+)$", line)
            if m:
                items.append(m.group(1).strip().strip("'\""))
                continue
            m = re.match(r"^\s{2,}\-\s+(.+)$", line)
            if m:
                items.append(m.group(1).strip().strip("'\""))
    return items


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Dry-run validation for feature hierarchy "
                    "(Python port of gald3r_feature_hierarchy_sync.ps1).",
        allow_abbrev=False)
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=str(Path.cwd()),
                        help="Repository root containing .gald3r/features/")
    parser.add_argument("-WarnOnly", "--warn-only", dest="warn_only",
                        action="store_true",
                        help="Always exit 0 (CI advisory mode).")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit single-line JSON summary to stdout.")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root)
    features_root = project_root / ".gald3r" / "features"
    if not features_root.exists():
        print(f"SKIP: no .gald3r/features at {features_root}")
        if args.json:
            print('{"status":"skip","issues":0}')
        return 0

    features_root_str = str(features_root)
    # by_id: case-insensitive multimap (casefolded id -> first-seen id + recs)
    by_id: Dict[str, Dict[str, object]] = {}
    records: List[Dict[str, object]] = []
    for path in sorted(features_root.rglob("*.md")):
        if not path.is_file():
            continue
        rel = str(path)[len(features_root_str):].lstrip("\\/")
        if not re.search(r"(?i)feat-\d+[_-]", rel):
            continue
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        fm = get_frontmatter_block(raw)
        if not fm:
            continue
        feat_id = get_yaml_scalar(fm, "id")
        if not feat_id:
            continue
        depth_str = get_yaml_scalar(fm, "depth")
        depth: Optional[int] = None
        if depth_str and re.match(r"^\d+$", depth_str):
            depth = int(depth_str)
        rec: Dict[str, object] = {
            "Path": rel,
            "FullPath": str(path),
            "Id": feat_id,
            "Parent": get_yaml_scalar(fm, "parent_feature"),
            "Area": get_yaml_scalar(fm, "feature_area"),
            "Depth": depth,
            "Children": get_yaml_string_list(fm, "children"),
        }
        records.append(rec)
        bucket = by_id.setdefault(feat_id.casefold(), {"id": feat_id, "recs": []})
        bucket["recs"].append(rec)  # type: ignore[union-attr]

    issues: List[str] = []

    for key, bucket in by_id.items():
        recs = bucket["recs"]
        if len(recs) > 1:  # type: ignore[arg-type]
            paths = "; ".join(str(r["Path"]) for r in recs)  # type: ignore[union-attr]
            issues.append(f"DUPLICATE_ID {bucket['id']} → {paths}")

    id_set = set(by_id.keys())
    for r in records:
        parent = r["Parent"]
        if parent:
            if str(parent).casefold() not in id_set:
                issues.append(f"MISSING_PARENT {r['Id']} parent_feature={parent} "
                              f"file={r['Path']}")
        for ch in r["Children"]:  # type: ignore[union-attr]
            if not ch:
                continue
            if str(ch).casefold() not in id_set:
                issues.append(f"STALE_CHILD {r['Id']} children entry '{ch}' "
                              f"missing feat file={r['Path']}")
        if r["Depth"] is not None:
            segs = len(re.split(r"[\\/]", str(r["Path"]))) - 1
            if r["Depth"] != segs:
                issues.append(f"DEPTH_MISMATCH {r['Id']} depth={r['Depth']} "
                              f"path_segments={segs} file={r['Path']}")

    for r in records:
        for ch in r["Children"]:  # type: ignore[union-attr]
            if not ch:
                continue
            bucket = by_id.get(str(ch).casefold())
            if not bucket:
                continue
            for cr in bucket["recs"]:  # type: ignore[union-attr]
                if cr["Parent"] and r["Id"] and cr["Parent"] != r["Id"]:
                    issues.append(f"CHILD_PARENT_MISMATCH parent {r['Id']} lists "
                                  f"child {ch} but {ch} has "
                                  f"parent_feature={cr['Parent']}")

    issue_count = len(issues)
    if not args.json:
        print("=== gald3r_feature_hierarchy_sync (dry-run) ===")
        print(f"Features scanned: {len(records)}")
        if issue_count == 0:
            print("OK: no hierarchy issues detected.")
        else:
            print(f"ISSUES ({issue_count}):")
            for i in issues:
                print(f"  - {i}")

    exit_code = 0 if issue_count == 0 else 1
    if args.warn_only:
        exit_code = 0

    if args.json:
        payload = {
            "status": "ok" if issue_count == 0 else "issues",
            "issues": issue_count,
            "detail": issues,
        }
        print(json.dumps(payload, separators=(",", ":")))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
