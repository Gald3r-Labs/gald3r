#!/usr/bin/env python3
"""Python port of gald3r_housekeeping_commit.ps1 (T1585).

Safe controller .gald3r/ housekeeping safety classifier (T531).

Used by /g-go pipelines at two points: (1) preflight, before the Clean
Controller Gate; (2) post-coordinator-write, after coordinator-owned shared
.gald3r writes. When the orchestration root has dirty paths and ALL of them
are safe controller .gald3r/ housekeeping/coordination files, the helper can
stage exactly those paths and create a focused commit — no `git add .`.

Exit codes:
  0 - clean OR safe-and-committed (caller may continue)
  1 - dirty, but contains unsafe/non-allowlisted paths (caller MUST stop)
  2 - configuration fault (not a git repo, member-repo target, conflict, etc.)

Examples:
  python gald3r_housekeeping_commit.py                       # classify only
  python gald3r_housekeeping_commit.py -Apply                # commit if safe
  python gald3r_housekeeping_commit.py -Mode post-write -Apply -TaskId 531
  python gald3r_housekeeping_commit.py -Json                 # structured output
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
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


def run_git(args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run git and return (returncode, stdout, stderr) without raising."""
    if _process is not None:
        r = _process.run_git(args, cwd=cwd, check=False)
        return r.returncode, r.stdout, r.stderr
    try:
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError:
        return 127, "", "git not found"


# Allowlisted controller .gald3r/ path globs (forward-slash repo-relative).
ALLOW_GLOBS: List[str] = [
    ".gald3r/TASKS.md",
    ".gald3r/BUGS.md",
    ".gald3r/FEATURES.md",
    ".gald3r/PRDS.md",
    ".gald3r/SUBSYSTEMS.md",
    ".gald3r/IDEA_BOARD.md",
    ".gald3r/learned-facts.md",
    ".gald3r/tracking/IDEA_BOARD.md",
    ".gald3r/tasks/*.md",
    ".gald3r/tasks/**/*.md",
    ".gald3r/tasks/open/*.md",
    ".gald3r/tasks/in-progress/*.md",
    ".gald3r/tasks/awaiting/*.md",
    ".gald3r/tasks/closed/*.md",
    ".gald3r/bugs/*.md",
    ".gald3r/bugs/**/*.md",
    ".gald3r/bugs/open/*.md",
    ".gald3r/bugs/closed/*.md",
    ".gald3r/features/*.md",
    ".gald3r/prds/*.md",
    ".gald3r/subsystems/*.md",
    ".gald3r/reports/*.md",
    ".gald3r/reports/*.json",
    ".gald3r/logs/wpac_auto_actions.log",
    ".gald3r/linking/sent_orders/*.md",
    ".gald3r/linking/INBOX.md",
]

# Always-unsafe globs (override allowlist; surfaced as blockers).
DENY_GLOBS: List[str] = [
    ".gald3r/.identity",
    ".gald3r/.user_id",
    ".gald3r/.project_id",
    ".gald3r/.vault_location",
    ".gald3r/vault/*",
    ".gald3r/vault/**/*",
    ".gald3r/config/*",
    ".gald3r/config/**/*",
    ".gald3r/.gald3r-worktree.json",
]

# Secret-name regex (filename match, case-insensitive).
SECRET_NAME_RX = re.compile(
    r"(secret|credential|token|password|api[._-]?key|private[._-]?key)", re.IGNORECASE)

USE_COLOR = True
_COLORS = {"GREEN": "\x1b[32m", "YELLOW": "\x1b[33m", "RED": "\x1b[31m", "INFO": "\x1b[36m"}


@dataclass
class Entry:
    xy: str
    path: str
    original: str
    raw: str


def write_status_line(level: str, message: str) -> None:
    if USE_COLOR and sys.stdout.isatty():
        color = _COLORS.get(level, _COLORS["INFO"])
        print(f"{color}[{level}] {message}\x1b[0m")
    else:
        print(f"[{level}] {message}")


def emit_json(payload: Dict[str, Any]) -> None:
    """ConvertTo-Json -Compress equivalent."""
    print(json.dumps(payload, separators=(",", ":")))


def find_default_orchestration_root() -> Optional[str]:
    here = Path(__file__).resolve().parent
    candidate = here.parent
    rc, out, _ = run_git(["-C", str(candidate), "rev-parse", "--show-toplevel"])
    if rc != 0 or not out.strip():
        return None
    return out.strip().splitlines()[-1].strip()


def test_member_repo_marker(root: str) -> bool:
    """True if the root LOOKS like a Workspace-Control member repo
    (marker-only .gald3r/: has .identity but no manifest AND no TASKS.md)."""
    r = Path(root)
    if not (r / ".gald3r" / ".identity").exists():
        return False
    if (r / ".gald3r" / "linking" / "workspace_manifest.yaml").exists():
        return False
    if (r / ".gald3r" / "TASKS.md").exists():
        return False
    return True


