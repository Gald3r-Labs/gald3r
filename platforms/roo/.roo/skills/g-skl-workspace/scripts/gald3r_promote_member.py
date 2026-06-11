#!/usr/bin/env python3
"""Python port of gald3r_promote_member.ps1 (T1585).

Promote a Workspace-Control ``controlled_member`` repository to a fully
self-managed ``autonomous_child`` (BUG-097 / T1435 / g-rl-36).

A controlled_member is intentionally restricted to a marker-only ``.gald3r/``
(``.identity`` + ``PROJECT.md``). When a member needs to become independent,
the g-rl-36 guard must be lifted AND the standard framework files that
postdate the original member creation (RELEASES.md, releases/, vocab.md,
workspace/topology.md, workspace/inbox.md, FEATURES.md, BUGS.md, PLAN.md)
must be scaffolded. This helper performs that migration safely.

Default mode is dry-run: reports the plan (files that would be created,
.identity changes, manifest role change) without touching the filesystem.
With -Apply it backfills missing standard files, rewrites ``.identity``
(workspace_role=autonomous_child, member_gald3r_marker_only removed,
gald3r_version bumped to current), and updates the workspace manifest
workspace_role for the member.

Exit codes:
  0 - dry-run plan produced, apply succeeded, or member already autonomous (info)
  1 - block (guard refused, member has unexpected state, manifest unwritable)
  2 - input or manifest error

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
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Files / dirs that a fully-equipped autonomous_child should have but a
# marker-only member lacks. Enumerated from BUG-097 + g-rl-25 slim layout.
STANDARD_FILES: Tuple[str, ...] = ('RELEASES.md', 'vocab.md', 'FEATURES.md',
                                   'BUGS.md', 'PLAN.md')
STANDARD_DIRS: Tuple[str, ...] = ('releases', 'workspace')
WORKSPACE_FILES: Tuple[str, ...] = ('topology.md', 'inbox.md')


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


def convert_to_normal_path(path: str) -> str:
    """Resolve `path` if it exists, normalize to forward slashes, trim '/'."""
    if not path:
        return ''
    resolved = path
    try:
        if os.path.exists(path):
            resolved = str(Path(path).resolve())
    except OSError:
        resolved = path
    return resolved.replace('\\', '/').rstrip('/')


def read_identity_map(identity_file: str) -> Dict[str, str]:
    """Read a .identity file into an ordered key=value map."""
    id_map: Dict[str, str] = {}
    if not os.path.exists(identity_file):
        return id_map
    with open(identity_file, 'r', encoding='utf-8-sig', errors='replace') as fh:
        for line in fh.read().splitlines():
            m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$', line)
            if m:
                id_map[m.group(1)] = m.group(2).strip()
    return id_map


def get_current_framework_version(controller_root: str, override: str) -> str:
    """Resolve the target gald3r framework version string."""
    if override:
        return override
    # Prefer the controller-installed system VERSION file.
    script_dir = Path(__file__).resolve().parent
    candidates: List[str] = []
    if controller_root:
        candidates.append(os.path.join(controller_root, '.gald3r_sys', 'VERSION'))
    candidates.append(str(script_dir / '..' / '..' / '..' / 'VERSION'))
    for c in candidates:
        if c and os.path.exists(c):
            try:
                with open(c, 'r', encoding='utf-8-sig', errors='replace') as fh:
                    v = fh.read().strip()
            except OSError:
                continue
            if v:
                return v
    return ''


def write_result(result: Dict[str, Any], as_json: bool) -> None:
    """Emit a promote result: JSON (PascalCase keys) or PS1-parity text."""
    if as_json:
        print(json.dumps(result, indent=2))
        return
    status_token = str(result.get('Status', '')).upper()
    print(f"[{status_token}] member promote: {result.get('Reason', '')}")
    if result.get('Message'):
        print(f"  {result['Message']}")
    if result.get('MemberId'):
        print(f"  member_id        : {result['MemberId']}")
    if result.get('MemberPath'):
        print(f"  member_path      : {result['MemberPath']}")
    if result.get('ControllerPath'):
        print(f"  controller       : {result['ControllerPath']}")
    if result.get('FromRole'):
        print(f"  from_role        : {result['FromRole']}")
    if result.get('ToRole'):
        print(f"  to_role          : {result['ToRole']}")
    if result.get('Gald3rVersion'):
        print(f"  gald3r_version   : {result['Gald3rVersion']}")
    if result.get('ManifestUpdated'):
        print(f"  manifest_updated : {result['ManifestUpdated']}")
    if result.get('Actions'):
        print('  actions:')
        for a in result['Actions']:
            if a:
                print(f'    - {a}')


def build_parser() -> argparse.ArgumentParser:
    """argparse surface mirroring the PS1 param() block (both spellings)."""
    parser = argparse.ArgumentParser(
        description=('Promote a Workspace-Control controlled_member to a '
                     'self-managed autonomous_child (BUG-097 / g-rl-36).'),
        allow_abbrev=False)
    parser.add_argument('member_path_pos', nargs='?', default=None,
                        metavar='MemberPath',
                        help='Member repository path (positional form).')
    parser.add_argument('-MemberPath', '--member-path', dest='member_path',
                        default=None, help='Member repository path.')
    parser.add_argument('-MemberId', '--member-id', dest='member_id',
                        default='', help='Member id (auto-derived when omitted).')
    parser.add_argument('-ControllerPath', '--controller-path', dest='controller_path',
                        default='', help='Workspace controller root.')
    parser.add_argument('-ManifestPath', '--manifest-path', dest='manifest_path',
                        default='', help='Explicit workspace manifest path.')
    parser.add_argument('-Gald3rVersion', '--gald3r-version', dest='gald3r_version',
                        default='', help='Override the target gald3r_version value.')
    parser.add_argument('-Apply', '--apply', dest='apply', action='store_true',
                        help='Perform the promotion (default is dry-run).')
    parser.add_argument('-Json', '--json', dest='json', action='store_true',
                        help='Emit JSON instead of text.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point — mirrors the PS1 main flow and exit codes (0/1/2)."""
    args = build_parser().parse_args(argv)
    member_path = args.member_path or args.member_path_pos or ''
    member_id: str = args.member_id
    as_json: bool = args.json
    if not member_path:
        build_parser().error('the following arguments are required: MemberPath')

    if not os.path.exists(member_path):
        write_result({
            'Status': 'error',
            'Reason': 'member_path_not_found',
            'Message': f'Member path does not exist: {member_path}',
            'MemberPath': member_path,
        }, as_json)
        return 2

    normal_member = convert_to_normal_path(member_path)

    # Delegate membership classification to the shared guard helper.
    guard = _import_guard()
    if guard is None:
        write_result({
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
        write_result({
            'Status': 'error',
            'Reason': 'guard_parse_failed',
            'Message': f'Could not parse guard output: {exc}.',
            'MemberPath': normal_member,
        }, as_json)
        return 2

    # Read the member identity to learn its current role and controller wiring
    # authoritatively (independent of guard manifest discovery).
    dot_gald3r = os.path.join(member_path, '.gald3r')
    identity_file = os.path.join(dot_gald3r, '.identity')
    identity = read_identity_map(identity_file)
    identity_role = identity.get('workspace_role', '')

    matched_id = guard_result.get('MatchedRepoId')
    matched_role = guard_result.get('MatchedRole') or ''
    if not member_id and matched_id:
        member_id = matched_id
    if not member_id and 'project_name' in identity:
        member_id = identity['project_name']

    # Resolve the controller root: explicit flag > member identity wiring.
    controller_root = ''
    if args.controller_path:
        if os.path.exists(args.controller_path):
            controller_root = str(Path(args.controller_path).resolve())
    elif ('workspace_controller_path' in identity
          and os.path.exists(identity['workspace_controller_path'])):
        controller_root = str(Path(identity['workspace_controller_path']).resolve())

    # Resolve the manifest file to rewrite on apply. Priority:
    #   explicit -ManifestPath > guard-discovered manifest > controller-derived path.
    manifest_file = ''
    if args.manifest_path and os.path.exists(args.manifest_path):
        manifest_file = str(Path(args.manifest_path).resolve())
    elif guard_result.get('ManifestPath'):
        manifest_file = str(guard_result['ManifestPath'])
    elif controller_root:
        candidate = os.path.join(controller_root, '.gald3r', 'linking',
                                 'workspace_manifest.yaml')
        if os.path.exists(candidate):
            manifest_file = str(Path(candidate).resolve())

    # If the role was unknown from the guard, derive it from the manifest entry.
    if not matched_role and manifest_file and member_id:
        try:
            with open(manifest_file, 'r', encoding='utf-8-sig', newline='') as fh:
                mtext = fh.read()
        except OSError:
            mtext = ''
        mrx = re.search(
            r'^- id:\s*' + re.escape(member_id)
            + r'\s*\r?\n(?:^(?!- id:)[^\r\n]*\r?\n)*?^  workspace_role:\s*([A-Za-z_]+)',
            mtext, re.M | re.S)
        if mrx:
            matched_role = mrx.group(1)

    effective_role = matched_role if matched_role else (identity_role or '')

    # Already autonomous? Informational no-op.
    if effective_role == 'autonomous_child' or identity_role == 'autonomous_child':
        write_result({
            'Status': 'info',
            'Reason': 'already_autonomous_child',
            'Message': (f'Member {member_id} is already workspace_role=autonomous_child. '
                        'Nothing to promote. Run @g-skl-setup --upgrade-existing if files '
                        'are still missing.'),
            'MemberId': member_id,
            'MemberPath': normal_member,
            'FromRole': effective_role,
            'ToRole': 'autonomous_child',
        }, as_json)
        return 0

    # Only controlled_member / migration_source are promotable.
    if effective_role not in ('controlled_member', 'migration_source'):
        write_result({
            'Status': 'block',
            'Reason': 'not_a_promotable_member',
            'Message': (f"Target role '{effective_role}' is not promotable. PROMOTE only "
                        'migrates controlled_member or migration_source to autonomous_child. '
                        f"Guard reason: {guard_result.get('Reason', '')}."),
            'MemberId': member_id,
            'MemberPath': normal_member,
            'FromRole': effective_role,
        }, as_json)
        return 1

    # Backfill controller root from the manifest path when not yet resolved.
    if not controller_root and manifest_file:
        # manifest lives at <controller>/.gald3r/linking/workspace_manifest.yaml
        linking = os.path.dirname(manifest_file)
        gald3r_dir = os.path.dirname(linking)
        controller_root = os.path.dirname(gald3r_dir)

    target_version = get_current_framework_version(controller_root, args.gald3r_version)

    # Build the scaffold plan.
    actions: List[str] = []

    if not os.path.exists(dot_gald3r):
        actions.append('create dir: .gald3r/')

    for d in STANDARD_DIRS:
        dir_path = os.path.join(dot_gald3r, d)
        if not os.path.exists(dir_path):
            actions.append(f'create dir: .gald3r/{d}/')

    for f in STANDARD_FILES:
        file_path = os.path.join(dot_gald3r, f)
        if not os.path.exists(file_path):
            actions.append(f'create file: .gald3r/{f}')
        else:
            actions.append(f'preserve: .gald3r/{f} (already present)')

    for wf in WORKSPACE_FILES:
        wf_path = os.path.join(dot_gald3r, 'workspace', wf)
        if not os.path.exists(wf_path):
            actions.append(f'create file: .gald3r/workspace/{wf}')
        else:
            actions.append(f'preserve: .gald3r/workspace/{wf} (already present)')

    actions.append('rewrite: .gald3r/.identity (workspace_role -> autonomous_child; '
                   f'remove member_gald3r_marker_only; gald3r_version -> {target_version})')
    if manifest_file:
        actions.append(f'update manifest: {manifest_file} '
                       f'(repositories[{member_id}].workspace_role -> autonomous_child)')
    else:
        actions.append('warn: no workspace manifest resolved; manifest workspace_role '
                       'not updated')

    if not args.apply:
        write_result({
            'Status': 'plan',
            'Reason': 'dry_run',
            'Message': (f'Dry-run: no files written. Pass -Apply to promote member '
                        f'{member_id} to autonomous_child.'),
            'MemberId': member_id,
            'MemberPath': normal_member,
            'ControllerPath': controller_root,
            'FromRole': effective_role,
            'ToRole': 'autonomous_child',
            'Gald3rVersion': target_version,
            'ManifestUpdated': False,
            'Actions': actions,
        }, as_json)
        return 0

    # ----------------------------------------------------------------------
    # Apply
    # ----------------------------------------------------------------------
    today = datetime.date.today().strftime('%Y-%m-%d')
    applied: List[str] = []

    if not os.path.exists(dot_gald3r):
        os.makedirs(dot_gald3r, exist_ok=True)
        applied.append('created dir: .gald3r/')

    for d in STANDARD_DIRS:
        dir_path = os.path.join(dot_gald3r, d)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            applied.append(f'created dir: .gald3r/{d}/')

    def write_stub_file(path: str, body: str) -> bool:
        """Create `path` with `body` only when absent; True when written."""
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(body + '\n')
            return True
        return False

    stubs: Dict[str, str] = {
        'RELEASES.md': (f'# Releases\n\n_Promoted to autonomous_child on {today}. Release '
                        'index managed by @g-release-* commands._\n\n## Release Index\n\n'
                        '| Version | Date | Status | Tasks |\n'
                        '|---------|------|--------|-------|\n'),
        'vocab.md': (f'# Project Vocabulary\n\n_Promoted to autonomous_child on {today}. '
                     'Manage with @g-vocab-add / @g-vocab-list._\n\n## Active Vocabulary\n\n'
                     '| Abbreviation | Expansion | Notes |\n'
                     '|--------------|-----------|-------|\n'),
        'FEATURES.md': (f'# Features\n\n_Promoted to autonomous_child on {today}. Managed '
                        'by @g-feat-* commands._\n\n## Feature Index\n\n'
                        '| ID | Title | Status |\n|----|-------|--------|\n'),
        'BUGS.md': (f'# Bugs\n\n_Promoted to autonomous_child on {today}. Managed by '
                    '@g-bug-* commands._\n\n## Bug Index\n\n'
                    '| ID | Title | Severity | Status |\n|----|-------|----------|--------|\n'),
        'PLAN.md': (f'# Plan\n\n_Promoted to autonomous_child on {today}. Managed by '
                    '@g-plan._\n\n## Strategy\n\n_Define the master strategy and '
                    'milestones here._\n'),
    }

    for name in STANDARD_FILES:
        file_path = os.path.join(dot_gald3r, name)
        if write_stub_file(file_path, stubs[name]):
            applied.append(f'created: .gald3r/{name}')
        else:
            applied.append(f'preserved: .gald3r/{name}')

    workspace_stubs: Dict[str, str] = {
        'topology.md': (f'# Workspace Topology\n\n> Created on promotion to '
                        f'autonomous_child ({today}).\n>\n> Declare WPAC parent / children '
                        '/ siblings here. An autonomous_child is\n> self-managed and '
                        'WPAC-linked to its controller.\n\n## Relationships\n\nparent: \n\n'
                        'children: []\n\nsiblings: []\n'),
        'inbox.md': (f'# Workspace Inbox\n\n> Created on promotion to autonomous_child '
                     f'({today}).\n>\n> Cross-project WPAC directives land here. Action '
                     'with @g-wpac-read.\n\n## Open Items\n\n_None._\n'),
    }

    for wf in WORKSPACE_FILES:
        wf_path = os.path.join(dot_gald3r, 'workspace', wf)
        if write_stub_file(wf_path, workspace_stubs[wf]):
            applied.append(f'created: .gald3r/workspace/{wf}')
        else:
            applied.append(f'preserved: .gald3r/workspace/{wf}')

    # Rewrite .identity: set role, drop marker flag, bump version. Preserve order
    # and any unknown keys.
    new_lines: List[str] = []
    saw_role = False
    saw_version = False
    if os.path.exists(identity_file):
        with open(identity_file, 'r', encoding='utf-8-sig', errors='replace') as fh:
            identity_lines = fh.read().splitlines()
        for line in identity_lines:
            if re.match(r'^\s*member_gald3r_marker_only\s*=', line):
                # Drop the marker-only flag entirely.
                continue
            if re.match(r'^(\s*)workspace_role\s*=', line):
                new_lines.append('workspace_role=autonomous_child')
                saw_role = True
            elif re.match(r'^(\s*)gald3r_version\s*=', line):
                if target_version:
                    new_lines.append(f'gald3r_version={target_version}')
                else:
                    new_lines.append(line)
                saw_version = True
            else:
                new_lines.append(line)
    if not saw_role:
        new_lines.append('workspace_role=autonomous_child')
    if not saw_version and target_version:
        new_lines.append(f'gald3r_version={target_version}')
    with open(identity_file, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(new_lines) + '\n')
    applied.append('rewrote: .gald3r/.identity (workspace_role=autonomous_child, marker '
                   f'flag removed, gald3r_version={target_version})')

    # Update the workspace manifest workspace_role for this member.
    manifest_updated = False
    if manifest_file and os.path.exists(manifest_file):
        with open(manifest_file, 'r', encoding='utf-8-sig', newline='') as fh:
            content = fh.read()
        # Match the member's repository entry block and rewrite its workspace_role.
        # Entry headers are `- id: <MemberId>`; the body uses two-space indent.
        pattern = re.compile(
            r'(^- id:\s*' + re.escape(member_id)
            + r'\s*\r?\n(?:^(?!- id:)[^\r\n]*\r?\n)*?^  workspace_role:\s*)([A-Za-z_]+)',
            re.M | re.S)
        if pattern.search(content):
            content = pattern.sub(lambda m: m.group(1) + 'autonomous_child', content,
                                  count=1)
            with open(manifest_file, 'w', encoding='utf-8', newline='') as fh:
                fh.write(content)
            manifest_updated = True
            applied.append(f'updated manifest: repositories[{member_id}].workspace_role '
                           '-> autonomous_child')
        else:
            applied.append(f'warn: could not locate repositories[{member_id}]'
                           '.workspace_role in manifest; update it manually')
    else:
        applied.append('warn: no workspace manifest resolved; manifest workspace_role '
                       'not updated')

    write_result({
        'Status': 'applied',
        'Reason': 'promotion_complete',
        'Message': (f'Member {member_id} promoted to autonomous_child. The g-rl-36 guard '
                    'now allows @g-skl-setup. Run @g-skl-setup --upgrade-existing for a '
                    'full file top-up, then @g-wrkspc-validate.'),
        'MemberId': member_id,
        'MemberPath': normal_member,
        'ControllerPath': controller_root,
        'FromRole': effective_role,
        'ToRole': 'autonomous_child',
        'Gald3rVersion': target_version,
        'ManifestUpdated': manifest_updated,
        'Actions': applied,
    }, as_json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
