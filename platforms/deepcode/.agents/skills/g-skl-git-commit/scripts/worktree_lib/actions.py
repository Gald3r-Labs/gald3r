"""Core worktree actions — Create, Remove, Cleanup, Keep, MergeToMain.

Python port of gald3r_worktree.ps1 (T1585) — action layer.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import re
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from worktree_lib.gitio import (
    WorktreeError,
    git_exit_code,
    invoke_git,
    is_blank,
    iso_o,
    parse_datetime,
    short_suffix,
    utc_now,
)
from worktree_lib import manifest as mf

SWARM_LOCK_DIRTY_PATTERN = re.compile(r"\.gald3r-swarm-locks/")


def create_worktree(
    repo_root: str,
    root: str,
    task_id: Optional[str],
    role: str,
    owner: str,
    base_branch: str,
    allow_dirty: bool,
    stale_base_action: str = "Warn",
) -> Dict[str, Any]:
    """PS1 New-Gald3rWorktree — create or reuse, with stale-base detection."""
    if is_blank(task_id):
        raise WorktreeError("-TaskId is required for Create.")
    assert task_id is not None

    existing = mf.find_worktree(root, repo_root, task_id, role, owner)
    if mf.valid_existing_worktree(repo_root, existing):
        assert existing is not None
        current_head = invoke_git(repo_root, ["rev-parse", "HEAD"]).strip()
        stored_base = existing.get("base_sha") or None
        if isinstance(stored_base, str) and not stored_base.strip():
            stored_base = None
        is_stale = stored_base is not None and stored_base != current_head

        if is_stale and stale_base_action == "Recreate":
            # Remove the stale worktree; fall through to fresh creation below.
            remove_worktree(repo_root, existing, apply=True)
        elif is_stale and stale_base_action == "Warn":
            warned = dict(existing)
            warned["stale_base"] = True
            warned["stale_base_detail"] = (
                f"Worktree base {str(stored_base)[:8]} predates current HEAD "
                f"{current_head[:8]}. Pass -StaleBaseAction Recreate to "
                "auto-refresh for rolling waves."
            )
            return warned
        else:
            # Reuse silently (explicit Reuse, or no base_sha on a legacy worktree).
            return existing

    # The ephemeral swarm-lock directory (T1059) never counts toward the dirty gate.
    dirty = [
        line
        for line in mf.dirty_status(repo_root)
        if not SWARM_LOCK_DIRTY_PATTERN.search(line)
    ]
    if dirty and not allow_dirty:
        raise WorktreeError(
            "Active checkout is dirty. Commit/stash changes, or rerun with "
            "-AllowDirty after recording explicit ownership. "
            f"Dirty entries: {'; '.join(dirty)}"
        )

    Path(root).mkdir(parents=True, exist_ok=True)
    slug = mf.repo_slug(repo_root)
    suffix = short_suffix()
    branch = mf.branch_name(task_id, role, owner, slug, suffix)
    if not mf.branch_name_valid(repo_root, branch):
        raise WorktreeError(f"Generated branch name '{branch}' is not a valid Git branch.")
    directory = mf.worktree_dir_name(task_id, role, owner, slug, suffix)
    worktree_path = str(Path(root) / directory)

    # Resolve the base ref to a concrete SHA before creating the worktree so
    # subsequent Create calls can run stale-base detection against it.
    resolved_base_sha = invoke_git(repo_root, ["rev-parse", base_branch]).strip()

    invoke_git(repo_root, ["worktree", "add", "-b", branch, worktree_path, base_branch])

    metadata: Dict[str, Any] = {
        "schema_version": "1.0",
        "gald3r_owned": True,
        "task_id": task_id,
        "role": role,
        "owner": owner,
        "repo_root": repo_root,
        "repo_slug": slug,
        "worktree_path": worktree_path,
        "worktree_branch": branch,
        "base_branch": base_branch,
        "base_sha": resolved_base_sha,
        "created_at": iso_o(utc_now()),
        # T967 — session resume fields; null until the Checkpoint action runs.
        "last_checkpoint_sha": None,
        "continuity_artifact_path": None,
    }
    mf.write_metadata(Path(worktree_path) / mf.MARKER_NAME, metadata)
    return metadata


def remove_worktree(repo_root: str, metadata: Optional[Dict[str, Any]], apply: bool) -> Dict[str, Any]:
    """PS1 Remove-Gald3rWorktree — report-only unless `apply`."""
    if metadata is None or not metadata.get("gald3r_owned"):
        raise WorktreeError("Refusing to remove worktree without gald3r ownership metadata.")

    worktree_path = metadata.get("worktree_path") or ""
    if not (Path(worktree_path) / mf.MARKER_NAME).exists():
        raise WorktreeError(
            f"Refusing to remove '{worktree_path}' because the ownership marker is missing."
        )

    if not apply:
        return {
            "action": "would_remove",
            "worktree_path": worktree_path,
            "worktree_branch": metadata.get("worktree_branch"),
        }

    if not mf.is_registered_worktree(repo_root, worktree_path):
        raise WorktreeError(
            f"Refusing to remove '{worktree_path}' because it is not registered "
            "in git worktree list."
        )

    invoke_git(repo_root, ["worktree", "remove", "--force", worktree_path])
    branch = metadata.get("worktree_branch") or ""
    if mf.branch_exists(repo_root, branch):
        invoke_git(repo_root, ["branch", "-D", branch])
    return {
        "action": "removed",
        "worktree_path": worktree_path,
        "worktree_branch": metadata.get("worktree_branch"),
    }


def keep_worktree(repo_root: str, metadata: Optional[Dict[str, Any]], keep_hours: int) -> Dict[str, Any]:
    """PS1 Set-Gald3rWorktreeKeep (T1118) — stamp keep_until + phase_handoff."""
    if metadata is None or not metadata.get("gald3r_owned"):
        raise WorktreeError(
            "Keep requires an existing gald3r-owned worktree (create it first with -Action Create)."
        )
    marker_path = Path(metadata.get("worktree_path") or "") / mf.MARKER_NAME
    if not marker_path.exists():
        raise WorktreeError(f"Ownership marker missing at '{marker_path}' - refusing to Keep.")

    keep_until = iso_o(utc_now() + timedelta(hours=max(0, keep_hours)))
    updated = dict(metadata)
    updated["phase_handoff"] = True
    updated["keep_until"] = keep_until
    mf.write_metadata(marker_path, updated)

    return {
        "action": "kept",
        "task_id": metadata.get("task_id"),
        "worktree_path": metadata.get("worktree_path"),
        "worktree_branch": metadata.get("worktree_branch"),
        "keep_until": keep_until,
    }


def cleanup_worktrees(
    repo_root: str,
    root: str,
    task_root: Optional[str],
    stale_hours: int,
    apply: bool,
) -> List[Dict[str, Any]]:
    """PS1 Invoke-Gald3rWorktreeCleanup — report-only unless `apply`."""
    cutoff = utc_now() - timedelta(hours=stale_hours)
    results: List[Dict[str, Any]] = []
    for metadata in mf.get_report(root, repo_root):
        # T1118 — never reclaim a worktree mid phase handoff (future keep_until).
        if mf.worktree_kept(metadata):
            continue
        created = parse_datetime(metadata.get("created_at"), assume_utc=False)
        task_file = mf.task_file_for_worktree(repo_root, task_root, metadata.get("task_id"))
        missing_task = task_file is None
        expired_claim = mf.task_claim_expired(task_file)
        missing_branch = not mf.branch_exists(repo_root, metadata.get("worktree_branch") or "")
        missing_path = not Path(metadata.get("worktree_path") or "").exists()
        old_by_age = created is not None and created <= cutoff
        claim_protects = (task_file is not None) and (not expired_claim)
        if (
            missing_path
            or missing_task
            or expired_claim
            or missing_branch
            or (old_by_age and not claim_protects)
        ):
            results.append(remove_worktree(repo_root, metadata, apply=apply))
    return results


# ---------------------------------------------------------------------------
# Integration merge (MergeToMain) — T1443 / BUG-099 recurrence prevention
# ---------------------------------------------------------------------------

def ahead_behind(repo_root: str, ref_a: str, ref_b: str) -> Dict[str, int]:
    """git rev-list --left-right --count A...B (PS1 Get-AheadBehind)."""
    out = invoke_git(repo_root, ["rev-list", "--left-right", "--count", f"{ref_a}...{ref_b}"]).strip()
    parts = re.split(r"\s+", out)
    return {"ahead": int(parts[0]), "behind": int(parts[1])}


def merge_to_main(
    repo_root: str,
    root: str,
    task_id: Optional[str],
    role: str,
    owner: str,
    source_branch: Optional[str],
    target_branch: str,
    apply: bool,
) -> Dict[str, Any]:
    """PS1 Invoke-Gald3rMergeToMain — FF-only; dry-run unless `apply`."""
    metadata: Optional[Dict[str, Any]] = None
    if is_blank(source_branch):
        if is_blank(task_id):
            raise WorktreeError(
                "MergeToMain requires either -SourceBranch or -TaskId "
                "(to resolve the code worktree branch)."
            )
        metadata = mf.find_worktree(root, repo_root, task_id, role, owner)
        if metadata is None:
            raise WorktreeError(
                f"No gald3r-owned worktree found for task '{task_id}', role '{role}', "
                f"owner '{owner}'. Pass -SourceBranch explicitly."
            )
        source_branch = metadata.get("worktree_branch")
    assert source_branch is not None

    result: Dict[str, Any] = {
        "action": "MergeToMain",
        "mode": "apply" if apply else "dry-run",
        "source": source_branch,
        "target": target_branch,
        "status": None,
        "message": None,
    }

    if not mf.branch_exists(repo_root, source_branch):
        result["status"] = "not-found"
        result["message"] = f"source branch '{source_branch}' does not exist"
        return result
    if not mf.branch_exists(repo_root, target_branch):
        # g-go-go contract: missing target branch is merge-blocked, not an error.
        result["status"] = "merge-blocked"
        result["message"] = f"target branch '{target_branch}' does not exist"
        return result

    ab = ahead_behind(repo_root, source_branch, target_branch)
    result["source_ahead_of_target"] = ab["ahead"]
    result["target_ahead_of_source"] = ab["behind"]
    ff_possible = (
        git_exit_code(repo_root, ["merge-base", "--is-ancestor", target_branch, source_branch]) == 0
    )

    if not ff_possible:
        result["status"] = "merge-blocked"
        result["message"] = (
            f"target '{target_branch}' is {ab['behind']} commit(s) ahead of source; "
            "fast-forward not possible (would require a merge commit / conflict "
            "resolution) — not forcing"
        )
        return result
    if ab["ahead"] == 0:
        result["status"] = "noop"
        result["message"] = (
            f"target '{target_branch}' already contains source '{source_branch}' (nothing to merge)"
        )
        # Already merged: still safe to clean up branches/worktree under apply.

    if not apply:
        if result["status"] != "noop":
            result["status"] = "would-merge"
            result["message"] = (
                f"would fast-forward '{target_branch}' to '{source_branch}' "
                f"(+{ab['ahead']} commit(s)), then delete code+review branches and worktree"
            )
        return result

    dirty = mf.dirty_status(repo_root)
    if dirty:
        result["status"] = "merge-skipped-dirty"
        result["message"] = (
            f"main checkout has {len(dirty)} uncommitted path(s); refusing to merge"
        )
        return result

    current_branch = invoke_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    if result["status"] != "noop":
        try:
            if current_branch == target_branch:
                invoke_git(repo_root, ["merge", "--ff-only", source_branch])
            else:
                # `git fetch . src:dst` updates dst only on fast-forward.
                invoke_git(repo_root, ["fetch", ".", f"{source_branch}:{target_branch}"])
        except WorktreeError as exc:
            result["status"] = "merge-blocked"
            result["message"] = f"fast-forward merge failed: {exc}"
            return result

    # Delete code + review branches and the worktree (best-effort; merge landed).
    deleted: List[str] = []
    if metadata is not None:
        try:
            remove_worktree(repo_root, metadata, apply=True)
        except WorktreeError:
            pass  # best-effort cleanup, mirroring the PS1 empty catch
    for branch in (source_branch,):
        if branch != target_branch and mf.branch_exists(repo_root, branch):
            try:
                invoke_git(repo_root, ["branch", "-D", branch])
                deleted.append(branch)
            except WorktreeError:
                pass  # best-effort
    review_match = re.match(r"^gald3r/([^/]+)/[^/]+/(.+)$", source_branch)
    if review_match:
        review_branch = f"gald3r/{review_match.group(1)}/review/{review_match.group(2)}"
        if mf.branch_exists(repo_root, review_branch):
            try:
                invoke_git(repo_root, ["branch", "-D", review_branch])
                deleted.append(review_branch)
            except WorktreeError:
                pass  # best-effort
    result["deleted_branches"] = deleted
    if result["status"] != "noop":
        result["status"] = "merged"
        result["message"] = (
            f"fast-forwarded '{target_branch}' to '{source_branch}'; "
            f"deleted {len(deleted)} branch(es) + worktree"
        )
    else:
        result["message"] = str(result["message"]) + f"; cleaned up {len(deleted)} branch(es) + worktree"
    return result
