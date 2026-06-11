#!/usr/bin/env python3
"""Python port of migrate_schemas.ps1 helpers (T1587).

Sibling helper module for migrate_schemas.py — parsing and pure-ish helpers
extracted so the CLI driver stays under the size budget:

* frontmatter / lightweight-YAML readers (``read_front_matter``,
  ``get_yaml_scalar``, ``get_migration_step``, ``parse_registry``)
* path resolution (``resolve_schemas_dir``, ``resolve_dot_gald3r_canonical``,
  ``get_schema_file_for_id``)
* git metadata (``get_git_creation_date``)
* T1485 conditional grouped-format SUBSYSTEMS.md regenerator
  (``update_grouped_subsystems_index`` — strict no-op without
  ``parent_system:`` data)
* shared console color helper (``cprint``) backed by ``gald3r.utils.console``
  when the engine is importable, stdlib fallback otherwise.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import glob as _glob
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Engine bootstrap (gald3r.utils) with graceful stdlib fallback
# ---------------------------------------------------------------------------

def _bootstrap_engine_path() -> None:
    """Locate .gald3r_sys/engine/src relative to this script and sys.path it."""
    here = Path(__file__).resolve().parent
    candidates: List[Path] = [here.parent / "engine" / "src"]
    for anc in [here, *here.parents]:
        candidates.append(anc / ".gald3r_sys" / "engine" / "src")
        candidates.append(
            anc / "gald3r_core" / "project_template" / ".gald3r_sys" / "engine" / "src"
        )
    for cand in candidates:
        if (cand / "gald3r" / "utils" / "console.py").is_file():
            sys.path.insert(0, str(cand))
            return


try:
    from gald3r.utils import console as _console
except ImportError:
    _bootstrap_engine_path()
    try:
        from gald3r.utils import console as _console
    except ImportError:
        _console = None  # stdlib fallback below

# PowerShell ConsoleColor -> ANSI mapping (bright variants for the plain names,
# dim variants for the Dark* names — matches Windows console rendering).
_ANSI = {
    "red": "\x1b[91m", "darkred": "\x1b[31m",
    "green": "\x1b[92m", "darkgreen": "\x1b[32m",
    "yellow": "\x1b[93m", "darkyellow": "\x1b[33m",
    "cyan": "\x1b[96m", "darkcyan": "\x1b[36m",
    "magenta": "\x1b[95m", "blue": "\x1b[94m",
    "gray": "\x1b[37m", "darkgray": "\x1b[90m",
    "white": "\x1b[97m",
}
_RESET = "\x1b[0m"


def _color_enabled() -> bool:
    if _console is not None:
        return _console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print `msg`, colored like ``Write-Host -ForegroundColor`` when a TTY."""
    code = _ANSI.get((color or "").lower())
    if code and _color_enabled():
        print(f"{code}{msg}{_RESET}")
    else:
        print(msg)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def resolve_schemas_dir(explicit: str, project: str, script_root: str) -> Optional[str]:
    """Mirror Resolve-SchemasDir: explicit -> script-sibling -> project-local."""
    if explicit and os.path.exists(explicit):
        return os.path.realpath(explicit)
    cand = os.path.join(os.path.dirname(script_root), "schemas")
    if os.path.exists(cand):
        return os.path.realpath(cand)
    cand = os.path.join(project, ".gald3r_sys", "schemas")
    if os.path.exists(cand):
        return os.path.realpath(cand)
    return None


def resolve_dot_gald3r_canonical(project: str, script_root: str) -> Optional[str]:
    """T1442: locate the pristine .gald3r/ template under template_verification/."""
    cand = os.path.join(os.path.dirname(script_root), "template_verification", ".gald3r")
    if os.path.exists(cand):
        return os.path.realpath(cand)
    cand = os.path.join(project, ".gald3r_sys", "template_verification", ".gald3r")
    if os.path.exists(cand):
        return os.path.realpath(cand)
    return None


# ---------------------------------------------------------------------------
# Frontmatter / lightweight YAML parsing
# ---------------------------------------------------------------------------

