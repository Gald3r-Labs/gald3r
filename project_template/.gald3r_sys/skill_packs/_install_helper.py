#!/usr/bin/env python3
"""Shared platform installer logic for personality and skill packs (T1601,
PS1-KILL epic T667 -- Python port of ``_install_helper.ps1``).

Imported by a pack's own ``install.py`` via:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import _install_helper as helper

Platform discovery: reads ``.gald3r_sys/platforms/`` to enumerate all supported
platforms, then loads capabilities from
``.gald3r_sys/_platform_capabilities.json``. Only installs to platforms whose
folders actually exist in the target project.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

_DEFAULT_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    ".cursor": {"hasRules": True, "rulesExt": ".mdc", "hasSkills": True,
                "rulesDir": "rules", "skillsDir": "skills"},
    ".claude": {"hasRules": True, "rulesExt": ".md", "hasSkills": True,
                "rulesDir": "rules", "skillsDir": "skills"},
}
_DEFAULT_KNOWN_PLATFORMS = [".cursor", ".claude", ".agent", ".codex", ".opencode", ".copilot"]


def find_gald3r_sys_root(start: Path) -> Path:
    """Locate the project root containing ``.gald3r_sys/`` from a helper-relative path.

    Mirrors the .ps1's own-path-based discovery: first assumes ``start`` is two
    levels below the project root (this file's own location, ``.gald3r_sys/
    skill_packs/_install_helper.py``), falling back to walking up to 6 levels.
    """
    candidate = start.parent.parent
    if (candidate / "_platform_capabilities.json").is_file():
        return candidate.parent if candidate.name == ".gald3r_sys" else candidate
    search = start
    for _ in range(6):
        search = search.parent
        if (search / ".gald3r_sys" / "_platform_capabilities.json").is_file():
            return search
    return candidate


def load_capabilities(gald_sys_root: Path) -> Dict[str, Dict[str, Any]]:
    """Load the platform capabilities map, falling back to minimal defaults."""
    capabilities_path = gald_sys_root / ".gald3r_sys" / "_platform_capabilities.json"
    if capabilities_path.is_file():
        try:
            return json.loads(capabilities_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    print(f"WARNING: Could not find _platform_capabilities.json at "
          f"{capabilities_path} -- using minimal defaults")
    return dict(_DEFAULT_CAPABILITIES)


def load_known_platforms(gald_sys_root: Path) -> List[str]:
    """Discover all supported platform names from .gald3r_sys/platforms/."""
    platforms_dir = gald_sys_root / ".gald3r_sys" / "platforms"
    if platforms_dir.is_dir():
        return sorted(p.name for p in platforms_dir.iterdir() if p.is_dir())
    return list(_DEFAULT_KNOWN_PLATFORMS)


def get_active_platforms(project_root: Path, known_platforms: List[str]) -> List[str]:
    """Return only platforms that exist as folders in the target project."""
    return [p for p in known_platforms if (project_root / p).is_dir()]


def get_platform_cap(capabilities: Dict[str, Dict[str, Any]], platform: str) -> Dict[str, Any]:
    """Get the capability dict for a platform, with safe defaults."""
    cap = capabilities.get(platform)
    if cap is None:
        return {"hasRules": False, "rulesExt": ".md", "hasSkills": False,
                "rulesDir": "rules", "skillsDir": "skills", "copilotInstructions": None}
    return {
        "hasRules": bool(cap.get("hasRules")),
        "rulesExt": str(cap.get("rulesExt", "")),
        "hasSkills": bool(cap.get("hasSkills")),
        "rulesDir": str(cap.get("rulesDir", "")),
        "skillsDir": str(cap.get("skillsDir", "")),
        "copilotInstructions": cap.get("copilotInstructions"),
    }


def install_rules(source_dir: Path, project_root: Path, platforms: List[str],
                   capabilities: Dict[str, Dict[str, Any]]) -> None:
    """Install .md rule files into each active platform's rules dir (or append
    to copilot-instructions.md when the platform uses that convention)."""
    if not source_dir.is_dir():
        return
    md_files = sorted(source_dir.glob("*.md"))
    if not md_files:
        return

    for platform in platforms:
        cfg = get_platform_cap(capabilities, platform)

        if cfg["copilotInstructions"]:
            ci_path = project_root / cfg["copilotInstructions"]
            ci_path.parent.mkdir(parents=True, exist_ok=True)
            for f in md_files:
                with open(ci_path, "a", encoding="utf-8") as fh:
                    fh.write("\n---\n" + f.read_text(encoding="utf-8"))
                print(f"  -> {cfg['copilotInstructions']} (appended {f.name})")
            continue

        if not cfg["hasRules"] or not cfg["rulesDir"]:
            continue
        dest_dir = project_root / platform / cfg["rulesDir"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in md_files:
            dest_name = f.stem + cfg["rulesExt"]
            shutil.copyfile(f, dest_dir / dest_name)
            print(f"  -> {platform}/{cfg['rulesDir']}/{dest_name}")


def remove_rules(file_basenames: List[str], project_root: Path, platforms: List[str],
                  capabilities: Dict[str, Dict[str, Any]]) -> None:
    """Remove previously-installed rule files (copilot-instructions appends are
    not reversible per-file, so those platforms are skipped)."""
    for platform in platforms:
        cfg = get_platform_cap(capabilities, platform)
        if cfg["copilotInstructions"]:
            continue
        if not cfg["hasRules"] or not cfg["rulesDir"]:
            continue
        rules_dir = project_root / platform / cfg["rulesDir"]
        for base in file_basenames:
            target = rules_dir / (base + cfg["rulesExt"])
            if target.is_file():
                target.unlink()
                print(f"  x removed {platform}/{cfg['rulesDir']}/{base}{cfg['rulesExt']}")


def install_skills(source_skills_dir: Path, project_root: Path, platforms: List[str],
                    capabilities: Dict[str, Dict[str, Any]]) -> None:
    """Copy each skill folder into every active platform's skills dir."""
    if not source_skills_dir.is_dir():
        return
    for platform in platforms:
        cfg = get_platform_cap(capabilities, platform)
        if not cfg["hasSkills"] or not cfg["skillsDir"]:
            continue
        dest_base = project_root / platform / cfg["skillsDir"]
        for skill_dir in sorted(p for p in source_skills_dir.iterdir() if p.is_dir()):
            dest = dest_base / skill_dir.name
            dest.mkdir(parents=True, exist_ok=True)
            for src_file in skill_dir.rglob("*"):
                if src_file.is_dir():
                    continue
                rel = src_file.relative_to(skill_dir)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_file, target)
            print(f"  -> {platform}/{cfg['skillsDir']}/{skill_dir.name}/")


