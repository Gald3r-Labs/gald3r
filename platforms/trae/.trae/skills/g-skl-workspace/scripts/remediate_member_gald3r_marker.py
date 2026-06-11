#!/usr/bin/env python3
"""Python port of remediate_member_gald3r_marker.ps1 (T1585).

Remediate an existing Workspace-Control member repository's ``.gald3r/``
folder so it conforms to the marker-only invariant
(BUG-021 / Task 213 / g-rl-36).

Default mode is dry-run: scans ``.gald3r/`` content and categorises each
entry as marker-safe (``.identity``, ``PROJECT.md``) or forbidden control
plane. Reports planned actions without touching the filesystem.

With -Apply: moves forbidden entries to a quarantine folder
(``<member_root>/.gald3r-quarantine/<timestamp>/``) by default, or to the
explicit -BackupTo path. Marker entries are preserved in place. Nothing
is permanently deleted.

Cross-script call: imports the sibling check_member_repo_gald3r_guard.py and
calls run_guard() in-process (the PS1 spawned it as a subprocess and parsed
its JSON). Engine ``gald3r.utils`` is intentionally not used: output text and
JSON keys are parity-locked to the PS1.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MARKER_ALLOWLIST: Tuple[str, ...] = ('.identity', 'PROJECT.md')


def _import_guard() -> Optional[Any]:
    """Import the sibling guard module (sys.path-insert of the script dir)."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    sys.dont_write_bytecode = True
    try:
        import check_member_repo_gald3r_guard as guard
        return guard
    except ImportError:
        return None


def convert_to_normal_path(input_path: str) -> str:
    """Resolve `input_path` if it exists, normalize to forward slashes, trim '/'."""
    if not input_path:
        return ''
    resolved = input_path
    try:
        if os.path.exists(input_path):
            resolved = str(Path(input_path).resolve())
    except OSError:
        resolved = input_path
    return resolved.replace('\\', '/').rstrip('/')


def write_remediate_result(result: Dict[str, Any], as_json: bool) -> None:
    """Emit a remediation result: JSON (PascalCase keys) or PS1-parity text."""
    if as_json:
        print(json.dumps(result, indent=2))
        return
    status_token = str(result.get('Status', '')).upper()
    print(f"[{status_token}] member-marker remediate: {result.get('Reason', '')}")
    if result.get('Message'):
        print(f"  {result['Message']}")
    if result.get('MemberPath'):
        print(f"  member_path     : {result['MemberPath']}")
    if result.get('MatchedRepoId'):
        print(f"  matched_repo_id : {result['MatchedRepoId']}")
    if result.get('QuarantineDir'):
        print(f"  quarantine_dir  : {result['QuarantineDir']}")
    if result.get('MarkerPreserved'):
        print('  preserved (marker):')
        for p in result['MarkerPreserved']:
            print(f'    - {p}')
    if result.get('Forbidden'):
        print('  forbidden (control plane):')
        for p in result['Forbidden']:
            print(f'    - {p}')
    if result.get('Actions'):
        print('  planned actions:')
        for a in result['Actions']:
            print(f'    - {a}')


