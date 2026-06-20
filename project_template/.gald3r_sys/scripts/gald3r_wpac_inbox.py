#!/usr/bin/env python3
"""Python port of gald3r_wpac_inbox.ps1 (T428).

WPAC inbox message-folder migration + archive.

Upgrades the WPAC cross-project inbox from a single flat INBOX.md into a
lightweight index table backed by individual message files, plus an archive
mechanism that keeps the active index lean.

Layout (anchored on the canonical linking/ directory the hook already reads):
  .gald3r/linking/INBOX.md                 <- lightweight index table
  .gald3r/linking/messages/                <- one file per message
      msg_{id}_{type}_{source}.md
  .gald3r/linking/messages/archive/        <- archived [DONE] message files
      archive_index.md                     <- append-only archive index table

Operations:
  -Migrate   Idempotent: extract inline messages from a legacy flat INBOX.md
             into individual message files and rewrite INBOX.md as the index.
             Safe to re-run (second run is a no-op when already migrated).
  -Archive   Move [DONE] messages older than -ThresholdDays (default 30) from
             the active index into messages/archive/ and prune their index rows.

Notes:
  - Pure ASCII source (BUG-127/132). The em-dash (U+2014) that real inbox
    headings use is referenced via the "\\u2014" escape, never embedded
    literally.
  - Backward-compat: if messages/ is absent it is created silently; a legacy
    flat INBOX.md (inline bodies) is recognized and migrated without data loss.
  - Inbox/message files are DATA: written as UTF-8 WITHOUT a BOM; reads are
    UTF-8 (BOM-tolerant).
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# U+2014 EM DASH - kept out of the source bytes for ASCII safety (matches the
# .ps1 [char]0x2014). The "\u2014" escape yields the em-dash character at
# runtime while keeping every source byte pure ASCII.
EM_DASH = "\u2014"


def read_utf8_text(path: Path) -> str:
    """Read a file as UTF-8, BOM-tolerant. Returns '' when absent/unreadable."""
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError:
        return ""


def read_utf8_lines(path: Path) -> list:
    text = read_utf8_text(path)
    if not text:
        return []
    return re.split(r"\r?\n", text)


def set_utf8_no_bom(path: Path, lines: list) -> None:
    """Write lines joined by LF (+trailing LF) as UTF-8 WITHOUT a BOM."""
    text = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def add_utf8_no_bom(path: Path, lines: list) -> None:
    """Append lines (LF-joined, +trailing LF) as UTF-8 WITHOUT a BOM."""
    existing = ""
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8-sig")
        except OSError:
            existing = ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    text = existing + ("\n".join(lines) + "\n")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def convert_to_slug(text: str) -> str:
    if not text:
        return "unknown"
    s = re.sub(r"[^a-z0-9]+", "_", text.lower())
    s = s.strip("_")
    if not s:
        return "unknown"
    if len(s) > 40:
        s = s[:40].strip("_")
    return s


def get_message_file_name(msg: dict) -> str:
    """Canonical message file name: msg_{id}_{type}_{source}.md (T428 AC#2).

    The id-slug has any leading "msg" token stripped so a synthetic id like
    "msg-20260416-001" does not produce a "msg_msg_..." double prefix.
    """
    id_slug = convert_to_slug(msg["id"])
    id_slug = re.sub(r"^msg_*", "", id_slug)
    if not id_slug:
        id_slug = "0"
    type_low = msg["kind"].lower()
    src_slug = convert_to_slug(msg["source"])
    return "msg_{0}_{1}_{2}.md".format(id_slug, type_low, src_slug)


def truncate_subject(text: str, max_len: int = 48) -> str:
    if not text:
        return "(no subject)"
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 3] + "..."


def format_age(then: datetime) -> str:
    delta = datetime.now() - then
    total_hours = delta.total_seconds() / 3600.0
    if total_hours < 24:
        return "{0}h".format(int(total_hours))
    return "{0}d".format(int(delta.days))


def get_project_name(project_root: Path) -> str:
    """Best-effort project name from .identity; falls back to the folder name."""
    identity_file = project_root / ".gald3r" / ".identity"
    if identity_file.exists():
        try:
            for line in identity_file.read_text(
                encoding="utf-8-sig", errors="replace"
            ).splitlines():
                m = re.match(r"^project_name=(.+)$", line)
                if m:
                    return m.group(1).strip()
        except OSError:
            pass
    return project_root.name


def get_legacy_messages(lines: list) -> list:
    """Parse a legacy flat INBOX.md into message dicts.

    Recognizes both heading styles the existing hook understands:
      "## [OPEN|DONE|CONFLICT] <id> - from: <proj> - YYYY-MM-DD"  (per-item)
      "## [STATUS] <free subject> - YYYY-MM-DD"                   (flat-body item)
    Section headers from the linking/INBOX.md template
      ("## [CONFLICT] - Items..." etc.) are treated as empty section scaffolding
      and ignored (no body, no date) so a fresh template migrates to an empty
      index.
    """
    messages = []
    current = None

    section_headers = [
        "[CONFLICT] " + EM_DASH + " Items That Block Work",
        "[REQUEST] " + EM_DASH + " Incoming Asks From Children",
        "[BROADCAST] " + EM_DASH + " Orders From Parent",
        "[SYNC] " + EM_DASH + " Peer Contract Updates From Siblings",
        "[RESOLVED] " + EM_DASH + " Archive",
    ]

    # Character class matching either an em-dash or a hyphen, used in the
    # structured-heading regexes (mirrors the .ps1 "[$EmDash\-]").
    dash_class = "[" + EM_DASH + r"\-]"

    for raw_line in lines:
        line = raw_line

        # Status heading of any of the recognized kinds.
        hm = re.match(r"^##\s+\[(OPEN|DONE|CONFLICT|RESOLVED)\]\s*(.*)$", line)
        if hm:
            status = hm.group(1).upper()
            rest = hm.group(2).strip()

            # Skip pure template section scaffolding lines (no real message body).
            is_section = False
            for h in section_headers:
                if "[{0}] {1}".format(status, rest) == h:
                    is_section = True
                    break
            if is_section or rest == "" or re.match(r"^" + EM_DASH, rest):
                if current is not None:
                    messages.append(current)
                current = None
                continue

            if current is not None:
                messages.append(current)

            # Try the structured per-item form first:
            #   <id> - from:/From: <proj> - YYYY-MM-DD
            item_id = ""
            src = ""
            subject = ""
            date = None
            sm = re.match(
                r"^(\S+)\s*" + dash_class + r"+\s*(?:from|From):\s*(.+?)\s*"
                + dash_class + r"+\s*(\d{4}-\d{2}-\d{2})\s*$",
                rest,
            )
            if sm:
                item_id = sm.group(1).strip()
                src = sm.group(2).strip()
                try:
                    date = datetime.strptime(sm.group(3), "%Y-%m-%d")
                except ValueError:
                    date = None
            else:
                fm = re.match(
                    r"^(.*?)\s*" + dash_class + r"+\s*(\d{4}-\d{2}-\d{2})\s*$",
                    rest,
                )
                if fm:
                    # Flat-body form: free subject then a trailing date.
                    subject = fm.group(1).strip()
                    try:
                        date = datetime.strptime(fm.group(2), "%Y-%m-%d")
                    except ValueError:
                        date = None
                else:
                    subject = rest

            kind = "INFO"
            if re.search(r"\bORDER\b", rest, re.IGNORECASE) or re.match(
                r"^ORD", item_id, re.IGNORECASE
            ):
                kind = "ORDER"
            elif re.search(r"\bREQUEST\b", rest, re.IGNORECASE) or re.match(
                r"^REQ", item_id, re.IGNORECASE
            ):
                kind = "REQUEST"
            elif re.search(r"\bBROADCAST\b", rest, re.IGNORECASE) or re.match(
                r"^BCAST", item_id, re.IGNORECASE
            ):
                kind = "BROADCAST"
            elif re.search(r"\bSYNC\b", rest, re.IGNORECASE) or re.match(
                r"^SYNC", item_id, re.IGNORECASE
            ):
                kind = "SYNC"
            elif re.match(r"^INFO", item_id, re.IGNORECASE):
                kind = "INFO"
            if status == "CONFLICT":
                kind = "CONFLICT"

            current = {
                "id": item_id,
                "status": status,
                "kind": kind,
                "source": src,
                "subject": subject,
                "date": date,
                "header_raw": rest,
                "body": [],
            }
            continue

        if current is not None:
            # Pull a Subject/From/Source from the body if not already captured.
            if not current["subject"]:
                sub_m = re.match(r"^\*\*Subject:\*\*\s*(.+)$", line)
                if sub_m:
                    current["subject"] = sub_m.group(1).strip()
            if not current["source"]:
                src_m = re.match(r"^\*\*(?:Source|From)\*\*:\s*(.+)$", line)
                if src_m:
                    current["source"] = re.sub(
                        r"\s*\(.*$", "", src_m.group(1).strip()
                    ).strip()
            current["body"].append(line)

    if current is not None:
        messages.append(current)

    # Stable synthetic IDs + dates for items that lacked them.
    seq = 0
    for m in messages:
        seq += 1
        if not m["date"]:
            m["date"] = datetime.now()
        if not m["source"]:
            m["source"] = "unknown"
        if not m["id"]:
            m["id"] = "msg-{0}-{1:03d}".format(m["date"].strftime("%Y%m%d"), seq)
    return messages


def write_message_file(msg: dict, msg_dir: Path) -> str:
    status_lower = msg["status"].lower()
    file_name = get_message_file_name(msg)
    file_path = msg_dir / file_name

    # Idempotency: never clobber an already-migrated message file.
    if file_path.exists():
        return file_name

    if msg["subject"]:
        subj = msg["subject"]
    elif msg["header_raw"]:
        subj = msg["header_raw"]
    else:
        subj = "(no subject)"
    created_at = msg["date"].strftime("%Y-%m-%d")
    actioned_at = created_at if msg["status"] in ("DONE", "RESOLVED") else ""

    fm = []
    fm.append("---")
    fm.append("id: {0}".format(msg["id"]))
    fm.append("type: {0}".format(msg["kind"]))
    fm.append("source_project: {0}".format(msg["source"]))
    fm.append("subject: '{0}'".format(subj.replace("'", "''")))
    fm.append("status: {0}".format(status_lower))
    fm.append("created_at: '{0}'".format(created_at))
    fm.append("actioned_at: '{0}'".format(actioned_at))
    fm.append("---")
    fm.append("")
    fm.append("# [{0}] {1}".format(msg["kind"], subj))
    fm.append("")
    if msg["source"] and msg["source"] != "unknown":
        fm.append("**Source**: {0}".format(msg["source"]))
        fm.append("")
    for b in msg["body"]:
        fm.append(b)

    set_utf8_no_bom(file_path, fm)
    return file_name


def new_index_lines(project_name: str, messages: list) -> list:
    lines = []
    lines.append("<!-- WPAC-INDEX-V1 -->")
    lines.append("# INBOX " + EM_DASH + " " + project_name)
    lines.append("")
    lines.append(
        "> WPAC cross-project coordination inbox (index). Managed by g-skl-wpac-read."
    )
    lines.append(
        "> Message bodies live under messages/. Session-start hook checks this file."
    )
    lines.append("> CONFLICT rows block session work until resolved via @g-wpac-read.")
    lines.append("")
    lines.append("| Status | ID | Type | Source | Subject | Age | File |")
    lines.append("|---|---|---|---|---|---|---|")
    for m in sorted(messages, key=lambda x: x["date"]):
        status_cell = "[{0}]".format(m["status"])
        subj_src = m["subject"] if m["subject"] else m["header_raw"]
        subj_cell = truncate_subject(subj_src)
        age = format_age(m["date"])
        file_name = get_message_file_name(m)
        link = "[{0}](messages/{0})".format(file_name)
        lines.append(
            "| {0} | {1} | {2} | {3} | {4} | {5} | {6} |".format(
                status_cell, m["id"], m["kind"], m["source"], subj_cell, age, link
            )
        )
    lines.append("")
    return lines


def get_index_rows(lines: list) -> list:
    """Read the migrated index table into row dicts."""
    rows = []
    for line in lines:
        if not line.startswith("|"):
            continue
        if re.match(r"^\|\s*Status\s*\|", line):
            continue  # header
        if re.match(r"^\|[\s\-:]+\|[\s\-:]+\|", line):
            continue  # separator
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        status_raw = re.sub(r"[\[\]]", "", cells[0])
        file_cell = cells[6]
        file_name = ""
        fm = re.search(r"\(messages/([^)]+)\)", file_cell)
        if fm:
            file_name = fm.group(1)
        else:
            bm = re.search(r"\[([^\]]+)\]", file_cell)
            if bm:
                file_name = bm.group(1)
        rows.append(
            {
                "raw_line": line,
                "status": status_raw.upper(),
                "id": cells[1],
                "kind": cells[2],
                "source": cells[3],
                "subject": cells[4],
                "age": cells[5],
                "file_name": file_name,
            }
        )
    return rows


def test_already_migrated(inbox_path: Path) -> bool:
    if not inbox_path.exists():
        return False
    raw = read_utf8_text(inbox_path)
    if not raw:
        return False
    return bool(re.search(r"<!--\s*WPAC-INDEX-V1\s*-->", raw))


def initialize_message_dirs(msg_dir: Path, archive_dir: Path) -> None:
    # Backward-compat: silently create messages/ (+ archive/) when absent.
    msg_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)


def invoke_migrate(project_root: Path, quiet: bool) -> None:
    linking_dir = project_root / ".gald3r" / "linking"
    inbox_path = linking_dir / "INBOX.md"
    msg_dir = linking_dir / "messages"
    archive_dir = msg_dir / "archive"

    def info(message: str) -> None:
        if not quiet:
            print(message)

    initialize_message_dirs(msg_dir, archive_dir)

    if not inbox_path.exists():
        # No inbox yet: write an empty index so the layout is initialized.
        idx = new_index_lines(get_project_name(project_root), [])
        set_utf8_no_bom(inbox_path, idx)
        info("WPAC inbox: initialized empty index at .gald3r/linking/INBOX.md")
        return

    if test_already_migrated(inbox_path):
        info("WPAC inbox: already migrated (index format) - no-op")
        return

    raw_lines = read_utf8_lines(inbox_path)
    if not raw_lines:
        raw_lines = []

    messages = get_legacy_messages(raw_lines)
    migrated = 0
    for m in messages:
        write_message_file(m, msg_dir)
        migrated += 1

    idx = new_index_lines(get_project_name(project_root), messages)
    set_utf8_no_bom(inbox_path, idx)

    info(
        "WPAC inbox: migrated {0} message(s) to messages/; INBOX.md rewritten as index".format(
            migrated
        )
    )


def invoke_archive(project_root: Path, threshold_days: int, quiet: bool) -> None:
    linking_dir = project_root / ".gald3r" / "linking"
    inbox_path = linking_dir / "INBOX.md"
    msg_dir = linking_dir / "messages"
    archive_dir = msg_dir / "archive"
    archive_idx = archive_dir / "archive_index.md"

    def info(message: str) -> None:
        if not quiet:
            print(message)

    initialize_message_dirs(msg_dir, archive_dir)

    if not inbox_path.exists():
        info("WPAC inbox: nothing to archive (no INBOX.md)")
        return
    if not test_already_migrated(inbox_path):
        # Archive only operates on the new index layout; migrate first.
        invoke_migrate(project_root, quiet)

    raw_lines = read_utf8_lines(inbox_path)
    if not raw_lines:
        raw_lines = []
    rows = get_index_rows(raw_lines)

    today = datetime.now().date()
    from datetime import timedelta

    cutoff = today - timedelta(days=threshold_days)
    to_archive = []

    for r in rows:
        if r["status"] != "DONE" and r["status"] != "RESOLVED":
            continue
        if not r["file_name"]:
            continue
        file_path = msg_dir / r["file_name"]
        if not file_path.exists():
            continue

        # created_at from the message file frontmatter decides eligibility.
        created = None
        for fl in read_utf8_lines(file_path):
            cm = re.match(r"^created_at:\s*'?(\d{4}-\d{2}-\d{2})'?", fl)
            if cm:
                try:
                    created = datetime.strptime(cm.group(1), "%Y-%m-%d")
                except ValueError:
                    created = None
                break
        if not created:
            continue
        if created.date() <= cutoff:
            to_archive.append(r)

    if len(to_archive) == 0:
        info(
            "WPAC inbox: no [DONE] messages older than {0} day(s) to archive".format(
                threshold_days
            )
        )
        return

    # Ensure the archive index has a header.
    if not archive_idx.exists():
        hdr = [
            "<!-- WPAC-ARCHIVE-INDEX-V1 -->",
            "# INBOX ARCHIVE",
            "",
            "> Archived [DONE] WPAC messages moved out of the active index.",
            "",
            "| Status | ID | Type | Source | Subject | Archived | File |",
            "|---|---|---|---|---|---|---|",
        ]
        set_utf8_no_bom(archive_idx, hdr)

    stamp = datetime.now().strftime("%Y-%m-%d")
    archived_rows = []
    for r in to_archive:
        src = msg_dir / r["file_name"]
        dst = archive_dir / r["file_name"]
        if src.exists():
            if dst.exists():
                dst.unlink()
            src.replace(dst)
        link = "[{0}]({0})".format(r["file_name"])
        archived_rows.append(
            "| [{0}] | {1} | {2} | {3} | {4} | {5} | {6} |".format(
                r["status"], r["id"], r["kind"], r["source"], r["subject"], stamp, link
            )
        )
    add_utf8_no_bom(archive_idx, archived_rows)

    # Prune archived rows from the active index (match by message file name).
    archive_names = {}
    for r in to_archive:
        archive_names[r["file_name"]] = True
    new_lines = []
    for line in raw_lines:
        drop = False
        if line.startswith("|"):
            for name in archive_names:
                if re.search(re.escape("messages/" + name), line):
                    drop = True
                    break
        if not drop:
            new_lines.append(line)
    set_utf8_no_bom(inbox_path, new_lines)

    info(
        "WPAC inbox: archived {0} [DONE] message(s) older than {1} day(s) to messages/archive/".format(
            len(to_archive), threshold_days
        )
    )


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="WPAC inbox message-folder migration + archive (Python port of gald3r_wpac_inbox.ps1)"
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default=os.getcwd()
    )
    parser.add_argument(
        "-Migrate", "--migrate", dest="migrate", action="store_true"
    )
    parser.add_argument(
        "-Archive", "--archive", dest="archive", action="store_true"
    )
    parser.add_argument(
        "-ThresholdDays",
        "--threshold-days",
        dest="threshold_days",
        type=int,
        default=30,
    )
    parser.add_argument("-Quiet", "--quiet", dest="quiet", action="store_true")
    args, _ = parser.parse_known_args(argv)

    project_root = Path(args.project_root)

    if args.archive:
        invoke_archive(project_root, args.threshold_days, args.quiet)
    else:
        # Default operation is Migrate (also the -Migrate switch path).
        invoke_migrate(project_root, args.quiet)

    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:
        # Never crash the host session on unexpected errors.
        sys.exit(0)
