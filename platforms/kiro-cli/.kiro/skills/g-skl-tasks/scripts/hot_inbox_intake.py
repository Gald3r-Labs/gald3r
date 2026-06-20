#!/usr/bin/env python3
"""Python port of hot_inbox_intake.ps1 (T1585).

Intake staged task/bug drafts from gitignored inbox folders into the live
tracked state (T1573). Scans .gald3r/tasks/inbox/ and .gald3r/bugs/inbox/ for
.md draft files, assigns the next sequential IDs, writes proper task/bug files
with full frontmatter, appends rows to TASKS.md / BUGS.md, and commits as a
single gald3r housekeeping commit.

Run at the start of each g-go-go iteration (before the WPAC gate and claim
loop) so new tasks/bugs created mid-run are never written to TASKS.md
directly.

Examples:
    python hot_inbox_intake.py
    python hot_inbox_intake.py -DryRun
    python hot_inbox_intake.py -ProjectRoot /path/to/repo -Quiet
"""
# @subsystems: TASK_MANAGEMENT
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple


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


_QUIET = False


def write_msg(msg: str) -> None:
    if not _QUIET:
        print(msg)


# -- ID helpers ----------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _max_id_in_tree(root: Path, file_glob: str, name_re) -> int:
    """Max numeric id from `<prefix><NNN>_*.md` filenames under a folder tree."""
    max_id = 0
    if root.is_dir():
        for p in root.rglob(file_glob):
            m = name_re.match(p.name)
            if m:
                max_id = max(max_id, int(m.group(1)))
    return max_id


def get_next_task_id(gald_path: Path) -> int:
    """Next task id = (max id across ALL task folders) + 1.

    Scans `tasks/` AND `archive/tasks/` for `task<NNN>_*.md` filenames — the
    files are the ground truth. TASKS.md is intentionally NOT consulted: its id
    format is regenerator-dependent (`[NNN]` vs a stray `[T NNN]`), which caused
    the T585-T596 inbox collision when one `[T572]` row was the only regex match.
    Folder scanning is immune to that and sees completed/paused/archived ids too.
    """
    name_re = re.compile(r"task0*(\d+)_")
    return max(
        _max_id_in_tree(gald_path / "tasks", "task*.md", name_re),
        _max_id_in_tree(gald_path / "archive" / "tasks", "task*.md", name_re),
    ) + 1


def get_next_bug_id(gald_path: Path) -> int:
    """Next bug id = (max id across ALL bug folders) + 1. Scans `bugs/` AND
    `archive/bugs/` for `bug<NNN>_*.md` filenames (ground truth, not BUGS.md)."""
    name_re = re.compile(r"bug0*(\d+)_")
    return max(
        _max_id_in_tree(gald_path / "bugs", "bug*.md", name_re),
        _max_id_in_tree(gald_path / "archive" / "bugs", "bug*.md", name_re),
    ) + 1


# -- Parse inbox draft ----------------------------------------------------------

@dataclass
class Draft:
    title: str
    priority: str
    type: str
    subsys: str
    notes: str


def read_draft(file_path: Path) -> Draft:
    """Regex frontmatter parse — no YAML dependency (mirrors the PS1)."""
    raw = _read_text(file_path)

    m = re.search(r"(?m)^title:\s*['\"]?(.+?)['\"]?\s*$", raw)
    if m:
        title = m.group(1).strip()
    else:
        title = re.sub(r"[-_]", " ", file_path.name[:-3]
                       if file_path.name.endswith(".md") else file_path.name)

    m = re.search(r"(?m)^priority:\s*(\w+)", raw)
    priority = m.group(1).strip() if m else "medium"

    m = re.search(r"(?m)^type:\s*(\w+)", raw)
    type_ = m.group(1).strip() if m else "feature"

    m = re.search(r"(?m)^subsystems:\s*(.+)", raw)
    subsys = m.group(1).strip() if m else "[]"

    if re.search(r"(?ms)^##\s+.+", raw):
        notes = re.sub(r"(?ms)^---.*?---\s*", "", raw, count=0)
    else:
        notes = ""

    return Draft(title=title, priority=priority, type=type_,
                 subsys=subsys, notes=notes)


def make_slug(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9 ]", "", title)
    slug = re.sub(r"\s+", "_", slug)
    slug = re.sub(r"_+", "_", slug)
    if len(slug) > 50:
        slug = slug[:50].rstrip("_")
    return slug.lower()


