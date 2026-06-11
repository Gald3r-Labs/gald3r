"""Temp files and gald3r root resolution — replacements for the
``$env:TEMP`` / walk-up-to-find-.gald3r patterns in the PS1 scripts.

Root discovery delegates to :func:`gald3r.config.find_root` so there is a
single implementation of the walk-up rule (g-rl-04).
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional, Union

from gald3r.config import find_root


def temp_file(prefix: str = "gald3r_", suffix: str = ".tmp") -> Path:
    """Create a temp file in the OS temp dir and return its Path.

    Cross-platform replacement for ``Join-Path $env:TEMP ...``. The file is
    created (so the name is reserved) and left empty; the caller owns cleanup.

    Args:
        prefix: Filename prefix.
        suffix: Filename suffix/extension.
    """
    fd, name = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(fd)
    return Path(name)


def gald3r_root(start: Optional[Union[str, Path]] = None) -> Path:
    """Walk up from `start` (or cwd) to the directory containing ``.gald3r/``.

    Raises:
        FileNotFoundError: When no ``.gald3r/`` exists at or above `start`.
    """
    return find_root(Path(start) if start else None)


def ecosystem_root(start: Optional[Union[str, Path]] = None) -> Path:
    """Return the parent of the gald3r root (the ecosystem folder)."""
    return gald3r_root(start).parent
