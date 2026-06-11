#!/usr/bin/env python3
"""Python port of bootstrap_member_gald3r_marker.ps1 (T1585).

Bootstrap the marker-only ``.gald3r/`` for a Workspace-Control member
repository. Creates ``.gald3r/.identity`` (if absent) tying the member back
to the workspace controller; creates a stub ``.gald3r/PROJECT.md`` (if
absent) identifying the member.

Used by:
  * @g-wrkspc-spawn --apply (after git init + minimal .gitignore/README)
  * @g-wrkspc-member-add --apply (when the path exists)
  * @g-wrkspc-adopt --apply (after adoption preflight passes)

This is the ONLY supported writer of member ``.gald3r/`` content. It refuses
to write anything outside the marker allowlist (``.identity``, ``PROJECT.md``).

BUG-021 / Task 213 / g-rl-36.

Cross-script call: imports the sibling check_member_repo_gald3r_guard.py and
calls run_guard() in-process (the PS1 spawned it as a subprocess and parsed
its JSON). Engine ``gald3r.utils`` is intentionally not used: output text and
JSON keys are parity-locked to the PS1 and no subprocess/fs-tree/temp
patterns exist in the source script.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import uuid
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


def get_controller_identity(controller_root: str) -> Dict[str, str]:
    """Read the controller's .gald3r/.identity into a key=value map."""
    id_file = os.path.join(controller_root, '.gald3r', '.identity')
    if not os.path.exists(id_file):
        return {}
    id_map: Dict[str, str] = {}
    with open(id_file, 'r', encoding='utf-8-sig', errors='replace') as fh:
        for line in fh.read().splitlines():
            m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)\s*$', line)
            if m:
                id_map[m.group(1)] = m.group(2).strip()
    return id_map


def new_marker_identity_content(member_id: str,
                                member_abs_path: str,
                                controller_identity: Dict[str, str],
                                controller_abs_path: str) -> str:
    """Render the member .identity marker content."""
    new_project_id = str(uuid.uuid4())
    controller_project_id = controller_identity.get('project_id', '')
    controller_project_name = controller_identity.get('project_name', '')
    user_id = controller_identity.get('user_id', '')
    user_name = controller_identity.get('user_name', '')
    gald3r_version = controller_identity.get('gald3r_version', '')

    return f"""# Workspace-Control member identity (marker-only — BUG-021 / Task 213 / g-rl-36)
# This file ties the member repository back to the workspace controller.
# Live gald3r task/bug/plan/feature state lives in the controller, not here.

project_id={new_project_id}
project_name={member_id}
project_path={member_abs_path}
user_id={user_id}
user_name={user_name}
gald3r_version={gald3r_version}

# Workspace-Control wiring
workspace_role=controlled_member
workspace_controller_id={controller_project_name}
workspace_controller_project_id={controller_project_id}
workspace_controller_path={controller_abs_path}
member_gald3r_marker_only=true"""


def new_marker_project_md_content(member_id: str,
                                  controller_path: str,
                                  controller_identity: Dict[str, str]) -> str:
    """Render the member PROJECT.md marker stub content."""
    controller_name = controller_identity.get('project_name', 'workspace controller') \
        or 'workspace controller'
    today = datetime.date.today().strftime('%Y-%m-%d')
    return f"""# {member_id}

> **Workspace-Control member repository** managed by {controller_name}.
>
> This is a marker-only `.gald3r/` (BUG-021 / Task 213 / g-rl-36). Live
> gald3r task, bug, plan, feature, release, subsystem, and orchestration
> state for this project lives in the workspace controller at
> `{controller_path}`, not here.
>
> Allowed in this folder: `.identity` and `PROJECT.md` only.

## Mission

_Member-specific mission to be filled in. The structure of this file
follows the standard gald3r `PROJECT.md` shape and is parity-maintained
with the workspace controller's documentation conventions._

## Workspace-Control Membership

- **Role**: `controlled_member`
- **Controller**: {controller_name}
- **Member ID**: `{member_id}`
- **Marker bootstrapped**: {today}

## Source of Truth

- Live tasks, bugs, plans, releases: workspace controller (`{controller_path}`)
- This member's source code, build configuration, runtime files: this repository
- Cross-project coordination (WPAC, INBOX, orders): workspace controller

## Why marker-only?

The Workspace-Control invariant (g-rl-36) requires that controlled member
repositories not contain live gald3r control-plane state. This prevents
member-vs-controller drift, accidental task/bug duplication, and broken
ownership boundaries. See `BUG-021` and `Task 213` for the full
rationale and the cleanup/remediation flow."""


