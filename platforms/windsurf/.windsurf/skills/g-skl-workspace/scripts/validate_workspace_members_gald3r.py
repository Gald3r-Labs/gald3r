#!/usr/bin/env python3
"""Python port of validate_workspace_members_gald3r.ps1 (T1585).

Workspace-Control member-marker AND license-posture validator
(BUG-021 / Task 213 / g-rl-36 + Task 804 / C-020).

Reads ``.gald3r/linking/workspace_manifest.yaml``, enumerates every
repository, and reports:

  Marker compliance (controlled_member + migration_source only):
    * clean              - .gald3r/ contains only .identity and/or PROJECT.md
    * marker_missing     - member exists, .gald3r/ absent or marker incomplete
    * has_violations     - .gald3r/ contains forbidden control-plane content
    * not_yet_created    - member path does not exist on disk yet

  License posture (every repository, including control_project):
    * license_match      - LICENSE file exists and matches manifest `license:` value
    * license_drift      - LICENSE file exists but content does not match template
    * license_missing    - LICENSE file absent
    * license_undeclared - manifest entry has no `license:` key
    * reference_archive  - skipped (historical archive, not a live workspace repo)

Exit codes:
  0 - all members compliant or only informational findings
  1 - one or more members have_violations OR license_drift / license_missing
  2 - manifest error

Cross-script call: imports the sibling check_member_repo_gald3r_guard.py for
the shared manifest parser and manifest walk-up (the PS1 inlined identical
copies). Fatal manifest errors are routed through engine
``gald3r.utils.console.err`` when importable, with a plain-stderr fallback.
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

MARKER_ALLOWLIST: Tuple[str, ...] = ('.identity', 'PROJECT.md')

# Map of license-posture key (manifest `license:` value) to canonical template
# path (resolved relative to the manifest's controller repo root).
LICENSE_TEMPLATE_MAP: Dict[str, str] = {
    'FSL-1.1-Apache': '.gald3r_sys/licenses/LICENSE_FSL_TEMPLATE.txt',
    'Proprietary': '.gald3r_sys/licenses/LICENSE_PROPRIETARY_TEMPLATE.txt',
}


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


def _load_engine_console() -> Optional[Any]:
    """Try engine gald3r.utils.console (walk up to .gald3r_sys/engine/src)."""
    try:
        from gald3r.utils import console
        return console
    except ImportError:
        pass
    cur = Path(__file__).resolve().parent
    for anc in (cur, *cur.parents):
        cand = anc / '.gald3r_sys' / 'engine' / 'src'
        if (cand / 'gald3r' / 'utils' / '__init__.py').is_file():
            sys.path.insert(0, str(cand))
            try:
                from gald3r.utils import console
                return console
            except ImportError:
                return None
    return None


def _error(msg: str) -> None:
    """Fatal-error reporting (PS1 Write-Error equivalent) — stderr."""
    console = _load_engine_console()
    if console is not None:
        console.err(msg)
    else:
        print(f'Error: {msg}', file=sys.stderr)


def test_member_license_posture(repo: Dict[str, str],
                                controller_root: str,
                                template_map: Dict[str, str]) -> Dict[str, str]:
    """Classify a repo's LICENSE posture against the canonical templates.

    Returns a dict with keys Status / Note / Posture, where Status is one of
    license_match | license_drift | license_missing | license_undeclared |
    license_path_missing.
    """
    posture = repo.get('License', '')
    if not posture:
        return {'Status': 'license_undeclared',
                'Note': 'Manifest entry missing license: key (C-020 violation).',
                'Posture': ''}
    if posture not in template_map:
        # Parity note: the PS1 message contains a literal "$posture" token
        # (the backtick in the source escapes the $); replicated verbatim.
        return {'Status': 'license_drift',
                'Note': ('Unknown posture value $posture '
                         f"(allowed: {', '.join(template_map.keys())})."),
                'Posture': posture}
    if not os.path.exists(repo.get('LocalPath', '')):
        return {'Status': 'license_path_missing',
                'Note': 'Repo path does not exist; cannot inspect LICENSE.',
                'Posture': posture}
    license_file = os.path.join(repo['LocalPath'], 'LICENSE')
    if not os.path.exists(license_file):
        return {'Status': 'license_missing',
                'Note': f'No LICENSE file at {license_file} (C-020: posture is {posture}).',
                'Posture': posture}
    template_file = os.path.join(controller_root, *template_map[posture].split('/'))
    if not os.path.exists(template_file):
        return {'Status': 'license_drift',
                'Note': (f'Canonical template not found at {template_file} '
                         '(controller setup issue).'),
                'Posture': posture}
    with open(license_file, 'r', encoding='utf-8-sig', errors='replace') as fh:
        actual = fh.read().strip()
    with open(template_file, 'r', encoding='utf-8-sig', errors='replace') as fh:
        expected = fh.read().strip()
    if actual == expected:
        return {'Status': 'license_match', 'Note': '', 'Posture': posture}
    # Soft compare: first 400 normalized chars.
    # (PS1 latent bug: it sliced the normalized string by the ORIGINAL length,
    # which could throw; here the slice is bounded by the normalized length.)
    norm_actual = re.sub(r'\s+', ' ', actual)[:400]
    norm_expected = re.sub(r'\s+', ' ', expected)[:400]
    if norm_actual == norm_expected:
        return {'Status': 'license_match',
                'Note': '(matched after whitespace normalization)',
                'Posture': posture}
    return {'Status': 'license_drift',
            'Note': f'LICENSE content does not match canonical {template_map[posture]}.',
            'Posture': posture}


def build_parser() -> argparse.ArgumentParser:
    """argparse surface mirroring the PS1 param() block (both spellings)."""
    parser = argparse.ArgumentParser(
        description=('Validate Workspace-Control member markers and license '
                     'posture (g-rl-36 / C-020).'),
        allow_abbrev=False)
    parser.add_argument('-ManifestPath', '--manifest-path', dest='manifest_path',
                        default='', help='Explicit workspace manifest path.')
    parser.add_argument('-Json', '--json', dest='json', action='store_true',
                        help='Emit JSON instead of text.')
    parser.add_argument('-WarnOnly', '--warn-only', dest='warn_only',
                        action='store_true',
                        help='Report failures but exit 0.')
    parser.add_argument('-SkipLicenseCheck', '--skip-license-check',
                        dest='skip_license_check', action='store_true',
                        help='Skip the C-020 license-posture sweep.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point — mirrors the PS1 main flow and exit codes (0/1/2)."""
    args = build_parser().parse_args(argv)

    guard = _import_guard()
    if guard is None:
        _error('Companion guard helper (check_member_repo_gald3r_guard.py) not found; '
               'cannot parse the workspace manifest.')
        return 2

    # Resolve manifest
    manifest_file: Optional[str] = None
    if args.manifest_path:
        if not os.path.exists(args.manifest_path):
            _error(f'Specified ManifestPath does not exist: {args.manifest_path}')
            return 2
        manifest_file = str(Path(args.manifest_path).resolve())
    else:
        manifest_file = guard.find_workspace_manifest(os.getcwd())

    if not manifest_file:
        _error('No .gald3r/linking/workspace_manifest.yaml found in current dir '
               'or any ancestor.')
        return 2

    try:
        repos = guard.read_workspace_manifest_repositories(manifest_file)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        _error(f'Could not parse workspace manifest: {exc}')
        return 2

    # Controller repo root = directory holding .gald3r/linking/workspace_manifest.yaml
    controller_root = str(Path(manifest_file).parents[2])

    results: List[Dict[str, Any]] = []
    violations_count = 0
    marker_missing_count = 0
    clean_count = 0
    not_created_count = 0
    template_skipped_count = 0
    license_match_count = 0
    license_drift_count = 0
    license_missing_count = 0
    license_undeclared_count = 0

    # License-posture sweep (every repository — including control_project)
    license_results: List[Dict[str, Any]] = []
    if not args.skip_license_check:
        for r in repos:
            if r['WorkspaceRole'] == 'reference_archive':
                license_results.append({
                    'Id': r['Id'],
                    'LocalPath': r['LocalPath'],
                    'Posture': r['License'],
                    'Status': 'reference_archive',
                    'Note': 'Reference archive skipped by C-020 license validation.',
                })
                continue
            check = test_member_license_posture(r, controller_root, LICENSE_TEMPLATE_MAP)
            license_results.append({
                'Id': r['Id'],
                'LocalPath': r['LocalPath'],
                'Posture': check['Posture'],
                'Status': check['Status'],
                'Note': check['Note'],
            })
            if check['Status'] == 'license_match':
                license_match_count += 1
            elif check['Status'] == 'license_drift':
                license_drift_count += 1
            elif check['Status'] == 'license_missing':
                license_missing_count += 1
            elif check['Status'] == 'license_undeclared':
                license_undeclared_count += 1
            # license_path_missing — informational

    allow_cf = {a.casefold() for a in MARKER_ALLOWLIST}
    for r in repos:
        if r['WorkspaceRole'] not in ('controlled_member', 'migration_source'):
            continue
        # Installable template repos intentionally ship full `.gald3r/`
        # scaffolding (g-rl-36 template_directory_exception).
        if re.match(r'^gald3r_template_(slim|full|adv)$', r['Id']):
            template_skipped_count += 1
            continue
        member_path = r['LocalPath']
        result_entry: Dict[str, Any] = {
            'Id': r['Id'],
            'LocalPath': member_path,
            'WorkspaceRole': r['WorkspaceRole'],
            'LifecycleStatus': r['LifecycleStatus'],
            'Status': '',
            'MarkerPreserved': [],
            'Forbidden': [],
            'Notes': [],
        }

        if not os.path.exists(member_path):
            result_entry['Status'] = 'not_yet_created'
            result_entry['Notes'].append(
                f"Path does not exist on disk; lifecycle_status={r['LifecycleStatus']}.")
            not_created_count += 1
            results.append(result_entry)
            continue

        dot_gald3r = os.path.join(member_path, '.gald3r')
        if not os.path.exists(dot_gald3r):
            result_entry['Status'] = 'marker_missing'
            result_entry['Notes'].append(
                '.gald3r/ directory absent. Run bootstrap_member_gald3r_marker.py '
                '-Apply to create the marker.')
            marker_missing_count += 1
            results.append(result_entry)
            continue

        try:
            entries = sorted(Path(dot_gald3r).iterdir())
        except OSError:
            entries = []
        for entry in entries:
            if entry.name.casefold() in allow_cf:
                result_entry['MarkerPreserved'].append(entry.name)
            else:
                result_entry['Forbidden'].append(entry.name)

        if result_entry['Forbidden']:
            result_entry['Status'] = 'has_violations'
            result_entry['Notes'].append(
                f"Run remediate_member_gald3r_marker.py -MemberPath '{member_path}' "
                '(dry-run first, then -Apply).')
            violations_count += 1
        else:
            preserved_cf = {p.casefold() for p in result_entry['MarkerPreserved']}
            missing_marker = [req for req in MARKER_ALLOWLIST
                              if req.casefold() not in preserved_cf]
            if missing_marker:
                result_entry['Status'] = 'marker_incomplete'
                result_entry['Notes'].append(
                    f"Marker pair incomplete: missing {', '.join(missing_marker)}. "
                    'Run bootstrap_member_gald3r_marker.py -Apply to fill in.')
                marker_missing_count += 1
            else:
                result_entry['Status'] = 'clean'
                clean_count += 1
        results.append(result_entry)

    license_fail = (license_drift_count + license_missing_count
                    + license_undeclared_count) > 0

    summary: Dict[str, Any] = {
        'ManifestPath': manifest_file,
        'MemberCount': len(results),
        'Clean': clean_count,
        'HasViolations': violations_count,
        'MarkerMissing': marker_missing_count,
        'NotYetCreated': not_created_count,
        'Members': results,
        'LicenseChecked': not args.skip_license_check,
        'LicenseRepoCount': len(license_results),
        'LicenseMatch': license_match_count,
        'LicenseDrift': license_drift_count,
        'LicenseMissing': license_missing_count,
        'LicenseUndeclared': license_undeclared_count,
        'Licenses': license_results,
        'OverallStatus': 'fail' if (violations_count > 0 or license_fail) else 'pass',
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print('Workspace member marker + license validation')
        print(f'  manifest         : {manifest_file}')
        print(f'  member count     : {len(results)}')
        if template_skipped_count > 0:
            print(f'  template_skipped : {template_skipped_count}  '
                  '(<template_slim>|full|adv carry intentional install .gald3r/)')
        print(f'  clean            : {clean_count}')
        print(f'  has_violations   : {violations_count}')
        print(f'  marker_missing   : {marker_missing_count}')
        print(f'  not_yet_created  : {not_created_count}')
        print('')
        for m in results:
            print(f"[{str(m['Status']).upper()}] {m['Id']}  "
                  f"({m['WorkspaceRole']}/{m['LifecycleStatus']})")
            print(f"  local_path      : {m['LocalPath']}")
            if m['MarkerPreserved']:
                print(f"  marker          : {', '.join(m['MarkerPreserved'])}")
            if m['Forbidden']:
                print(f"  forbidden       : {', '.join(m['Forbidden'])}")
            for n in m['Notes']:
                print(f'  note            : {n}')
            print('')
        if not args.skip_license_check:
            print('License posture (C-020):')
            print(f'  license_match    : {license_match_count}')
            print(f'  license_drift    : {license_drift_count}')
            print(f'  license_missing  : {license_missing_count}')
            print(f'  license_undeclared: {license_undeclared_count}')
            for lic in license_results:
                print(f"[{str(lic['Status']).upper()}] {lic['Id']}  "
                      f"posture={lic['Posture']}")
                if lic['Note']:
                    print(f"  note            : {lic['Note']}")
            print('')
        print(f"Overall: {str(summary['OverallStatus']).upper()}")

    if summary['OverallStatus'] == 'fail':
        return 0 if args.warn_only else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