def test_path_against_globs(path: str, globs: List[str]) -> bool:
    """Mirror PS -like (case-insensitive; * matches any chars incl. '/').
    ** is collapsed to * as in the PS1."""
    p = path.lower()
    for g in globs:
        g2 = g.replace("**", "*").lower()
        if fnmatch.fnmatchcase(p, g2):
            return True
    return False


def get_porcelain_entries(root: str) -> Optional[List[Entry]]:
    """git status --porcelain=v1 -uall parsed into entries (None on failure)."""
    rc, out, _ = run_git(["-C", root, "status", "--porcelain=v1", "-uall"])
    if rc != 0:
        return None
    entries: List[Entry] = []
    for line in out.splitlines():
        s = str(line)
        if len(s) < 4:
            continue
        xy = s[:2]
        rest = s[3:]
        path = rest
        orig = ""
        m = re.match(r"^(.+)\s->\s(.+)$", rest)
        if m:
            orig = m.group(1).strip('"')
            path = m.group(2)
        path = path.strip('"').replace("\\", "/")
        entries.append(Entry(xy=xy, path=path, original=orig, raw=s))
    return entries


def test_path_safety(path: str, xy: str) -> Dict[str, Any]:
    # Conflict markers: U?, ?U, AA, DD all imply unresolved merge state.
    if "U" in xy or xy in ("AA", "DD"):
        return {"Safe": False, "Reason": "unresolved-conflict"}
    # Must live inside .gald3r/.
    if not path.startswith(".gald3r/"):
        return {"Safe": False, "Reason": "not-in-gald3r"}
    # Filename secret heuristic.
    leaf = path.rsplit("/", 1)[-1]
    if SECRET_NAME_RX.search(leaf):
        return {"Safe": False, "Reason": "secret-name-pattern"}
    # Deny list wins.
    if test_path_against_globs(path, DENY_GLOBS):
        return {"Safe": False, "Reason": "sensitive-gald3r-path"}
    # Allow list.
    if test_path_against_globs(path, ALLOW_GLOBS):
        return {"Safe": True, "Reason": "allowlisted"}
    return {"Safe": False, "Reason": "unknown-gald3r-path"}


