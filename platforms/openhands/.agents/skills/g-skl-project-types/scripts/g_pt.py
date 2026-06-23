#!/usr/bin/env python3
"""g-pt — workflow-profile management CLI (T417, BUG-149 rename).

`@g-pt` ("project type") lets users list, switch, copy, locate, and validate
gald3r Workflow Profiles without hand-editing YAML. It is the management
front-end for the profiles consumed by ``load_profile.py`` (T1239/T1335).

This CLI deliberately REUSES the profile-resolution primitives in
``load_profile.py`` rather than re-implementing them:

* :func:`load_profile.find_project_root` — walk up to the ``.gald3r/`` root.
* :func:`load_profile.resolve_profile` — the hybrid activation chain that
  decides which profile is *active* (task frontmatter > PROJECT.md >
  ``.identity`` > ``.project_type`` > freeform).
* :data:`load_profile.PROFILE_ALIASES` — legacy id normalization
  (e.g. ``software_development`` -> ``software_dev``).

Subcommands:
  list                     List built-in + custom profiles, mark the active one.
  use <profile>            Set ``workflow_profile: <profile>`` in PROJECT.md.
  copy <src> <new-name>    Copy ``<src>.yaml`` to ``<new-name>.yaml`` (rewrites id/name).
  edit <profile>           Print the resolved absolute path to ``<profile>.yaml``.
  validate <profile>       Structurally validate a profile; non-zero exit on any problem.

Profiles live as individual ``<id>.yaml`` files under
``.gald3r/config/workflow_profiles/``. The original T417 spec mentioned a
single ``custom.yaml``; this is reconciled to the *real* convention the loader
uses — one file per profile, read by name — so ``copy`` writes
``<new-name>.yaml`` (see the task report / docstring note).
"""
# @subsystems: TASK_MANAGEMENT
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- Reuse load_profile.py (sibling module) -------------------------------
# Mirror load_profile.py's engine-bootstrap pattern: make the sibling module
# importable whether g_pt.py is run as a script or imported as a module.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import load_profile  # noqa: E402  (sibling module; path inserted above)
from load_profile import (  # noqa: E402
    PROFILE_ALIASES,
    find_project_root,
    resolve_profile,
)

PROFILES_SUBDIR = ("config", "workflow_profiles")
REQUIRED_FIELDS = ("id", "name", "task_statuses")


# --------------------------------------------------------------------------
# Path / resolution helpers (thin wrappers over load_profile primitives)
# --------------------------------------------------------------------------
def get_profiles_dir(root: Path) -> Path:
    """Return the ``.gald3r/config/workflow_profiles/`` directory for ``root``.

    Args:
        root: Repo root containing a ``.gald3r/`` directory.

    Returns:
        Absolute path to the workflow_profiles directory (may not yet exist).
    """
    return root.joinpath(".gald3r", *PROFILES_SUBDIR)


def get_project_md(root: Path) -> Path:
    """Return the path to ``.gald3r/PROJECT.md`` for ``root``.

    Args:
        root: Repo root containing a ``.gald3r/`` directory.

    Returns:
        Absolute path to PROJECT.md (may not yet exist).
    """
    return root / ".gald3r" / "PROJECT.md"


def normalize_profile_id(name: str) -> str:
    """Lower-case and alias-normalize a profile id the way the loader does.

    Args:
        name: Raw profile id as typed by the user.

    Returns:
        The canonical profile id (e.g. ``software_development`` -> ``software_dev``).
    """
    key = name.strip().lower()
    return PROFILE_ALIASES.get(key, key)


def profile_path(profiles_dir: Path, name: str) -> Path:
    """Resolve the ``<profile>.yaml`` path for ``name`` (after alias normalize).

    Args:
        profiles_dir: The workflow_profiles directory.
        name: Profile id (raw or canonical).

    Returns:
        Absolute path to the profile's YAML file (may not exist).
    """
    return profiles_dir / f"{normalize_profile_id(name)}.yaml"


def list_profile_ids(profiles_dir: Path) -> List[str]:
    """List profile ids present in ``profiles_dir`` (file stem of each ``*.yaml``).

    Args:
        profiles_dir: The workflow_profiles directory.

    Returns:
        Sorted list of profile ids; empty if the directory is missing.
    """
    if not profiles_dir.is_dir():
        return []
    return sorted(p.stem for p in profiles_dir.glob("*.yaml"))


