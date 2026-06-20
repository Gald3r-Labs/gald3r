#!/usr/bin/env python3
"""Python port of g-hk-wpac-inbox-check.ps1 (T1584).

Cross-project INBOX scanner (T168 rewrite). Safe to call at session start,
before command work, during swarm heartbeats, and at final summaries.
Reads .gald3r/linking/INBOX.md, surfaces a per-item one-line summary grouped
by type, and auto-actions LOW-RISK item types only.

Auto-action policy (T168):
  [INFO]      -> auto-mark-read (low risk, no action required).
  [SYNC]      -> auto-mark-read (peer snapshot copy is left to @g-wpac-read).
  [BROADCAST] -> surface only; user must @g-wpac-read --ack <id>.
  [REQUEST]   -> surface only; user must @g-wpac-read --accept|--decline <id>.
  [ORDER]     -> surface only; user must @g-wpac-read --accept <id>; blocking.
  [CONFLICT]  -> preserve existing g-rl-25 behavior (warning + session gate).

With -BlockOnConflict, exits with ConflictExitCode when open CONFLICT items
exist (this is the hook's documented blocking purpose and is preserved).
Idempotent: auto-actioned items become [DONE]; re-runs are no-ops. Every
auto-action is audited to .gald3r/logs/wpac_auto_actions.log.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; this hook is pure stdlib)

# U+2014 EM DASH - kept out of the source bytes for ASCII safety (mirrors the
# .ps1 [char]0x2014). Real inbox headings separate fields with an em-dash; the
# regex below matches either an em-dash or a hyphen.
_EM = "\u2014"
ITEM_HEADING = re.compile(
    r"^## \[(OPEN|DONE|CONFLICT)\]\s+(\S+)\s*["
    + _EM
    + r"\-]+\s*from:\s*([^"
    + _EM
    + r"\-]+?)\s*["
    + _EM
    + r"\-]+\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)
CONFLICT_SECTION = re.compile(r"^## \[CONFLICT\]\s*$", re.IGNORECASE)
CHECKBOX_ITEM = re.compile(r"^\s*-\s*\[\s*\]\s*(.+)$")
SUBJECT_LINE = re.compile(r"^\*\*Subject:\*\*\s*(.+)$", re.IGNORECASE)


def format_age(then: datetime) -> str:
    delta = datetime.now() - then
    hours = delta.total_seconds() / 3600.0
    if hours < 24:
        return f"{int(round(hours))}h ago"
    return f"{int(round(hours / 24.0))}d ago"


def kind_for(item_id: str, status: str) -> str:
    kind = "INFO"
    if re.match(r"^REQ", item_id, re.IGNORECASE):
        kind = "REQUEST"
    elif re.match(r"^BCAST", item_id, re.IGNORECASE):
        kind = "BROADCAST"
    elif re.match(r"^SYNC", item_id, re.IGNORECASE):
        kind = "SYNC"
    elif re.match(r"^ORD", item_id, re.IGNORECASE):
        kind = "ORDER"
    elif re.match(r"^INFO", item_id, re.IGNORECASE):
        kind = "INFO"
    if status == "CONFLICT":
        kind = "CONFLICT"
    return kind


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r cross-project INBOX scanner (Python port of g-hk-wpac-inbox-check.ps1)"
    )
    parser.add_argument(
        "-ProjectRoot", "--project-root", dest="project_root", default=os.getcwd()
    )
    parser.add_argument(
        "-BlockOnConflict",
        "--block-on-conflict",
        dest="block_on_conflict",
        action="store_true",
    )
    parser.add_argument("-Quiet", "--quiet", dest="quiet", action="store_true")
    parser.add_argument(
        "-ConflictExitCode",
        "--conflict-exit-code",
        dest="conflict_exit_code",
        type=int,
        default=2,
    )
    parser.add_argument(
        "-NoAutoAction", "--no-auto-action", dest="no_auto_action", action="store_true"
    )
    # --- Message-folder system (T428) ---
    parser.add_argument("-Migrate", "--migrate", dest="migrate", action="store_true")
    parser.add_argument("-Archive", "--archive", dest="archive", action="store_true")
    parser.add_argument(
        "-ThresholdDays",
        "--threshold-days",
        dest="threshold_days",
        type=int,
        default=30,
    )
    args, _ = parser.parse_known_args(argv)

    project_root = Path(args.project_root)
    inbox_path = project_root / ".gald3r" / "linking" / "INBOX.md"
    logs_dir = project_root / ".gald3r" / "logs"
    auto_log = logs_dir / "wpac_auto_actions.log"
    msg_dir = project_root / ".gald3r" / "linking" / "messages"

    def emit(message: str) -> None:
        if not args.quiet:
            print(message)

    def write_auto_log(item_id: str, action: str) -> None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        # NOTE: local time with a literal 'Z' suffix - replicates the .ps1 stamp.
        stamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(auto_log, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} | {item_id} | {action}\n")

    # --- Message-folder system (T428) -----------------------------------------
    # INBOX.md is evolving into a lightweight INDEX backed by per-message files
    # under .gald3r/linking/messages/ (+ archive/). The migration + archive logic
    # lives in the shared script gald3r_wpac_inbox.py. -Migrate / --migrate and
    # -Archive / --archive delegate to it and return; the default scanner path
    # below is unchanged for backward-compat and also silently initializes
    # messages/ when absent (T428 AC#8).
    inbox_script = project_root / ".gald3r_sys" / "scripts" / "gald3r_wpac_inbox.py"
    if args.migrate or args.archive:
        if inbox_script.exists():
            if args.archive:
                cmd = [
                    sys.executable,
                    str(inbox_script),
                    "-Archive",
                    "-ThresholdDays",
                    str(args.threshold_days),
                    "-ProjectRoot",
                    str(project_root),
                ]
            else:
                cmd = [
                    sys.executable,
                    str(inbox_script),
                    "-Migrate",
                    "-ProjectRoot",
                    str(project_root),
                ]
            if args.quiet:
                cmd.append("-Quiet")
            try:
                subprocess.run(cmd)
            except OSError:
                pass
        elif not args.quiet:
            emit(
                "WPAC inbox: migration script not found at .gald3r_sys/scripts/gald3r_wpac_inbox.py"
            )
        return 0

    # Backward-compat: ensure messages/ exists so file-per-message writers never
    # fail.
    msg_dir.mkdir(parents=True, exist_ok=True)

    # Graceful: linking/ not configured.
    if not inbox_path.exists():
        emit("INBOX: not configured")
        return 0

    try:
        raw_lines = inbox_path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        raw_lines = []

    if not raw_lines:
        emit("INBOX: clear")
        return 0

    # --- Parse INBOX.md into items ---
    items = []
    current = None
    in_conflict_section = False

    # --- Index format (T428) --------------------------------------------------
    # When INBOX.md is the new index table (marked WPAC-INDEX-V1), parse the
    # table rows into the same item shape the legacy parser produces, so the
    # conflict gate, summary, and auto-action logic below all work unchanged.
    is_index_format = bool(
        re.search(r"<!--\s*WPAC-INDEX-V1\s*-->", "\n".join(raw_lines))
    )
    if is_index_format:
        for line in raw_lines:
            if not line.startswith("|"):
                continue
            if re.match(r"^\|\s*Status\s*\|", line):
                continue  # header row
            if re.match(r"^\|[\s\-:]+\|[\s\-:]+\|", line):
                continue  # separator row
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 7:
                continue
            row_status = re.sub(r"[\[\]]", "", cells[0]).strip().upper()
            row_kind = cells[2].strip().upper()
            if not row_kind:
                row_kind = "INFO"
            row_date = datetime.now()
            age_cell = cells[5].strip()
            am = re.match(r"^(\d+)d$", age_cell)
            if am:
                row_date = datetime.now() - timedelta(days=int(am.group(1)))
            else:
                ah = re.match(r"^(\d+)h$", age_cell)
                if ah:
                    row_date = datetime.now() - timedelta(hours=int(ah.group(1)))
            # Map index Status to the legacy OPEN/DONE/CONFLICT vocabulary.
            if row_status in ("DONE", "RESOLVED"):
                mapped_status = "DONE"
            elif row_status == "CONFLICT":
                mapped_status = "CONFLICT"
            else:
                mapped_status = "OPEN"
            items.append(
                {
                    "status": mapped_status,
                    "id": cells[1].strip(),
                    "source": cells[3].strip(),
                    "date": row_date,
                    "kind": row_kind,
                    "subject": cells[4].strip(),
                    "body": [],
                }
            )

    # --- Parse INBOX.md into items (legacy flat format) -----------------------
    # Items use one of two heading styles:
    #   "## [OPEN] REQ-NNN - from: <proj> - YYYY-MM-DD"  (per-item, all kinds)
    #   "## [CONFLICT]"                                   (section header - checkbox items follow)
    if not is_index_format:
        for line in raw_lines:
            # Section-style CONFLICT header.
            if CONFLICT_SECTION.match(line):
                if current is not None:
                    items.append(current)
                current = None
                in_conflict_section = True
                continue

            # Per-item heading (any kind).
            m = ITEM_HEADING.match(line)
            if m:
                if current is not None:
                    items.append(current)
                status = m.group(1).upper()
                item_id = m.group(2).strip()
                src = m.group(3).strip()
                try:
                    date = datetime.strptime(m.group(4), "%Y-%m-%d")
                except ValueError:
                    date = datetime.now()

                current = {
                    "status": status,
                    "id": item_id,
                    "source": src,
                    "date": date,
                    "kind": kind_for(item_id, status),
                    "subject": "",
                    "body": [],
                }
                in_conflict_section = False
                continue

            # CONFLICT-section checkbox items: "- [ ] subject"
            if in_conflict_section:
                cm = CHECKBOX_ITEM.match(line)
                if cm:
                    items.append(
                        {
                            "status": "CONFLICT",
                            "id": "CFL-" + format(len(items) + 1, "03d"),
                            "source": "(section)",
                            "date": datetime.now(),
                            "kind": "CONFLICT",
                            "subject": cm.group(1).strip(),
                            "body": [],
                        }
                    )
                    continue

            if current is not None:
                sm = SUBJECT_LINE.match(line)
                if sm and not current["subject"]:
                    current["subject"] = sm.group(1).strip()
                current["body"].append(line)
        if current is not None:
            items.append(current)

    # --- Counts ---
    open_conflicts = [i for i in items if i["kind"] == "CONFLICT" and i["status"] != "DONE"]
    open_requests = [i for i in items if i["kind"] == "REQUEST" and i["status"] == "OPEN"]
    open_broadcasts = [i for i in items if i["kind"] == "BROADCAST" and i["status"] == "OPEN"]
    open_orders = [i for i in items if i["kind"] == "ORDER" and i["status"] == "OPEN"]
    open_syncs = [i for i in items if i["kind"] == "SYNC" and i["status"] == "OPEN"]
    open_infos = [i for i in items if i["kind"] == "INFO" and i["status"] == "OPEN"]

    total_conflicts = len(open_conflicts)
    total = (
        total_conflicts
        + len(open_requests)
        + len(open_broadcasts)
        + len(open_orders)
        + len(open_syncs)
        + len(open_infos)
    )

    if total == 0:
        emit("INBOX: clear")
        return 0

    # --- Conflict gate (preserves existing g-rl-25 Step 6 behavior) ---
    if total_conflicts > 0:
        emit("")
        emit(f"INBOX CONFLICT GATE - {total_conflicts} CONFLICT item(s) detected")
        emit(
            "   Conflicts MUST be resolved via @g-wpac-read before task claiming, implementation, verification, or planning continues."
        )
        emit("   File: .gald3r/linking/INBOX.md")
        sorted_conflicts = sorted(open_conflicts, key=lambda i: i["date"])
        for c in sorted_conflicts[:10]:
            age = format_age(c["date"])
            subj = c["subject"] if c["subject"] else "(no subject)"
            emit("   - " + c["id"] + " from " + c["source"] + ": " + subj + " (" + age + ")")
        if len(open_conflicts) > 10:
            emit("   +" + str(len(open_conflicts) - 10) + " more")
        emit("")
        if args.block_on_conflict:
            return args.conflict_exit_code
        return 0

    # --- Per-item summary (T168) ---
    def emit_group(label: str, emoji: str, group: list) -> None:
        if not group:
            return
        emit("")
        emit(f"{emoji} {label} ({len(group)})")
        for it in sorted(group, key=lambda i: i["date"])[:10]:  # oldest first
            age = format_age(it["date"])
            subj = it["subject"] if it["subject"] else "(no subject)"
            emit("   - " + it["id"] + " from " + it["source"] + ": " + subj + " (" + age + ")")
        if len(group) > 10:
            emit(
                "   +"
                + str(len(group) - 10)
                + " more - run @g-wpac-read --all to see them all"
            )

    emit("INBOX: " + str(total) + " open")
    emit_group("ORDERS (parent - explicit acceptance required)", "ORD", open_orders)
    emit_group("REQUESTS (child - explicit decision required)", "REQ", open_requests)
    emit_group("BROADCASTS (parent - explicit ack required)", "BCT", open_broadcasts)
    emit_group("SYNCS (sibling - auto-marked-read)", "SYN", open_syncs)
    emit_group("INFO (auto-marked-read)", "INF", open_infos)

    # --- Auto-action policy (T168) ---
    # INFO + SYNC items are auto-marked-read. ORDERS / REQUESTS / BROADCASTS /
    # CONFLICTS are surface-only.
    if args.no_auto_action:
        emit("")
        emit(
            "Auto-action: skipped (-NoAutoAction); ORDERS/REQUESTS/BROADCASTS still need @g-wpac-read."
        )
        return 0

    auto_ids = {it["id"] for it in open_infos} | {it["id"] for it in open_syncs}
    auto_actioned = 0

    if is_index_format:
        # --- Index-format auto-action (T428) ---
        # Rewrite the table row status cell [OPEN] -> [DONE] for INFO/SYNC items
        # and update the backing message file's status:/actioned_at: frontmatter.
        stamp = datetime.now().strftime("%Y-%m-%d")
        if auto_ids:
            new_lines = []
            for line in raw_lines:
                out = line
                if line.startswith("|"):
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if len(cells) >= 7:
                        row_id = cells[1].strip()
                        row_status = re.sub(r"[\[\]]", "", cells[0]).strip().upper()
                        if row_status == "OPEN" and row_id in auto_ids:
                            out = line.replace("[OPEN]", "[DONE]")
                            # Update the message file frontmatter, if reachable.
                            file_name = ""
                            fm = re.search(r"\(messages/([^)]+)\)", cells[6])
                            if fm:
                                file_name = fm.group(1)
                            if file_name:
                                mp = msg_dir / file_name
                                if mp.exists():
                                    try:
                                        mc = mp.read_text(encoding="utf-8-sig")
                                        mc = re.sub(
                                            r"(?m)^status:\s*.*$", "status: done", mc
                                        )
                                        mc = re.sub(
                                            r"(?m)^actioned_at:\s*.*$",
                                            "actioned_at: '" + stamp + "'",
                                            mc,
                                        )
                                        with open(
                                            mp, "w", encoding="utf-8", newline=""
                                        ) as fh:
                                            fh.write(mc)
                                    except OSError:
                                        pass
                            write_auto_log(row_id, "auto-mark-read")
                            auto_actioned += 1
                new_lines.append(out)
            if auto_actioned > 0:
                # UTF-8 (no BOM), LF-joined with a trailing LF (mirrors the .ps1
                # [System.IO.File]::WriteAllText index rewrite).
                with open(inbox_path, "w", encoding="utf-8", newline="") as fh:
                    fh.write("\n".join(new_lines) + "\n")

        # Archive prompt: too many [DONE] rows in the active index (T428 AC#9,
        # default threshold 50).
        active_rows = [i for i in items if i["status"] == "DONE"]
        if len(active_rows) > 50:
            emit("")
            emit(
                "INBOX: "
                + str(len(active_rows))
                + " [DONE] rows in the active index (> 50). Run @g-wpac-archive-inbox to archive stale items."
            )
    elif auto_ids:
        # Rewrite [OPEN] -> [DONE] for auto-actioned items and stamp them.
        new_lines = []
        has_recently_actioned = False
        stamp = datetime.now().strftime("%Y-%m-%d")
        i = 0
        while i < len(raw_lines):
            line = raw_lines[i]
            hm = re.match(r"^## \[OPEN\]\s+(\S+)\s*(.*)$", line, re.IGNORECASE)
            if hm:
                hdr_id = hm.group(1).strip()
                if hdr_id in auto_ids:
                    new_lines.append(
                        re.sub(r"^## \[OPEN\]", "## [DONE]", line, flags=re.IGNORECASE)
                    )
                    i += 1
                    new_lines.append(f"**Auto-actioned:** {stamp} by g-hk-wpac-inbox-check")
                    write_auto_log(hdr_id, "auto-mark-read")
                    auto_actioned += 1
                    continue
            if re.match(r"^## Recently Actioned", line, re.IGNORECASE):
                has_recently_actioned = True
            new_lines.append(line)
            i += 1

        if not has_recently_actioned and auto_actioned > 0:
            new_lines.append("")
            new_lines.append("## Recently Actioned")
            new_lines.append("")
            new_lines.append(
                "Auto-actioned items (INFO + SYNC) are stamped above with **Auto-actioned:** YYYY-MM-DD. Audit log: .gald3r/logs/wpac_auto_actions.log"
            )

        if auto_actioned > 0:
            # UTF-8 (no BOM) with the platform newline - mirrors pwsh Set-Content.
            with open(inbox_path, "w", encoding="utf-8", newline="") as fh:
                for ln in new_lines:
                    fh.write(ln + os.linesep)

    if auto_actioned > 0:
        emit("")
        emit(
            "Auto-actioned: "
            + str(auto_actioned)
            + " item(s) (INFO + SYNC); audit log: .gald3r/logs/wpac_auto_actions.log"
        )

    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:
        # Never crash the host session on unexpected errors. The deliberate
        # -BlockOnConflict exit path above uses sys.exit (SystemExit) and is
        # NOT swallowed here - blocking is that path's documented purpose.
        sys.exit(0)