def remove_skills(skill_names: List[str], project_root: Path, platforms: List[str],
                   capabilities: Dict[str, Dict[str, Any]]) -> None:
    """Remove installed skill folders. Never silently removes ``_evolved`` variants."""
    for platform in platforms:
        cfg = get_platform_cap(capabilities, platform)
        if not cfg["hasSkills"] or not cfg["skillsDir"]:
            continue
        skills_dir = project_root / platform / cfg["skillsDir"]
        for name in skill_names:
            evolved = skills_dir / f"{name}_evolved"
            if evolved.is_dir():
                print(f"  ! Skipping {name}_evolved in {platform} "
                      f"(user-evolved -- use --force to remove)")
                continue
            target = skills_dir / name
            if target.is_dir():
                shutil.rmtree(target)
                print(f"  x removed {platform}/{cfg['skillsDir']}/{name}/")


class InstallHelper:
    """Convenience bundle: resolves the gald3r_sys root + capabilities once,
    then exposes the module-level functions as bound methods."""

    def __init__(self, project_root: Optional[Path] = None,
                 helper_path: Optional[Path] = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        start = Path(helper_path) if helper_path else Path(__file__).resolve()
        self.gald_sys_root = find_gald3r_sys_root(start)
        self.capabilities = load_capabilities(self.gald_sys_root)
        self.known_platforms = load_known_platforms(self.gald_sys_root)

    def active_platforms(self) -> List[str]:
        return get_active_platforms(self.project_root, self.known_platforms)

    def platform_cap(self, platform: str) -> Dict[str, Any]:
        return get_platform_cap(self.capabilities, platform)

    def install_rules(self, source_dir: Path, platforms: Optional[List[str]] = None) -> None:
        install_rules(Path(source_dir), self.project_root,
                     platforms or self.active_platforms(), self.capabilities)

    def remove_rules(self, file_basenames: List[str],
                      platforms: Optional[List[str]] = None) -> None:
        remove_rules(file_basenames, self.project_root,
                    platforms or self.active_platforms(), self.capabilities)

    def install_skills(self, source_skills_dir: Path,
                        platforms: Optional[List[str]] = None) -> None:
        install_skills(Path(source_skills_dir), self.project_root,
                       platforms or self.active_platforms(), self.capabilities)

    def remove_skills(self, skill_names: List[str],
                       platforms: Optional[List[str]] = None) -> None:
        remove_skills(skill_names, self.project_root,
                      platforms or self.active_platforms(), self.capabilities)
