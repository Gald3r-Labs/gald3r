#!/usr/bin/env python3
"""Python port of gald3r_tasks_archive_gate.ps1 (T1585).

TASKS.md line-count archive gate. Checks whether TASKS.md has grown beyond the
configured threshold and, when -Apply is passed, automatically archives all
terminal (completed/failed) tasks to .gald3r/archive/.

Exit codes:
    0  -- line count is below WarnAt (clean), or archive applied successfully
    1  -- line count is in the warning zone [WarnAt, Threshold)
    2  -- line count meets or exceeds Threshold (gate fires, no -Apply)
    3  -- error (bad paths, write failure, etc.)

With -Apply the archive operation runs when exit would be 2.
With -CheckOnly (default behavior) the script never mutates files.
"""
# @subsystems: TASK_MANAGEMENT
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


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


_HAS_ENGINE = _bootstrap_engine()  # pure-filesystem script; engine is optional

CHECK_CHAR = chr(0x2705)  # completed marker emoji
CROSS_CHAR = chr(0x274C)  # failed/cancelled marker emoji

_JSON_MODE = False


def write_out(msg: str) -> None:
    if not _JSON_MODE:
        print(msg)


def emit_json(data: Dict[str, Any]) -> None:
    if _JSON_MODE:
        print(json.dumps(data, separators=(",", ":")))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TASKS.md line-count archive gate (auto-archive terminal "
                    "tasks to .gald3r/archive/).")
    parser.add_argument("-CheckOnly", "--check-only", dest="check_only",
                        action="store_true",
                        help="Inspect and report only. Never writes (default).")
    parser.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                        help="When threshold is breached, run the archive operation.")
    parser.add_argument("-Threshold", "--threshold", dest="threshold", type=int,
                        default=1200, help="Line count at which the gate fires "
                                           "(default: 1200).")
    parser.add_argument("-WarnAt", "--warn-at", dest="warn_at", type=int,
                        default=900, help="Line count warning zone start "
                                          "(default: 900).")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=".", help="Root of the gald3r project.")
    parser.add_argument("-Json", "--json", dest="json", action="store_true",
                        help="Emit a single-line JSON object instead of "
                             "human-readable output.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    global _JSON_MODE
    args = build_parser().parse_args(argv)
    _JSON_MODE = args.json
    threshold = args.threshold
    warn_at = args.warn_at

    # ----------------------------------------------------------------------
    # Resolve paths
    # ----------------------------------------------------------------------
    root_p = Path(args.project_root)
    if not root_p.exists():
        print(f"ProjectRoot not found: {args.project_root}", file=sys.stderr)
        return 3
    root = root_p.resolve()

    gald3r_dir = root / ".gald3r"
    tasks_file = gald3r_dir / "TASKS.md"
    tasks_dir = gald3r_dir / "tasks"
    archive_root = gald3r_dir / "archive"

    if not tasks_file.is_file():
        print(f"TASKS.md not found at: {tasks_file}", file=sys.stderr)
        return 3

    # ----------------------------------------------------------------------
    # Count lines
    # ----------------------------------------------------------------------
    try:
        all_lines = tasks_file.read_text(encoding="utf-8-sig",
                                         errors="replace").splitlines()
    except OSError as exc:
        print(f"Failed to read TASKS.md: {exc}", file=sys.stderr)
        return 3
    line_count = len(all_lines)

    write_out("")
    write_out("======================================================")
    write_out("  TASKS.md Archive Gate")
    write_out("======================================================")
    write_out(f"  File       : {tasks_file}")
    write_out(f"  Line count : {line_count}  (threshold={threshold}, warn>={warn_at})")

    # Determine gate state
    gate_state = "clean"
    exit_code = 0
    if line_count >= threshold:
        gate_state = "breached"
        exit_code = 2
        write_out("")
        write_out(f"  [!] THRESHOLD BREACHED -- {line_count} lines >= {threshold}")
    elif line_count >= warn_at:
        gate_state = "warning"
        exit_code = 1
        write_out("")
        write_out(f"  [!] WARNING ZONE -- {line_count} lines >= {warn_at} "
                  f"(threshold: {threshold})")
    else:
        write_out(f"  [OK] Clean -- {line_count} lines (threshold: {threshold})")

    # ----------------------------------------------------------------------
    # Not breached -- report and exit
    # ----------------------------------------------------------------------
    if gate_state != "breached":
        emit_json({"gate_state": gate_state, "line_count": line_count,
                   "threshold": threshold, "warn_at": warn_at, "action": "none"})
        write_out("======================================================")
        return exit_code

    # ----------------------------------------------------------------------
    # Breached and CheckOnly
    # ----------------------------------------------------------------------
    if not args.apply:
        write_out("")
        write_out("  Run with -Apply to archive terminal tasks automatically.")
        write_out("  Command: .claude/skills/g-skl-tasks/scripts/"
                  "gald3r_tasks_archive_gate.py -Apply")
        emit_json({"gate_state": gate_state, "line_count": line_count,
                   "threshold": threshold, "warn_at": warn_at,
                   "action": "check_only"})
        write_out("======================================================")
        return 2

    # ======================================================================
    # APPLY MODE -- archive terminal tasks
    # ======================================================================
    write_out("")
    write_out("  Applying archive operation...")

    check_token = "[" + CHECK_CHAR + "]"
    cross_token = "[" + CROSS_CHAR + "]"
    terminal_rows = [line for line in all_lines
                     if check_token in line or cross_token in line]
    terminal_count = len(terminal_rows)
    write_out(f"  Terminal rows found: {terminal_count}")

    if terminal_count == 0:
        write_out("  [!] No terminal tasks found to archive. File is large but "
                  "all tasks are active.")
        write_out("  Consider reviewing non-terminal content for cleanup.")
        emit_json({"gate_state": gate_state, "line_count": line_count,
                   "threshold": threshold, "action": "no_terminal_tasks",
                   "terminal_count": 0})
        write_out("======================================================")
        return 0

    # ----------------------------------------------------------------------
    # Extract task metadata from rows
    # ----------------------------------------------------------------------
    # Supported row formats:
    #   Table:  | [x] | [123](tasks/task123_slug.md) | Title | type | deps |
    #   Bullet: - [x] **Task 123** -- Title   (also Task 123-1)
    archived_tasks: List[Dict[str, Any]] = []
    for row in terminal_rows:
        task_id: Optional[str] = None
        task_title: Optional[str] = None
        task_file: Optional[str] = None
        status_val = "completed" if check_token in row else "failed"

        m = re.search(
            r"\|\s*\[[^\]]+\]\s*\|\s*\[([^\]]+)\]\((tasks/[^\)]+)\)\s*\|\s*([^\|]+)\|",
            row)
        if m:
            task_id = m.group(1).strip()
            task_file = m.group(2).strip()
            task_title = m.group(3).strip()
        else:
            m = re.search(r"\*\*Task\s+([\d][\d\-]*)\*\*\s*[-]+\s*(.+)", row)
            if m:
                task_id = "T" + m.group(1).strip()
                task_title = m.group(2).strip()
                file_pattern = "task" + m.group(1).replace("-", "") + "_*.md"
                if tasks_dir.is_dir():
                    found = sorted(tasks_dir.glob(file_pattern))
                    if found:
                        task_file = "tasks/" + found[0].name

        if task_id:
            archived_tasks.append({
                "RowText": row, "TaskId": task_id, "TaskTitle": task_title,
                "TaskFile": task_file, "Status": status_val,
            })

    write_out(f"  Parseable terminal tasks: {len(archived_tasks)}")

    # ----------------------------------------------------------------------
    # Determine archive bucket
    # ----------------------------------------------------------------------
    archive_tasks_dir = archive_root / "tasks"
    archive_tasks_dir.mkdir(parents=True, exist_ok=True)

    next_ordinal_start = 0
    if archive_root.is_dir():
        for bucket in archive_root.glob("archive_tasks_*.md"):
            m = re.match(r"archive_tasks_(\d+)_(\d+)\.md$", bucket.name)
            if m:
                candidate_start = int(m.group(2)) + 1
                if candidate_start > next_ordinal_start:
                    next_ordinal_start = candidate_start

    bucket_size = 1000
    bucket_index = math.floor(next_ordinal_start / bucket_size)
    bucket_start = bucket_index * bucket_size
    bucket_end = bucket_start + bucket_size - 1
    bucket_name = f"tasks_{bucket_start:04d}_{bucket_end:04d}"
    bucket_dir = archive_tasks_dir / bucket_name
    bucket_start_fmt = f"{bucket_start:04d}"
    bucket_end_fmt = f"{bucket_end:04d}"
    bucket_file_name = f"archive_tasks_{bucket_start_fmt}_{bucket_end_fmt}.md"
    bucket_index_file = archive_root / bucket_file_name

    bucket_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%Y-%m-%d")

    # ----------------------------------------------------------------------
    # Move task files
    # ----------------------------------------------------------------------
    moved_files: List[str] = []
    ordinal = next_ordinal_start
    for task in archived_tasks:
        if task["TaskFile"]:
            src_file = gald3r_dir / task["TaskFile"]
            if src_file.is_file():
                dst_file = bucket_dir / src_file.name
                try:
                    shutil.move(str(src_file), str(dst_file))
                except OSError as exc:
                    print(f"Failed to move {src_file}: {exc}", file=sys.stderr)
                    return 3
                moved_files.append(str(src_file))
                write_out(f"    Moved: {task['TaskId']} -> {bucket_name}/")
        task["Ordinal"] = ordinal
        ordinal += 1

    write_out(f"  Files moved: {len(moved_files)}")

    # ----------------------------------------------------------------------
    # Build archive index rows
    # ----------------------------------------------------------------------
    index_rows = [
        "| {0} | {1} | [{2}] | {3} | {4} | {5} |".format(
            t["Ordinal"], t["TaskId"], t["Status"], t["TaskTitle"],
            t["TaskFile"], today)
        for t in archived_tasks
    ]

    # ----------------------------------------------------------------------
    # Write / append archive index file
    # ----------------------------------------------------------------------
    try:
        if bucket_index_file.is_file():
            existing_index = bucket_index_file.read_text(encoding="utf-8-sig",
                                                         errors="replace")
            append_block = "\n".join(index_rows)
            bucket_index_file.write_text(
                existing_index.rstrip() + "\n" + append_block + "\n",
                encoding="utf-8")
            write_out(f"  Archive index updated: {bucket_index_file}")
        else:
            header_block = (
                f"# Archive: Tasks {bucket_start_fmt}-{bucket_end_fmt}\n\n"
                f"Archive bucket: {bucket_name}\n"
                f"Archived: {today}\n"
                f"Total entries: {len(archived_tasks)}\n"
                "Source: .gald3r/TASKS.md -- <gald3r_source> controller\n"
                "Authorized by: gald3r_tasks_archive_gate.py -Apply "
                f"(auto-gate, {today})\n\n"
                "---\n\n"
                "## Index\n\n"
                "| Ordinal | Task ID | Status | Title | Original File | Archived |\n"
                "|---------|---------|--------|-------|---------------|----------|")
            footer_pointer = "*Archive pointers in TASKS.md reference this file.*"
            footer_files = (f"*Individual task files preserved in {bucket_name}/ "
                            "bucket.*")
            full_content = (header_block + "\n" + "\n".join(index_rows)
                            + "\n\n---\n\n" + footer_pointer + "\n"
                            + footer_files + "\n")
            bucket_index_file.write_text(full_content, encoding="utf-8")
            write_out(f"  Archive index created: {bucket_index_file}")
    except OSError as exc:
        print(f"Failed to write archive index: {exc}", file=sys.stderr)
        return 3

    # ----------------------------------------------------------------------
    # Rewrite TASKS.md without terminal rows
    # ----------------------------------------------------------------------
    terminal_row_set = set(terminal_rows)
    new_lines: List[str] = []
    skipped = 0
    for line in all_lines:
        if line in terminal_row_set:
            skipped += 1
        else:
            new_lines.append(line)

    archive_pointer_row = (
        "| [" + bucket_file_name + "](archive/" + bucket_file_name + ") | "
        + str(next_ordinal_start) + "-" + str(ordinal - 1)
        + f" | Auto-archived {today} | {today} | {len(archived_tasks)} |")

    has_archive_section = False
    for i, line in enumerate(new_lines):
        if re.match(r"^## Archive Pointers", line):
            has_archive_section = True
            for j in range(i + 1, len(new_lines)):
                if re.match(r"^\*Task files at", new_lines[j]):
                    new_lines.insert(j, archive_pointer_row)
                    break
            break

    if not has_archive_section:
        new_lines.extend([
            "", "---", "", "## Archive Pointers", "",
            "*Completed and cancelled task history has been moved to "
            ".gald3r/archive/. Task files are preserved; only active indexes "
            "and in-progress tasks remain above.*",
            "",
            "| Archive Index | Ordinal Range | Task IDs | Archived | Count |",
            "|--------------|---------------|----------|----------|-------|",
            archive_pointer_row,
            "",
            "*Task files at: .gald3r/archive/tasks/" + bucket_name + "/*",
        ])

    try:
        tasks_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"Failed to rewrite TASKS.md: {exc}", file=sys.stderr)
        return 3

    # ----------------------------------------------------------------------
    # Final report
    # ----------------------------------------------------------------------
    new_line_count = len(tasks_file.read_text(encoding="utf-8-sig",
                                              errors="replace").splitlines())

    write_out("")
    write_out("  [OK] Archive complete!")
    write_out(f"  Terminal rows removed : {skipped}")
    write_out(f"  Files moved           : {len(moved_files)}")
    write_out(f"  TASKS.md before       : {line_count} lines")
    write_out(f"  TASKS.md after        : {new_line_count} lines")
    write_out(f"  Archive index         : {bucket_index_file}")
    write_out(f"  Archive files bucket  : {bucket_dir}")

    emit_json({
        "gate_state": "archived",
        "line_count_before": line_count,
        "line_count_after": new_line_count,
        "threshold": threshold,
        "terminal_rows_removed": skipped,
        "files_moved": len(moved_files),
        "archive_index": str(bucket_index_file),
        "archive_bucket": str(bucket_dir),
        "action": "archived",
    })

    write_out("======================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