def convert_to_version_number(ver: Optional[str]) -> int:
    """'v0' -> 0, 'v1' -> 1; blank/unparseable -> 0 (ConvertTo-VersionNumber)."""
    if ver is None or not ver.strip():
        return 0
    m = re.search(r"v(\d+)\s*$", ver)
    return int(m.group(1)) if m else 0


@dataclass
class FrontMatter:
    """Result of read_front_matter — mirrors the PS1 Read-FrontMatter hashtable."""

    newline: str = "\n"
    has_front_matter: bool = False
    fm_start: int = -1
    fm_end: int = -1
    lines: List[str] = field(default_factory=list)
    fields: Dict[str, str] = field(default_factory=dict)


def read_front_matter(path: str) -> FrontMatter:
    """Lightweight YAML-frontmatter reader (top-level `key: value` scalars only)."""
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        raw = fh.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = re.split(r"\r?\n", raw)
    fm = FrontMatter(newline=nl, lines=lines)

    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                fm.has_front_matter = True
                fm.fm_start = 0
                fm.fm_end = i
                break

    if fm.has_front_matter:
        for i in range(1, fm.fm_end):
            m = re.match(r"^([A-Za-z0-9_]+):\s?(.*)$", lines[i])
            if m:
                fm.fields[m.group(1)] = m.group(2)
    return fm


def get_yaml_scalar(path: str, key: str) -> Optional[str]:
    """Read a single top-level scalar from a YAML file (Get-YamlScalar)."""
    rx = re.compile(rf"^{re.escape(key)}:\s*[\"']?([^\"'#]+?)[\"']?\s*(#.*)?$")
    with open(path, "r", encoding="utf-8-sig") as fh:
        for line in fh:
            m = rx.match(line.rstrip("\r\n"))
            if m:
                return m.group(1).strip()
    return None