def build_parser() -> argparse.ArgumentParser:
    """argparse surface mirroring the PS1 param() block (both spellings)."""
    parser = argparse.ArgumentParser(
        description='Remediate a member .gald3r/ to the marker-only invariant (g-rl-36).',
        allow_abbrev=False)
    parser.add_argument('member_path_pos', nargs='?', default=None,
                        metavar='MemberPath',
                        help='Member repository path (positional form).')
    parser.add_argument('-MemberPath', '--member-path', dest='member_path',
                        default=None, help='Member repository path.')
    parser.add_argument('-BackupTo', '--backup-to', dest='backup_to',
                        default='', help='Explicit quarantine destination path.')
    parser.add_argument('-ManifestPath', '--manifest-path', dest='manifest_path',
                        default='', help='Explicit workspace manifest path.')
    parser.add_argument('-Apply', '--apply', dest='apply', action='store_true',
                        help='Quarantine forbidden entries (default is dry-run).')
    parser.add_argument('-Json', '--json', dest='json', action='store_true',
                        help='Emit JSON instead of text.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point — mirrors the PS1 main flow and exit codes (0/2)."""
    args = build_parser().parse_args(argv)
    member_path = args.member_path or args.member_path_pos or ''
    as_json: bool = args.json
    if not member_path:
        build_parser().error('the following arguments are required: MemberPath')

    if not os.path.exists(member_path):
        write_remediate_result({
            'Status': 'error',
            'Reason': 'member_path_not_found',
            'Message': f'Member path does not exist: {member_path}',
            'MemberPath': member_path,
        }, as_json)
        return 2

    normal_member = convert_to_normal_path(member_path)

    guard = _import_guard()
    if guard is None:
        write_remediate_result({
            'Status': 'error',
            'Reason': 'guard_helper_missing',
            'Message': ('Companion guard helper not found at '
                        f"{Path(__file__).resolve().parent / 'check_member_repo_gald3r_guard.py'}"),
            'MemberPath': normal_member,
        }, as_json)
        return 2

    try:
        guard_result, _guard_code = guard.run_guard(
            target_path=member_path,
            allow_marker_init=True,
            manifest_path=args.manifest_path or '')
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        write_remediate_result({
            'Status': 'error',
            'Reason': 'guard_parse_failed',
            'Message': f'Could not parse guard output: {exc}',
            'MemberPath': normal_member,
        }, as_json)
        return 2

    matched_role = guard_result.get('MatchedRole')
    if matched_role not in ('controlled_member', 'migration_source'):
        write_remediate_result({
            'Status': 'error',
            'Reason': 'not_a_member_repository',
            'Message': ('Target is not a Workspace-Control controlled_member or '
                        'migration_source. Remediation only applies to member repositories. '
                        f"Guard reason: {guard_result.get('Reason', '')}"),
            'MemberPath': normal_member,
        }, as_json)
        return 2

    matched_id = guard_result.get('MatchedRepoId')
    dot_gald3r = os.path.join(member_path, '.gald3r')

    if not os.path.exists(dot_gald3r):
        write_remediate_result({
            'Status': 'clean',
            'Reason': 'no_dot_gald3r',
            'Message': f'Member {matched_id} has no .gald3r/ directory. Nothing to remediate.',
            'MemberPath': normal_member,
            'MatchedRepoId': matched_id,
            'MarkerPreserved': [],
            'Forbidden': [],
            'Actions': [],
        }, as_json)
        return 0

    marker_preserved: List[str] = []
    forbidden: List[str] = []
    allow_cf = {a.casefold() for a in MARKER_ALLOWLIST}
    try:
        entries = sorted(Path(dot_gald3r).iterdir())
    except OSError:
        entries = []
    for entry in entries:
        if entry.name.casefold() in allow_cf:
            marker_preserved.append(entry.name)
        else:
            forbidden.append(entry.name)

    if not forbidden:
        write_remediate_result({
            'Status': 'clean',
            'Reason': 'already_marker_only',
            'Message': (f'Member {matched_id} .gald3r/ is already marker-only. '
                        'No remediation needed.'),
            'MemberPath': normal_member,
            'MatchedRepoId': matched_id,
            'MarkerPreserved': marker_preserved,
            'Forbidden': [],
            'Actions': [],
        }, as_json)
        return 0

    if args.backup_to:
        quarantine_dir = args.backup_to
    else:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        quarantine_dir = os.path.join(member_path, '.gald3r-quarantine', timestamp)

    actions: List[str] = []
    for entry in forbidden:
        dst = os.path.join(quarantine_dir, entry)
        actions.append(f'move: .gald3r/{entry} -> {dst}')
    for entry in marker_preserved:
        actions.append(f'preserve: .gald3r/{entry}')

    if not args.apply:
        write_remediate_result({
            'Status': 'plan',
            'Reason': 'dry_run',
            'Message': (f'Dry-run: {len(forbidden)} forbidden entries would be quarantined '
                        f'to {quarantine_dir}. Pass -Apply to execute.'),
            'MemberPath': normal_member,
            'MatchedRepoId': matched_id,
            'QuarantineDir': quarantine_dir,
            'MarkerPreserved': marker_preserved,
            'Forbidden': forbidden,
            'Actions': actions,
        }, as_json)
        return 0

    if not os.path.exists(quarantine_dir):
        os.makedirs(quarantine_dir, exist_ok=True)

    moved_actions: List[str] = []
    for entry in forbidden:
        src = os.path.join(dot_gald3r, entry)
        dst = os.path.join(quarantine_dir, entry)
        shutil.move(src, dst)
        moved_actions.append(f'moved: .gald3r/{entry} -> {dst}')
    for entry in marker_preserved:
        moved_actions.append(f'preserved: .gald3r/{entry}')

    write_remediate_result({
        'Status': 'applied',
        'Reason': 'remediation_complete',
        'Message': (f'Quarantined {len(forbidden)} forbidden entries from member '
                    f'{matched_id} .gald3r/. Marker preserved. Review and delete the '
                    'quarantine folder when no longer needed.'),
        'MemberPath': normal_member,
        'MatchedRepoId': matched_id,
        'QuarantineDir': quarantine_dir,
        'MarkerPreserved': marker_preserved,
        'Forbidden': forbidden,
        'Actions': moved_actions,
    }, as_json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
