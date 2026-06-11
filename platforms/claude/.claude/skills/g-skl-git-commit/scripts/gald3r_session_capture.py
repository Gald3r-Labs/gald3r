#!/usr/bin/env python3
"""Python port of gald3r_session_capture.ps1 (T1585).

Capture Claude Code session JSONL from a worktree to the host for
cross-sandbox resume (T1124). Locates the session JSONL for a given worktree,
copies it to a stable host location keyed by project + task + session id,
rewrites embedded `cwd` / worktree absolute-path references to the host repo
path so `claude --resume <session_id>` works natively, and records session
metadata in sessions.json.

Actions:
  Capture - locate, copy, cwd-rewrite, and record one session (needs -Apply)
  List    - list recorded sessions for a project from sessions.json
  Resolve - given -SessionId, print the host JSONL path and resume command
  Report  - default; print what Capture would do (no writes)

Default locations (overridable):
  Claude projects dir : $CLAUDE_CONFIG_DIR/projects, else ~/.claude/projects
  Sessions root       : $GALD3R_SESSIONS_ROOT, else ~/.gald3r-sessions
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _bootstrap_engine() -> bool:
    """Make `gald3r.utils` importable (installed package or bundled engine src)."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        engine_src = parent / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()
if _HAS_ENGINE:
    from gald3r.utils import process as _process
else:
    _process = None  # graceful stdlib fallback


