"""gald3r — file-first agent OS engine (tier-gated, Mode A pure core).

MVP: the `tasks` vertical slice. The engine reads/writes the existing `.gald3r/`
markdown formats so it is drop-in compatible with the markdown-driven system that
Cursor / Claude Code / OpenCode / etc. already use. It makes no LLM calls and
assumes nothing about its caller — the same core is reused by the CLI, the MCP
server, and (later) the HTTP backend and the Mode-B harness.
"""
from __future__ import annotations

__version__ = "0.1.0"

from gald3r.core import Gald3r

__all__ = ["Gald3r", "__version__"]
