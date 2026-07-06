#!/usr/bin/env python3
"""Stamp the Python interpreter into installed hook trigger configs (T1651, BUG-207).

gald3r hook trigger configs (Claude ``settings.json``, Cursor ``hooks.json``,
and the per-platform equivalents) ship with the bare ``python`` interpreter
token — the Windows-safe default. Stock modern Linux (Debian 12+, Ubuntu,
Fedora, RHEL 9+) ships **only** ``python3``; Windows conversely usually lacks
``python3`` (or worse, carries the broken Microsoft Store alias stub). Hook
command strings are executed by each IDE's hook runner (``sh`` on Linux/macOS,
``cmd``/PowerShell on Windows), so no single hardcoded name works everywhere,
and an inline ``python3 X || python X`` fallback is unacceptable: ``||``
conflates "interpreter missing" with a legitimate non-zero hook exit (blocking
guards exit 2 — the verdict would be lost and the hook re-run).

This script resolves the interpreter ONCE, at install time, on the machine the
project is installed onto, and rewrites the leading ``python`` token of every
hook ``"command"`` string in the known hook-config files:

- On Windows: no-op (the shipped ``python`` token is already correct).
- On POSIX: rewrites to ``python3`` when it is on PATH (kept at ``python``
  when only ``python`` exists — e.g. a ``python-is-python3`` box).

``setup_gald3r_project.py`` runs this automatically after copying the template
layers. It is safe and idempotent to re-run at any time — e.g. after cloning a
project that was installed on the other OS family::

    python3 .gald3r_sys/scripts/stamp_python_interpreter.py --project-root .

Only the leading interpreter token of ``"command"`` JSON string values is
touched; script paths, arguments, ``${CLAUDE_PROJECT_DIR}`` / ``${PLUGIN_ROOT}``
variables, and Windsurf's Windows-only ``"powershell"`` command variants are
never modified.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

#: Hook trigger configs that may carry bare-``python`` command strings, as
#: project-root-relative paths. Every platform overlay that registers Python
#: hooks via a JSON command string MUST be listed here (a maintainer test in
#: gald3r_templates_dev pins this list against the shipped trees). Windsurf is
#: listed for completeness although its ``command`` values already ship as
#: ``python3`` (its Windows variant lives under the ``powershell`` key, which
#: this script never touches).
KNOWN_HOOK_CONFIGS: Tuple[str, ...] = (
    ".claude/settings.json",
    ".cursor/hooks.json",
    ".agent/hooks.json",
    ".gemini/settings.json",
    ".qwen/settings.json",
    ".openhands/hooks.json",
    ".kiro/agents/gald3r.json",
    ".agents/hooks.json",
    ".agents/plugins/gald3r-hooks/hooks/hooks.json",
    ".github/hooks/gald3r-hooks.json",
    ".codex/hooks.json",
    ".windsurf/hooks.json",
)

#: Leading bare-``python`` interpreter token of a ``"command"`` string value.
#: Deliberately anchored on the ``"command"`` key so Windsurf's ``"powershell"``
#: values and arbitrary JSON strings are never rewritten, and deliberately
#: requiring trailing whitespace so ``python3`` (already stamped) never
#: re-matches — the rewrite is idempotent by construction.
_COMMAND_TOKEN = re.compile(r'("command"\s*:\s*")python(?=\s)')


def resolve_interpreter(is_windows: Optional[bool] = None) -> Optional[str]:
    """Resolve the interpreter token hook commands should launch with.

    Args:
        is_windows: Platform override for tests; defaults to the host OS.

    Returns:
        ``None`` on Windows (the shipped ``python`` token is already correct —
        nothing to stamp), otherwise the POSIX interpreter name: ``python3``
        when present on PATH, ``python`` when only it exists, and ``python3``
        as the forward-looking default when neither resolves (hooks cannot run
        either way; stamp the name every modern distro ships).
    """
    if is_windows is None:
        is_windows = os.name == "nt"
    if is_windows:
        return None
    if shutil.which("python3"):
        return "python3"
    if shutil.which("python"):
        return "python"
    return "python3"


def stamp_file(path: Path, interpreter: str, dry_run: bool = False) -> int:
    """Rewrite the leading interpreter token of every command string in one file.

    Args:
        path: Hook config file to stamp.
        interpreter: Interpreter token to stamp in (e.g. ``python3``).
        dry_run: When True nothing is written.

    Returns:
        Number of command strings rewritten (0 when already stamped).
    """
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return 0
    new_text, count = _COMMAND_TOKEN.subn(r"\g<1>" + interpreter, text)
    if count and interpreter == "python":
        # Replacing `python` with `python` — nothing actually changes.
        return 0
    if count and not dry_run:
        path.write_bytes(new_text.encode("utf-8"))
    return count


def stamp_project(
    project_root: Path,
    interpreter: Optional[str] = None,
    is_windows: Optional[bool] = None,
    dry_run: bool = False,
) -> List[Tuple[Path, int]]:
    """Stamp every known hook config under ``project_root``.

    Args:
        project_root: Installed project root.
        interpreter: Explicit interpreter token; resolved from the host
            (see :func:`resolve_interpreter`) when omitted.
        is_windows: Platform override for tests.
        dry_run: When True nothing is written.

    Returns:
        List of ``(config_path, replacements)`` for configs that exist and had
        (or would have) command strings rewritten. Empty on Windows.
    """
    if interpreter is None:
        interpreter = resolve_interpreter(is_windows=is_windows)
    if interpreter is None or interpreter == "python":
        return []
    results: List[Tuple[Path, int]] = []
    for rel in KNOWN_HOOK_CONFIGS:
        path = project_root / Path(rel)
        if not path.is_file():
            continue
        count = stamp_file(path, interpreter, dry_run=dry_run)
        if count:
            results.append((path, count))
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stamp_python_interpreter.py",
        description=(
            "Rewrite the leading `python` token of hook command strings to the "
            "interpreter that actually exists on this machine (BUG-207)."
        ),
    )
    parser.add_argument(
        "--project-root", default=".",
        help="Installed project root (default: current directory).",
    )
    parser.add_argument(
        "--interpreter", default=None,
        help="Explicit interpreter token to stamp (default: auto-resolve).",
    )
    parser.add_argument(
        "--platform", choices=("auto", "posix", "windows"), default="auto",
        help="Platform override (default: auto-detect the host OS).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would be rewritten without writing anything.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.is_dir():
        print(f"stamp_python_interpreter: not a directory: {root}",
              file=sys.stderr)
        return 2
    is_windows: Optional[bool]
    if args.platform == "auto":
        is_windows = None
    else:
        is_windows = args.platform == "windows"
    results = stamp_project(
        root, interpreter=args.interpreter, is_windows=is_windows,
        dry_run=args.dry_run,
    )
    prefix = "[DRY] would stamp" if args.dry_run else "stamped"
    if not results:
        print("stamp_python_interpreter: nothing to stamp "
              "(Windows host, already stamped, or no hook configs present).")
        return 0
    for path, count in results:
        try:
            shown = path.relative_to(root)
        except ValueError:
            shown = path
        print(f"  {prefix} {count:3d} command string(s): {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