def get_migration_step(schema_file: Optional[str], version_num: int) -> Dict[str, list]:
    """Parse migration_notes.vN.{added,deprecated,removed} (compact + block forms)."""
    result: Dict[str, list] = {"added": [], "deprecated": [], "removed": []}
    if not schema_file or not os.path.exists(schema_file):
        return result
    with open(schema_file, "r", encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()

    in_migration = False
    in_version = False
    cur_list: Optional[str] = None
    ver_key = f"v{version_num}"

    for i, line in enumerate(lines):
        if re.match(r"^migration_notes:\s*$", line, re.IGNORECASE):
            in_migration = True
            continue
        if not in_migration:
            continue
        # A new top-level key ends the migration_notes block.
        if re.match(r"^[A-Za-z0-9_]+:", line, re.IGNORECASE) and not re.match(r"^\s", line):
            break

        if re.match(rf"^\s{{2}}{re.escape(ver_key)}:\s*$", line, re.IGNORECASE):
            in_version = True
            cur_list = None
            continue
        if in_version and re.match(r"^\s{2}v\d+:\s*$", line, re.IGNORECASE):
            in_version = False
            cur_list = None
            continue
        if not in_version:
            continue

        # Compact list:  added: [a, b]
        m_inline = re.match(r"^\s{4}(added|deprecated|removed):\s*\[(.*)\]\s*$", line)
        if m_inline:
            key = m_inline.group(1)
            items = [s.strip() for s in m_inline.group(2).split(",") if s.strip()]
            for it in items:
                result[key].append({"field": it, "rename_to": None})
            continue
        # Block list header:  added:
        m_hdr = re.match(r"^\s{4}(added|deprecated|removed):\s*$", line)
        if m_hdr:
            cur_list = m_hdr.group(1)
            continue
        # Block list item:  - field: phase   (peek ahead for rename_to)
        if cur_list:
            m_field = re.match(r"^\s{6,}-\s*field:\s*(.+)$", line)
            if m_field:
                entry = {"field": m_field.group(1).strip(), "rename_to": None}
                for j in range(i + 1, len(lines)):
                    if re.match(r"^\s{6,}-\s", lines[j]):
                        break
                    if re.match(r"^\s{4}\S", lines[j]):
                        break
                    mr = re.match(r"^\s{6,}rename_to:\s*(.+)$", lines[j])
                    if mr:
                        entry["rename_to"] = mr.group(1).strip()
                result[cur_list].append(entry)
    return result


# ---------------------------------------------------------------------------
# Registry / schema-file lookup
# ---------------------------------------------------------------------------

def parse_registry(registry_path: str) -> List[Dict[str, Optional[str]]]:
    """Parse `- pattern:` entries (with schema_id / current_version) from _registry.yaml."""
    schemas: List[Dict[str, Optional[str]]] = []
    cur: Optional[Dict[str, Optional[str]]] = None
    with open(registry_path, "r", encoding="utf-8-sig") as fh:
        for line in fh.read().splitlines():
            m_pat = re.match(r"^\s*-\s*pattern:\s*[\"'`]?([^\"'`]+?)[\"'`]?\s*$", line)
            if m_pat:
                if cur:
                    schemas.append(cur)
                cur = {"pattern": m_pat.group(1).strip(),
                       "schema_id": None, "current_version": None}
                continue
            if cur:
                m_id = re.match(r"^\s+schema_id:\s*(.+)$", line)
                if m_id:
                    cur["schema_id"] = m_id.group(1).strip()
                m_cv = re.match(r"^\s+current_version:\s*(.+)$", line)
                if m_cv:
                    cur["current_version"] = m_cv.group(1).strip()
    if cur:
        schemas.append(cur)
    return schemas


def get_schema_file_for_id(schema_id: Optional[str], version_num: int,
                           schemas_dir: str) -> Optional[str]:
    """schema_id 'task-file' -> '<schemas>/task_file.v<N>.schema.yaml' (with fallback)."""
    base = (schema_id or "").replace("-", "_")
    candidate = os.path.join(schemas_dir, f"{base}.v{version_num}.schema.yaml")
    if os.path.exists(candidate):
        return candidate
    any_match = sorted(_glob.glob(os.path.join(schemas_dir, f"{base}.v*.schema.yaml")))
    if any_match:
        return any_match[-1]
    return None


# ---------------------------------------------------------------------------
# Git metadata
# ---------------------------------------------------------------------------

def get_git_creation_date(file_path: str, repo_dir: str) -> Optional[str]:
    """First-ADD commit date for a file (yyyy-mm-dd) — Get-GitCreationDate."""
    try:
        proc = subprocess.run(
            ["git", "-C", repo_dir, "log", "--diff-filter=A", "--follow",
             "--format=%ad", "--date=short", "--", file_path],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode == 0 and proc.stdout:
            dates = [ln for ln in proc.stdout.splitlines()
                     if re.match(r"^\d{4}-\d{2}-\d{2}$", ln)]
            if dates:
                return dates[-1]  # earliest ADD
    except (OSError, subprocess.SubprocessError):
        pass
    return None


# ---------------------------------------------------------------------------
# T1485: Conditional grouped-format SUBSYSTEMS.md regenerator
# ---------------------------------------------------------------------------

def get_defined_groups_list(product_systems_path: str) -> List[str]:
    """Ordered defined_groups: block-list from PRODUCT_SYSTEMS.md frontmatter."""
    groups: List[str] = []
    if not os.path.exists(product_systems_path):
        return groups
    with open(product_systems_path, "r", encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()
    in_fm = False
    in_groups = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_fm = True
            continue
        if in_fm and line.strip() == "---":
            break  # end of frontmatter
        if not in_fm:
            continue
        if re.match(r"^defined_groups:\s*$", line, re.IGNORECASE):
            in_groups = True
            continue
        if in_groups:
            m_item = re.match(r"^\s+-\s*(.+?)\s*$", line)
            if m_item:
                groups.append(m_item.group(1).strip().strip('"').strip("'"))
                continue
            if re.match(r"^\S", line):  # next top-level key ends the list
                in_groups = False
    return groups


def get_subsystem_purpose(lines: List[str]) -> str:
    """First non-empty, non-placeholder line under '## Responsibility'."""
    in_resp = False
    for line in lines:
        if re.match(r"^##\s+Responsibility\s*$", line, re.IGNORECASE):
            in_resp = True
            continue
        if in_resp:
            if re.match(r"^##\s", line):
                break  # next section
            t = line.strip()
            if t and not re.match(r"^\[.*\]$", t):
                return t
    return ""


def update_grouped_subsystems_index(dot_gald3r: str, do_apply: bool) -> str:
    """Regenerate SUBSYSTEMS.md grouped by L1 system. Strict no-op without data.

    Returns one of: 'regenerated', 'to-regenerate', 'index-section-missing',
    'no-subsystems-md', 'no-product-systems-md', 'no-parent-system-data'.
    """
    subsystems_md = os.path.join(dot_gald3r, "SUBSYSTEMS.md")
    product_systems_md = os.path.join(dot_gald3r, "PRODUCT_SYSTEMS.md")
    specs_dir = os.path.join(dot_gald3r, "subsystems")

    if not os.path.isfile(subsystems_md):
        return "no-subsystems-md"
    if not os.path.isfile(product_systems_md):
        return "no-product-systems-md"
    if not os.path.isdir(specs_dir):
        return "no-parent-system-data"

    specs = sorted(
        os.path.join(r, f)
        for r, _dirs, files in os.walk(specs_dir)
        for f in files if f.lower().endswith(".md")
    )
    if not specs:
        return "no-parent-system-data"

    by_group: Dict[str, List[dict]] = {}
    ungrouped: List[dict] = []
    any_parent = False

    def _unquote(v: str) -> str:
        return v.strip().strip('"').strip("'")

    for spec in specs:
        fm = read_front_matter(spec)
        if not fm.has_front_matter:
            continue
        spec_name = os.path.basename(spec)
        name = _unquote(fm.fields["name"]) if "name" in fm.fields \
            else os.path.splitext(spec_name)[0]
        status = _unquote(fm.fields["status"]) if "status" in fm.fields else "active"
        rel = "subsystems/" + spec_name
        purpose = get_subsystem_purpose(fm.lines)
        parent = _unquote(fm.fields["parent_system"]) if "parent_system" in fm.fields else ""
        row = {"name": name, "status": status, "rel": rel, "purpose": purpose}
        if not parent.strip():
            ungrouped.append(row)
        else:
            any_parent = True
            by_group.setdefault(parent, []).append(row)

    # KEY NO-OP guard: no spec carries parent_system: -> do nothing at all.
    if not any_parent:
        return "no-parent-system-data"

    defined_groups = get_defined_groups_list(product_systems_md)
    ordered_groups: List[str] = []
    for g in defined_groups:
        if g in by_group and g not in ordered_groups:
            ordered_groups.append(g)
    for g in by_group:
        if g not in ordered_groups:
            ordered_groups.append(g)

    idx: List[str] = ["## Subsystem Index", ""]
    idx.append("*(Grouped by L1 product system -- regenerated by migrate_schemas.ps1 "
               "from parent_system: tags.)*")
    for g in ordered_groups:
        idx += ["", f"### {g}", "",
                "| Subsystem | Status | Spec File | Purpose |",
                "|-----------|--------|-----------|---------|"]
        for row in sorted(by_group[g], key=lambda r: r["name"]):
            idx.append("| {0} | {1} | `{2}` | {3} |".format(
                row["name"], row["status"], row["rel"], row["purpose"]))
    if ungrouped:
        idx += ["", "### Ungrouped (run @g-subsystem-audit)", "",
                "| Subsystem | Status | Spec File | Purpose |",
                "|-----------|--------|-----------|---------|"]
        for row in sorted(ungrouped, key=lambda r: r["name"]):
            idx.append("| {0} | {1} | `{2}` | {3} |".format(
                row["name"], row["status"], row["rel"], row["purpose"]))

    # Splice in place of the existing '## Subsystem Index' section.
    fm_main = read_front_matter(subsystems_md)
    all_lines = list(fm_main.lines)
    start_idx = -1
    end_idx = len(all_lines)
    for i, line in enumerate(all_lines):
        if re.match(r"^##\s+Subsystem Index\s*$", line, re.IGNORECASE):
            start_idx = i
            break
    if start_idx < 0:
        return "index-section-missing"
    for i in range(start_idx + 1, len(all_lines)):
        if re.match(r"^##\s", all_lines[i]):
            end_idx = i
            break

    rebuilt = all_lines[:start_idx] + idx + [""] + all_lines[end_idx:]

    if do_apply:
        with open(subsystems_md, "w", encoding="utf-8", newline="") as fh:
            fh.write(fm_main.newline.join(rebuilt))
        return "regenerated"
    return "to-regenerate"
