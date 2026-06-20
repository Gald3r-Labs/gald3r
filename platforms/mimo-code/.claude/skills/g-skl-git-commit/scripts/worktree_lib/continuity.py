"""Session resume + mid-flight course correction — Checkpoint, Resume, Steer, Queue.

Python port of gald3r_worktree.ps1 (T1585) — T967 continuity artifact and
T969 steer/queue layer. Artifact writes are atomic (temp file + rename) so a
crash mid-write always leaves the previous good artifact intact.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from worktree_lib.gitio import (
    WorktreeError,
    atomic_write_text,
    collapse_newlines,
    is_blank,
    iso_o,
    regex_count,
    utc_now,
)
from worktree_lib import manifest as mf


def _format_ac_list(items: Sequence[str], box: str) -> str:
    """PS1 Format-ContinuityAcList — '- [box] item' lines or '_none_'."""
    if not items:
        return "_none_"
    return "\n".join(f"- [{box}] {item}" for item in items)


def _format_bullets(items: Sequence[str]) -> str:
    """PS1 Format-ContinuityBullets — '- item' lines or '_none_'."""
    if not items:
        return "_none_"
    return "\n".join(f"- {item}" for item in items)


def _artifact_body(
    task_id: Any,
    goal: Optional[str],
    completed_acs: Sequence[str],
    pending_acs: Sequence[str],
    last_tool_summary: Optional[str],
    next_action: Optional[str],
    blockers: Sequence[str],
    checkpoint_sha: Optional[str],
    worktree_branch: Any,
) -> str:
    """PS1 New-ContinuityArtifactBody — structured resume summary markdown."""
    stamp = iso_o(utc_now())
    goal_text = "_not recorded_" if is_blank(goal) else str(goal)
    sha_text = (
        "_pending (artifact written before commit)_"
        if is_blank(checkpoint_sha)
        else str(checkpoint_sha)
    )
    last_tool = "_not recorded_" if is_blank(last_tool_summary) else str(last_tool_summary)
    next_text = "_not recorded_" if is_blank(next_action) else str(next_action)

    lines = [
        f"# Continuity Artifact — Task {task_id}",
        "",
        "<!-- gald3r session-resume artifact (T967). Structured resume summary, not a transcript. -->",
        "",
        f"- **Task**: {task_id}",
        f"- **Worktree branch**: {worktree_branch}",
        f"- **Last checkpoint SHA**: {sha_text}",
        f"- **Written at**: {stamp}",
        "",
        "## Goal",
        "",
        goal_text,
        "",
        "## Completed Acceptance Criteria",
        "",
        _format_ac_list(completed_acs, "x"),
        "",
        "## Pending Acceptance Criteria",
        "",
        _format_ac_list(pending_acs, " "),
        "",
        "## Last Tool Summary",
        "",
        last_tool,
        "",
        "## Next Planned Action",
        "",
        next_text,
        "",
        "## Blockers",
        "",
        _format_bullets(blockers),
        "",
    ]
    return "\n".join(lines)


def write_continuity_artifact(
    repo_root: str,
    metadata: Optional[Dict[str, Any]],
    goal: Optional[str],
    completed_acs: Sequence[str],
    pending_acs: Sequence[str],
    last_tool_summary: Optional[str],
    next_action: Optional[str],
    blockers: Sequence[str],
    checkpoint_sha: Optional[str],
) -> Dict[str, Any]:
    """PS1 Write-ContinuityArtifact — atomic artifact write + marker update."""
    if metadata is None or not metadata.get("gald3r_owned"):
        raise WorktreeError(
            "Checkpoint requires an existing gald3r-owned worktree "
            "(create it first with -Action Create)."
        )
    worktree_path = metadata.get("worktree_path") or ""
    marker_path = Path(worktree_path) / mf.MARKER_NAME
    if not marker_path.exists():
        raise WorktreeError(
            f"Ownership marker missing at '{marker_path}' — refusing to write "
            "a continuity artifact."
        )

    artifact_path = str(Path(worktree_path) / "continuity_artifact.md")
    body = _artifact_body(
        metadata.get("task_id"),
        goal,
        completed_acs,
        pending_acs,
        last_tool_summary,
        next_action,
        blockers,
        checkpoint_sha,
        metadata.get("worktree_branch"),
    )
    # Atomic write (AC5): temp file in the same directory + rename.
    atomic_write_text(Path(artifact_path), body)

    # Update the ownership marker (additive) with the resume pointers (AC2).
    updated = dict(metadata)
    if not is_blank(checkpoint_sha):
        updated["last_checkpoint_sha"] = checkpoint_sha
    elif "last_checkpoint_sha" not in updated:
        updated["last_checkpoint_sha"] = None
    updated["continuity_artifact_path"] = artifact_path
    updated["continuity_updated_at"] = iso_o(utc_now())
    mf.write_metadata(marker_path, updated)

    return {
        "action": "checkpoint",
        "task_id": metadata.get("task_id"),
        "worktree_path": worktree_path,
        "worktree_branch": metadata.get("worktree_branch"),
        "continuity_artifact_path": artifact_path,
        "last_checkpoint_sha": updated["last_checkpoint_sha"],
        "completed_ac_count": len(list(completed_acs)),
        "pending_ac_count": len(list(pending_acs)),
    }


def resume_from_artifact(
    root: str, repo_root: str, task_id: Optional[str], role: str, owner: str
) -> Dict[str, Any]:
    """PS1 Resume-FromContinuityArtifact — read-only resume banner + context."""
    if is_blank(task_id):
        raise WorktreeError("-TaskId is required for Resume.")

    metadata = mf.find_worktree(root, repo_root, task_id, role, owner)
    if metadata is None:
        raise WorktreeError(
            f"No gald3r-owned worktree found for task '{task_id}', role '{role}', "
            f"owner '{owner}' — nothing to resume."
        )

    stored = metadata.get("continuity_artifact_path")
    if not is_blank(stored):
        artifact_path = str(stored)
    else:
        artifact_path = str(Path(metadata.get("worktree_path") or "") / "continuity_artifact.md")

    if not Path(artifact_path).exists():
        raise WorktreeError(
            f"No continuity artifact found at '{artifact_path}' — task '{task_id}' "
            "has no checkpoint to resume from."
        )

    body = Path(artifact_path).read_text(encoding="utf-8-sig")

    # Derive the AC counts for the resume banner (AC4).
    completed = regex_count(r"^- \[x\] ", body)
    remaining = regex_count(r"^- \[ \] ", body)

    sha = metadata.get("last_checkpoint_sha")
    sha_text = sha if not is_blank(sha if sha is None else str(sha)) else "(no commit recorded)"

    banner = f"Resuming from checkpoint {sha_text} — {completed} ACs complete, {remaining} remaining"

    return {
        "action": "resume",
        "task_id": metadata.get("task_id"),
        "worktree_path": metadata.get("worktree_path"),
        "worktree_branch": metadata.get("worktree_branch"),
        "last_checkpoint_sha": metadata.get("last_checkpoint_sha"),
        "continuity_artifact_path": artifact_path,
        "completed_ac_count": completed,
        "remaining_ac_count": remaining,
        "banner": banner,
        "context_prefix": body,
    }


def steer(
    root: str,
    repo_root: str,
    task_id: Optional[str],
    role: str,
    owner: str,
    steer_text: Optional[str],
) -> Dict[str, Any]:
    """PS1 Invoke-WorktreeSteer (T969) — write, or read+clear, steer.md."""
    if is_blank(task_id):
        raise WorktreeError("-TaskId is required for Steer.")

    metadata = mf.find_worktree(root, repo_root, task_id, role, owner)
    if metadata is None:
        raise WorktreeError(
            f"No gald3r-owned worktree found for task '{task_id}', role '{role}', "
            f"owner '{owner}' — cannot steer."
        )

    worktree_path = metadata.get("worktree_path") or ""
    steer_path = str(Path(worktree_path) / "steer.md")
    stamp = iso_o(utc_now())

    if not is_blank(steer_text):
        # WRITE mode — atomic so a poll never reads a half-written file.
        assert steer_text is not None
        body = "\n".join(
            [
                f"# Steer — Task {task_id}",
                "",
                "<!-- gald3r mid-flight steering prompt (T969). g-go-code injects "
                "this at the next AC-gate, logs 'STEERED', then deletes it. -->",
                "",
                f"- **Written at**: {stamp}",
                "",
                "## Steering Prompt",
                "",
                steer_text.strip(),
                "",
            ]
        )
        atomic_write_text(Path(steer_path), body)
        return {
            "action": "steer-write",
            "task_id": metadata.get("task_id"),
            "worktree_path": worktree_path,
            "steer_path": steer_path,
            "written_at": stamp,
        }

    # READ + CLEAR mode (the AC-gate poll).
    if not Path(steer_path).exists():
        return {
            "action": "steer-read",
            "task_id": metadata.get("task_id"),
            "worktree_path": worktree_path,
            "steer_path": steer_path,
            "steered": False,
            "steer_prompt": None,
        }

    raw = Path(steer_path).read_text(encoding="utf-8-sig")
    Path(steer_path).unlink()
    return {
        "action": "steer-read",
        "task_id": metadata.get("task_id"),
        "worktree_path": worktree_path,
        "steer_path": steer_path,
        "steered": True,
        "steer_prompt": raw,
    }


def queue(
    root: str,
    repo_root: str,
    task_id: Optional[str],
    role: str,
    owner: str,
    queue_text: Optional[str],
) -> Dict[str, Any]:
    """PS1 Invoke-WorktreeQueue (T969) — append to, or read, queue.md."""
    if is_blank(task_id):
        raise WorktreeError("-TaskId is required for Queue.")

    metadata = mf.find_worktree(root, repo_root, task_id, role, owner)
    if metadata is None:
        raise WorktreeError(
            f"No gald3r-owned worktree found for task '{task_id}', role '{role}', "
            f"owner '{owner}' — cannot queue."
        )

    worktree_path = metadata.get("worktree_path") or ""
    queue_path = Path(worktree_path) / "queue.md"

    if not is_blank(queue_text):
        # APPEND mode — create the file with a header on first write.
        assert queue_text is not None
        if not queue_path.exists():
            header = "\n".join(
                [
                    f"# Follow-up Queue — Task {task_id}",
                    "",
                    "<!-- gald3r mid-flight follow-up queue (T969). g-go-code drains "
                    "these after the main goal is complete. One item per line. -->",
                    "",
                ]
            )
            queue_path.write_text(header + "\n", encoding="utf-8")
        # Single-line item; collapse internal newlines so each entry stays on one row.
        item = "- [ ] " + collapse_newlines(queue_text.strip())
        with open(queue_path, "a", encoding="utf-8") as fh:
            fh.write(item + "\n")
        pending = regex_count(r"^- \[ \] ", queue_path.read_text(encoding="utf-8-sig"))
        return {
            "action": "queue-append",
            "task_id": metadata.get("task_id"),
            "worktree_path": worktree_path,
            "queue_path": str(queue_path),
            "appended_item": item,
            "pending_count": pending,
        }

    # READ mode.
    if not queue_path.exists():
        return {
            "action": "queue-read",
            "task_id": metadata.get("task_id"),
            "worktree_path": worktree_path,
            "queue_path": str(queue_path),
            "pending_count": 0,
            "items": [],
        }

    body = queue_path.read_text(encoding="utf-8-sig")
    items: List[str] = re.findall(r"^- \[ \] (.+)$", body, flags=re.MULTILINE)
    return {
        "action": "queue-read",
        "task_id": metadata.get("task_id"),
        "worktree_path": worktree_path,
        "queue_path": str(queue_path),
        "pending_count": len(items),
        "items": items,
    }
