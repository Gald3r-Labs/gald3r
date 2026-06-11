#!/usr/bin/env python3
"""Python port of invoke_triage.ps1 (T1585).

Auto-Triage L0 runner -- assess risk, attempt fix if safe, log outcome.
Phase 1 (cautious). Only fixes bounded, low-risk spec/schema defects.

Preserves the exact PS1 argument interface (rules reference it):
    invoke_triage.py -BugId "BUG-098" -Kind spec_defect -Files <p1> <p2>
        -FixType schema_comment -FixContent "<text>" -ProjectRoot <root>
        [-TargetLine N] [-DryRun] [-BugFilePath <bug.md>]

Outcome is printed as a JSON object on the final line (the PS1 returned a
PSCustomObject); exit code is 0 in all outcome paths, matching the PS1.
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from calculate_risk import (  # noqa: E402  (sibling import after sys.path bootstrap)
    VALID_FIX_TYPES,
    VALID_KINDS,
    calculate_risk,
)


def _timestamp() -> str:
    """Local time with literal 'Z' suffix, mirroring the PS1 format string."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


class TriageContext:
    """Carries the per-run state shared by audit logging and frontmatter updates."""

    def __init__(self, bug_id: str, kind: str, fix_type: str,
                 project_root: str, dry_run: bool) -> None:
        self.bug_id = bug_id
        self.kind = kind
        self.fix_type = fix_type
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.timestamp = _timestamp()
        date_stamp = datetime.now().strftime("%Y%m%d")
        self.audit_log = self.project_root / ".gald3r" / "logs" / f"triage_auto_{date_stamp}.log"

    def write_audit_log(self, msg: str) -> None:
        """Append one audit row (or print it with [DRY-RUN] when dry-running)."""
        line = f"{self.timestamp} | {self.bug_id} | {self.kind} | fix={self.fix_type} | {msg}"
        if self.dry_run:
            print(f"[DRY-RUN] AUDIT: {line}")
        else:
            self.audit_log.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            print(f"AUDIT: {line}")

    def update_bug_frontmatter(self, bug_file: str, triage_status: str,
                               risk_score: float, triage_note: str) -> None:
        """Add or update triage fields in the bug file's YAML frontmatter."""
        path = Path(bug_file)
        if not path.is_file():
            print(f"WARNING: Bug file not found, skipping frontmatter update: {bug_file}")
            return

        content = path.read_text(encoding="utf-8", errors="replace")
        ts = _timestamp()

        fields_to_set = {
            "triage_status": triage_status,
            "triage_risk_score": str(risk_score),
            "triage_attempted": f"'{ts}'",
            "triage_notes": f"'{triage_note}'",
            "kind": self.kind,
        }

        for key, val in fields_to_set.items():
            # NB: replacement is passed as a callable so backslashes in val
            # (Windows paths in triage_notes) are not parsed as regex escapes.
            replacement = f"{key}: {val}"
            if re.search(rf"(?m)^{re.escape(key)}:", content):
                # Update existing field
                content = re.sub(rf"(?m)^{re.escape(key)}:.*$",
                                 lambda m, r=replacement: r, content)
            else:
                # Insert after the OPENING --- only (the PS1 -replace hit every
                # fence line; first-occurrence is the intended behavior).
                content = re.sub(r"(?m)^---\r?\n",
                                 lambda m, r=replacement: f"---\n{r}\n",
                                 content, count=1)

        if self.dry_run:
            print(f"[DRY-RUN] Would update frontmatter in: {bug_file}")
            print(f"[DRY-RUN] triage_status={triage_status} risk={risk_score}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"Updated frontmatter: {bug_file}")


def _insert_after_line(file_content: str, fix_content: str, target_line: int) -> str:
    """Insert fix_content after 1-based target_line; append at EOF when out of range."""
    if target_line > 0:
        lines = file_content.split("\n")
        if target_line <= len(lines):
            before = "\n".join(lines[:target_line])
            after = "\n".join(lines[target_line:])
            return before + "\n" + fix_content + "\n" + after
    return file_content.rstrip() + "\n" + fix_content + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_fix(ctx: TriageContext, files: Sequence[str], fix_type: str,
              fix_content: str, target_line: int) -> List[str]:
    """Apply the gated fix to each file; return the list of changed files."""
    applied_changes: List[str] = []

    for file_str in files:
        path = Path(file_str)
        if not path.is_file():
            print(f"[{ctx.bug_id}] WARNING: File not found, skipping: {file_str}")
            continue

        file_content = path.read_text(encoding="utf-8", errors="replace")
        original_hash = _sha256(path)

        if fix_type in ("schema_comment", "manifest_annotation",
                        "command_annotation", "rule_annotation"):
            # Append/insert the annotation after a specific line or at end of file.
            new_content = _insert_after_line(file_content, fix_content, target_line)
        elif fix_type == "constraint_expire":
            # Change status: active -> archived for clearly expired constraints.
            # Safety: only status fields with explicit expiry markers already met.
            new_content = re.sub(r"(?m)^(\s*status:\s*)active(\s*#.*expiry.*met)",
                                 r"\1archived\2", file_content)
            if new_content == file_content:
                print(f"[{ctx.bug_id}] WARNING: constraint_expire found no eligible "
                      f"'status: active # expiry met' pattern in {file_str}")
                continue
        else:  # defensive -- argparse choices already gate this
            print(f"[{ctx.bug_id}] WARNING: unknown fix_type '{fix_type}', skipping: {file_str}")
            continue

        if ctx.dry_run:
            print(f"[DRY-RUN] Would write to: {file_str}")
            print("[DRY-RUN] Content preview (first 200 chars of change):")
            print(fix_content[:200])
        else:
            path.write_text(new_content, encoding="utf-8")
            new_hash = _sha256(path)
            if new_hash == original_hash:
                print(f"[{ctx.bug_id}] WARNING: File hash unchanged after write "
                      f"-- fix may be a no-op: {file_str}")
            else:
                print(f"[{ctx.bug_id}] Written: {file_str}")
                applied_changes.append(file_str)

    return applied_changes


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Auto-Triage L0 runner -- assess risk, attempt fix if safe, log outcome."
    )
    p.add_argument("-BugId", "--bug-id", dest="bug_id", required=True,
                   help='e.g. "BUG-098"')
    p.add_argument("-Kind", "--kind", dest="kind", required=True, choices=VALID_KINDS)
    p.add_argument("-Files", "--files", dest="files", required=True, nargs="+",
                   help="Absolute paths to files the fix would touch.")
    p.add_argument("-FixType", "--fix-type", dest="fix_type", required=True,
                   choices=VALID_FIX_TYPES)
    p.add_argument("-FixContent", "--fix-content", dest="fix_content", default="")
    p.add_argument("-TargetLine", "--target-line", dest="target_line", type=int, default=-1,
                   help="1-based line number to insert the annotation AFTER; omit to append.")
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", required=True)
    p.add_argument("-DryRun", "--dry-run", dest="dry_run", action="store_true")
    p.add_argument("-BugFilePath", "--bug-file-path", dest="bug_file_path", default="")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the triage loop: assess -> gate -> fix-if-safe -> log."""
    args = build_parser().parse_args(argv)
    ctx = TriageContext(args.bug_id, args.kind, args.fix_type,
                        args.project_root, args.dry_run)

    # --- Step 1: Run risk assessment ---
    print(f"[{args.bug_id}] Assessing risk for kind={args.kind} "
          f"fixType={args.fix_type} files=[{', '.join(args.files)}]")

    assessment = calculate_risk(
        kind=args.kind, files=args.files, fix_type=args.fix_type,
        project_root=args.project_root,
    )

    print(f"[{args.bug_id}] Risk score: {assessment['risk_score']} "
          f"| Eligible: {assessment['eligible']}")
    print(f"[{args.bug_id}] Reason: {assessment['reason']}")

    def emit(outcome: Dict[str, object]) -> int:
        print(json.dumps(outcome))
        return 0

    # --- Step 2: Gate check ---
    if not assessment["eligible"]:
        status = "blocked_by_risk" if float(assessment["risk_score"]) >= 99.0 else "needs_attention"
        ctx.write_audit_log(f"risk={assessment['risk_score']} | {status} | {assessment['reason']}")
        if args.bug_file_path:
            ctx.update_bug_frontmatter(args.bug_file_path, status,
                                       float(assessment["risk_score"]),
                                       str(assessment["reason"]))
        print(f"[{args.bug_id}] Outcome: {status} -- no changes made")
        return emit({"outcome": status, "risk_score": assessment["risk_score"], "changes": []})

    # --- Step 3: Validate fix content ---
    if args.fix_content == "" and args.fix_type != "constraint_expire":
        print(f"[{args.bug_id}] ERROR: FixContent is required for fix_type={args.fix_type}")
        ctx.write_audit_log(f"risk={assessment['risk_score']} | error | FixContent empty, aborting")
        return emit({"outcome": "error", "risk_score": assessment["risk_score"], "changes": []})

    # --- Step 4: Apply fix ---
    applied_changes = apply_fix(ctx, args.files, args.fix_type,
                                args.fix_content, args.target_line)

    # --- Step 5: Log and update bug frontmatter ---
    outcome = "auto_resolved" if (applied_changes or args.dry_run) else "needs_attention"
    note_str = f"Applied {args.fix_type} to: {', '.join(args.files)}"

    ctx.write_audit_log(f"risk={assessment['risk_score']} | {outcome} | {note_str}")

    if args.bug_file_path:
        ctx.update_bug_frontmatter(args.bug_file_path, outcome,
                                   float(assessment["risk_score"]), note_str)

    print(f"[{args.bug_id}] Outcome: {outcome} | Changes: {len(applied_changes)} file(s)")

    return emit({
        "outcome": outcome,
        "risk_score": assessment["risk_score"],
        "changes": applied_changes,
        "dry_run": args.dry_run,
    })


if __name__ == "__main__":
    raise SystemExit(main())
