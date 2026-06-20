#!/usr/bin/env python3
"""Shared bootstrap for gald3r Python hooks (T1584).

Every ported hook imports this module first. It provides:
- project_root(): locate the gald3r project root from the hook's own location
- bootstrap_engine(): make `gald3r.utils` importable by adding the bundled
  engine source to sys.path when the engine is not installed
- read_stdin_json(): parse the hook payload JSON that Claude Code / Cursor
  pipe to hook commands on stdin (returns {} when absent/malformed)

Hooks must never crash the host session: callers wrap main() and exit 0 on
unexpected errors unless the hook's documented purpose is to block.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict


def project_root() -> Path:
    """Walk up from this file to the directory containing `.gald3r/` or
    `.gald3r_sys/` (hooks live at `<root>/.claude/hooks/` or a platform
    equivalent). Falls back to the current working directory."""
    here = Path(__file__).resolve()
    for d in here.parents:
        if (d / ".gald3r").is_dir() or (d / ".gald3r_sys").is_dir():
            return d
    return Path.cwd()


def bootstrap_engine() -> bool:
    """Make the `gald3r` package importable.

    Tries the installed package first, then falls back to the engine source
    bundled at `<root>/.gald3r_sys/engine/src`. Returns True when the import
    works — hooks degrade gracefully (pure-stdlib path) when it does not.
    """
    try:
        import gald3r  # noqa: F401

        return True
    except ImportError:
        pass
    engine_src = project_root() / ".gald3r_sys" / "engine" / "src"
    if engine_src.is_dir():
        sys.path.insert(0, str(engine_src))
        try:
            import gald3r  # noqa: F401

            return True
        except ImportError:
            return False
    return False


def read_stdin_json() -> Dict[str, Any]:
    """Read the hook payload JSON from stdin.

    Claude Code and Cursor pipe a JSON object describing the event to hook
    commands. Returns {} for an empty/absent/malformed payload so hooks can
    run standalone (manual invocation, tests) without special-casing.
    """
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
