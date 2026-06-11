#!/usr/bin/env python3
"""Python port of load_profile.ps1 (T1585).

Load a gald3r Workflow Profile YAML and emit a JSON snapshot for agents.
T1281 (Project Types epic); hybrid activation + freeform fallback added by
T1335 (BUG-092 reconciliation). Phase 1 loader stub — informational only;
commands still use their hardcoded status lists until Phase 2.

Hybrid activation chain (highest priority first, T1335 decision #3):
  1. -ProjectType parameter (explicit override, e.g. for testing)
  2. Task frontmatter `workflow_profile:` (when -TaskFile is supplied)
  3. PROJECT.md `workflow_profile:` field
  4. .gald3r/.identity `project_type=` (or .gald3r/.project_type dotfile)
  5. freeform (final safe-default fallback)

Filenames are canonical: <profile>.yaml. The five canonical profiles are
software_development, content_creation, 3d_modeling, research_analysis,
freeform. If a resolved profile file is missing, the loader warns and loads
freeform.yaml.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

FALLBACK = "freeform"  # T1335 decision #3: freeform is the safe default

# T1239: normalize legacy project_type / project-types-epic ids onto the
# canonical T1238 workflow-profile filenames actually shipped under
# .gald3r/config/workflow_profiles/. Keeps the .identity project_type= switch
# (e.g. software_development) resolving to the real software_dev.yaml file.
PROFILE_ALIASES = {
    "software_development": "software_dev",
    "software": "software_dev",
    "research_analysis": "research",
    "research_science": "research",
    "content": "content_creation",
}


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


def _warn(msg: str) -> None:
    """Write-Warning equivalent."""
    print(f"WARNING: {msg}", file=sys.stderr)


def find_project_root(start: Optional[str]) -> Path:
    """Walk up (max 12 levels) from `start` or the script dir to find .gald3r/."""
    d = Path(start) if start else Path(__file__).resolve().parent
    for _ in range(12):
        if (d / ".gald3r").exists():
            return d
        parent = d.parent
        if parent == d:
            break
        d = parent
    return Path.cwd()


def get_workflow_profile_field(path: Optional[Path]) -> Optional[str]:
    """Read a `workflow_profile:` value from a markdown file's YAML frontmatter."""
    if path is None or not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    for line in text.splitlines():
        m = re.match(r"^\s*workflow_profile\s*:\s*(.+?)\s*$", line)
        if m:
            val = m.group(1).strip().strip('"').strip("'").lower()
            if val and val != "null":
                return val
            return None
    return None


def resolve_profile(root: Path, task_file_path: Optional[str]) -> str:
    """Hybrid activation chain — returns the resolved profile id (string)."""
    # 2. Task frontmatter workflow_profile: (highest after explicit param)
    if task_file_path:
        task_profile = get_workflow_profile_field(Path(task_file_path))
        if task_profile:
            return task_profile

    # 3. PROJECT.md workflow_profile:
    proj_profile = get_workflow_profile_field(root / ".gald3r" / "PROJECT.md")
    if proj_profile:
        return proj_profile

    # 4a. .identity combined file: project_type=...
    identity = root / ".gald3r" / ".identity"
    if identity.exists():
        try:
            for line in identity.read_text(encoding="utf-8-sig").splitlines():
                m = re.match(r"^\s*project_type\s*=\s*(.+)\s*$", line)
                if m:
                    v = m.group(1).strip().lower()
                    if v:
                        return v
                    break
        except OSError:
            pass
    # 4b. .project_type dotfile (gald3r_install idiom)
    dotfile = root / ".gald3r" / ".project_type"
    if dotfile.exists():
        try:
            v = dotfile.read_text(encoding="utf-8-sig").strip().lower()
            if v:
                return v
        except OSError:
            pass

    # 5. final fallback
    return FALLBACK


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point — mirrors the PS1 param() block."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Load a gald3r Workflow Profile YAML and emit a JSON "
                    "snapshot (Python port of load_profile.ps1, T1281/T1335).",
        allow_abbrev=False)
    parser.add_argument("-ProjectType", "--project-type", dest="project_type",
                        default=None,
                        help="Override the resolved profile (e.g. freeform).")
    parser.add_argument("-TaskFile", "--task-file", dest="task_file", default=None,
                        help="Optional path to a task .md file; its "
                             "workflow_profile: frontmatter field wins over "
                             "PROJECT.md and .identity.")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=None,
                        help="Repo root containing .gald3r/. Defaults to walking "
                             "up from the script.")
    args = parser.parse_args(argv)

    root = find_project_root(args.project_root)
    project_type = args.project_type
    if not project_type:
        project_type = resolve_profile(root, args.task_file)
    project_type = project_type.lower()
    if project_type in PROFILE_ALIASES:
        project_type = PROFILE_ALIASES[project_type]

    profile_dir = root / ".gald3r" / "config" / "workflow_profiles"
    profile_path = profile_dir / f"{project_type}.yaml"

    if not profile_path.exists():
        # T1239: prefer freeform.yaml; if absent, fall back to the T1238 default
        # profile (software_dev) before the builtin minimal snapshot below.
        freeform_path = profile_dir / f"{FALLBACK}.yaml"
        default_path = profile_dir / "software_dev.yaml"
        if freeform_path.exists():
            _warn(f"Profile '{project_type}' not found; falling back to '{FALLBACK}'.")
            project_type = FALLBACK
            profile_path = freeform_path
        elif default_path.exists():
            _warn(f"Profile '{project_type}' not found and no '{FALLBACK}.yaml'; "
                  "falling back to 'software_dev'.")
            project_type = "software_dev"
            profile_path = default_path
        else:
            profile_path = freeform_path

    if not profile_path.exists():
        # Last-resort minimal snapshot so callers never hard-fail (freeform shape).
        snapshot: Dict[str, Any] = {
            "id": FALLBACK,
            "name": "Freeform",
            "source": "builtin-fallback",
            "task_statuses": ["open", "in-progress", "done", "paused", "cancelled"],
            "task_types": ["task", "note", "chore"],
            "default_task_type": "task",
            "review_gate": {"required": False, "self_verify_allowed": True},
        }
        print(json.dumps(snapshot, indent=2))
        return 0

    raw_yaml = profile_path.read_text(encoding="utf-8-sig")

    # Prefer PyYAML; degrade gracefully if absent (no hard dependency).
    parsed: Optional[Dict[str, Any]] = None
    try:
        import yaml  # type: ignore[import-untyped]

        try:
            loaded = yaml.safe_load(raw_yaml)
            if isinstance(loaded, dict):
                parsed = loaded
        except yaml.YAMLError:
            parsed = None
    except ImportError:
        parsed = None

    if parsed is not None:
        parsed["source"] = str(profile_path)
        print(json.dumps(parsed, indent=2, default=str))
    else:
        # No YAML parser available — emit a structured pointer rather than failing.
        _warn("PyYAML not installed; emitting raw-pointer snapshot. "
              "Install with: uv pip install pyyaml")
        print(json.dumps({
            "id": project_type,
            "source": str(profile_path),
            "parsed": False,
            "note": "Install PyYAML for a structured snapshot; raw YAML "
                    "available at source path.",
            "raw_yaml": raw_yaml,
        }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