def run_git(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run git and return (returncode, stdout, stderr) without raising."""
    if _process is not None:
        r = _process.run_git(args, cwd=cwd, check=False)
        return r.returncode, r.stdout, r.stderr
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError:
        return 127, "", "git not found"


def get_home_dir() -> str:
    for var in ("USERPROFILE", "HOME"):
        val = os.environ.get(var, "")
        if val.strip():
            return val
    return str(Path.home())


def to_claude_project_folder(path: str) -> str:
    """Mirror Claude Code's project-folder encoding: non-alphanumeric -> '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def resolve_git_top_level(path: str) -> Optional[str]:
    if not Path(path).exists():
        return None
    rc, out, _ = run_git(["-C", path, "rev-parse", "--show-toplevel"])
    if rc == 0 and out.strip():
        return str(Path(out.strip()).resolve())
    return None


def resolve_host_repo_path(worktree_path: str) -> Optional[str]:
    """Host repo = the COMMON git dir's working tree, not the worktree itself."""
    if not Path(worktree_path).exists():
        return None
    rc, out, _ = run_git(["-C", worktree_path, "rev-parse",
                          "--path-format=absolute", "--git-common-dir"])
    if rc == 0 and out.strip():
        common_dir = Path(out.strip())
        # common-dir is "<mainrepo>/.git"; its parent is the host working tree.
        parent = common_dir.parent
        if str(parent) and parent.exists():
            return str(parent.resolve())
    # Fallback: the worktree's own top-level (no worktree => host == worktree).
    return resolve_git_top_level(worktree_path)


def get_project_id_for(repo_path: str) -> str:
    id_file = Path(repo_path) / ".gald3r" / ".project_id"
    if id_file.is_file():
        try:
            val = id_file.read_text(encoding="utf-8", errors="replace").strip()
            if val:
                return val
        except OSError:
            pass
    return to_claude_project_folder(repo_path)


class Context:
    """Resolved common context shared by all actions."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.as_json: bool = args.json
        home_dir = get_home_dir()

        self.sessions_root: str = args.sessions_root or ""
        if not self.sessions_root.strip():
            self.sessions_root = str(Path(home_dir) / ".gald3r-sessions")

        self.claude_projects_dir: str = args.claude_projects_dir or ""
        if not self.claude_projects_dir.strip():
            config_dir = os.environ.get("CLAUDE_CONFIG_DIR", "")
            if config_dir.strip():
                self.claude_projects_dir = str(Path(config_dir) / "projects")
            else:
                self.claude_projects_dir = str(Path(home_dir) / ".claude" / "projects")

        self.worktree_abs: str = args.worktree_path
        if Path(args.worktree_path).exists():
            self.worktree_abs = str(Path(args.worktree_path).resolve())

        self.host_repo_path: Optional[str] = args.host_repo_path
        if not (self.host_repo_path or "").strip():
            self.host_repo_path = resolve_host_repo_path(self.worktree_abs)
        if self.host_repo_path and Path(self.host_repo_path).exists():
            self.host_repo_path = str(Path(self.host_repo_path).resolve())

        self.project_id: Optional[str] = args.project_id
        if not (self.project_id or "").strip() and self.host_repo_path:
            self.project_id = get_project_id_for(self.host_repo_path)

        self.task_id: str = args.task_id or ""
        self.session_id: str = args.session_id or ""

    def emit(self, obj: Any, text: str) -> None:
        if self.as_json:
            print(json.dumps(obj, indent=2, default=str))
        else:
            print(text)


def _sessions_json_path(ctx: Context) -> Path:
    return Path(ctx.sessions_root) / str(ctx.project_id) / "sessions.json"


def _load_records(sessions_json: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(sessions_json.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError, ValueError):
        return []
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    return []


def invoke_list(ctx: Context) -> None:
    sessions_json = _sessions_json_path(ctx)
    if not sessions_json.is_file():
        ctx.emit({"project_id": ctx.project_id, "sessions": []},
                 f"No captured sessions for project '{ctx.project_id}' "
                 f"(expected {sessions_json}).")
        return
    records = _load_records(sessions_json)
    if ctx.as_json:
        print(json.dumps({"project_id": ctx.project_id, "sessions": records},
                         indent=2, default=str))
        return
    print(f"Captured sessions for project '{ctx.project_id}':")
    for s in records:
        print("  {0}  task={1}  {2}".format(
            s.get("session_id", ""), s.get("task_id", ""), s.get("timestamp", "")))


def invoke_resolve(ctx: Context) -> None:
    if not ctx.session_id.strip():
        raise SystemExit("Resolve requires -SessionId.")
    sessions_json = _sessions_json_path(ctx)
    rec: Optional[Dict[str, Any]] = None
    if sessions_json.is_file():
        for r in _load_records(sessions_json):
            if r.get("session_id") == ctx.session_id:
                rec = r
                break
    if rec:
        host_jsonl = str(rec.get("host_jsonl_path", ""))
    else:
        # Parity note: the PS1 dereferences $rec.task_id when $rec is null here
        # (latent fault path); the port falls back to the Capture default
        # "_no-task" task segment instead.
        host_jsonl = str(Path(ctx.sessions_root) / str(ctx.project_id)
                         / "_no-task" / f"{ctx.session_id}.jsonl")
    resume_cmd = f"claude --resume {ctx.session_id}"
    if ctx.as_json:
        print(json.dumps({
            "session_id": ctx.session_id,
            "host_jsonl_path": host_jsonl,
            "resume_command": resume_cmd,
            "record": rec,
        }, indent=2, default=str))
        return
    print(f"Session:  {ctx.session_id}")
    print(f"JSONL:    {host_jsonl}")
    print(f"Resume:   {resume_cmd}")
    if not rec:
        print(f"(no metadata record found in {sessions_json})")


def find_worktree_session_jsonl(ctx: Context) -> Tuple[Path, Optional[Path]]:
    folder_name = to_claude_project_folder(ctx.worktree_abs)
    proj_folder = Path(ctx.claude_projects_dir) / folder_name
    if not proj_folder.is_dir():
        return proj_folder, None
    if ctx.session_id.strip():
        candidate = proj_folder / f"{ctx.session_id}.jsonl"
        return proj_folder, candidate if candidate.is_file() else None
    newest: Optional[Path] = None
    newest_mtime = -1.0
    for f in proj_folder.glob("*.jsonl"):
        if not f.is_file():
            continue
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if mtime > newest_mtime:
            newest_mtime = mtime
            newest = f
    return proj_folder, newest


def repair_cwd_paths(lines: List[str], from_path: str, to_path: str) -> List[str]:
    """Rewrite worktree absolute-path references to the host repo path.

    JSON encodes Windows backslashes as "\\\\"; rewrite both raw and
    JSON-escaped forms so cwd, file references, and tool args all resolve
    under the host repo after --resume.
    """
    from_esc = from_path.replace("\\", "\\\\")
    to_esc = to_path.replace("\\", "\\\\")
    out: List[str] = []
    for line in lines:
        rewritten = line.replace(from_esc, to_esc).replace(from_path, to_path)
        out.append(rewritten)
    return out


def invoke_capture(ctx: Context, do_apply: bool) -> None:
    proj_folder, found = find_worktree_session_jsonl(ctx)
    result: Dict[str, Any] = {
        "action": "Capture",
        "applied": do_apply,
        "worktree_path": ctx.worktree_abs,
        "host_repo_path": ctx.host_repo_path,
        "project_id": ctx.project_id,
        "task_id": ctx.task_id,
        "claude_proj_dir": str(proj_folder),
        "session_id": None,
        "source_jsonl": None,
        "host_jsonl_path": None,
        "sessions_json": None,
        "cwd_rewrites": 0,
        "status": None,
    }

    if found is None:
        result["status"] = "no-session-found"
        ctx.emit(result,
                 f"No session JSONL found under {proj_folder}. Nothing to capture.")
        return

    source_jsonl = str(found)
    sid = ctx.session_id if ctx.session_id.strip() else found.stem
    result["session_id"] = sid
    result["source_jsonl"] = source_jsonl

    task_seg = ctx.task_id if ctx.task_id.strip() else "_no-task"
    dest_dir = Path(ctx.sessions_root) / str(ctx.project_id) / task_seg
    dest_jsonl = dest_dir / f"{sid}.jsonl"
    sessions_json = _sessions_json_path(ctx)
    result["host_jsonl_path"] = str(dest_jsonl)
    result["sessions_json"] = str(sessions_json)

    # Compute cwd-rewrite count for reporting (and to perform it on apply).
    lines = found.read_text(encoding="utf-8", errors="replace").splitlines()
    rewritten = lines
    do_rewrite = bool(ctx.host_repo_path) and (ctx.worktree_abs != ctx.host_repo_path)
    if do_rewrite:
        rewritten = repair_cwd_paths(lines, ctx.worktree_abs, str(ctx.host_repo_path))
        result["cwd_rewrites"] = sum(
            1 for a, b in zip(lines, rewritten) if a != b)

    if not do_apply:
        result["status"] = "dry-run"
        ctx.emit(result, (
            "[dry-run] Would capture session:\n"
            f"  source : {source_jsonl}\n"
            f"  dest   : {dest_jsonl}\n"
            f"  cwd     rewrites: {result['cwd_rewrites']} line(s) "
            f"({ctx.worktree_abs} -> {ctx.host_repo_path})\n"
            f"  meta   : {sessions_json}\n"
            "Pass -Apply to write."))
        return

    # --- writes ---
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_jsonl.write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    # Upsert sessions.json metadata.
    records = _load_records(sessions_json) if sessions_json.is_file() else []
    records = [r for r in records if r.get("session_id") != sid]
    records.append({
        "session_id": sid,
        "task_id": ctx.task_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "worktree_path": ctx.worktree_abs,
        "host_repo_path": ctx.host_repo_path,
        "host_jsonl_path": str(dest_jsonl),
        "cwd_rewrites": result["cwd_rewrites"],
    })
    sessions_json.parent.mkdir(parents=True, exist_ok=True)
    sessions_json.write_text(json.dumps(records, indent=2, default=str) + "\n",
                             encoding="utf-8")

    result["status"] = "captured"
    ctx.emit(result, (
        f"Captured session {sid}\n"
        f"  -> {dest_jsonl}\n"
        f"  cwd rewrites: {result['cwd_rewrites']} line(s)\n"
        f"  metadata: {sessions_json}\n"
        f"  resume: claude --resume {sid}"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture Claude Code session JSONL from a worktree to the "
                    "host for cross-sandbox resume (T1124).")
    parser.add_argument("-Action", "--action", dest="action", default="Report",
                        choices=["Capture", "List", "Resolve", "Report"],
                        help="Operation to run (default: Report).")
    parser.add_argument("-WorktreePath", "--worktree-path", dest="worktree_path",
                        default=".", help="Worktree/sandbox path the session ran in.")
    parser.add_argument("-HostRepoPath", "--host-repo-path", dest="host_repo_path",
                        default=None, help="Canonical host repo path for cwd rewrite.")
    parser.add_argument("-ProjectId", "--project-id", dest="project_id",
                        default=None, help="Stable project id (sessions.json key).")
    parser.add_argument("-TaskId", "--task-id", dest="task_id", default=None,
                        help="Task id associated with this capture.")
    parser.add_argument("-SessionId", "--session-id", dest="session_id",
                        default=None, help="Explicit Claude session id.")
    parser.add_argument("-SessionsRoot", "--sessions-root", dest="sessions_root",
                        default=os.environ.get("GALD3R_SESSIONS_ROOT", ""),
                        help="Root for captured sessions "
                             "(default: $GALD3R_SESSIONS_ROOT or ~/.gald3r-sessions).")
    parser.add_argument("-ClaudeProjectsDir", "--claude-projects-dir",
                        dest="claude_projects_dir", default=None,
                        help="Claude Code projects directory.")
    parser.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                        help="Perform writes (Capture is dry-run without it).")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit a machine-readable JSON result object.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    ctx = Context(args)
    if args.action == "List":
        invoke_list(ctx)
    elif args.action == "Resolve":
        invoke_resolve(ctx)
    elif args.action == "Capture":
        invoke_capture(ctx, do_apply=bool(args.apply))
    else:  # Report
        invoke_capture(ctx, do_apply=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
