#!/usr/bin/env python3
"""Register a global ``gald3r`` command on PATH, cross-OS (T471).

Makes ``gald3r --version`` (and every subcommand) invokable from any directory
by placing a small launcher on a PATH directory:

* Windows  -> writes ``gald3r.cmd`` into ``%LOCALAPPDATA%\\gald3r\\bin`` and adds
  that folder to the **user** PATH (HKCU\\Environment) idempotently.
* macOS/Linux -> writes a ``gald3r`` POSIX shim into ``~/.local/bin`` (created if
  missing) and marks it executable; warns if that folder is not already on PATH.

The launcher invokes the bundled engine via ``uv run`` (preferred, zero global
Python needed) falling back to the current interpreter + ``-m gald3r``. The
engine location is resolved relative to this script's project so the shim keeps
working after the source moves.

This script is **idempotent** and **dry-run capable** (``--dry-run`` /
``-DryRun``). It cannot mutate the live machine PATH inside a test run, so the
dry-run path prints every planned operation and writes nothing. See
``../docs/adr/ADR-016-install-home-and-global-cli.md``.

Usage:
    python install_global_cli.py                 # register for the current user
    python install_global_cli.py --dry-run       # preview only, write nothing
    python install_global_cli.py --uninstall     # remove the launcher + PATH entry
    python install_global_cli.py --bin-dir DIR   # override the launcher directory
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import os
import platform
import stat
import sys
from pathlib import Path
from typing import Optional, Sequence

# -- Engine import bootstrap (mirrors setup_gald3r_project.py) --------------------
# Add the bundled engine src/ to sys.path so we can reuse the single install-home
# resolver instead of duplicating per-OS path logic (g-rl-04).


def _bootstrap_engine_imports() -> None:
    """Add candidate engine src/ directories to sys.path for ``gald3r.home``."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "engine" / "src",                       # installed layout
        script_dir.parent.parent / ".gald3r_sys" / "engine" / "src",
        Path.cwd() / ".gald3r_sys" / "engine" / "src",
    ]
    for cand in candidates:
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


_bootstrap_engine_imports()

try:
    from gald3r import home as _home
except ImportError:  # pure-stdlib fallback — replicate only the bin-dir default
    _home = None


def _default_bin_dir() -> Path:
    """Return the default launcher directory (reusing the install-home resolver)."""
    if _home is not None:
        return _home.resolve_install_home() / "bin"
    # Fallback when the engine is not importable: mirror the per-OS default.
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "gald3r" / "bin"
    return Path.home() / ".local" / "bin"


def _engine_dir() -> Optional[Path]:
    """Locate the bundled engine project dir (the one holding pyproject.toml)."""
    script_dir = Path(__file__).resolve().parent
    for cand in (script_dir.parent / "engine",
                 Path.cwd() / ".gald3r_sys" / "engine"):
        if (cand / "pyproject.toml").is_file():
            return cand
    return None


def _windows_launcher(engine_dir: Optional[Path]) -> str:
    """Return the contents of the Windows ``gald3r.cmd`` launcher."""
    if engine_dir is not None:
        ed = str(engine_dir)
        return (
            "@echo off\r\n"
            "REM gald3r global launcher (T471) -- prefers uv, falls back to python -m\r\n"
            f'set "GALD3R_ENGINE_DIR={ed}"\r\n'
            'where uv >nul 2>nul && (\r\n'
            '  uv run --project "%GALD3R_ENGINE_DIR%" gald3r %*\r\n'
            ') || (\r\n'
            '  python -m gald3r %*\r\n'
            ')\r\n'
        )
    return (
        "@echo off\r\n"
        "REM gald3r global launcher (T471)\r\n"
        "python -m gald3r %*\r\n"
    )


def _posix_launcher(engine_dir: Optional[Path]) -> str:
    """Return the contents of the POSIX ``gald3r`` shim."""
    if engine_dir is not None:
        ed = str(engine_dir)
        return (
            "#!/usr/bin/env bash\n"
            "# gald3r global launcher (T471) -- prefers uv, falls back to python -m\n"
            f'GALD3R_ENGINE_DIR="{ed}"\n'
            'if command -v uv >/dev/null 2>&1; then\n'
            '  exec uv run --project "$GALD3R_ENGINE_DIR" gald3r "$@"\n'
            'else\n'
            '  exec python3 -m gald3r "$@"\n'
            'fi\n'
        )
    return (
        "#!/usr/bin/env bash\n"
        "# gald3r global launcher (T471)\n"
        'exec python3 -m gald3r "$@"\n'
    )


def _path_contains(path_value: str, target: Path) -> bool:
    """Return True when `target` is already an entry in a PATH-style string."""
    want = os.path.normcase(str(target).rstrip("\\/"))
    for entry in path_value.split(os.pathsep):
        if entry and os.path.normcase(entry.rstrip("\\/")) == want:
            return True
    return False