def resolve_active(root: Path) -> str:
    """Return the active profile id using the loader's hybrid activation chain.

    Args:
        root: Repo root containing a ``.gald3r/`` directory.

    Returns:
        The active, alias-normalized profile id.
    """
    return normalize_profile_id(resolve_profile(root, None))


# --------------------------------------------------------------------------
# YAML load helper (shared by validate / copy)
# --------------------------------------------------------------------------
def _load_yaml(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse a YAML file into a dict.

    Args:
        path: File to parse.

    Returns:
        A ``(data, error)`` tuple. On success ``data`` is the parsed mapping
        and ``error`` is ``None``. On failure ``data`` is ``None`` and
        ``error`` is a human-readable message.
    """
    if not path.exists():
        return None, f"file not found: {path}"
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return None, f"cannot read {path}: {exc}"
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None, "PyYAML not installed (uv pip install pyyaml)"
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    if not isinstance(loaded, dict):
        return None, "top-level YAML is not a mapping/object"
    return loaded, None


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def cmd_list(root: Path) -> int:
    """Print every profile, marking the active one with ``*``.

    Args:
        root: Repo root containing a ``.gald3r/`` directory.

    Returns:
        Process exit code (0 on success, 1 if no profiles found).
    """
    profiles_dir = get_profiles_dir(root)
    ids = list_profile_ids(profiles_dir)
    if not ids:
        print(f"No profiles found under {profiles_dir}", file=sys.stderr)
        return 1
    active = resolve_active(root)
    print(f"Workflow profiles ({profiles_dir}):")
    for pid in ids:
        marker = "*" if pid == active else " "
        # Pull the human name when PyYAML is available; tolerate failures.
        data, _ = _load_yaml(profiles_dir / f"{pid}.yaml")
        name = ""
        if data is not None and isinstance(data.get("name"), str):
            name = f" — {data['name']}"
        suffix = "  (active)" if pid == active else ""
        print(f"  {marker} {pid}{name}{suffix}")
    return 0


def _set_project_md_field(project_md: Path, profile: str) -> str:
    """Insert or update ``workflow_profile: <profile>`` in PROJECT.md frontmatter.

    The field is written into the leading ``---`` YAML frontmatter block. If
    PROJECT.md has no frontmatter block, one is created at the top. An existing
    ``workflow_profile:`` line is replaced in place.

    Args:
        project_md: Path to PROJECT.md (must exist).
        profile: Canonical profile id to record.

    Returns:
        A human-readable description of the action taken.
    """
    text = project_md.read_text(encoding="utf-8-sig")
    # Preserve the platform's newline style; default to the OS default.
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split("\n")
    # Strip a trailing '\r' left over from a CRLF split so we re-join cleanly.
    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in lines]

    field_line = f"workflow_profile: {profile}"

    # Replace an existing field anywhere in the file (frontmatter is at top,
    # but be liberal so we never produce a duplicate).
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("workflow_profile:"):
            lines[i] = field_line
            project_md.write_text(newline.join(lines), encoding="utf-8")
            return f"updated workflow_profile -> {profile} in {project_md}"

    # No existing field. Insert into the frontmatter block if present.
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines.insert(i, field_line)
                project_md.write_text(newline.join(lines), encoding="utf-8")
                return f"added workflow_profile: {profile} to frontmatter of {project_md}"
        # Frontmatter open but never closed — fall through to prepend a block.

    # No frontmatter block — create one at the very top.
    block = ["---", field_line, "---", ""]
    lines = block + lines
    project_md.write_text(newline.join(lines), encoding="utf-8")
    return f"created frontmatter with workflow_profile: {profile} in {project_md}"


def cmd_use(root: Path, profile: str) -> int:
    """Set the active profile by writing ``workflow_profile:`` to PROJECT.md.

    Args:
        root: Repo root containing a ``.gald3r/`` directory.
        profile: Profile id to activate (validated to exist first).

    Returns:
        Process exit code (0 on success, 1 on error).
    """
    profiles_dir = get_profiles_dir(root)
    canonical = normalize_profile_id(profile)
    target = profile_path(profiles_dir, canonical)
    if not target.exists():
        available = ", ".join(list_profile_ids(profiles_dir)) or "(none)"
        print(
            f"ERROR: profile '{profile}' (resolved '{canonical}') not found. "
            f"Available: {available}",
            file=sys.stderr,
        )
        return 1
    project_md = get_project_md(root)
    if not project_md.exists():
        print(f"ERROR: PROJECT.md not found at {project_md}", file=sys.stderr)
        return 1
    msg = _set_project_md_field(project_md, canonical)
    print(msg)
    return 0


def cmd_copy(root: Path, src: str, new_name: str) -> int:
    """Copy ``<src>.yaml`` to ``<new-name>.yaml``, rewriting its id/name.

    Args:
        root: Repo root containing a ``.gald3r/`` directory.
        src: Source profile id to copy from (must exist).
        new_name: Target profile id to create (must not exist).

    Returns:
        Process exit code (0 on success, 1 on error).
    """
    profiles_dir = get_profiles_dir(root)
    src_canon = normalize_profile_id(src)
    # The new name is taken literally (not alias-normalized) so users can
    # freely create e.g. "my_workflow"; only lower/strip for filesystem safety.
    dst_id = new_name.strip().lower()
    src_path = profile_path(profiles_dir, src_canon)
    dst_path = profiles_dir / f"{dst_id}.yaml"

    if not src_path.exists():
        available = ", ".join(list_profile_ids(profiles_dir)) or "(none)"
        print(
            f"ERROR: source profile '{src}' (resolved '{src_canon}') not found. "
            f"Available: {available}",
            file=sys.stderr,
        )
        return 1
    if not dst_id:
        print("ERROR: new profile name is empty", file=sys.stderr)
        return 1
    if dst_path.exists():
        print(f"ERROR: target profile '{dst_id}' already exists at {dst_path}",
              file=sys.stderr)
        return 1

    shutil.copyfile(src_path, dst_path)
    _rewrite_id_name(dst_path, dst_id)
    print(f"copied {src_path.name} -> {dst_path.name} (id/name set to '{dst_id}')")
    return 0


def _rewrite_id_name(path: Path, new_id: str) -> None:
    """Rewrite the top-level ``id:`` and ``name:`` lines of a profile YAML.

    Does a line-oriented edit (not a full YAML re-serialize) so the file's
    comments and formatting are preserved. ``name`` is set to a Title Cased
    form of ``new_id`` (underscores -> spaces) when a ``name:`` line exists.

    Args:
        path: Profile YAML file to edit in place.
        new_id: The new profile id.
    """
    text = path.read_text(encoding="utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split("\n")
    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in lines]
    pretty_name = new_id.replace("_", " ").title()
    found_id = False
    found_name = False
    for i, ln in enumerate(lines):
        stripped = ln.lstrip()
        if not found_id and stripped.startswith("id:"):
            lines[i] = f"id: {new_id}"
            found_id = True
        elif not found_name and stripped.startswith("name:"):
            lines[i] = f"name: {pretty_name}"
            found_name = True
    path.write_text(newline.join(lines), encoding="utf-8")


def cmd_edit(root: Path, profile: str) -> int:
    """Print the resolved absolute path to ``<profile>.yaml`` (no-GUI-safe edit).

    Args:
        root: Repo root containing a ``.gald3r/`` directory.
        profile: Profile id to locate (must exist).

    Returns:
        Process exit code (0 on success, 1 if the profile is missing).
    """
    profiles_dir = get_profiles_dir(root)
    canonical = normalize_profile_id(profile)
    target = profile_path(profiles_dir, canonical)
    if not target.exists():
        available = ", ".join(list_profile_ids(profiles_dir)) or "(none)"
        print(
            f"ERROR: profile '{profile}' (resolved '{canonical}') not found. "
            f"Available: {available}",
            file=sys.stderr,
        )
        return 1
    print(str(target))
    return 0


def validate_profile_data(data: Dict[str, Any]) -> List[str]:
    """Structurally validate a parsed profile mapping.

    Checks:
      * required fields present (``id``, ``name``, ``task_statuses``);
      * ``task_statuses`` is a non-empty list of mappings each with an ``id``;
      * no duplicate status ids;
      * ``transitions`` (if present) reference only defined status ids.

    Args:
        data: The parsed profile mapping.

    Returns:
        A list of problem strings; empty if the profile is valid.
    """
    problems: List[str] = []

    for field in REQUIRED_FIELDS:
        if field not in data or data[field] in (None, "", []):
            problems.append(f"missing required field: {field}")

    statuses = data.get("task_statuses")
    status_ids: List[str] = []
    if statuses is None:
        # Already reported as a missing required field above.
        pass
    elif not isinstance(statuses, list) or not statuses:
        problems.append("task_statuses must be a non-empty list")
    else:
        seen = set()
        for idx, entry in enumerate(statuses):
            if not isinstance(entry, dict):
                problems.append(f"task_statuses[{idx}] is not a mapping")
                continue
            sid = entry.get("id")
            if not sid:
                problems.append(f"task_statuses[{idx}] missing 'id'")
                continue
            if sid in seen:
                problems.append(f"duplicate status id: {sid}")
            seen.add(sid)
            status_ids.append(sid)

    # transitions: optional. Accept either a dict {from: [to, ...]} or a list
    # of {from, to} mappings. Any referenced id must be a defined status id.
    transitions = data.get("transitions")
    if transitions is not None and status_ids:
        defined = set(status_ids)
        refs: List[str] = []
        if isinstance(transitions, dict):
            for frm, tos in transitions.items():
                refs.append(str(frm))
                if isinstance(tos, list):
                    refs.extend(str(t) for t in tos)
                elif tos is not None:
                    refs.append(str(tos))
        elif isinstance(transitions, list):
            for entry in transitions:
                if isinstance(entry, dict):
                    if "from" in entry:
                        refs.append(str(entry["from"]))
                    to_val = entry.get("to")
                    if isinstance(to_val, list):
                        refs.extend(str(t) for t in to_val)
                    elif to_val is not None:
                        refs.append(str(to_val))
        else:
            problems.append("transitions must be a mapping or a list")
        for ref in refs:
            if ref not in defined:
                problems.append(f"transition references unknown status id: {ref}")

    return problems


def cmd_validate(root: Path, profile: str) -> int:
    """Validate a profile and report each problem; non-zero exit on any.

    Args:
        root: Repo root containing a ``.gald3r/`` directory.
        profile: Profile id to validate (must exist).

    Returns:
        Process exit code (0 if valid, 1 if any problem is found).
    """
    profiles_dir = get_profiles_dir(root)
    canonical = normalize_profile_id(profile)
    target = profile_path(profiles_dir, canonical)
    data, err = _load_yaml(target)
    if err is not None:
        print(f"INVALID {canonical}: {err}", file=sys.stderr)
        return 1
    assert data is not None  # narrowed by err is None
    problems = validate_profile_data(data)
    if problems:
        print(f"INVALID {canonical} ({len(problems)} problem(s)):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK {canonical}: valid")
    return 0


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the ``g-pt`` CLI.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="g_pt",
        description="g-pt — list, switch, copy, locate, and validate gald3r "
                    "workflow profiles (T417).",
        allow_abbrev=False,
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default=None,
        help="Repo root containing .gald3r/. Defaults to walking up from the script.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all profiles, marking the active one.")

    p_use = sub.add_parser("use", help="Set the active profile in PROJECT.md.")
    p_use.add_argument("profile", help="Profile id to activate.")

    p_copy = sub.add_parser("copy", help="Copy a profile to a new name.")
    p_copy.add_argument("src", help="Source profile id.")
    p_copy.add_argument("new_name", help="New profile id (file <new-name>.yaml).")

    p_edit = sub.add_parser("edit", help="Print the absolute path to a profile YAML.")
    p_edit.add_argument("profile", help="Profile id to locate.")

    p_val = sub.add_parser("validate", help="Structurally validate a profile.")
    p_val.add_argument("profile", help="Profile id to validate.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)

    root = find_project_root(args.project_root)

    if args.command == "list":
        return cmd_list(root)
    if args.command == "use":
        return cmd_use(root, args.profile)
    if args.command == "copy":
        return cmd_copy(root, args.src, args.new_name)
    if args.command == "edit":
        return cmd_edit(root, args.profile)
    if args.command == "validate":
        return cmd_validate(root, args.profile)
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable; parser.error raises SystemExit


if __name__ == "__main__":
    sys.exit(main())
