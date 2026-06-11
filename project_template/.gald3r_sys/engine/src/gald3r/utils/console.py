"""Colored console output — cross-platform replacement for
``Write-Host -ForegroundColor`` patterns in the PS1 scripts.

Respects the ``NO_COLOR`` convention (https://no-color.org) and ``FORCE_COLOR``.
On Windows 10+ ANSI is enabled via colorama when available, with a raw
VT-activation fallback when it is not installed.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import os
import sys
from typing import Optional, TextIO

_RESET = "\x1b[0m"
_STYLE = {
    "info": ("\x1b[36m", "[INFO]"),
    "ok": ("\x1b[32m", "[ OK ]"),
    "warn": ("\x1b[33m", "[WARN]"),
    "err": ("\x1b[31m", "[ERR ]"),
}
_windows_ansi_ready = False


def _enable_windows_ansi() -> None:
    """Enable ANSI escape processing on Windows consoles (one-shot)."""
    global _windows_ansi_ready
    if _windows_ansi_ready or os.name != "nt":
        return
    try:
        import colorama  # optional dependency — degrade gracefully

        colorama.just_fix_windows_console()
    except ImportError:
        # Spawning any shell flips the console into VT mode on Win10+.
        os.system("")
    _windows_ansi_ready = True


def color_enabled(stream: Optional[TextIO] = None) -> bool:
    """Return True when colored output should be emitted to `stream`.

    Order of precedence: ``NO_COLOR`` set → False; ``FORCE_COLOR`` set → True;
    otherwise True only when the stream is a TTY.

    Args:
        stream: Target stream; defaults to stdout.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    stream = stream or sys.stdout
    return bool(getattr(stream, "isatty", lambda: False)())


def _emit(level: str, msg: str, stream: Optional[TextIO] = None) -> None:
    stream = stream or (sys.stderr if level == "err" else sys.stdout)
    color, prefix = _STYLE[level]
    if color_enabled(stream):
        _enable_windows_ansi()
        print(f"{color}{prefix}{_RESET} {msg}", file=stream)
    else:
        print(f"{prefix} {msg}", file=stream)


def info(msg: str) -> None:
    """Print an informational message (cyan)."""
    _emit("info", msg)


def ok(msg: str) -> None:
    """Print a success message (green)."""
    _emit("ok", msg)


def warn(msg: str) -> None:
    """Print a warning message (yellow)."""
    _emit("warn", msg)


def err(msg: str) -> None:
    """Print an error message (red) to stderr."""
    _emit("err", msg)
