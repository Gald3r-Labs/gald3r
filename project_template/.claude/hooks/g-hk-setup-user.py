#!/usr/bin/env python3
"""Python port of g-hk-setup-user.ps1 (T1584); reconciled onto the unified home (T627).

Run this ONCE from a terminal to set your gald3r user identity. Your user ID is
stored in the ONE unified per-user identity record managed by T530/T531 —
``<gald3r-home>/user_config.json`` (``%LOCALAPPDATA%/gald3r`` on Windows,
``~/.config/gald3r`` on POSIX) — and used across all AI sessions (Cursor, Claude
Code, Gemini) on this machine. There is no longer a second ``~/.gald3r`` identity
file (T627 retired that divergent path; any pre-existing one is migrated in, not
regenerated).

Interactive: suggests a user ID from git global email, the Cursor cached email
(state.vscdb), and the OS username, then prompts via input() with a [1] default
hint. Identity provisioning (id generation, idempotent create-or-read, never
clobbering an existing record) is delegated to ``gald3r.user_config`` /
``gald3r.home`` (T530/T531) — this hook does NOT re-derive the home path or
regenerate ids. The extra setup fields (mcp_url, platform, setup_completed,
setup_date, created_by) are written to a SEPARATE ``setup_meta.json`` sidecar in
the same home — they are setup metadata, not a competing identity record.

Usage:
  python .claude/hooks/g-hk-setup-user.py
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import datetime
import json
import os
import platform as _platform
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

#: Setup metadata filename (sidecar to the identity record, NOT the identity).
SETUP_META_FILENAME = "setup_meta.json"

#: Legacy identity file retired by T627. Only read once, to migrate ids forward.
LEGACY_CONFIG_PATH = Path.home() / ".gald3r" / "user_config.json"

#: Breadcrumb dropped next to a migrated legacy file so the migration is one-time.
LEGACY_MIGRATED_BREADCRUMB = ".migrated-to-unified-home"


def _is_generated_id(value: str) -> bool:
    """True when ``value`` looks like an engine-generated id (``uuid.uuid4().hex``).

    Generated ids are 32 lowercase hex chars (see ``gald3r.user_config.ensure``). A
    deliberate, human-chosen user_id (email / nickname / username) does not match,
    so this distinguishes a freshly-provisioned placeholder from a real identity —
    we only overwrite the former (clobber-safe).
    """
    return len(value) == 32 and all(c in "0123456789abcdef" for c in value)


def _git_global_email() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "--global", "user.email"],
            capture_output=True, text=True, timeout=10,
        )
        return (result.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _cursor_cached_email() -> str:
    """Read the Cursor cached login email from its state.vscdb (sqlite)."""
    try:
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            return ""
        vsc_db = Path(appdata) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
        if not vsc_db.is_file():
            return ""
        import sqlite3

        conn = sqlite3.connect(str(vsc_db))
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT value FROM ItemTable WHERE key = 'cursorAuth/cachedEmail'"
            )
            row = cur.fetchone()
            return (row[0] if row else "").strip()
        finally:
            conn.close()
    except Exception:
        return ""


def _os_username() -> str:
    username = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if username:
        return username
    try:
        import getpass

        return getpass.getuser()
    except Exception:
        return ""


def _machine_id() -> str:
    """Stable machine ID — Windows registry MachineGuid; random GUID elsewhere."""
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography"
            ) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                if value:
                    return str(value)
        except OSError:
            pass
    return str(uuid.uuid4())


def _migrate_legacy_identity(user_config, config_path: Path) -> None:
    """One-time fold a pre-existing ``~/.gald3r/user_config.json`` into the unified home.

    Preserves the legacy ``user_id`` / ``machine_id`` (never regenerates them) by
    seeding the unified record from them BEFORE :func:`ensure` would create fresh
    ids. Runs only when the unified record does not yet exist and a legacy file is
    present + readable; honors the never-clobber invariant (does nothing if the
    unified record already exists). Drops a breadcrumb so it never repeats, and
    leaves the legacy file in place (non-destructive).
    """
    if config_path.exists():
        return  # unified record already present — never clobber
    if not LEGACY_CONFIG_PATH.is_file():
        return
    try:
        legacy = json.loads(LEGACY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError, ValueError):
        return  # unreadable legacy file → leave it; ensure() will create fresh
    if not isinstance(legacy, dict):
        return
    legacy_user = str(legacy.get("user_id") or "").strip()
    legacy_machine = str(legacy.get("machine_id") or "").strip()
    if not legacy_user or not legacy_machine:
        return  # nothing identity-bearing to carry forward
    # Seed the unified record with the EXACT legacy ids (no regeneration).
    seeded = user_config.UserConfig(
        user_id=legacy_user,
        machine_id=legacy_machine,
        display_name=str(legacy.get("display_name") or ""),
        email=legacy.get("email"),
    )
    user_config.write(config_path, seeded)
    try:
        (LEGACY_CONFIG_PATH.parent / LEGACY_MIGRATED_BREADCRUMB).write_text(
            f"migrated to {config_path} on "
            f"{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}\n",
            encoding="utf-8",
        )
    except OSError:
        pass  # breadcrumb is best-effort; migration already succeeded


def _write_setup_meta(home_dir: Path) -> Path:
    """Write the non-identity setup metadata sidecar (T627 AC2).

    These fields (mcp_url, platform, setup_completed, setup_date, created_by) were
    formerly co-mingled with identity in the legacy ``~/.gald3r/user_config.json``.
    They are setup bookkeeping, not identity, so they live in their own file and
    never compete with the unified ``user_config.json`` identity record. ``mcp_url``
    is preserved across re-runs if already set.
    """
    meta_path = home_dir / SETUP_META_FILENAME
    meta: dict = {}
    if meta_path.is_file():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8-sig"))
            if isinstance(existing, dict):
                meta.update(existing)
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    meta["mcp_url"] = meta.get("mcp_url") or "http://localhost:8082"
    meta["platform"] = "windows" if os.name == "nt" else sys.platform
    meta["setup_completed"] = True
    meta["setup_date"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["created_by"] = "g-hk-setup-user.py"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    return meta_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r user setup — store your user ID in the unified gald3r home."
    )
    parser.parse_args(argv)

    # -- Bootstrap the engine (DRY: reuse T530/T531 home + user_config primitives) --
    if not _hook_common.bootstrap_engine():
        print(
            "ERROR: [g-hk-setup-user] could not import the gald3r engine "
            "(gald3r.user_config / gald3r.home). Identity setup is delegated to the "
            "engine to keep ONE unified record — run this from a gald3r project "
            "checkout (with .gald3r_sys/engine) or an environment where `gald3r` is "
            "installed.",
            file=sys.stderr,
        )
        return 1
    from gald3r import home as _home  # noqa: E402
    from gald3r import user_config as _user_config  # noqa: E402

    print("")
    print("=======================================")
    print("  gald3r User Setup")
    print("=======================================")
    print("")
    print("Your user ID identifies you across all AI memory sessions on this machine.")
    print("Use your email, a nickname, initials -- whatever you want.")
    print("")

    # -- Detect suggestions ----------------------------------------------------
    suggestions = []

    git_email = _git_global_email()
    if git_email:
        suggestions.append(git_email)

    cursor_email = _cursor_cached_email()
    if cursor_email and cursor_email not in suggestions:
        suggestions.append(cursor_email)

    win_user = _os_username()
    if win_user:
        suggestions.append(win_user)

    # -- Show suggestions --------------------------------------------------------
    if suggestions:
        print("Detected options:")
        for i, suggestion in enumerate(suggestions):
            print(f"  [{i + 1}] {suggestion}")
        print("")

    try:
        user_input = input(
            "Enter your user ID (or press Enter to use suggestion [1]): "
        )
    except EOFError:
        user_input = ""

    # Resolve choice
    user_id = user_input.strip()
    if not user_id:
        if suggestions:
            user_id = suggestions[0]
            print(f"Using: {user_id}")
        else:
            user_id = f"user_{_os_username()}"
            print(f"Using: {user_id}")
    elif user_id.isdigit():
        # User typed a number — pick from suggestions list
        idx = int(user_id) - 1
        if 0 <= idx < len(suggestions):
            user_id = suggestions[idx]
            print(f"Using: {user_id}")

    # -- Resolve the ONE unified identity record (T530/T531) ----------------------
    env = dict(os.environ)
    platform_name = _platform.system()
    config_path = _user_config.default_config_path(env, platform_name)

    # One-time fold any pre-existing legacy ~/.gald3r/user_config.json forward,
    # preserving its ids (T627). No-op if the unified record already exists.
    _migrate_legacy_identity(_user_config, config_path)

    # Idempotent create-or-read: existing ids are NEVER regenerated (T531 contract).
    cfg = _user_config.ensure_user_config(env, platform_name)

    # Apply the interactively-chosen user_id ONLY when the record carries a
    # generated placeholder id (freshly created this run). An existing, deliberate
    # user_id is preserved — clobber-safe (AC3).
    fresh = _is_generated_id(cfg.user_id)
    if fresh and user_id and user_id != cfg.user_id:
        updated = _user_config.UserConfig(
            user_id=user_id,
            machine_id=cfg.machine_id,
            display_name=cfg.display_name,
            email=cfg.email,
        )
        _user_config.write(config_path, updated)
        cfg = updated

    # Relocate the non-identity setup fields to their own sidecar (AC2).
    home_dir = _home.resolve_home(env, platform_name)
    meta_path = _write_setup_meta(home_dir)

    print("")
    print("=======================================")
    print("  Setup complete!")
    print("=======================================")
    print("")
    print(f"  User ID  : {cfg.user_id}")
    print(f"  Identity : {config_path}")
    print(f"  Setup    : {meta_path}")
    print("")
    print("This ID will be used for all gald3r memory sessions on this machine.")
    print(f"To change it later, edit: {config_path}")
    print("")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        print(f"WARNING: [g-hk-setup-user] setup failed: {exc}", file=sys.stderr)
        sys.exit(0)
