"""Worktree root resolution, ownership-marker IO, and metadata queries.

Python port of gald3r_worktree.ps1 (T1585) — manifest/metadata layer.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from worktree_lib.gitio import (
    WorktreeError,
    full_path,
    git_exit_code,
    invoke_git,
    is_blank,
    parse_datetime,
    path_inside,
    read_json_file,
    safe_segment,
    strings_equal_ci,
    utc_now,
    write_json_file,
)

MARKER_NAME = ".gald3r-worktree.json"


def resolve_repo_root(repo_path: str) -> str:
    """Resolve `repo_path` to the git toplevel directory (PS1 Resolve-RepoRoot)."""
    resolved = Path(repo_path).resolve()
    if not resolved.exists():
        raise WorktreeError(f"Cannot resolve path '{repo_path}' — it does not exist.")
    top = invoke_git(str(resolved), ["rev-parse", "--show-toplevel"]).strip()
    return str(Path(top).resolve())


def default_worktree_root(repo_root: str) -> str:
    """<repo-parent>/.gald3r-worktrees/<repo-name> (PS1 Get-DefaultWorktreeRoot)."""
    repo = Path(repo_root)
    return str(repo.parent / ".gald3r-worktrees" / repo.name)


def resolve_worktree_root(repo_root: str, requested_root: Optional[str]) -> str:
    """Resolve the worktree root; refuse one nested inside the active checkout."""
    root = default_worktree_root(repo_root) if is_blank(requested_root) else full_path(str(requested_root))
    if path_inside(root, repo_root):
        raise WorktreeError(
            f"Worktree root '{root}' is inside active repo '{repo_root}'. "
            "Set GALD3R_WORKTREE_ROOT to a sibling or external path."
        )
    return root


def repo_slug(repo_root: str) -> str:
    """Safe segment from the repo folder name."""
    return safe_segment(Path(repo_root).name)


def branch_name(task_id: str, role: str, owner: str, slug: str, suffix: str) -> str:
    """gald3r/{task}/{role}/{repo_slug}/{owner}-{suffix} (PS1 New-BranchName)."""
    return (
        f"gald3r/{safe_segment(task_id)}/{safe_segment(role)}/{slug}/"
        f"{safe_segment(owner)}-{suffix}"
    )


def worktree_dir_name(task_id: str, role: str, owner: str, slug: str, suffix: str) -> str:
    """{task}-{role}-{repo_slug}-{owner}-{suffix} (PS1 New-WorktreeDirectoryName)."""
    return f"{safe_segment(task_id)}-{safe_segment(role)}-{slug}-{safe_segment(owner)}-{suffix}"


def branch_name_valid(repo_root: str, name: str) -> bool:
    """git check-ref-format --branch validation."""
    return git_exit_code(repo_root, ["check-ref-format", "--branch", name]) == 0


def branch_exists(repo_root: str, name: str) -> bool:
    """git show-ref --verify refs/heads/<name>."""
    return git_exit_code(repo_root, ["show-ref", "--verify", "--quiet", f"refs/heads/{name}"]) == 0


def find_markers(root: str) -> List[Path]:
    """All .gald3r-worktree.json ownership markers under `root` (recursive)."""
    base = Path(root)
    if not base.exists():
        return []
    found: List[Path] = []
    for cur, _dirs, files in os.walk(base):
        if MARKER_NAME in files:
            found.append(Path(cur) / MARKER_NAME)
    return found


def git_worktree_paths(repo_root: str) -> List[str]:
    """Registered worktree paths from ``git worktree list --porcelain``."""
    paths: List[str] = []
    for line in invoke_git(repo_root, ["worktree", "list", "--porcelain"]).splitlines():
        if line.startswith("worktree "):
            paths.append(full_path(line[len("worktree "):]))
    return paths


def is_registered_worktree(repo_root: str, worktree_path: str) -> bool:
    """True when `worktree_path` is registered in git worktree list."""
    target = full_path(worktree_path).lower()
    return any(p.lower() == target for p in git_worktree_paths(repo_root))


def read_metadata(marker_path: Path) -> Optional[Dict[str, Any]]:
    """Parse a marker file; None on failure (PS1 Read-Gald3rWorktreeMetadata)."""
    return read_json_file(marker_path)


def write_metadata(marker_path: Path, metadata: Dict[str, Any]) -> None:
    """Persist a marker file (PS1 Write-Metadata)."""
    write_json_file(marker_path, metadata)


def find_worktree(
    root: str, repo_root: str, task_id: Optional[str], role: str, owner: str
) -> Optional[Dict[str, Any]]:
    """Locate the marker matching repo/task/role/owner (PS1 Find-Gald3rWorktree)."""
    for marker in find_markers(root):
        metadata = read_metadata(marker)
        if metadata is None:
            continue
        if (
            metadata.get("gald3r_owned")
            and strings_equal_ci(metadata.get("repo_root"), repo_root)
            and strings_equal_ci(metadata.get("task_id"), task_id)
            and strings_equal_ci(metadata.get("role"), role)
            and strings_equal_ci(metadata.get("owner"), owner)
        ):
            return metadata
    return None


def get_report(root: str, repo_root: str) -> List[Dict[str, Any]]:
    """All gald3r-owned worktree metadata for this repo (PS1 Get-Gald3rWorktreeReport)."""
    items: List[Dict[str, Any]] = []
    for marker in find_markers(root):
        metadata = read_metadata(marker)
        if metadata is None:
            continue
        if not strings_equal_ci(metadata.get("repo_root"), repo_root):
            continue
        items.append(metadata)
    return items


def dirty_status(repo_root: str) -> List[str]:
    """Non-empty ``git status --short`` lines (PS1 Get-DirtyStatus)."""
    return [line for line in invoke_git(repo_root, ["status", "--short"]).splitlines() if line]


def valid_existing_worktree(repo_root: str, metadata: Optional[Dict[str, Any]]) -> bool:
    """PS1 Test-ValidExistingWorktree — marker + registration + branch check."""
    if metadata is None or not metadata.get("gald3r_owned"):
        return False
    worktree_path = metadata.get("worktree_path") or ""
    if not Path(worktree_path).exists():
        return False
    if not (Path(worktree_path) / MARKER_NAME).exists():
        return False
    if not is_registered_worktree(repo_root, worktree_path):
        return False
    branch = invoke_git(worktree_path, ["branch", "--show-current"]).strip()
    return branch == metadata.get("worktree_branch")


def task_file_for_worktree(
    repo_root: str, task_root: Optional[str], task_id: Optional[str]
) -> Optional[Path]:
    """First spec file for a worktree id under the task root (PS1 Get-TaskFileForWorktree).

    Tries ``task{id}_*.md`` first (task worktrees -- behavior unchanged). When no task
    spec is found, also tries ``bug{id}_*.md`` recursively under ``.gald3r/bugs`` (incl.
    ``bugs/done/`` and any archive) so bug worktrees created via the ``-BugId`` alias
    resolve to their real spec instead of being treated as an expired/missing claim by
    ``task_claim_expired`` (BUG-197).
    """
    base = Path(task_root) if not is_blank(task_root) else Path(repo_root) / ".gald3r" / "tasks"
    if base.exists():
        matches = sorted(p for p in base.glob(f"task{task_id}_*.md") if p.is_file())
        if matches:
            return matches[0]
    bug_base = Path(repo_root) / ".gald3r" / "bugs"
    if bug_base.exists():
        bug_matches = sorted(p for p in bug_base.rglob(f"bug{task_id}_*.md") if p.is_file())
        if bug_matches:
            return bug_matches[0]
    return None


def task_claim_expired(task_file: Optional[Path]) -> bool:
    """PS1 Test-TaskClaimExpired — missing file counts as expired."""
    if task_file is None or not task_file.exists():
        return True
    try:
        text = task_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    match = re.search(r'claim_expires_at:\s*"?([^"\r\n]+)"?', text)
    if not match:
        return False
    expires = parse_datetime(match.group(1), assume_utc=False)
    if expires is None:
        return False
    return expires < utc_now()


def worktree_kept(metadata: Dict[str, Any]) -> bool:
    """True when keep_until is set and still in the future (PS1 Test-WorktreeKept, T1118)."""
    raw = metadata.get("keep_until")
    if raw is None or is_blank(str(raw)):
        return False
    until = parse_datetime(raw, assume_utc=False)
    if until is None:
        return False
    return until > utc_now()
