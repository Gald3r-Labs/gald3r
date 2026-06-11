#!/usr/bin/env python3
"""Python port of preflight_touch_set.ps1 (T1585).

Human- and CI-friendly touch-set git preflight (T504 / g-rl-33).
Resolves the orchestration repo + optional workspace manifest members and
prints a short GREEN / YELLOW / RED checklist with copy-paste next commands.

Exit codes:
  0 - every resolved git root has a clean working tree (and no config faults)
  1 - one or more roots are dirty (typical g-go coordinator gate failure)
  2 - configuration fault (not a git repo, unknown manifest id, manifest
      missing when required)

Examples:
  python scripts/preflight_touch_set.py
  python scripts/preflight_touch_set.py -WorkspaceRepoId example_desktop,example_app
  python scripts/preflight_touch_set.py -TaskFile .gald3r/tasks/task230_example.md

Engine utils: git invocations go through ``gald3r.utils.process.run_cmd`` and
color gating through ``gald3r.utils.console.color_enabled`` when the engine is
importable (direct import, then walk-up to ``.gald3r_sys/engine/src``); plain
``subprocess`` / isatty fallbacks otherwise.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ANSI = {'GREEN': '\x1b[32m', 'YELLOW': '\x1b[33m', 'RED': '\x1b[31m',
         'INFO': '\x1b[36m'}
_RESET = '\x1b[0m'


def _load_engine_utils() -> Tuple[Optional[Any], Optional[Any]]:
    """Return (console, process) from gald3r.utils, or (None, None).

    Tries the direct import first; on ImportError walks up from this script
    to find ``.gald3r_sys/engine/src`` and inserts it on sys.path.
    """
    try:
        from gald3r.utils import console, process
        return console, process
    except ImportError:
        pass
    cur = Path(__file__).resolve().parent
    for anc in (cur, *cur.parents):
        cand = anc / '.gald3r_sys' / 'engine' / 'src'
        if (cand / 'gald3r' / 'utils' / '__init__.py').is_file():
            sys.path.insert(0, str(cand))
            try:
                from gald3r.utils import console, process
                return console, process
            except ImportError:
                return None, None
    return None, None


_CONSOLE, _PROCESS = _load_engine_utils()
_USE_COLOR = True  # flipped by -NoColor in main()


def _color_enabled() -> bool:
    """True when ANSI color should be emitted (engine gate or isatty)."""
    if not _USE_COLOR:
        return False
    if _CONSOLE is not None:
        return bool(_CONSOLE.color_enabled())
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('FORCE_COLOR'):
        return True
    return bool(getattr(sys.stdout, 'isatty', lambda: False)())


def write_status_line(level: str, message: str) -> None:
    """Print a [GREEN]/[YELLOW]/[RED]/[INFO] checklist line (colored if able)."""
    if _color_enabled():
        print(f'{_ANSI.get(level, _ANSI["INFO"])}[{level}] {message}{_RESET}')
    else:
        print(f'[{level}] {message}')


def _run_git(git_args: List[str]) -> Tuple[int, str]:
    """Run git with the given args; return (returncode, stdout)."""
    if _PROCESS is not None:
        result = _PROCESS.run_cmd(['git', *git_args], check=False)
        return result.returncode, result.stdout
    try:
        proc = subprocess.run(['git', *git_args], capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return 127, ''
    return proc.returncode, proc.stdout or ''


def find_git_root(start_dir: str) -> Optional[str]:
    """Return the git toplevel for `start_dir`, or None when not a repo."""
    p = str(Path(start_dir).resolve())
    rc, out = _run_git(['-C', p, 'rev-parse', '--show-toplevel'])
    if rc != 0:
        return None
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        return None
    return lines[-1].strip()


def find_default_orchestration_root() -> Optional[str]:
    """Git root of the directory above this script (the skill folder)."""
    here = Path(__file__).resolve().parent
    candidate = (here / '..').resolve()
    return find_git_root(str(candidate))


def find_workspace_manifest_path(start_path: str) -> Optional[str]:
    """Walk up from `start_path` to find the workspace manifest."""
    c = start_path
    while c and os.path.exists(c):
        m = os.path.join(c, '.gald3r', 'linking', 'workspace_manifest.yaml')
        if os.path.exists(m):
            return str(Path(m).resolve())
        parent = os.path.dirname(c)
        if not parent or parent == c:
            break
        c = parent
    return None


def read_manifest_repositories(manifest_file: str) -> Dict[str, str]:
    """Parse the manifest repositories block into an id -> local_path map."""
    with open(manifest_file, 'r', encoding='utf-8-sig', newline='') as fh:
        all_text = fh.read()
    m = re.search(r'^repositories:\s*\r?\n(?P<body>.*?)(?=^controlled_members:\s*\r?\n)',
                  all_text, re.M | re.S)
    if not m:
        return {}
    block = m.group('body')

    repo_map: Dict[str, str] = {}
    cur_id: Optional[str] = None
    for line in re.split(r'\r?\n', block):
        m_id = re.match(r'^-\s*id:\s*(.+)$', line)
        if m_id:
            cur_id = m_id.group(1).strip()
            continue
        if cur_id:
            m_lp = re.match(r'^\s+local_path:\s*(.+)$', line)
            if m_lp:
                raw = m_lp.group(1).strip().strip("'").strip('"')
                repo_map[cur_id] = raw
                cur_id = None
    return repo_map


def get_task_frontmatter(path: str) -> str:
    """Return the YAML frontmatter body of a task file ('' when absent)."""
    with open(path, 'r', encoding='utf-8-sig', newline='') as fh:
        raw = fh.read()
    m = re.search(r'^---\s*\r?\n(.+?)\r?\n---', raw, re.S)
    if not m:
        return ''
    return m.group(1)


def expand_yaml_string_list_key(frontmatter: str, key: str) -> List[str]:
    """Expand `key:` as inline ``[a, b]`` or block ``- a`` YAML string list."""
    ids: List[str] = []
    inline = re.search(rf'^{re.escape(key)}:\s*\[(.*?)\]\s*$', frontmatter, re.M)
    if inline:
        for p in inline.group(1).split(','):
            t = p.strip().strip("'").strip('"')
            if t:
                ids.append(t)
        return ids
    lines = re.split(r'\r?\n', frontmatter)
    capture = False
    for line in lines:
        if re.match(rf'^{re.escape(key)}:\s*$', line):
            capture = True
            continue
        if capture:
            m_item = re.match(r'^\s*-\s+(.+)$', line)
            if m_item:
                ids.append(m_item.group(1).strip().strip("'").strip('"'))
                continue
            if re.match(r'^\s*(#|$)', line):
                continue
            if re.match(r'^\s+$', line):
                continue
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*:', line):
                break
    return ids


def get_absolute_paths_from_subsystem_spec(spec_path: str) -> List[str]:
    """Extract absolute (Windows + POSIX) paths from a subsystem spec frontmatter."""
    paths: List[str] = []
    if not os.path.exists(spec_path):
        return paths
    with open(spec_path, 'r', encoding='utf-8-sig', newline='') as fh:
        raw = fh.read()
    m = re.search(r'^---\s*\r?\n(.+?)\r?\n---', raw, re.S)
    if not m:
        return paths
    fm = m.group(1)
    for wm in re.finditer(r'["\']([A-Za-z]:[/\\][^"\'\r\n]+)["\']', fm):
        paths.append(wm.group(1))
    for pm in re.finditer(r'(?:^\s*-\s+|:\s+)["\']?(/[^"\'\s\]\r\n]+)["\']?', fm, re.M):
        v = pm.group(1)
        if v.startswith('/'):
            paths.append(v)
    return paths


def resolve_to_git_root(path_like: str) -> Optional[str]:
    """Expand env vars in `path_like` and return its containing git root."""
    if not path_like:
        return None
    expanded = os.path.expandvars(path_like)
    if not os.path.exists(expanded):
        return None
    if os.path.isdir(expanded):
        directory = str(Path(expanded).resolve())
    else:
        directory = os.path.dirname(str(Path(expanded).resolve()))
    return find_git_root(directory)


def _split_ids(values: List[str]) -> List[str]:
    """Split repeated/comma-separated CLI values into a flat trimmed list."""
    out: List[str] = []
    for v in values:
        for part in v.split(','):
            t = part.strip()
            if t:
                out.append(t)
    return out


def _unique(seq: List[str]) -> List[str]:
    """Order-preserving de-duplication (Select-Object -Unique)."""
    seen: set = set()
    out: List[str] = []
    for s in seq:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def build_parser() -> argparse.ArgumentParser:
    """argparse surface mirroring the PS1 param() block (both spellings)."""
    parser = argparse.ArgumentParser(
        description='Touch-set git preflight checklist (T504 / g-rl-33).',
        allow_abbrev=False)
    parser.add_argument('-OrchestrationRoot', '--orchestration-root',
                        dest='orchestration_root', default='',
                        help='Orchestration git root (auto-discovered when omitted).')
    parser.add_argument('-WorkspaceRepoId', '--workspace-repo-id',
                        '-WorkspaceRepos', '--workspace-repos',
                        dest='workspace_repo_id', action='append', default=[],
                        help='Workspace manifest repository id(s); comma-separable.')
    parser.add_argument('-ExtendedTouchRepoId', '--extended-touch-repo-id',
                        dest='extended_touch_repo_id', action='append', default=[],
                        help='Extended-touch repository id(s); comma-separable.')
    parser.add_argument('-TouchRepoId', '--touch-repo-id', dest='touch_repo_id',
                        action='append', default=[],
                        help='Touch repository id(s); comma-separable.')
    parser.add_argument('-SubsystemName', '--subsystem-name', dest='subsystem_name',
                        action='append', default=[],
                        help='Subsystem spec name(s) to scan; comma-separable.')
    parser.add_argument('-TaskFile', '--task-file', dest='task_file', default='',
                        help='Task file whose frontmatter declares the touch set.')
    parser.add_argument('-ManifestPath', '--manifest-path', dest='manifest_path',
                        default='', help='Explicit workspace manifest path.')
    parser.add_argument('-Json', '--json', dest='json', action='store_true',
                        help='Emit JSON instead of the text checklist.')
    parser.add_argument('-NoColor', '--no-color', dest='no_color',
                        action='store_true', help='Disable ANSI colors.')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point — mirrors the PS1 main flow and exit codes (0/1/2)."""
    global _USE_COLOR
    args = build_parser().parse_args(argv)
    _USE_COLOR = not args.no_color
    preflight_exit = 0

    orch = args.orchestration_root
    if not orch:
        orch = find_default_orchestration_root()
    if not orch:
        write_status_line('RED', 'Could not resolve orchestration git root. Run from '
                          'inside <gald3r_source> or pass -OrchestrationRoot.')
        print('')
        print('Next:')
        print('  cd <path-to-your-controller-repo>')
        print('  git rev-parse --show-toplevel')
        return 2
    if not os.path.exists(orch):
        write_status_line('RED', f'OrchestrationRoot does not exist: {orch}')
        return 2
    orch = str(Path(orch).resolve())

    manifest: Optional[str] = args.manifest_path
    if not manifest:
        manifest = find_workspace_manifest_path(orch)
    elif not os.path.isabs(manifest):
        manifest = os.path.join(orch, manifest.lstrip('/\\'))
    if manifest:
        if not os.path.exists(manifest):
            # PS1 Resolve-Path would terminate here; report it as the
            # documented config-fault exit (2).
            write_status_line('RED', f'Failed to read manifest: {manifest}')
            return 2
        manifest = str(Path(manifest).resolve())

    subsystem_names_from_task: List[str] = []
    repo_ids: List[str] = []
    repo_ids.extend(_split_ids(args.workspace_repo_id))
    repo_ids.extend(_split_ids(args.extended_touch_repo_id))
    repo_ids.extend(_split_ids(args.touch_repo_id))

    if args.task_file:
        tf = args.task_file
        if not os.path.isabs(tf):
            tf = os.path.join(os.getcwd(), tf)
        if not os.path.exists(tf):
            write_status_line('RED', f'TaskFile not found: {tf}')
            return 2
        fm = get_task_frontmatter(tf)
        for k in ('workspace_repos', 'extended_touch_repos', 'touch_repos'):
            repo_ids.extend(expand_yaml_string_list_key(fm, k))
        for sn in expand_yaml_string_list_key(fm, 'subsystems'):
            if sn:
                subsystem_names_from_task.append(sn)

    subsystem_scan_list = _unique(
        [s for s in (_split_ids(args.subsystem_name) + subsystem_names_from_task) if s])
    repo_ids = _unique([r for r in repo_ids if r])

    manifest_map: Dict[str, str] = {}
    if manifest:
        try:
            manifest_map = read_manifest_repositories(manifest)
        except (OSError, UnicodeDecodeError, ValueError):
            write_status_line('RED', f'Failed to read manifest: {manifest}')
            return 2
    elif repo_ids:
        write_status_line('RED', f'workspace_manifest.yaml not found under {orch} but '
                          'repository IDs were supplied. Fix path or create manifest.')
        print('')
        print('Next:')
        print('  python scripts/validate_workspace_members_gald3r.py')
        return 2

    git_roots: Dict[str, str] = {orch: 'orchestration'}

    for rid in repo_ids:
        if rid not in manifest_map:
            write_status_line('RED', f'Unknown repository.id in manifest: {rid}')
            print('')
            print('Next:')
            print('  Open .gald3r/linking/workspace_manifest.yaml and confirm '
                  'repositories[].id, or fix task frontmatter workspace_repos.')
            return 2
        lp = manifest_map[rid]
        if not os.path.exists(lp):
            write_status_line('YELLOW', f'Skip {rid} - local_path not on disk: {lp} '
                              '(planned / not cloned yet)')
            continue
        g = resolve_to_git_root(lp)
        if not g:
            write_status_line('RED', f'Member {rid} path exists but is not inside a '
                              f'git repo: {lp}')
            return 2
        if g not in git_roots:
            git_roots[g] = rid

    for sn in subsystem_scan_list:
        spec = os.path.join(orch, '.gald3r', 'subsystems', f'{sn}.md')
        for abs_path in get_absolute_paths_from_subsystem_spec(spec):
            g = resolve_to_git_root(abs_path)
            if g and g != orch and g not in git_roots:
                git_roots[g] = f'subsystem:{sn}'

    results: List[Dict[str, Any]] = []
    for root, label in git_roots.items():
        rc, out = _run_git(['-C', root, 'status', '--short'])
        if rc != 0:
            results.append({'Root': root, 'Label': label, 'State': 'RED',
                            'Detail': 'git status failed', 'Lines': []})
            preflight_exit = 2
            continue
        lines = [ln for ln in out.splitlines() if ln]
        if not lines:
            results.append({'Root': root, 'Label': label, 'State': 'GREEN',
                            'Detail': 'clean', 'Lines': []})
        else:
            results.append({'Root': root, 'Label': label, 'State': 'RED',
                            'Detail': f'{len(lines)} path(s) dirty', 'Lines': lines})
            if preflight_exit < 1:
                preflight_exit = 1

    if args.json:
        # ConvertTo-Json parity: a single result serializes as an object,
        # multiple results as an array.
        payload: Any = results[0] if len(results) == 1 else results
        print(json.dumps(payload, indent=2))
        return preflight_exit

    print('')
    print(f'=== preflight_touch_set ===  orchestration: {orch}')
    if manifest:
        print(f'                      manifest: {manifest}')
    print('')

    for r in results:
        write_status_line(r['State'], f"{r['Label']}  {r['Root']}")
        line_list: List[str] = r['Lines']
        if r['State'] == 'RED' and line_list:
            for ln in line_list[:8]:
                print(f'      {ln}')
            if len(line_list) > 8:
                more_n = len(line_list) - 8
                print(f'      ... {more_n} more lines')

    print('')
    print('--- Next commands ---')
    if preflight_exit == 0:
        write_status_line('GREEN', 'All listed git roots are clean. Safe to proceed with '
                          'coordinator writes / checkpoint commit (subject to your '
                          'staging allowlist).')
        print('')
        print(f'  git -C "{orch}" status')
    else:
        for r in (x for x in results if x['State'] == 'RED'):
            print('')
            print(f"  # {r['Label']} ({r['Root']})")
            print(f"  git -C \"{r['Root']}\" status")
            print(f"  git -C \"{r['Root']}\" add -- YOUR_PATHS    # then")
            print(f"  git -C \"{r['Root']}\" commit -m \"fix: ...\"")
            print('  # or stash unrelated WIP:')
            print(f"  git -C \"{r['Root']}\" stash push -u -m \"wip: preflight_touch_set\"")
        print('')
        rerun_line = 'python scripts/preflight_touch_set.py'
        if repo_ids:
            rerun_line += ' -WorkspaceRepoId ' + ','.join(repo_ids)
        write_status_line('INFO', f'Re-run:  {rerun_line}')

    print('')
    return preflight_exit


if __name__ == '__main__':
    sys.exit(main())
