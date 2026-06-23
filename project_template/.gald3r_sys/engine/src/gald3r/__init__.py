"""gald3r — file-first agent OS engine (tier-gated, Mode A pure core).

MVP: the `tasks` vertical slice. The engine reads/writes the existing `.gald3r/`
markdown formats so it is drop-in compatible with the markdown-driven system that
Cursor / Claude Code / OpenCode / etc. already use. It makes no LLM calls and
assumes nothing about its caller — the same core is reused by the CLI, the MCP
server, and (later) the HTTP backend and the Mode-B harness.
"""
from __future__ import annotations

from importlib import metadata as _metadata

# BUG-175: derive the version from the INSTALLED package metadata (the build stamps
# pyproject.toml's `version`), so `gald3r --version` is never a stale hardcoded literal.
# Falls back to the shipped `.gald3r_sys/VERSION` runtime marker, then a sentinel, when
# the package isn't installed (a raw source checkout).
try:
    __version__ = _metadata.version("gald3r")
except _metadata.PackageNotFoundError:  # pragma: no cover - raw source checkout
    from pathlib import Path as _Path

    __version__ = "0.0.0+source"
    for _anc in _Path(__file__).resolve().parents:
        if _anc.name == ".gald3r_sys":
            _vf = _anc / "VERSION"
            if _vf.is_file():
                __version__ = _vf.read_text(encoding="utf-8").strip() or __version__
            break

from gald3r.core import Gald3r

__all__ = ["Gald3r", "__version__"]
