"""Resolve how to invoke the gald3r engine — the HYBRID delivery model (T1642, né T1622).

The proprietary engine ships as a **Nuitka-compiled binary**, not readable
source (that is the IP leak-stop: an install no longer carries
``.gald3r_sys/engine/src`` in the clear). Skills and hooks must therefore stop
running ``uv run --project .gald3r_sys/engine gald3r`` against source and instead
call the resolved engine command returned here.

This module is deliberately **zero-IP** — it is just PATH/filesystem lookup, so
it ships readable alongside the editable skill prompts. It carries no engine
logic itself.

Resolution order (first hit wins), owner-chosen HYBRID = PATH → bundled → dev:
    1. ``GALD3R_BIN`` env var — an explicit absolute path to the binary (escape
       hatch / CI override).
    2. A global ``gald3r`` on PATH — the launcher ``install_global_cli.py``
       (T471) registers (since T1645 it execs the compiled ``gald3r-agent``
       binary that ``g-install-agent`` / ``gald3r install agent`` (T1615)
       downloads into the gald3r home ``bin/``), or a ``uv tool install`` /
       OS installer placed. This is the primary path for a normal install.
    3. A **bundled** binary next to the project:
       ``<project>/.gald3r_sys/bin/gald3r[.exe]`` — the self-contained fallback
       so an install works even when nothing is on PATH.
    4. **Dev fallback** — only if the engine SOURCE is present
       (``.gald3r_sys/engine/pyproject.toml`` exists): ``uv run --project
       <engine> gald3r``. This never fires in a shipped (binary-only) install; it
       keeps this dev repo (where source IS present) working unchanged.
    5. Otherwise raise :class:`EngineNotFoundError` with install guidance.

The return value is a **command prefix** (``list[str]``) — callers append their
subcommand, e.g. ``resolve_engine_cmd(root) + ["task", "list"]``.
"""

# @subsystems: WORKSPACE_COORDINATION, PLATFORM_INTEGRATION

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

__all__ = ["EngineNotFoundError", "resolve_engine_cmd", "find_project_root"]

#: Windows executable suffix (empty on POSIX).
_EXE = ".exe" if os.name == "nt" else ""


class EngineNotFoundError(RuntimeError):
    """No gald3r engine could be resolved (no PATH binary, no bundle, no source)."""


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk up from ``start`` (or CWD) to the nearest dir containing ``.gald3r_sys``."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".gald3r_sys").is_dir():
            return candidate
    return None


def _bundled_binary(project_root: Path) -> Path | None:
    """The self-contained fallback binary, if present."""
    candidate = project_root / ".gald3r_sys" / "bin" / f"gald3r{_EXE}"
    return candidate if candidate.is_file() else None


def _engine_source(project_root: Path) -> Path | None:
    """The engine SOURCE project (dev only) — present in this repo, absent in a ship."""
    engine = project_root / ".gald3r_sys" / "engine"
    return engine if (engine / "pyproject.toml").is_file() else None


def resolve_engine_cmd(
    project_root: Path | None = None,
    *,
    allow_dev_source: bool = True,
) -> list[str]:
    """Return the command prefix that invokes the gald3r engine (HYBRID order).

    Args:
        project_root: Project whose ``.gald3r_sys`` to resolve against. Defaults
            to walking up from CWD.
        allow_dev_source: When ``False``, skip the ``uv run --project`` source
            fallback even if source is present — use to PROVE a binary-only ship
            resolves without touching source (test/verification).

    Returns:
        A ``list[str]`` command prefix (e.g. ``["gald3r"]`` or
        ``["/path/.gald3r_sys/bin/gald3r.exe"]``).

    Raises:
        EngineNotFoundError: nothing resolvable.
    """
    root = project_root or find_project_root()

    # 1. Explicit override.
    override = os.environ.get("GALD3R_BIN", "").strip()
    if override and Path(override).is_file():
        return [override]

    # 2. Global binary on PATH.
    on_path = shutil.which("gald3r")
    if on_path:
        return [on_path]

    # 3. Bundled fallback next to the project.
    if root is not None:
        bundled = _bundled_binary(root)
        if bundled is not None:
            return [str(bundled)]

        # 4. Dev fallback — engine source present (this repo; never a ship).
        if allow_dev_source:
            engine = _engine_source(root)
            if engine is not None:
                return ["uv", "run", "--project", str(engine), "gald3r"]

    raise EngineNotFoundError(
        "gald3r engine not found. Install the compiled Gald3r Agent binary: "
        "run the `g-install-agent` command (`/g-install-agent` in Claude Code, "
        "`@g-install-agent` in Cursor) — or `gald3r install agent` from any "
        "machine that already has the binary. It downloads the signed binary + "
        "SHA-256 sidecar from the public Gald3r-Labs/gald3r_agent GitHub "
        "releases into the gald3r home bin/ (kept on PATH by "
        "install_global_cli.py). Alternatively drop a binary at "
        "`.gald3r_sys/bin/gald3r` or set GALD3R_BIN to its absolute path. "
        "Engine SOURCE does not ship with installs (T1645)."
    )


if __name__ == "__main__":  # pragma: no cover - manual smoke
    try:
        print(" ".join(resolve_engine_cmd()))
    except EngineNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
