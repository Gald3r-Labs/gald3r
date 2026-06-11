#!/usr/bin/env python3
"""Python port of g-hk-vault-resolve.ps1 (T1584).

Resolves the gald3r vault and repos-mirror locations from `.gald3r/.identity`
(`vault_location=` / `repos_location=`) with `.env` fallbacks
(GALD3R_VAULT_LOCATION / GALD3R_KNOWLEDGE_WELL_PATH / GALD3R_REPOS_LOCATION),
falls back to the local `.gald3r/vault/` and `.gald3r/repos/` when the shared
location is unset, `{LOCAL}`, or not writable, and ensures the project's
`projects/<name>/sessions|decisions` directories exist.

Import this from other hooks (the Python analogue of dot-sourcing the .ps1):

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "g_hk_vault_resolve", str(Path(__file__).parent / "g-hk-vault-resolve.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ctx = mod.resolve()

`resolve()` returns a dict mirroring the PS1's exported variables:
  VaultPath, ReposPath, VaultLocalPath, ReposLocalPath, VaultUsingFallback,
  VaultMigrationCandidate, VaultMessages, ProjectId, ProjectName, ProjectDir,
  SessionsDir, DecisionsDir, ProjectRoot.

Standalone execution performs the same resolution/directory creation and
prints nothing (matching the .ps1). Never crashes the session: exits 0.
"""
# @subsystems: VAULT_AND_RESEARCH
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402,F401


def get_gald3r_identity_map(identity_path: Path) -> Dict[str, str]:
    """Parse `.gald3r/.identity` `key=value` lines into a map."""
    id_map = {
        "project_id": "",
        "project_name": "",
        "user_id": "",
        "user_name": "",
        "gald3r_version": "",
        "vault_location": "",
        "repos_location": "",
    }
    if identity_path.is_file():
        for line in identity_path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^(\w+)=(.*)$", line)
            if m:
                id_map[m.group(1)] = m.group(2).strip()
    return id_map


def get_env_setting(env_path: Path, keys: List[str]) -> Optional[str]:
    """Return the first non-empty `KEY=value` for any of `keys` in a .env file."""
    if not env_path.is_file():
        return None
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    for key in keys:
        pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=\s*(.+)$")
        for line in lines:
            m = pattern.match(line)
            if m:
                value = m.group(1).strip().strip('"').strip("'")
                if value:
                    return value
    return None


def test_gald3r_path_writable(path_to_check: str) -> bool:
    """Create the directory if needed and probe a temp write inside it."""
    try:
        p = Path(path_to_check)
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".gald3r_write_probe.tmp"
        probe.write_text("", encoding="utf-8")
        try:
            probe.unlink()
        except OSError:
            pass
        return True
    except (OSError, ValueError):
        return False


def get_markdown_count(path_to_scan: Path) -> int:
    """Count *.md files under a path, excluding `.obsidian/` contents."""
    if not path_to_scan.is_dir():
        return 0
    count = 0
    for f in path_to_scan.rglob("*.md"):
        if f.is_file() and ".obsidian" not in f.parts:
            count += 1
    return count


def resolve(project_root: Optional[str] = None) -> Dict[str, Any]:
    """Resolve vault/repos paths and ensure the directory layout exists."""
    root = Path(project_root) if project_root else Path.cwd()
    identity_path = root / ".gald3r" / ".identity"
    env_path = root / ".env"
    identity = get_gald3r_identity_map(identity_path)

    vault_local_path = root / ".gald3r" / "vault"
    repos_local_path = root / ".gald3r" / "repos"
    vault_using_fallback = False
    vault_migration_candidate = False
    vault_messages: List[str] = []

    vault_location = identity["vault_location"]
    if not vault_location:
        vault_location = get_env_setting(
            env_path, ["GALD3R_VAULT_LOCATION", "GALD3R_KNOWLEDGE_WELL_PATH"]
        ) or ""

    repos_location = identity["repos_location"]
    if not repos_location:
        repos_location = get_env_setting(env_path, ["GALD3R_REPOS_LOCATION"]) or ""

    if not vault_location or vault_location == "{LOCAL}":
        vault_path = vault_local_path
    elif test_gald3r_path_writable(vault_location):
        vault_path = Path(vault_location)
    else:
        vault_path = vault_local_path
        vault_using_fallback = True
        vault_messages.append(
            "Shared vault unavailable; writing to local fallback at `.gald3r/vault/`."
        )

    if not repos_location or repos_location == "{LOCAL}":
        repos_path = repos_local_path
    elif test_gald3r_path_writable(repos_location):
        repos_path = Path(repos_location)
    else:
        repos_path = repos_local_path
        vault_messages.append(
            "Configured repos mirror unavailable; using local `.gald3r/repos/`."
        )

    for path in (vault_local_path, repos_local_path, vault_path, repos_path):
        path.mkdir(parents=True, exist_ok=True)

    local_vault_md_count = get_markdown_count(vault_local_path)
    if vault_path != vault_local_path and local_vault_md_count > 0:
        vault_migration_candidate = True
        vault_messages.append(
            f"Local vault contains {local_vault_md_count} markdown files while a"
            " shared vault is configured. Consider running migration."
        )

    project_id = identity["project_id"] or "unknown"

    project_name = identity["project_name"]
    if not project_name or project_name == "{project_name}":
        project_name = root.name

    project_dir = vault_path / "projects" / project_name
    sessions_dir = project_dir / "sessions"
    decisions_dir = project_dir / "decisions"
    for path in (project_dir, sessions_dir, decisions_dir):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "ProjectRoot": str(root),
        "VaultPath": str(vault_path),
        "ReposPath": str(repos_path),
        "VaultLocalPath": str(vault_local_path),
        "ReposLocalPath": str(repos_local_path),
        "VaultUsingFallback": vault_using_fallback,
        "VaultMigrationCandidate": vault_migration_candidate,
        "VaultMessages": vault_messages,
        "ProjectId": project_id,
        "ProjectName": project_name,
        "ProjectDir": str(project_dir),
        "SessionsDir": str(sessions_dir),
        "DecisionsDir": str(decisions_dir),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve gald3r vault/repos paths from .gald3r/.identity and .env;"
            " ensures local fallback directories exist. Prints nothing (matches"
            " the .ps1 — it only exports variables when dot-sourced)."
        )
    )
    parser.parse_args(argv)
    resolve()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        sys.exit(0)
