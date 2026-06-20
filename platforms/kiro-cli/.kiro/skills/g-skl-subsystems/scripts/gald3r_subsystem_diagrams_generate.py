#!/usr/bin/env python3
"""Python port of gald3r_subsystem_diagrams_generate.ps1 (T1585).

Generate Mermaid architecture markdown under .gald3r/reports/architecture/.

Reads .gald3r/subsystems/*.md frontmatter and emits SYSTEM_ARCHITECTURE.md,
SUBSYSTEM_TREE.md, DEPENDENCY_GRAPH.md. Hierarchy edges use
parent_subsystem/domain/layer; dependency edges use dependencies: (separate
graph). Safe to re-run; timestamps in header.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
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
    return items


def _mermaid_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Generate Mermaid architecture markdown under "
                    ".gald3r/reports/architecture/ (Python port of "
                    "gald3r_subsystem_diagrams_generate.ps1).",
        allow_abbrev=False)
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=str(Path.cwd()), help="Repository root.")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root)
    sub_root = project_root / ".gald3r" / "subsystems"
    out_dir = project_root / ".gald3r" / "reports" / "architecture"
    if not sub_root.exists():
        print(f"Missing {sub_root}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    nodes: List[Dict[str, object]] = []
    for path in sorted(sub_root.rglob("*.md")):
        if not path.is_file():
            continue
        if re.match(r"^(SYSTEM_|SUBSYSTEM_TREE|DEPENDENCY_GRAPH)", path.name,
                    re.IGNORECASE):
            continue
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        fm = get_frontmatter_block(raw)
        if not fm:
            continue
        name = get_yaml_scalar(fm, "name") or path.stem
        nodes.append({
            "Name": name,
            "Status": get_yaml_scalar(fm, "status"),
            "Domain": get_yaml_scalar(fm, "domain") or "general",
            "Layer": get_yaml_scalar(fm, "layer") or "unspecified",
            "Parent": get_yaml_scalar(fm, "parent_subsystem"),
            "Deps": get_yaml_string_list(fm, "dependencies"),
        })

    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S") + "Z"
    banner = (
        "<!-- AUTO-GENERATED - do not hand-edit. Source: "
        ".claude/skills/g-skl-subsystems/scripts/gald3r_subsystem_diagrams_generate.py -->\n"
        f"<!-- Generated (UTC): {iso} -->\n"
        "<!-- Regenerate: python .claude/skills/g-skl-subsystems/scripts/"
        "gald3r_subsystem_diagrams_generate.py -ProjectRoot (repo root) -->\n"
    )

    # --- SYSTEM_ARCHITECTURE overview ---
    arch: List[str] = [banner, "# System architecture overview", ""]
    arch.append("Legend: **Domain** groups related subsystems. **Layer** is advisory "
                "(transport, policy, presentation, etc.). **Depends-on** edges are "
                "runtime/data coupling; **parent/child** is organizational containment "
                "from parent_subsystem metadata and nested spec paths.")
    arch.append("")
    domains: Dict[str, List[Dict[str, object]]] = {}
    for n in nodes:
        domains.setdefault(str(n["Domain"]), []).append(n)
    for domain in sorted(domains):
        arch.append(f"## Domain: {domain}")
        for n in sorted(domains[domain], key=lambda x: str(x["Name"])):
            status = n["Status"] if n["Status"] is not None else ""
            arch.append(f"- **{n['Name']}** - layer {n['Layer']} - status {status}")
        arch.append("")
    (out_dir / "SYSTEM_ARCHITECTURE.md").write_text(
        "\n".join(arch) + "\n", encoding="utf-8")

    # --- Tree (containment / hierarchy) ---
    tree: List[str] = [banner, "# Subsystem tree (hierarchy / grouping)", "",
                       "```mermaid", "flowchart TB"]
    for n in nodes:
        nid = _mermaid_id(str(n["Name"]))
        lbl = "{0}<br/>{1} / {2}".format(n["Name"], n["Domain"],
                                         n["Layer"]).replace('"', "'")
        tree.append(f'  {nid}["{lbl}"]')
    for n in nodes:
        if not n["Parent"]:
            continue
        cid = _mermaid_id(str(n["Name"]))
        parent_node = _mermaid_id(str(n["Parent"]))
        tree.append(f"  {parent_node} --> {cid}")
    tree.append("```")
    tree.append("")
    (out_dir / "SUBSYSTEM_TREE.md").write_text(
        "\n".join(tree) + "\n", encoding="utf-8")

    # --- Dependency graph ---
    dep: List[str] = [banner, "# Subsystem dependency graph (depends-on)", "",
                      "```mermaid", "flowchart LR"]
    for n in nodes:
        nid = _mermaid_id(str(n["Name"]))
        nm = str(n["Name"]).replace('"', "'")
        dep.append(f'  {nid}["{nm}"]')
    for n in nodes:
        tid = _mermaid_id(str(n["Name"]))
        for d in n["Deps"]:  # type: ignore[union-attr]
            if not d:
                continue
            did = _mermaid_id(str(d))
            dep.append(f"  {did} --> {tid}")
    dep.append("```")
    dep.append("")
    (out_dir / "DEPENDENCY_GRAPH.md").write_text(
        "\n".join(dep) + "\n", encoding="utf-8")

    print("Wrote:")
    print(f"  {out_dir / 'SYSTEM_ARCHITECTURE.md'}")
    print(f"  {out_dir / 'SUBSYSTEM_TREE.md'}")
    print(f"  {out_dir / 'DEPENDENCY_GRAPH.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