def format_commit_message(mode: str, task_id: str, bug_id: str,
                          override: str, file_count: int) -> str:
    if override:
        return override
    if mode == "preflight":
        title = "chore(gald3r): preflight gald3r housekeeping"
        body = ("Commit controller .gald3r housekeeping before g-go clean gate "
                f"execution.\n\nFiles: {file_count}")
    else:
        title = "chore(gald3r): commit g-go coordination state"
        body = ("Commit controller .gald3r coordination updates after g-go "
                f"shared-state writes.\n\nFiles: {file_count}")
    refs = []
    if task_id:
        refs.append(f"Task: #{task_id}")
    if bug_id:
        refs.append(f"Bug: {bug_id}")
    if refs:
        body += "\n" + "\n".join(refs)
    return f"{title}\n\n{body}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe controller .gald3r/ housekeeping safety classifier (T531).")
    parser.add_argument("-OrchestrationRoot", "--orchestration-root",
                        dest="orchestration_root", default="",
                        help="Orchestration git root (default: resolved from script location).")
    parser.add_argument("-Mode", "--mode", dest="mode", default="preflight",
                        choices=["preflight", "post-write"],
                        help="Classification mode (default: preflight).")
    parser.add_argument("-TaskId", "-Task", "-Bug", "--task-id", dest="task_id",
                        default="", help="Task id reference for the commit trailer.")
    parser.add_argument("-BugId", "--bug-id", dest="bug_id", default="",
                        help="Bug id reference for the commit trailer.")
    parser.add_argument("-Message", "--message", dest="message", default="",
                        help="Override commit message.")
    parser.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                        help="Stage + commit the safe path set when uniform.")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit a compact JSON result object.")
    parser.add_argument("-NoColor", "--no-color", dest="no_color",
                        action="store_true", help="Disable colored output.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    global USE_COLOR
    args = build_parser().parse_args(argv)
    USE_COLOR = not args.no_color
    as_json = args.json

    orch = args.orchestration_root or find_default_orchestration_root()
    if not orch:
        if as_json:
            emit_json({"status": "config-fault", "reason": "no-orchestration-root"})
        else:
            write_status_line("RED", "Could not resolve orchestration git root.")
        return 2
    orch_path = Path(orch)
    if not orch_path.exists():
        if as_json:
            emit_json({"status": "config-fault", "reason": "no-orchestration-root"})
        else:
            write_status_line("RED", "Could not resolve orchestration git root.")
        return 2
    orch = str(orch_path.resolve())

    # Refuse to operate on member-repo targets (T213/g-rl-36 boundary).
    if test_member_repo_marker(orch):
        if as_json:
            emit_json({"status": "config-fault", "reason": "member-repo-target",
                       "root": orch})
        else:
            write_status_line(
                "RED", f"Refusing to run: {orch} looks like a Workspace-Control "
                       "member repo (marker-only .gald3r/).")
        return 2

    entries = get_porcelain_entries(orch)
    if entries is None:
        if as_json:
            emit_json({"status": "config-fault", "reason": "git-status-failed",
                       "root": orch})
        else:
            write_status_line("RED", "git status --porcelain failed.")
        return 2

    if not entries:
        payload = {"status": "clean", "mode": args.mode, "root": orch,
                   "files": [], "unsafe": []}
        if as_json:
            emit_json(payload)
        else:
            write_status_line("GREEN", f"Clean working tree at {orch}")
        return 0

    safe: List[Dict[str, str]] = []
    unsafe: List[Dict[str, str]] = []
    for e in entries:
        r = test_path_safety(e.path, e.xy)
        rec = {"Path": e.path, "XY": e.xy, "Reason": r["Reason"]}
        (safe if r["Safe"] else unsafe).append(rec)

    # Drift check: any unsafe -> mixed-dirty / unsafe-gald3r / conflict.
    if unsafe:
        has_conflict = any(u["Reason"] == "unresolved-conflict" for u in unsafe)
        has_non_gald3r = any(u["Reason"] == "not-in-gald3r" for u in unsafe)
        if has_conflict:
            status = "conflict"
        elif has_non_gald3r:
            status = "mixed-dirty"
        else:
            status = "unsafe-gald3r"
        payload = {
            "status": status, "mode": args.mode, "root": orch,
            "files": [{"path": s["Path"], "xy": s["XY"], "reason": s["Reason"]}
                      for s in safe],
            "unsafe": [{"path": u["Path"], "xy": u["XY"], "reason": u["Reason"]}
                       for u in unsafe],
        }
        if as_json:
            emit_json(payload)
        else:
            write_status_line(
                "RED", f"Blocker: {status} ({len(unsafe)} unsafe path(s); "
                       f"{len(safe)} safe path(s))")
            for u in unsafe:
                print(f"  {u['XY']} {u['Path']}  -- {u['Reason']}")
            if safe:
                print()
                print("Safe paths (would have been committed if dirt set were uniform):")
                for s in safe:
                    print(f"  {s['XY']} {s['Path']}")
            print()
            print("Resolve unsafe paths first (commit/stash/move them), then re-run.")
        return 1

    # Pure safe set.
    cls = ("safe-gald3r-housekeeping" if args.mode == "preflight"
           else "safe-gald3r-coordination")

    if not args.apply:
        payload = {
            "status": cls, "mode": args.mode, "root": orch,
            "files": [{"path": s["Path"], "xy": s["XY"], "reason": s["Reason"]}
                      for s in safe],
            "unsafe": [],
        }
        if as_json:
            emit_json(payload)
        else:
            write_status_line(
                "YELLOW", f"{cls} -- {len(safe)} safe path(s); pass -Apply to commit.")
            for s in safe:
                print(f"  {s['XY']} {s['Path']}")
        return 0

    # Apply: stage explicit paths, re-check drift, commit, post-check drift.
    paths: List[str] = []
    for s in safe:
        if s["Path"] not in paths:
            paths.append(s["Path"])
    rc, _, _ = run_git(["-C", orch, "add", "--", *paths])
    if rc != 0:
        if as_json:
            emit_json({"status": "config-fault", "reason": "git-add-failed",
                       "root": orch})
        else:
            write_status_line("RED", "git add failed.")
        return 2

    # Drift re-check: anything unstaged outside our path set => fail closed.
    post = get_porcelain_entries(orch) or []
    drift = [e for e in post if len(e.xy) > 1 and e.xy[1] != " "
             and e.path not in paths]
    if drift:
        run_git(["-C", orch, "reset", "HEAD", "--", *paths])
        if as_json:
            emit_json({
                "status": "drift-detected", "mode": args.mode, "root": orch,
                "files": [],
                "unsafe": [{"path": d.path, "xy": d.xy, "reason": "concurrent-write"}
                           for d in drift],
            })
        else:
            write_status_line(
                "RED", "Drift detected after staging: another writer touched the "
                       "tree concurrently. Staging reverted.")
            for d in drift:
                print(f"  {d.xy} {d.path}")
        return 1

    msg = format_commit_message(args.mode, args.task_id, args.bug_id,
                                args.message, len(paths))

    # Use a temp file to avoid shell quoting hazards on Windows.
    fd, tmp = tempfile.mkstemp(prefix="gald3r_commit_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(msg)
        rc, _, _ = run_git(["-C", orch, "commit", "-F", tmp])
        if rc != 0:
            if as_json:
                emit_json({"status": "config-fault", "reason": "git-commit-failed",
                           "root": orch})
            else:
                write_status_line("RED", "git commit failed.")
            return 2
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    _, sha_out, _ = run_git(["-C", orch, "rev-parse", "HEAD"])
    sha = sha_out.strip()
    payload = {
        "status": f"committed-{cls}", "mode": args.mode, "root": orch,
        "commit_sha": sha, "file_count": len(paths),
        "files": [{"path": p, "xy": "", "reason": "allowlisted"} for p in paths],
        "unsafe": [],
    }
    if as_json:
        emit_json(payload)
    else:
        write_status_line(
            "GREEN", f"Committed {len(paths)} safe path(s) as {sha} ({cls}). "
                     "Run continues.")
        for p in paths:
            print(f"  -- {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
