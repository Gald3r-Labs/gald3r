#!/usr/bin/env python3
"""Python port of check_member_repo_gald3r_guard.ps1 (T1585).

Workspace-Control member-repo .gald3r/ guard.

Blocks accidental live control-plane ``.gald3r/`` writes into ordinary
Workspace-Control members while allowing installable template repos to carry
their intended template ``.gald3r/`` content.

Non-template member repos may contain ONLY a slim ``.gald3r/`` marker:
  * .gald3r/.identity   - identifies the member; ties back to controller
  * .gald3r/PROJECT.md  - copied / parity-maintained from controller

Exit codes:
  0 - clear (write is allowed)
  1 - block (member repo + control-plane path)
  2 - input or manifest error

Modes (mutually informative):
  * Default (no -DotGald3rPath, no -AllowMarkerInit): for member targets,
    BLOCK because intent is unspecified.
  * -DotGald3rPath <relative_path>: evaluate the specific path; ALLOW iff it
    is the ``.identity`` file or the ``PROJECT.md`` file.
  * -AllowMarkerInit: caller asserts they will only write marker-safe files.

This module is also imported by the sibling ports
(bootstrap_member_gald3r_marker.py, remediate_member_gald3r_marker.py,
gald3r_promote_member.py, validate_workspace_members_gald3r.py) which call
:func:`run_guard` / the manifest helpers directly instead of spawning a
subprocess. Engine ``gald3r.utils`` is intentionally not used here: every
output line and JSON key is parity-locked to the PS1 (plain stdout text and
PascalCase JSON), and the script needs no subprocess/fs-tree/temp helpers.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Marker allowlist: relative paths inside .gald3r/ that are safe in member repos.
# Bare basenames only (one level under .gald3r/). Anything else is control plane.
MARKER_ALLOWLIST: Tuple[str, ...] = ('.identity', 'PROJECT.md')

# Forbidden examples for diagnostic output (not exhaustive - anything not in
# the allowlist is forbidden).
CONTROL_PLANE_EXAMPLES: Tuple[str, ...] = (
    'TASKS.md', 'tasks/', 'BUGS.md', 'bugs/', 'PLAN.md', 'FEATURES.md',
    'SUBSYSTEMS.md', 'RELEASES.md', 'CONSTRAINTS.md', 'IDEA_BOARD.md',
    'PRDS.md', 'config/', 'linking/', 'experiments/', 'logs/', 'reports/',
    'archive/', 'specifications_collection/', 'features/', 'releases/',
    'subsystems/', 'prds/', 'learned-facts.md',
)

MANIFEST_RELATIVE = '.gald3r/linking/workspace_manifest.yaml'


def convert_to_normal_path(path: str, lowercase: bool = False) -> str:
    """Resolve `path` if it exists, normalize to forward slashes, trim '/'.

    Mirrors the PS1 ``ConvertTo-NormalPath`` (the guard variant additionally
    lowercases; pass ``lowercase=True`` for that behavior).
    """
    if not path:
        return ''
    resolved = path
    try:
        if os.path.exists(path):
            resolved = str(Path(path).resolve())
    except OSError:
        resolved = path
    resolved = resolved.replace('\\', '/').rstrip('/')
    return resolved.lower() if lowercase else resolved


def convert_to_dot_gald3r_relative(path: str) -> str:
    """Strip any leading ``.gald3r/`` prefix and slashes from a relative path."""
    if not path:
        return ''
    p = path.replace('\\', '/')
    p = re.sub(r'^\.gald3r/+', '', p)
    p = re.sub(r'^/+', '', p)
    return p.rstrip('/')


def is_marker_safe_path(dot_gald3r_relative: str) -> bool:
    """True when the relative path is in the marker allowlist (case-insensitive)."""
    if not dot_gald3r_relative:
        return False
    rel = dot_gald3r_relative.casefold()
    return any(rel == allowed.casefold() for allowed in MARKER_ALLOWLIST)


def is_template_path(normal_path: str) -> bool:
    """True when the normalized path is inside a gald3r_template_(slim|full|adv) repo."""
    if not normal_path:
        return False
    return re.search(r'/gald3r_template_(slim|full|adv)(/|$)', normal_path,
                     re.IGNORECASE) is not None


def find_workspace_manifest(start_path: str) -> Optional[str]:
    """Walk up from `start_path` (then from cwd) to find the workspace manifest."""
    candidate = start_path
    if candidate and os.path.exists(candidate):
        candidate = str(Path(candidate).resolve())
    while candidate and os.path.exists(candidate):
        manifest = os.path.join(candidate, *MANIFEST_RELATIVE.split('/'))
        if os.path.exists(manifest):
            return str(Path(manifest).resolve())
        parent = os.path.dirname(candidate)
        if not parent or parent == candidate:
            break
        candidate = parent
    cwd = os.getcwd()
    while cwd:
        manifest = os.path.join(cwd, *MANIFEST_RELATIVE.split('/'))
        if os.path.exists(manifest):
            return str(Path(manifest).resolve())
        parent = os.path.dirname(cwd)
        if not parent or parent == cwd:
            break
        cwd = parent
    return None


def read_workspace_manifest_repositories(manifest_file: str) -> List[Dict[str, str]]:
    """Parse the v1 workspace manifest ``repositories:`` block (regex-based).

    Returns a list of dicts with keys Id, LocalPath, WorkspaceRole,
    LifecycleStatus, License (License is used by the validate sibling; the
    guard itself ignores it).
    """
    with open(manifest_file, 'r', encoding='utf-8-sig', newline='') as fh:
        content = fh.read()

    # v1 workspace manifest: sequence items are `- id:` at line start; fields
    # use two-space indent. Block ends at top-level `controlled_members:`.
    m = re.search(r'^repositories:\s*\r?\n(.*?)^controlled_members:\s*$',
                  content, re.M | re.S)
    repos_block = m.group(1) if m else None
    if not repos_block:
        return []

    entries: List[Dict[str, str]] = []
    # Do not use re.S here: . would span newlines and swallow subsequent
    # `- id:` repo headers.
    entry_pattern = re.compile(
        r'^- id:\s*([A-Za-z][A-Za-z0-9_]*)\s*\r?\n((?:^(?!- id:)[^\r\n]*\r?\n)*)',
        re.M)
    for em in entry_pattern.finditer(repos_block):
        rid = em.group(1)
        body = em.group(2)
        local_path = ''
        workspace_role = ''
        lifecycle_status = ''
        license_value = ''
        lp = re.search(r'^  local_path:\s*[\'"]?([^\'"\r\n]+?)[\'"]?\s*$', body, re.M)
        if lp:
            local_path = lp.group(1).strip()
        wr = re.search(r'^  workspace_role:\s*([A-Za-z_]+)\s*$', body, re.M)
        if wr:
            workspace_role = wr.group(1).strip()
        ls = re.search(r'^  lifecycle_status:\s*([A-Za-z_]+)\s*$', body, re.M)
        if ls:
            lifecycle_status = ls.group(1).strip()
        lic = re.search(r'^  license:\s*[\'"]?([A-Za-z0-9.\-_]+)[\'"]?\s*$', body, re.M)
        if lic:
            license_value = lic.group(1).strip()
        entries.append({
            'Id': rid,
            'LocalPath': local_path,
            'WorkspaceRole': workspace_role,
            'LifecycleStatus': lifecycle_status,
            'License': license_value,
        })
    return entries


def write_result(result: Dict[str, Any], as_json: bool) -> None:
    """Emit a guard result: JSON (PascalCase keys, PS1-compatible) or text."""
    if as_json:
        print(json.dumps(result, indent=2))
        return
    status_token = str(result.get('Status', '')).upper()
    print(f"[{status_token}] member-repo .gald3r guard: {result.get('Reason', '')}")
    if result.get('Message'):
        print(f"  {result['Message']}")
    if result.get('MatchedRepoId'):
        print(f"  matched_repo_id : {result['MatchedRepoId']}")
        print(f"  matched_role    : {result.get('MatchedRole', '')}")
    if result.get('DotGald3rPath'):
        print(f"  dot_gald3r_path  : {result['DotGald3rPath']}")
    if result.get('MarkerAllowlist'):
        print(f"  marker_allowed  : {', '.join(result['MarkerAllowlist'])}")
    if result.get('ManifestPath'):
        print(f"  manifest        : {result['ManifestPath']}")
    print(f"  target_path     : {result.get('TargetPath', '')}")


def run_guard(target_path: str,
              dot_gald3r_path: str = '',
              allow_marker_init: bool = False,
              manifest_path: str = '',
              warn_only: bool = False) -> Tuple[Dict[str, Any], int]:
    """Evaluate the member-repo guard; return (result_dict, exit_code).

    Result keys and values match the PS1 ``ConvertTo-Json`` output so callers
    that previously parsed the PS1 JSON keep working unchanged.
    """
    if not target_path:
        return ({
            'Status': 'error',
            'Reason': 'missing_target_path',
            'Message': 'TargetPath is required.',
            'TargetPath': '',
        }, 2)

    normal_target = convert_to_normal_path(target_path, lowercase=True)
    relative_dot_path = convert_to_dot_gald3r_relative(dot_gald3r_path)

    if is_template_path(normal_target):
        return ({
            'Status': 'allow',
            'Reason': 'template_directory_exception',
            'Message': ('Target is inside a gald3r_template_(slim|full|adv) repo; '
                        '.gald3r/ template content is allowed.'),
            'TargetPath': normal_target,
            'DotGald3rPath': relative_dot_path,
        }, 0)

    manifest_file: Optional[str] = None
    if manifest_path:
        if not os.path.exists(manifest_path):
            return ({
                'Status': 'error',
                'Reason': 'manifest_not_found',
                'Message': f'Specified ManifestPath does not exist: {manifest_path}',
                'TargetPath': normal_target,
            }, 2)
        manifest_file = str(Path(manifest_path).resolve())
    else:
        manifest_file = find_workspace_manifest(target_path)

    if not manifest_file:
        return ({
            'Status': 'allow',
            'Reason': 'no_workspace_manifest',
            'Message': ('No .gald3r/linking/workspace_manifest.yaml found near target. '
                        'Workspace-Control inactive; member-repo boundary not enforced.'),
            'TargetPath': normal_target,
            'ManifestPath': None,
            'DotGald3rPath': relative_dot_path,
        }, 0)

    try:
        repos = read_workspace_manifest_repositories(manifest_file)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return ({
            'Status': 'error',
            'Reason': 'manifest_parse_failed',
            'Message': f'Could not parse repositories block: {exc}',
            'TargetPath': normal_target,
            'ManifestPath': manifest_file,
        }, 2)

    if not repos:
        return ({
            'Status': 'allow',
            'Reason': 'manifest_empty_repositories',
            'Message': ('Workspace manifest parsed but no repositories[] entries found. '
                        'Boundary not enforced.'),
            'TargetPath': normal_target,
            'ManifestPath': manifest_file,
            'DotGald3rPath': relative_dot_path,
        }, 0)

    normal_target_with_slash = f'{normal_target}/'
    match: Optional[Dict[str, str]] = None
    for r in repos:
        if not r['LocalPath']:
            continue
        r_norm = r['LocalPath'].replace('\\', '/').rstrip('/').lower()
        if not r_norm:
            continue
        if normal_target == r_norm or normal_target_with_slash.startswith(f'{r_norm}/'):
            match = r
            break

    if match is None:
        return ({
            'Status': 'allow',
            'Reason': 'outside_workspace',
            'Message': 'Target path is not registered as any workspace repository.',
            'TargetPath': normal_target,
            'ManifestPath': manifest_file,
            'DotGald3rPath': relative_dot_path,
        }, 0)

    if match['WorkspaceRole'] == 'control_project':
        return ({
            'Status': 'allow',
            'Reason': 'control_project',
            'Message': (f"Target is the workspace control project ({match['Id']}); "
                        '.gald3r/ is permitted here.'),
            'TargetPath': normal_target,
            'ManifestPath': manifest_file,
            'MatchedRepoId': match['Id'],
            'MatchedRole': match['WorkspaceRole'],
            'DotGald3rPath': relative_dot_path,
        }, 0)

    # Member or migration_source path matched. Apply marker policy.
    is_member_role = match['WorkspaceRole'] in ('controlled_member', 'migration_source')

    if not is_member_role:
        return ({
            'Status': 'warn',
            'Reason': f"unknown_workspace_role:{match['WorkspaceRole']}",
            'Message': (f"Target matches manifest entry {match['Id']} with unrecognized "
                        f"workspace_role '{match['WorkspaceRole']}'. Treating as advisory; "
                        'do not write to .gald3r/ here without explicit task authorization.'),
            'TargetPath': normal_target,
            'ManifestPath': manifest_file,
            'MatchedRepoId': match['Id'],
            'MatchedRole': match['WorkspaceRole'],
            'DotGald3rPath': relative_dot_path,
        }, 0 if warn_only else 1)

    # Member or migration_source.
    if relative_dot_path:
        if is_marker_safe_path(relative_dot_path):
            return ({
                'Status': 'allow',
                'Reason': 'marker_safe_path',
                'Message': (f'Path .gald3r/{relative_dot_path} is in the marker allowlist '
                            f"for member repository {match['Id']}."),
                'TargetPath': normal_target,
                'ManifestPath': manifest_file,
                'MatchedRepoId': match['Id'],
                'MatchedRole': match['WorkspaceRole'],
                'DotGald3rPath': relative_dot_path,
                'MarkerAllowlist': list(MARKER_ALLOWLIST),
            }, 0)
        return ({
            'Status': 'block',
            'Reason': 'controlled_member_control_plane_path',
            'Message': (f'BLOCK: .gald3r/{relative_dot_path} is forbidden in member '
                        f"repository {match['Id']} - it is live gald3r control-plane state. "
                        f"Marker allowlist: {', '.join(MARKER_ALLOWLIST)}. "
                        f"Forbidden examples: {', '.join(CONTROL_PLANE_EXAMPLES)}."),
            'TargetPath': normal_target,
            'ManifestPath': manifest_file,
            'MatchedRepoId': match['Id'],
            'MatchedRole': match['WorkspaceRole'],
            'DotGald3rPath': relative_dot_path,
            'MarkerAllowlist': list(MARKER_ALLOWLIST),
        }, 0 if warn_only else 1)

    if allow_marker_init:
        return ({
            'Status': 'allow',
            'Reason': 'marker_init_authorized',
            'Message': (f"Marker-init mode authorized for member {match['Id']}. Caller MUST "
                        f"write only marker-safe paths ({', '.join(MARKER_ALLOWLIST)}). Use "
                        'bootstrap_member_gald3r_marker.py for the actual filesystem write '
                        'to enforce the allowlist.'),
            'TargetPath': normal_target,
            'ManifestPath': manifest_file,
            'MatchedRepoId': match['Id'],
            'MatchedRole': match['WorkspaceRole'],
            'MarkerAllowlist': list(MARKER_ALLOWLIST),
        }, 0)

    # Default member match without -DotGald3rPath or -AllowMarkerInit: BLOCK.
    return ({
        'Status': 'block',
        'Reason': 'controlled_member_repository',
        'Message': (f"BLOCK: Target ({match['Id']}) is a Workspace-Control "
                    f"{match['WorkspaceRole']}. Specify -DotGald3rPath <path> to evaluate a "
                    'specific .gald3r/ write, or -AllowMarkerInit when bootstrapping the '
                    f"marker pair ({', '.join(MARKER_ALLOWLIST)}). Live control-plane content "
                    'is forbidden in member repositories; use the workspace control project '
                    'for project task state.'),
        'TargetPath': normal_target,
        'ManifestPath': manifest_file,
        'MatchedRepoId': match['Id'],
        'MatchedRole': match['WorkspaceRole'],
        'MarkerAllowlist': list(MARKER_ALLOWLIST),
    }, 0 if warn_only else 1)


def build_parser() -> argparse.ArgumentParser:
    """argparse surface mirroring the PS1 param() block (both spellings)."""
    parser = argparse.ArgumentParser(
        description='Workspace-Control member-repo .gald3r/ guard (g-rl-36).',
        allow_abbrev=False)
    parser.add_argument('target_path_pos', nargs='?', default=None,
                        metavar='TargetPath',
                        help='Target repository path (positional form).')
    parser.add_argument('-TargetPath', '--target-path', dest='target_path',
                        default=None, help='Target repository path.')
    parser.add_argument('-DotGald3rPath', '--dot-gald3r-path', dest='dot_gald3r_path',
                        default='', help='Specific .gald3r/-relative path to evaluate.')
    parser.add_argument('-AllowMarkerInit', '--allow-marker-init',
                        dest='allow_marker_init', action='store_true',
                        help='Caller asserts marker-safe writes only.')
    parser.add_argument('-ManifestPath', '--manifest-path', dest='manifest_path',
                        default='', help='Explicit workspace manifest path.')
    parser.add_argument('-WarnOnly', '--warn-only', dest='warn_only',
                        action='store_true',
                        help='Report blocks/warns but exit 0.')
    parser.add_argument('-Json', '--json', dest='json', action='store_true',
                        help='Emit JSON instead of text.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point — prints the result and returns the guard exit code."""
    args = build_parser().parse_args(argv)
    target_path = args.target_path or args.target_path_pos or ''
    if not target_path:
        result = {
            'Status': 'error',
            'Reason': 'missing_target_path',
            'Message': 'TargetPath is required.',
            'TargetPath': '',
        }
        write_result(result, args.json)
        return 2
    result, code = run_guard(
        target_path=target_path,
        dot_gald3r_path=args.dot_gald3r_path,
        allow_marker_init=args.allow_marker_init,
        manifest_path=args.manifest_path,
        warn_only=args.warn_only)
    write_result(result, args.json)
    return code


if __name__ == '__main__':
    sys.exit(main())
