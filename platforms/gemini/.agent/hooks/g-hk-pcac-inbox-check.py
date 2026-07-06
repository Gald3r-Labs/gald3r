#!/usr/bin/env python3
"""Python port of g-hk-pcac-inbox-check.ps1 (T1601, PS1-KILL epic T667).

Cross-project INBOX scanner (T168 rewrite). Safe to call at session start,
before command work, during swarm heartbeats, and at final summaries. Reads
.gald3r/linking/INBOX.md, surfaces a per-item one-line summary grouped by
type, and auto-actions LOW-RISK item types only.

Auto-action policy (T168):
  [INFO]      -> auto-mark-read (low risk, no action required).
  [SYNC]      -> auto-mark-read (peer snapshot copy is left to @g-pcac-read).
  [BROADCAST] -> surface only; user must @g-pcac-read --ack <id>.
  [REQUEST]   -> surface only; user must @g-pcac-read --accept|--decline <id>.
  [ORDER]     -> surface only; user must @g-pcac-read --accept <id>; blocking.
  [CONFLICT]  -> preserve existing g-rl-25 behavior (warning + session gate).

With -BlockOnConflict, exits with ConflictExitCode when open CONFLICT items
exist. Idempotent: auto-actioned items become [DONE]; re-runs are no-ops.
Every auto-action is audited to .gald3r/logs/pcac_auto_actions.log.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

_EM = "—"
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
        return f"{int(hours)}h ago"
    return f"{int(hours / 24.0)}d ago"


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
        description="gald3r cross-project INBOX scanner (Python port of "
                    "g-hk-pcac-inbox-check.ps1)"
    )
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=os.getcwd())
    parser.add_argument("-BlockOnConflict", "--block-on-conflict",
                        dest="block_on_conflict", action="store_true")
    parser.add_argument("-Quiet", "--quiet", dest="quiet", action="store_true")
    parser.add_argument("-ConflictExitCode", "--conflict-exit-code",
                        dest="conflict_exit_code", type=int, default=2)
    parser.add_argument("-NoAutoAction", "--no-auto-action",
                        dest="no_auto_action", action="store_true")
    args, _ = parser.parse_known_args(argv)

    project_root = Path(args.project_root)
    inbox_path = project_root / ".gald3r" / "linking" / "INBOX.md"
    logs_dir = project_root / ".gald3r" / "logs"
    auto_log = logs_dir / "pcac_auto_actions.log"

    def emit(message: str) -> None:
        if not args.quiet:
            print(message)

    def write_auto_log(item_id: str, action: str) -> None:
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(auto_log, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} | {item_id} | {action}\n")

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
    # Items use one of two heading styles:
    #   "## [OPEN] REQ-NNN - from: <proj> - YYYY-MM-DD"  (per-item, all kinds)
    #   "## [CONFLICT]"                                   (section header - checkbox items follow)
    items = []
    current = None
    in_conflict_section = False

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
                items.append({
                    "status": "CONFLICT",
                    "id": "CFL-" + format(len(items) + 1, "03d"),
                    "source": "(section)",
                    "date": datetime.now(),
                    "kind": "CONFLICT",
                    "subject": cm.group(1).strip(),
                    "body": [],
                })
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
    total = (total_conflicts + len(open_requests) + len(open_broadcasts)
             + len(open_orders) + len(open_syncs) + len(open_infos))

    if total == 0:
        emit("INBOX: clear")
        return 0

    # --- Conflict gate (preserves existing g-rl-25 Step 6 behavior) ---
    if total_conflicts > 0:
        emit("")
        emit(f"INBOX CONFLICT GATE - {total_conflicts} CONFLICT item(s) detected")
        emit("   Conflicts MUST be resolved via @g-pcac-read before task claiming, "
             "implementation, verification, or planning continues.")
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
            emit("   +" + str(len(group) - 10) + " more - run @g-pcac-read --all to see them all")

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
        emit("Auto-action: skipped (-NoAutoAction); ORDERS/REQUESTS/BROADCASTS "
             "still need @g-pcac-read.")
        return 0

    auto_ids = {it["id"] for it in open_infos} | {it["id"] for it in open_syncs}
    auto_actioned = 0

    if auto_ids:
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
                    new_lines.append(f"**Auto-actioned:** {stamp} by g-hk-pcac-inbox-check")
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
                "Auto-actioned items (INFO + SYNC) are stamped above with "
                "**Auto-actioned:** YYYY-MM-DD. Audit log: "
                ".gald3r/logs/pcac_auto_actions.log"
            )

        if auto_actioned > 0:
            # UTF-8 (no BOM) with the platform newline - mirrors pwsh Set-Content.
            with open(inbox_path, "w", encoding="utf-8", newline="") as fh:
                for ln in new_lines:
                    fh.write(ln + os.linesep)

    if auto_actioned > 0:
        emit("")
        emit("Auto-actioned: " + str(auto_actioned) + " item(s) (INFO + SYNC); "
             "audit log: .gald3r/logs/pcac_auto_actions.log")

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