def short_title(title: str) -> str:
    return title[:62] + "..." if len(title) > 65 else title


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Intake staged task/bug drafts from gitignored inbox "
                    "folders into the live tracked state (T1573).")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=str(Path.cwd()),
                        help="Root of the gald3r repo (default: cwd).")
    parser.add_argument("-DryRun", "--dry-run", dest="dry_run",
                        action="store_true",
                        help="Print planned actions without writing anything.")
    parser.add_argument("-Quiet", "--quiet", dest="quiet", action="store_true",
                        help="Suppress per-file output (still prints final summary).")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    global _QUIET
    args = build_parser().parse_args(argv)
    _QUIET = args.quiet
    dry_run = args.dry_run

    project_root = Path(args.project_root)
    gald_path = project_root / ".gald3r"
    task_inbox = gald_path / "tasks" / "inbox"
    bug_inbox = gald_path / "bugs" / "inbox"
    tasks_dir = gald_path / "tasks" / "open"
    bugs_dir = gald_path / "bugs"
    tasks_md = gald_path / "TASKS.md"
    bugs_md = gald_path / "BUGS.md"

    staged_paths: List[Path] = []
    tasks_ingested = 0
    bugs_ingested = 0
    today = date.today().strftime("%Y-%m-%d")

    # -- Process task inbox -----------------------------------------------------
    if task_inbox.is_dir():
        drafts = sorted(task_inbox.glob("*.md"), key=lambda p: p.name)
        for draft in drafts:
            d = read_draft(draft)
            task_id = get_next_task_id(gald_path)
            slug = make_slug(d.title)
            filename = f"task{task_id}_{slug}.md"
            dest_path = tasks_dir / filename
            s_title = short_title(d.title)

            task_body = f"""---
id: T{task_id}
title: "{d.title}"
status: pending
priority: {d.priority}
type: {d.type}
subsystems: {d.subsys}
created: {today}
source: inbox_intake
---

## Requirements

{d.notes}

## Status History

| Timestamp | From | To | Agent | Message |
|-----------|------|----|-------|---------|
| {today} | — | pending | hot_inbox_intake.py | Ingested from tasks/inbox/{draft.name} |"""

            tasks_row = (f"| [pending] | [T{task_id}](tasks/open/{filename}) | "
                         f"{s_title} | {d.priority} | {d.type} |")

            if dry_run:
                write_msg(f"  [DRY-RUN] Would create: {dest_path}")
                write_msg(f"  [DRY-RUN] Would append TASKS.md: {tasks_row}")
            else:
                tasks_dir.mkdir(parents=True, exist_ok=True)
                dest_path.write_text(task_body.rstrip() + "\n", encoding="utf-8")
                write_msg(f"  CREATED: {dest_path}")

                # Append row to TASKS.md — insert after the last [pending] row
                if tasks_md.is_file():
                    lines = _read_text(tasks_md).splitlines()
                    # Update total count comment
                    lines = [
                        re.sub(r"(?<=Total: )\d+(?= tasks)",
                               lambda m: str(int(m.group(0)) + 1), ln)
                        for ln in lines
                    ]
                    last_pending_idx = -1
                    for i in range(len(lines) - 1, -1, -1):
                        if re.search(r"^\| \[pending\]|\[📋\]", lines[i]):
                            last_pending_idx = i
                            break
                    if last_pending_idx >= 0:
                        lines.insert(last_pending_idx + 1, tasks_row)
                        tasks_md.write_text("\n".join(lines), encoding="utf-8")
                    else:
                        with tasks_md.open("a", encoding="utf-8") as fh:
                            fh.write(tasks_row + "\n")

                draft.unlink()
                staged_paths.append(dest_path)
                staged_paths.append(tasks_md)
            tasks_ingested += 1

    # -- Process bug inbox --------------------------------------------------------
    if bug_inbox.is_dir():
        drafts = sorted(bug_inbox.glob("*.md"), key=lambda p: p.name)
        for draft in drafts:
            d = read_draft(draft)
            bug_num = get_next_bug_id(gald_path)
            bug_id = f"BUG-{bug_num}"
            slug = make_slug(d.title)
            filename = f"bug{bug_num}_{slug}.md"
            dest_path = bugs_dir / filename
            s_title = short_title(d.title)

            bug_body = f"""---
id: {bug_id}
title: "{d.title}"
severity: {d.priority}
status: open
subsystems: {d.subsys}
reported: {today}
source: inbox_intake
---

## Description

{d.notes}

## Status History

| Timestamp | From | To | Agent | Message |
|-----------|------|----|-------|---------|
| {today} | — | open | hot_inbox_intake.py | Ingested from bugs/inbox/{draft.name} |"""

            bugs_row = (f"| [{bug_id}](bugs/{filename}) | {s_title} | "
                        f"{d.priority} | open | {d.subsys} | {today} |")

            if dry_run:
                write_msg(f"  [DRY-RUN] Would create: {dest_path}")
                write_msg(f"  [DRY-RUN] Would append BUGS.md: {bugs_row}")
            else:
                bugs_dir.mkdir(parents=True, exist_ok=True)
                dest_path.write_text(bug_body.rstrip() + "\n", encoding="utf-8")
                write_msg(f"  CREATED: {dest_path}")

                if bugs_md.is_file():
                    with bugs_md.open("a", encoding="utf-8") as fh:
                        fh.write(bugs_row + "\n")

                draft.unlink()
                staged_paths.append(dest_path)
                staged_paths.append(bugs_md)
            bugs_ingested += 1

    # -- Summary and commit -------------------------------------------------------
    total = tasks_ingested + bugs_ingested
    if total == 0:
        write_msg("Inbox empty — nothing to intake.")
        return 0

    write_msg(f"Intake complete: {tasks_ingested} task(s), {bugs_ingested} bug(s)")

    if dry_run:
        write_msg("DRY-RUN: no files written, no commit.")
        return 0

    # Commit — stage explicit paths only, never `git add .`
    unique_paths: List[Path] = []
    for p in staged_paths:
        if p not in unique_paths:
            unique_paths.append(p)
    for p in unique_paths:
        try:
            rel = p.resolve().relative_to(project_root.resolve())
        except ValueError:
            continue
        if (project_root / rel).exists():
            run_git(["add", "--", str(rel).replace("\\", "/")], cwd=project_root)
    _, staged, _ = run_git(["diff", "--cached", "--name-only"], cwd=project_root)
    if staged.strip():
        msg = (f"chore(gald3r): intake {tasks_ingested} task(s) / "
               f"{bugs_ingested} bug(s) from inbox")
        run_git(["commit", "-m", msg], cwd=project_root)
        _, sha, _ = run_git(["rev-parse", "--short", "HEAD"], cwd=project_root)
        write_msg(f"Committed: {msg} ({sha.strip()})")
    else:
        write_msg("Nothing staged — files may already be current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