def _install_windows(bin_dir: Path, engine_dir: Optional[Path],
                     dry_run: bool, uninstall: bool) -> int:
    """Install/remove the Windows launcher + user-PATH entry (HKCU\\Environment)."""
    launcher = bin_dir / "gald3r.cmd"
    if uninstall:
        if dry_run:
            print(f"[DRY] would remove launcher: {launcher}")
            print(f"[DRY] would remove '{bin_dir}' from user PATH (HKCU\\Environment)")
            return 0
        if launcher.exists():
            launcher.unlink()
            print(f"  removed launcher: {launcher}")
        _set_windows_user_path(bin_dir, add=False, dry_run=False)
        return 0

    if dry_run:
        print(f"[DRY] would create dir: {bin_dir}")
        print(f"[DRY] would write launcher: {launcher}")
        print(f"[DRY] would add '{bin_dir}' to user PATH (HKCU\\Environment) if absent")
        return 0

    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher.write_text(_windows_launcher(engine_dir), encoding="ascii", newline="")
    print(f"  wrote launcher: {launcher}")
    _set_windows_user_path(bin_dir, add=True, dry_run=False)
    print("  Done. Open a NEW terminal, then: gald3r --version")
    return 0


def _set_windows_user_path(bin_dir: Path, *, add: bool, dry_run: bool) -> None:
    """Add/remove `bin_dir` on the persisted user PATH (idempotent)."""
    if dry_run:
        return
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        print("  (winreg unavailable -- add the folder to PATH manually)")
        return
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            current, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current, kind = "", winreg.REG_EXPAND_SZ
        entries = [e for e in current.split(os.pathsep) if e]
        present = _path_contains(current, bin_dir)
        if add and not present:
            entries.append(str(bin_dir))
            winreg.SetValueEx(key, "Path", 0, kind, os.pathsep.join(entries))
            print(f"  added to user PATH: {bin_dir}")
        elif add and present:
            print(f"  user PATH already contains: {bin_dir}")
        elif not add and present:
            want = os.path.normcase(str(bin_dir).rstrip("\\/"))
            kept = [e for e in entries
                    if os.path.normcase(e.rstrip("\\/")) != want]
            winreg.SetValueEx(key, "Path", 0, kind, os.pathsep.join(kept))
            print(f"  removed from user PATH: {bin_dir}")


def _install_posix(bin_dir: Path, engine_dir: Optional[Path],
                   dry_run: bool, uninstall: bool) -> int:
    """Install/remove the POSIX shim in `bin_dir` (e.g. ~/.local/bin)."""
    shim = bin_dir / "gald3r"
    if uninstall:
        if dry_run:
            print(f"[DRY] would remove shim: {shim}")
            return 0
        if shim.exists():
            shim.unlink()
            print(f"  removed shim: {shim}")
        return 0

    if dry_run:
        print(f"[DRY] would create dir: {bin_dir}")
        print(f"[DRY] would write executable shim: {shim}")
        print(f"[DRY] would warn if '{bin_dir}' is not already on PATH")
        return 0

    bin_dir.mkdir(parents=True, exist_ok=True)
    shim.write_text(_posix_launcher(engine_dir), encoding="utf-8", newline="\n")
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"  wrote shim: {shim} (chmod +x)")
    if not _path_contains(os.environ.get("PATH", ""), bin_dir):
        print(f"  NOTE: '{bin_dir}' is not on PATH. Add to your shell profile:")
        print(f'        export PATH="{bin_dir}:$PATH"')
    print("  Then: gald3r --version")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser (kebab + PascalCase spellings for PS1 parity)."""
    parser = argparse.ArgumentParser(
        prog="install_global_cli.py",
        description="Register a global gald3r command on PATH (cross-OS, T471).",
        allow_abbrev=False,
    )
    parser.add_argument("--dry-run", "-DryRun", dest="dry_run", action="store_true",
                        help="Preview only -- print planned operations, write nothing.")
    parser.add_argument("--uninstall", "-Uninstall", dest="uninstall",
                        action="store_true",
                        help="Remove the launcher and (Windows) the user PATH entry.")
    parser.add_argument("--bin-dir", "-BinDir", dest="bin_dir", default="",
                        help="Override the launcher directory "
                             "(default: <install-home>/bin on Windows, ~/.local/bin on POSIX).")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns a process exit code (0 ok / 1 error)."""
    args = build_parser().parse_args(argv)
    bin_dir = (Path(args.bin_dir).expanduser() if args.bin_dir
               else _default_bin_dir())
    engine_dir = _engine_dir()

    print(f"  gald3r global CLI {'uninstall' if args.uninstall else 'install'}"
          f"{' (DRY RUN)' if args.dry_run else ''}")
    print(f"  launcher dir : {bin_dir}")
    print(f"  engine dir   : {engine_dir or '(not found -- launcher uses python -m gald3r)'}")

    if platform.system() == "Windows":
        return _install_windows(bin_dir, engine_dir, args.dry_run, args.uninstall)
    return _install_posix(bin_dir, engine_dir, args.dry_run, args.uninstall)


if __name__ == "__main__":
    sys.exit(main())
