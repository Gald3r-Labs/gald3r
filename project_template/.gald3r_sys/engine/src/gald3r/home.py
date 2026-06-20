"""Centralized gald3r install home + USB-portable resolution (T471).

The *install home* is the single OS-appropriate folder that holds gald3r's
shared, cross-product state: ``settings/``, ``logs/``, ``gald3r_vault/`` and a
``VERSION`` manifest file. It is distinct from a project's ``.gald3r/`` (which is
per-repo, resolved by :func:`gald3r.config.find_root`); the install home is
machine-wide (or medium-wide, when portable) and shared by gald3r_agent, the
throne, and any other product.

This module is the SINGLE resolution point for that path — every product calls
:func:`resolve_install_home`. Resolution precedence (highest wins):

    1. explicit ``override`` argument (tests / embedding callers)
    2. portable mode — ``portable=True`` arg, ``GALD3R_PORTABLE`` truthy env, or
       an explicit ``portable_root`` — resolves to ``<root>/gald3r`` co-located
       on the medium (no writes outside it)
    3. ``GALD3R_HOME`` environment variable
    4. the per-OS default (``%LOCALAPPDATA%\\gald3r`` on Windows,
       ``$XDG_DATA_HOME/gald3r`` -> ``~/.local/share/gald3r`` on Linux,
       ``~/Library/Application Support/gald3r`` on macOS)

It mirrors the override-then-env-then-default pattern that
:mod:`gald3r_forge.paths` (T412) established for the build-output workspace, and
is pure stdlib (``os`` / ``pathlib`` / ``platform``) so it runs anywhere uv puts
a Python, with NO hardcoded drive letters or path separators. See
``ADR-016-install-home-and-global-cli.md`` for the recorded decision.
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Optional, Union

#: Env var that overrides the default install-home location (a single path).
HOME_ENV_VAR = "GALD3R_HOME"

#: Env var (truthy: 1/true/yes/on) that forces USB-portable mode.
PORTABLE_ENV_VAR = "GALD3R_PORTABLE"

#: Env var that, when set, names the portable medium root that portable mode
#: relocates the home onto (e.g. a removable drive). Falls back to the install
#: location of the running engine when unset (see _portable_medium_root).
PORTABLE_ROOT_ENV_VAR = "GALD3R_PORTABLE_ROOT"

#: The folder name created on the OS-default parent or the portable medium.
HOME_DIR_NAME = "gald3r"

#: Subdirectories that make up the install-home layout. Kept as plain names so
#: callers reference them through :func:`subdir` rather than hardcoding strings.
SETTINGS_DIR = "settings"
LOGS_DIR = "logs"
VAULT_DIR = "gald3r_vault"

#: The version/manifest file at the root of the install home.
VERSION_FILE = "VERSION"

_TRUTHY = {"1", "true", "yes", "on"}


def _is_truthy(value: Optional[str]) -> bool:
    """Return True when an env-var string represents an enabled flag."""
    return bool(value) and value.strip().casefold() in _TRUTHY


def _os_default_home() -> Path:
    """Return the per-OS default install-home path (no env/portable overrides).

    Windows: ``%LOCALAPPDATA%\\gald3r`` (fallback ``~/AppData/Local/gald3r``).
    macOS:   ``~/Library/Application Support/gald3r``.
    Linux/other: ``$XDG_DATA_HOME/gald3r`` (fallback ``~/.local/share/gald3r``).
    """
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", "").strip()
        parent = Path(base) if base else Path.home() / "AppData" / "Local"
    elif system == "Darwin":
        parent = Path.home() / "Library" / "Application Support"
    else:  # Linux and any other POSIX
        xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        parent = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return parent / HOME_DIR_NAME


def _portable_medium_root() -> Path:
    """Return the medium root that portable mode co-locates the home onto.

    Precedence: ``GALD3R_PORTABLE_ROOT`` env var -> the anchor (drive root /
    filesystem root) of the directory that contains the running engine package.
    Using the engine's own anchor keeps everything on the same medium the
    portable install was launched from, with no hardcoded drive letter.
    """
    explicit = os.environ.get(PORTABLE_ROOT_ENV_VAR, "").strip()
    if explicit:
        return Path(explicit)
    # Anchor of this package's location = the medium it lives on (e.g. "E:\\" on
    # Windows or "/media/usb" mountpoint's filesystem root on POSIX).
    here = Path(__file__).resolve()
    return Path(here.anchor) if here.anchor else here.parent


def resolve_install_home(
    override: Optional[Union[str, Path]] = None,
    *,
    portable: Optional[bool] = None,
    portable_root: Optional[Union[str, Path]] = None,
) -> Path:
    """Resolve the centralized gald3r install-home directory (T471).

    This is the one function every product uses to find the shared home. It does
    not create the directory — call :func:`ensure_install_home` for that.

    Args:
        override: Explicit path; wins over everything (tests / embedding).
        portable: Tri-state portable toggle. ``True`` forces portable mode,
            ``False`` forces it off (ignoring the env var), ``None`` (default)
            consults the ``GALD3R_PORTABLE`` env var.
        portable_root: Explicit medium root for portable mode; overrides the
            ``GALD3R_PORTABLE_ROOT`` env var and the auto-detected medium.

    Returns:
        The resolved install-home root (absolute, not necessarily existing).
        Resolution order: ``override`` -> portable -> ``GALD3R_HOME`` -> per-OS
        default.
    """
    if override:
        return Path(override).expanduser().resolve()

    use_portable = portable if portable is not None else _is_truthy(
        os.environ.get(PORTABLE_ENV_VAR)
    )
    if use_portable or portable_root:
        root = (
            Path(portable_root)
            if portable_root
            else _portable_medium_root()
        )
        return (root / HOME_DIR_NAME).expanduser().resolve()

    env_value = os.environ.get(HOME_ENV_VAR, "").strip()
    if env_value:
        return Path(env_value).expanduser().resolve()

    return _os_default_home().expanduser().resolve()


def resolve_home(env: dict, platform_name: str) -> Path:
    """Resolve the per-user gald3r home from an injected env + platform (T557).

    This is the pure, side-effect-free resolver that templates, Throne, and Agent
    all share so they agree on one location. Unlike :func:`resolve_install_home`
    (the machine/medium install home, T471), this is the per-*user* config home and
    uses the simpler T530 precedence:

        1. ``GALD3R_HOME`` (in ``env``) wins, if set & non-blank.
        2. else the per-OS default:
           * Windows: ``%LOCALAPPDATA%\\gald3r`` (fallback ``~/AppData/Local/gald3r``
             when ``LOCALAPPDATA`` is unset/blank).
           * Linux / macOS / other: ``~/.config/gald3r``.

    Args:
        env: An environment mapping (e.g. ``os.environ`` or a test dict). Injected
            so the function is pure and trivially testable.
        platform_name: A platform string in the ``platform.system()`` vocabulary
            (``"Windows"`` / ``"Darwin"`` / ``"Linux"`` / other).

    Returns:
        The resolved per-user home path (absolute, not necessarily existing). This
        function does NOT create the directory.
    """
    override = (env.get(HOME_ENV_VAR) or "").strip()
    if override:
        return Path(override).expanduser().resolve()

    if platform_name == "Windows":
        local_appdata = (env.get("LOCALAPPDATA") or "").strip()
        parent = Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local"
        return (parent / HOME_DIR_NAME).expanduser().resolve()

    # Linux, macOS (Darwin), and any other POSIX → XDG-style per-user config dir.
    return (Path.home() / ".config" / HOME_DIR_NAME).expanduser().resolve()


def subdir(name: str, *, home: Optional[Path] = None, **kwargs) -> Path:
    """Return a subpath inside the install home (e.g. ``settings``/``logs``).

    Args:
        name: Subdirectory name (use the ``*_DIR`` constants).
        home: Pre-resolved install home; resolved via :func:`resolve_install_home`
            (passing through ``kwargs``) when omitted.
        **kwargs: Forwarded to :func:`resolve_install_home` when ``home`` is None.
    """
    base = home if home is not None else resolve_install_home(**kwargs)
    return base / name


def ensure_install_home(
    override: Optional[Union[str, Path]] = None,
    *,
    portable: Optional[bool] = None,
    portable_root: Optional[Union[str, Path]] = None,
) -> Path:
    """Create the install home + its standard layout if missing; return its path.

    Creates ``<home>/settings``, ``<home>/logs``, ``<home>/gald3r_vault`` and
    writes a ``VERSION`` manifest stamped with the engine version when absent.
    Idempotent — existing files are left untouched. Arguments mirror
    :func:`resolve_install_home`.
    """
    home = resolve_install_home(
        override, portable=portable, portable_root=portable_root
    )
    for sub in (SETTINGS_DIR, LOGS_DIR, VAULT_DIR):
        (home / sub).mkdir(parents=True, exist_ok=True)
    version_path = home / VERSION_FILE
    if not version_path.exists():
        from gald3r import __version__

        version_path.write_text(f"{__version__}\n", encoding="utf-8", newline="\n")
    return home
