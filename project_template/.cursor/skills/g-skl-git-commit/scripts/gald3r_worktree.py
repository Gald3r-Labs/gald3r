#!/usr/bin/env python3
"""Python port of gald3r_worktree.ps1 (T1585).

Shared gald3r Git worktree helper for agent isolation. Creates, detects/
reuses, reports, removes, and cleans up gald3r-owned worktrees without
nesting them inside the active repository checkout.

Actions (parity with the PS1 -Action set):
    Create      — create or reuse a worktree (stale-base aware; optional
                  swarm file-lock claim via -LockFiles, T1059)
    Report      — list gald3r-owned worktrees for this repo
    Remove      — remove one worktree (dry-run unless -Apply)
    Cleanup     — reclaim stale worktrees (report-only unless -Apply)
    Run         — launch an agent subprocess in a worktree (T1123)
    Cancel      — terminate the agent on one worktree; worktree preserved
    CancelAll   — cancel every active agent owned by a -TaskId
    Checkpoint  — write a continuity artifact for crash-safe resume (T967)
    Resume      — read the continuity artifact + resume banner (T967)
    Steer       — write or read+clear steer.md (T969)
    Queue       — append to or read queue.md (T969)
    LockReport  — coordinator-side swarm lock conflict report (T1059)
    Keep        — protect a worktree across the g-go phase handoff (T1118)
    MergeToMain — FF-only integration merge (dry-run unless -Apply, T1443)

Default worktree root:
    $GALD3R_WORKTREE_ROOT when set, otherwise
    <repo-parent>/.gald3r-worktrees/<repo-name>

Ownership proof: .gald3r-worktree.json inside each created worktree.
Safety: never creates worktrees inside the active checkout; Create blocks on
a dirty checkout unless -AllowDirty; Cleanup/Remove only touch directories
carrying gald3r ownership metadata; Cleanup is report-only unless -Apply.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

ACTIONS = [
    "Create", "Report", "Remove", "Cleanup", "Run", "Cancel", "CancelAll",
    "Checkpoint", "Resume", "Steer", "Queue", "LockReport", "Keep", "MergeToMain",
]
STALE_BASE_ACTIONS = ["Reuse", "Warn", "Recreate"]

# Every registered option spelling (lowercased) — used by the -AgentArguments
# pre-parser so agent args that start with "-" (e.g. "-c") are not mistaken
# for options, matching the PS1 [string[]]$AgentArguments behavior.
KNOWN_OPTIONS = {
    "-h", "--help",
    "-action", "--action", "-repopath", "--repo-path", "-taskid", "--task-id", "-bugid", "--bug-id",
    "-role", "--role", "-owner", "--owner", "-basebranch", "--base-branch", "-branch", "--branch",
    "-targetbranch", "--target-branch", "-sourcebranch", "--source-branch",
    "-worktreeroot", "--worktree-root", "-taskroot", "--task-root",
    "-stalehours", "--stale-hours", "-keephours", "--keep-hours",
    "-allowdirty", "--allow-dirty", "-stalebaseaction", "--stale-base-action",
    "-apply", "--apply", "-json", "--json",
    "-agentcommand", "--agent-command", "-agentarguments", "--agent-arguments",
    "-wait", "--wait", "-graceseconds", "--grace-seconds", "-reason", "--reason",
    "-goal", "--goal", "-completedacs", "--completed-acs",
    "-pendingacs", "--pending-acs", "-lasttoolsummary", "--last-tool-summary",
    "-nextaction", "--next-action", "-blockers", "--blockers",
    "-checkpointsha", "--checkpoint-sha", "-steertext", "--steer-text",
    "-queuetext", "--queue-text", "-bucketid", "--bucket-id",
    "-lockfiles", "--lock-files", "-bucketttlminutes", "--bucket-ttl-minutes",
}


def _split_agent_arguments(argv: List[str]) -> "tuple[List[str], Optional[List[str]]]":
    """Pull ``-AgentArguments`` values out before argparse sees them.

    Consumes every token after the flag up to the next known option, so agent
    arguments beginning with ``-`` (e.g. ``-c``) survive intact.
    """
    remaining: List[str] = []
    collected: Optional[List[str]] = None
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.lower() in ("-agentarguments", "--agent-arguments"):
            collected = [] if collected is None else collected
            i += 1
            while i < len(argv) and argv[i].lower() not in KNOWN_OPTIONS:
                collected.append(argv[i])
                i += 1
            continue
        remaining.append(token)
        i += 1
    return remaining, collected


def _bootstrap_engine_utils() -> None:
    """Make gald3r engine utils importable when running from an installed template.

    Tries ``import gald3r.utils`` first; on ImportError walks up from this
    script to find ``.gald3r_sys/engine/src`` and prepends it to sys.path.
    worktree_lib.gitio still has a local subprocess fallback, so a missing
    engine never hard-fails the import.
    """
    try:
        import gald3r.utils  # noqa: F401 — probe only
        return
    except ImportError:
        pass
    here = Path(__file__).resolve().parent
    for parent in (here, *here.parents):
        candidate = parent / ".gald3r_sys" / "engine" / "src"
        if (candidate / "gald3r" / "utils" / "process.py").is_file():
            sys.path.insert(0, str(candidate))
            return


_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
_bootstrap_engine_utils()

from worktree_lib import actions as wt_actions
from worktree_lib import agents as wt_agents
from worktree_lib import continuity as wt_continuity
from worktree_lib import locks as wt_locks
from worktree_lib import manifest as wt_manifest
from worktree_lib.gitio import WorktreeError, resolve_owner


def _choice(valid: Sequence[str]) -> Callable[[str], str]:
    """Case-insensitive ValidateSet-style converter (canonical casing returned)."""
    table = {v.lower(): v for v in valid}

    def convert(value: str) -> str:
        key = value.lower()
        if key not in table:
            raise argparse.ArgumentTypeError(f"must be one of: {', '.join(valid)}")
        return table[key]

    return convert


def build_parser() -> argparse.ArgumentParser:
    """Argument surface mirroring the PS1 param() block (both spellings)."""
    p = argparse.ArgumentParser(
        prog="gald3r_worktree.py",
        description="Shared gald3r Git worktree helper for agent isolation (T1585 port).",
    )
    p.add_argument("-Action", "--action", dest="action", type=_choice(ACTIONS),
                   default="Report", metavar="ACTION",
                   help=f"One of: {', '.join(ACTIONS)} (default: Report)")
    p.add_argument("-RepoPath", "--repo-path", dest="repo_path", default=".",
                   help="Path inside the target repository (default: .)")
    p.add_argument("-TaskId", "--task-id", "-BugId", "--bug-id", dest="task_id", default=None,
                   help="gald3r task id owning the worktree")
    p.add_argument("-Role", "--role", dest="role", default="agent",
                   help="Agent role segment (default: agent)")
    p.add_argument("-Owner", "--owner", dest="owner", default=None,
                   help="Owner segment (default: USERNAME / USER / agent)")
    p.add_argument("-BaseBranch", "--base-branch", "-Branch", "--branch", dest="base_branch", default="HEAD",
                   help="Ref the worktree branch forks from (default: HEAD)")
    p.add_argument("-TargetBranch", "--target-branch", dest="target_branch", default="main",
                   help="MergeToMain integration target (default: main)")
    p.add_argument("-SourceBranch", "--source-branch", dest="source_branch", default=None,
                   help="MergeToMain explicit source branch (default: resolved from metadata)")
    p.add_argument("-WorktreeRoot", "--worktree-root", dest="worktree_root",
                   default=os.environ.get("GALD3R_WORKTREE_ROOT"),
                   help="Worktree root (default: $GALD3R_WORKTREE_ROOT or "
                        "<repo-parent>/.gald3r-worktrees/<repo-name>)")
    p.add_argument("-TaskRoot", "--task-root", dest="task_root", default=None,
                   help="Task files directory (default: <repo>/.gald3r/tasks)")
    p.add_argument("-StaleHours", "--stale-hours", dest="stale_hours", type=int, default=24,
                   help="Cleanup age threshold in hours (default: 24)")
    p.add_argument("-KeepHours", "--keep-hours", dest="keep_hours", type=int, default=2,
                   help="Keep protection window in hours (default: 2, T1118)")
    p.add_argument("-AllowDirty", "--allow-dirty", dest="allow_dirty", action="store_true",
                   help="Allow Create on a dirty active checkout (explicit override)")
    p.add_argument("-StaleBaseAction", "--stale-base-action", dest="stale_base_action",
                   type=_choice(STALE_BASE_ACTIONS), default="Warn", metavar="MODE",
                   help="Reuse | Warn | Recreate when an existing worktree base is stale "
                        "(default: Warn)")
    p.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                   help="Perform destructive operations (Remove/Cleanup/MergeToMain write mode)")
    p.add_argument("-Json", "--json", dest="json", action="store_true",
                   help="Emit JSON instead of formatted text")
    p.add_argument("-AgentCommand", "--agent-command", dest="agent_command", default=None,
                   help="Run: agent executable to launch inside the worktree (T1123)")
    p.add_argument("-AgentArguments", "--agent-arguments", dest="agent_arguments",
                   nargs="*", default=[], metavar="ARG",
                   help="Run: arguments passed to the agent command")
    p.add_argument("-Wait", "--wait", dest="wait", action="store_true",
                   help="Run: block until the agent exits (default: non-blocking)")
    p.add_argument("-GraceSeconds", "--grace-seconds", dest="grace_seconds", type=int, default=5,
                   help="Cancel: grace period before forced tree-kill (default: 5)")
    p.add_argument("-Reason", "--reason", dest="reason", default="coordinator-cancel",
                   help="Cancel: free-text reason recorded in the cancellation log")
    p.add_argument("-Goal", "--goal", dest="goal", default=None,
                   help="Checkpoint: goal summary (T967)")
    p.add_argument("-CompletedAcs", "--completed-acs", dest="completed_acs",
                   nargs="*", default=[], metavar="AC",
                   help="Checkpoint: completed acceptance criteria")
    p.add_argument("-PendingAcs", "--pending-acs", dest="pending_acs",
                   nargs="*", default=[], metavar="AC",
                   help="Checkpoint: pending acceptance criteria")
    p.add_argument("-LastToolSummary", "--last-tool-summary", dest="last_tool_summary",
                   default=None, help="Checkpoint: last tool summary")
    p.add_argument("-NextAction", "--next-action", dest="next_action", default=None,
                   help="Checkpoint: next planned action")
    p.add_argument("-Blockers", "--blockers", dest="blockers", nargs="*", default=[],
                   metavar="ITEM", help="Checkpoint: blockers")
    p.add_argument("-CheckpointSha", "--checkpoint-sha", dest="checkpoint_sha", default=None,
                   help="Checkpoint: SHA of the checkpoint commit this artifact precedes")
    p.add_argument("-SteerText", "--steer-text", dest="steer_text", default=None,
                   help="Steer: write this prompt; omit to read+clear steer.md (T969)")
    p.add_argument("-QueueText", "--queue-text", dest="queue_text", default=None,
                   help="Queue: append this item; omit to read pending queue (T969)")
    p.add_argument("-BucketId", "--bucket-id", dest="bucket_id", default=None,
                   help="Swarm bucket id for file-lock manifests (T1059)")
    p.add_argument("-LockFiles", "--lock-files", dest="lock_files", nargs="*", default=[],
                   metavar="PATH", help="Create: file paths this bucket intends to modify")
    p.add_argument("-BucketTtlMinutes", "--bucket-ttl-minutes", dest="bucket_ttl_minutes",
                   type=int, default=60,
                   help="Bucket TTL in minutes; expiry = created_at + 2*TTL (default: 60)")
    return p


def _require_task_id(task_id: Optional[str], action: str) -> None:
    """Mirror the PS1 'throw \"-TaskId is required for <Action>.\"' guards."""
    if task_id is None or not str(task_id).strip():
        raise WorktreeError(f"-TaskId is required for {action}.")


def _find_required(root: str, repo_root: str, args: argparse.Namespace,
                   missing_suffix: str) -> Dict[str, Any]:
    """Locate the worktree for task/role/owner or raise the PS1-equivalent error."""
    metadata = wt_manifest.find_worktree(root, repo_root, args.task_id, args.role, args.owner)
    if metadata is None:
        raise WorktreeError(
            f"No gald3r-owned worktree found for task '{args.task_id}', "
            f"role '{args.role}', owner '{args.owner}'{missing_suffix}"
        )
    return metadata


def dispatch(args: argparse.Namespace) -> Union[None, Dict[str, Any], List[Dict[str, Any]]]:
    """Execute the requested action (mirrors the PS1 switch block)."""
    repo_root = wt_manifest.resolve_repo_root(args.repo_path)
    root = wt_manifest.resolve_worktree_root(repo_root, args.worktree_root)
    action = args.action

    if action == "Create":
        # T655 / BUG-168 — fail closed for swarm code buckets. A `code-swarm`
        # bucket that supplies no -LockFiles would silently skip the T1059 lock
        # claim, letting two parallel buckets edit the same files with no
        # pre-spawn LOCK_CONFLICT guard. Refuse rather than no-op. Non-swarm
        # roles keep their prior lock-optional behavior.
        if str(args.role).lower() == "code-swarm" and not args.lock_files:
            raise WorktreeError(
                "LOCK_REQUIRED: -Role code-swarm requires -LockFiles (the "
                "repo-relative paths this bucket intends to modify) so the "
                "T1059 swarm file-lock claim engages. Derive the bucket's "
                "planned touch set and pass it via -LockFiles, or use a "
                "non-swarm role."
            )
        # T1059 — claim the lock manifest FIRST so a conflicting bucket never
        # even spawns its worktree (fails with LOCK_CONFLICT before creation).
        lock_result: Optional[Dict[str, Any]] = None
        if args.lock_files:
            lock_result = wt_locks.write_swarm_lock_manifest(
                repo_root, args.bucket_id, args.owner, args.lock_files,
                args.bucket_ttl_minutes,
            )
        result = wt_actions.create_worktree(
            repo_root, root, args.task_id, args.role, args.owner,
            args.base_branch, args.allow_dirty, args.stale_base_action,
        )
        if lock_result is not None:
            result = dict(result)
            result["swarm_lock_manifest"] = lock_result["manifest_path"]
            result["swarm_lock_bucket_id"] = lock_result["bucket_id"]
            result["swarm_lock_expires_at"] = lock_result["expires_at"]
        return result
    if action == "Report":
        return wt_manifest.get_report(root, repo_root)
    if action == "Remove":
        _require_task_id(args.task_id, "Remove")
        metadata = _find_required(root, repo_root, args, ".")
        return wt_actions.remove_worktree(repo_root, metadata, apply=args.apply)
    if action == "Cleanup":
        return wt_actions.cleanup_worktrees(
            repo_root, root, args.task_root, args.stale_hours, apply=args.apply
        )
    if action == "Keep":
        _require_task_id(args.task_id, "Keep")
        metadata = _find_required(root, repo_root, args, ". Create it first.")
        return wt_actions.keep_worktree(repo_root, metadata, args.keep_hours)
    if action == "Run":
        _require_task_id(args.task_id, "Run")
        metadata = _find_required(root, repo_root, args, ". Create it first.")
        return wt_agents.run_agent_in_worktree(
            repo_root, metadata, args.agent_command, args.agent_arguments, args.wait
        )
    if action == "Cancel":
        _require_task_id(args.task_id, "Cancel")
        metadata = _find_required(root, repo_root, args, ".")
        return wt_agents.stop_worktree_agent(repo_root, metadata, args.grace_seconds, args.reason)
    if action == "CancelAll":
        return wt_agents.cancel_all_for_task(
            repo_root, root, args.task_id, args.grace_seconds, args.reason
        )
    if action == "Checkpoint":
        _require_task_id(args.task_id, "Checkpoint")
        metadata = _find_required(root, repo_root, args, ". Create it first.")
        return wt_continuity.write_continuity_artifact(
            repo_root, metadata, args.goal, args.completed_acs, args.pending_acs,
            args.last_tool_summary, args.next_action, args.blockers, args.checkpoint_sha,
        )
    if action == "Resume":
        return wt_continuity.resume_from_artifact(root, repo_root, args.task_id,
                                                  args.role, args.owner)
    if action == "Steer":
        return wt_continuity.steer(root, repo_root, args.task_id, args.role,
                                   args.owner, args.steer_text)
    if action == "Queue":
        return wt_continuity.queue(root, repo_root, args.task_id, args.role,
                                   args.owner, args.queue_text)
    if action == "LockReport":
        return wt_locks.swarm_lock_conflict_report(repo_root)
    # MergeToMain (T1443) — FF-only; dry-run by default, -Apply to write.
    return wt_actions.merge_to_main(
        repo_root, root, args.task_id, args.role, args.owner,
        args.source_branch, args.target_branch, apply=args.apply,
    )


def _render_value(value: Any) -> str:
    """Render a value the way Format-List shows it."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, dict):
        inner = "; ".join(f"{k}={_render_value(v)}" for k, v in value.items())
        return "@{" + inner + "}"
    if isinstance(value, (list, tuple)):
        return "{" + ", ".join(_render_value(v) for v in value) + "}"
    return str(value)