def write_result(result: Dict[str, Any], as_json: bool) -> None:
    """Emit a bootstrap result: JSON (PascalCase keys) or PS1-parity text."""
    if as_json:
        print(json.dumps(result, indent=2))
        return
    status_token = str(result.get('Status', '')).upper()
    print(f"[{status_token}] member-marker bootstrap: {result.get('Reason', '')}")
    if result.get('Message'):
        print(f"  {result['Message']}")
    for action in result.get('Actions') or []:
        if action:
            print(f"  - {action}")
    if result.get('MemberId'):
        print(f"  member_id      : {result['MemberId']}")
    if result.get('MemberPath'):
        print(f"  member_path    : {result['MemberPath']}")
    if result.get('ControllerPath'):
        print(f"  controller     : {result['ControllerPath']}")


def build_parser() -> argparse.ArgumentParser:
    """argparse surface mirroring the PS1 param() block (both spellings)."""
    parser = argparse.ArgumentParser(
        description='Bootstrap the marker-only .gald3r/ for a Workspace-Control member.',
        allow_abbrev=False)
    parser.add_argument('-MemberPath', '--member-path', dest='member_path',
                        required=True, help='Member repository path.')
    parser.add_argument('-MemberId', '--member-id', dest='member_id',
                        required=True, help='Member id (manifest repositories[].id).')
    parser.add_argument('-ControllerPath', '--controller-path', dest='controller_path',
                        default='', help='Workspace controller root (auto-discovered when omitted).')
    parser.add_argument('-ManifestPath', '--manifest-path', dest='manifest_path',
                        default='', help='Explicit workspace manifest path.')
    parser.add_argument('-Apply', '--apply', dest='apply', action='store_true',
                        help='Write the marker (default is dry-run).')
    parser.add_argument('-Force', '--force', dest='force', action='store_true',
                        help='Override member-id mismatch against the manifest (rare).')
    parser.add_argument('-Json', '--json', dest='json', action='store_true',
                        help='Emit JSON instead of text.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point — mirrors the PS1 main flow and exit codes (0/1/2)."""
    args = build_parser().parse_args(argv)
    member_path: str = args.member_path
    member_id: str = args.member_id
    as_json: bool = args.json

    normal_member = convert_to_normal_path(member_path)
    if not normal_member:
        write_result({
            'Status': 'error',
            'Reason': 'invalid_member_path',
            'Message': 'MemberPath did not resolve to a valid path.',
            'MemberPath': member_path,
        }, as_json)
        return 2

    if not os.path.exists(member_path):
        write_result({
            'Status': 'error',
            'Reason': 'member_path_not_found',
            'Message': (f'Member path does not exist: {normal_member}. Create the '
                        'directory first (g-wrkspc-spawn handles this).'),
            'MemberPath': normal_member,
            'MemberId': member_id,
        }, as_json)
        return 2

    # Resolve controller path: explicit --ControllerPath > walk upward to find manifest
    controller_root: Optional[str] = None
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

    if args.controller_path:
        if not os.path.exists(args.controller_path):
            write_result({
                'Status': 'error',
                'Reason': 'controller_path_not_found',
                'Message': f'ControllerPath does not exist: {args.controller_path}',
                'MemberPath': normal_member,
                'MemberId': member_id,
                'ControllerPath': args.controller_path,
            }, as_json)
            return 2
        controller_root = str(Path(args.controller_path).resolve())
    else:
        # Find from manifest discovery (member walk-up, then cwd walk-up).
        manifest = guard.find_workspace_manifest(member_path)
        if manifest:
            # manifest lives at <controller>/.gald3r/linking/workspace_manifest.yaml
            controller_root = str(Path(manifest).parents[2])

    if not controller_root:
        write_result({
            'Status': 'error',
            'Reason': 'controller_not_found',
            'Message': ('Could not locate workspace controller (no '
                        '.gald3r/linking/workspace_manifest.yaml in any ancestor of '
                        'MemberPath or current directory). Pass -ControllerPath explicitly.'),
            'MemberPath': normal_member,
            'MemberId': member_id,
        }, as_json)
        return 2

    # Run the guard helper to confirm member identity matches the manifest.
    # Use AllowMarkerInit to confirm membership without blocking.
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

    if guard_result.get('Status') != 'allow':
        write_result({
            'Status': 'error',
            'Reason': f"guard_refused:{guard_result.get('Reason', '')}",
            'Message': (f'Guard refused marker-init for {member_path}. '
                        f"{guard_result.get('Message', '')}"),
            'MemberPath': normal_member,
            'MemberId': member_id,
        }, as_json)
        return 2

    matched_repo_id = guard_result.get('MatchedRepoId')
    if matched_repo_id and matched_repo_id != member_id and not args.force:
        write_result({
            'Status': 'error',
            'Reason': 'member_id_mismatch',
            'Message': (f"MemberId '{member_id}' does not match manifest entry "
                        f"'{matched_repo_id}' for path {normal_member}. "
                        'Pass -Force to override (rare).'),
            'MemberPath': normal_member,
            'MemberId': member_id,
        }, as_json)
        return 2

    # Determine actions
    actions: List[str] = []
    violations: List[str] = []
    dot_gald3r_path = os.path.join(member_path, '.gald3r')
    identity_path = os.path.join(dot_gald3r_path, '.identity')
    project_md_path = os.path.join(dot_gald3r_path, 'PROJECT.md')
    allow_cf = {a.casefold() for a in MARKER_ALLOWLIST}

    # Scan existing .gald3r/ for forbidden content
    if os.path.exists(dot_gald3r_path):
        try:
            entries = sorted(Path(dot_gald3r_path).iterdir())
        except OSError:
            entries = []
        for entry in entries:
            if entry.name.casefold() in allow_cf:
                continue
            violations.append(entry.name)
        if violations:
            actions.append('skip: existing .gald3r/ contains non-marker content: '
                           f"{', '.join(violations)}. Run remediate_member_gald3r_marker.py first.")
    else:
        actions.append(f'create dir: {dot_gald3r_path}')

    # .identity action
    if not os.path.exists(identity_path):
        actions.append(f'create: {identity_path} (member identity tying back to controller)')
    else:
        actions.append(f'preserve: {identity_path} (already present)')

    # PROJECT.md action
    if not os.path.exists(project_md_path):
        actions.append(f'create: {project_md_path} '
                       '(member-stub identifying member + cross-link to controller)')
    else:
        actions.append(f'preserve: {project_md_path} (already present)')

    if violations:
        # Refuse to write into a member with existing forbidden content
        write_result({
            'Status': 'block',
            'Reason': 'member_gald3r_has_control_plane',
            'Message': ('Member .gald3r/ already contains non-marker content. Bootstrap '
                        'refuses to proceed until remediation is run. Forbidden entries: '
                        f"{', '.join(violations)}. Use "
                        '.claude/skills/g-skl-workspace/scripts/remediate_member_gald3r_marker.py '
                        f"-MemberPath '{member_path}' --dry-run, then -Apply, before "
                        're-running bootstrap.'),
            'Actions': actions,
            'MemberPath': normal_member,
            'MemberId': member_id,
            'ControllerPath': controller_root,
        }, as_json)
        return 1

    if not args.apply:
        write_result({
            'Status': 'plan',
            'Reason': 'dry_run',
            'Message': 'Dry-run: no files written. Pass -Apply to write the marker.',
            'Actions': actions,
            'MemberPath': normal_member,
            'MemberId': member_id,
            'ControllerPath': controller_root,
        }, as_json)
        return 0

    # Apply mode
    controller_identity = get_controller_identity(controller_root)

    if not os.path.exists(dot_gald3r_path):
        os.makedirs(dot_gald3r_path, exist_ok=True)

    if not os.path.exists(identity_path):
        identity_content = new_marker_identity_content(
            member_id=member_id,
            member_abs_path=normal_member,
            controller_identity=controller_identity,
            controller_abs_path=controller_root)
        with open(identity_path, 'w', encoding='utf-8') as fh:
            fh.write(identity_content + '\n')

    if not os.path.exists(project_md_path):
        project_md_content = new_marker_project_md_content(
            member_id=member_id,
            controller_path=controller_root,
            controller_identity=controller_identity)
        with open(project_md_path, 'w', encoding='utf-8') as fh:
            fh.write(project_md_content + '\n')

    write_result({
        'Status': 'applied',
        'Reason': 'marker_bootstrap_complete',
        'Message': (f'Marker .gald3r/ bootstrapped for member {member_id}. Live '
                    'control-plane content remains forbidden here per g-rl-36.'),
        'Actions': actions,
        'MemberPath': normal_member,
        'MemberId': member_id,
        'ControllerPath': controller_root,
    }, as_json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
