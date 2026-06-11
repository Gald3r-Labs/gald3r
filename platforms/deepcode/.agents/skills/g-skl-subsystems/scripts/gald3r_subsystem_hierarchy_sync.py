#!/usr/bin/env python3
"""Python port of gald3r_subsystem_hierarchy_sync.ps1 (T1585).

Dry-run validation for subsystem hierarchy metadata under
.gald3r/subsystems/**/*.md.

Recursively scans nested subsystem specs, validates parent_subsystem /
children / locations:, cross-checks SUBSYSTEMS.md index paths against files
on disk (drift either direction), and flags optional domain mismatch vs
parent. Does not mutate files.
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
        description="Dry-run validation for subsystem hierarchy metadata "
                    "(Python port of gald3r_subsystem_hierarchy_sync.ps1).",
        allow_abbrev=False)
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=str(Path.cwd()), help="Repository root.")
    parser.add_argument("-WarnOnly", "--warn-only", dest="warn_only",
                        action="store_true",
                        help="Exit 0 even when issues found.")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit JSON summary.")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root)
    sub_root = project_root / ".gald3r" / "subsystems"
    if not sub_root.exists():
        if args.json:
            print('{"status":"skip","issues":0}')
        return 0

    gald3r_dir = project_root / ".gald3r"
    gald3r_dir_str = str(gald3r_dir)

    def rel_from_gald3r(full_path: str) -> Optional[str]:
        if not full_path.lower().startswith(gald3r_dir_str.lower()):
            return None
        r = full_path[len(gald3r_dir_str):].lstrip("\\/")
        return r.replace("\\", "/")

    # Paths listed in SUBSYSTEMS.md (subsystems/*.md), normalized forward slashes.
    # Case-insensitive set: casefolded key -> first-seen original string.
    index_paths: Dict[str, str] = {}
    subsystems_md = gald3r_dir / "SUBSYSTEMS.md"
    if subsystems_md.exists():
        idx_raw = subsystems_md.read_text(encoding="utf-8-sig")
        for rx in (r"(?i)`(subsystems/[^`]+\.md)`",
                   r"(?i)\]\((subsystems/[^)]+\.md)\)",
                   r"(?i)\|\s*`?(subsystems/[^`|]+\.md)`?\s*\|"):
            for m in re.finditer(rx, idx_raw):
                v = m.group(1).replace("\\", "/")
                index_paths.setdefault(v.casefold(), v)

    # by_name: case-insensitive multimap (casefolded key -> first-seen name + recs)
    by_name: Dict[str, Dict[str, object]] = {}
    records: List[Dict[str, object]] = []
    for path in sorted(sub_root.rglob("*.md")):
        if not path.is_file():
            continue
        if re.match(r"^(SYSTEM_|SUBSYSTEM_TREE|DEPENDENCY_GRAPH)", path.name,
                    re.IGNORECASE):
            continue
        name = path.stem
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        fm = get_frontmatter_block(raw)
        if not fm:
            continue
        yaml_name = get_yaml_scalar(fm, "name")
        if yaml_name:
            name = yaml_name
        rec: Dict[str, object] = {
            "File": path.name,
            "RelPath": rel_from_gald3r(str(path)),
            "Name": name,
            "Parent": get_yaml_scalar(fm, "parent_subsystem"),
            "Domain": get_yaml_scalar(fm, "domain"),
            "Layer": get_yaml_scalar(fm, "layer"),
            "Dependencies": get_yaml_string_list(fm, "dependencies"),
            "Children": get_yaml_string_list(fm, "children"),
            "HasLocationsBlock": bool(re.search(r"(?m)^locations:", fm)),
        }
        records.append(rec)
        bucket = by_name.setdefault(name.casefold(), {"name": name, "recs": []})
        bucket["recs"].append(rec)  # type: ignore[union-attr]

    issues: List[str] = []
    name_set = set(by_name.keys())

    for key, bucket in by_name.items():
        recs = bucket["recs"]
        if len(recs) > 1:  # type: ignore[arg-type]
            issues.append(f"DUPLICATE_SUBSYSTEM_NAME {bucket['name']} "
                          f"({len(recs)} specs)")  # type: ignore[arg-type]

    for r in records:
        parent = r["Parent"]
        if parent:
            if str(parent).casefold() not in name_set:
                issues.append(f"MISSING_PARENT_SUBSYSTEM {r['Name']} "
                              f"parent_subsystem={parent}")
        for ch in r["Children"]:  # type: ignore[union-attr]
            if not ch:
                continue
            if str(ch).casefold() not in name_set:
                issues.append(f"STALE_CHILD {r['Name']} children='{ch}'")
        # Intentionally do not validate dependencies: edges here — dependency
        # graph is generated separately (Task 516); YAML dependency list formats
        # vary (quoted JSON-style arrays, inline lists) and are not hierarchy
        # errors.
        if not r["HasLocationsBlock"]:
            rel_norm = str(r["RelPath"]).replace("\\", "/") if r["RelPath"] else ""
            is_adopted_stub = bool(re.match(r"(?i)^adopted_", str(r["File"])))
            if rel_norm and rel_norm.casefold() in index_paths and not is_adopted_stub:
                issues.append(f"INCOMPLETE_LOCATIONS {r['Name']} ({rel_norm}) - "
                              "add locations: mapping per subsystem spec policy")
        if parent:
            bucket = by_name.get(str(parent).casefold())
            if bucket and bucket["recs"]:  # type: ignore[truthy-bool]
                p0 = bucket["recs"][0]  # type: ignore[index]
                if (r["Domain"] and p0["Domain"]
                        and r["Domain"] != p0["Domain"]):
                    issues.append(f"DOMAIN_MISMATCH {r['Name']} domain={r['Domain']} "
                                  f"vs parent {p0['Name']} domain={p0['Domain']}")

    for ip in index_paths.values():
        full = gald3r_dir / ip
        if not full.exists():
            issues.append(f"INDEX_BROKEN_LINK {ip} listed in SUBSYSTEMS.md but "
                          "file missing")

    issue_count = len(issues)
    if not args.json:
        print("=== gald3r_subsystem_hierarchy_sync (dry-run) ===")
        print(f"Specs scanned: {len(records)}")
        if issue_count == 0:
            print("OK: no blocking issues detected.")
        else:
            print(f"ISSUES ({issue_count}):")
            for i in issues:
                print(f"  - {i}")

    hard_count = issue_count
    exit_code = 0 if hard_count == 0 else 1
    if args.warn_only:
        exit_code = 0

    if args.json:
        disk_set: Dict[str, str] = {}
        for r in records:
            if r["RelPath"]:
                disk_set.setdefault(str(r["RelPath"]).casefold(), str(r["RelPath"]))
        not_indexed = [v for k, v in disk_set.items() if k not in index_paths]
        payload = {
            "status": "ok" if hard_count == 0 else "issues",
            "issues": hard_count,
            "detail": issues,
            "specs_scanned": len(records),
            "index_paths": list(index_paths.values()),
            "disk_not_indexed": not_indexed,
        }
        print(json.dumps(payload, separators=(",", ":")))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