def format_list(result: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    """Approximate the PS1 ``Format-List`` text output."""
    items = result if isinstance(result, list) else [result]
    blocks: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            blocks.append(str(item))
            continue
        if not item:
            continue
        width = max(len(str(k)) for k in item)
        blocks.append("\n".join(
            f"{str(k).ljust(width)} : {_render_value(v)}" for k, v in item.items()
        ))
    return "\n\n".join(blocks)


def emit(result: Union[None, Dict[str, Any], List[Dict[str, Any]]], as_json: bool) -> None:
    """Print the action result (JSON or Format-List style, matching the PS1 tail)."""
    if as_json:
        if result is None or (isinstance(result, list) and not result):
            print("[]")
        elif isinstance(result, list) and len(result) == 1:
            # PS pipeline unwraps single-element arrays before ConvertTo-Json.
            print(json.dumps(result[0], indent=2, default=str))
        else:
            print(json.dumps(result, indent=2, default=str))
        return
    if result is None:
        return
    text = format_list(result)
    if text:
        print(text)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on operational failure."""
    raw = list(argv) if argv is not None else sys.argv[1:]
    remaining, agent_arguments = _split_agent_arguments(raw)
    args = build_parser().parse_args(remaining)
    if agent_arguments is not None:
        args.agent_arguments = agent_arguments
    args.owner = resolve_owner(args.owner)
    try:
        result = dispatch(args)
    except WorktreeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    emit(result, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
