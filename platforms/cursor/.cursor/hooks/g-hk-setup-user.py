#!/usr/bin/env python3
"""Python port of g-hk-setup-user.ps1 (T1584).

Run this ONCE from a terminal to set your gald3r user identity. Your user ID
is stored in ~/.gald3r/user_config.json and used across all AI sessions
(Cursor, Claude Code, Gemini) on this machine.

Interactive: suggests a user ID from git global email, the Cursor cached
email (state.vscdb), and the OS username, then prompts via input() with a
[1] default hint. The stable machine ID is read from the Windows registry
(HKLM\\SOFTWARE\\Microsoft\\Cryptography MachineGuid) on Windows only; on
other platforms (or on registry failure) a random GUID is generated.

Usage:
  python .claude/hooks/g-hk-setup-user.py
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402,F401


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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r user setup — store your user ID in ~/.gald3r/user_config.json."
    )
    parser.parse_args(argv)

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

    # -- Read or create existing user_config.json ---------------------------------
    config_dir = Path.home() / ".gald3r"
    config_file = config_dir / "user_config.json"

    config_dir.mkdir(parents=True, exist_ok=True)

    cfg = {}
    if config_file.is_file():
        try:
            existing = json.loads(config_file.read_text(encoding="utf-8-sig"))
            if isinstance(existing, dict):
                # Preserve all existing fields
                cfg.update(existing)
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    # Stable machine ID
    machine_id = cfg.get("machine_id")
    if not machine_id:
        machine_id = _machine_id()

    # Update / set fields
    cfg["user_id"] = user_id
    cfg["machine_id"] = machine_id
    cfg["mcp_url"] = cfg.get("mcp_url") or "http://localhost:8082"
    cfg["platform"] = "windows" if os.name == "nt" else sys.platform
    cfg["setup_completed"] = True
    cfg["setup_date"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    cfg["created_by"] = "g-hk-setup-user.py"

    config_file.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    print("")
    print("=======================================")
    print("  Setup complete!")
    print("=======================================")
    print("")
    print(f"  User ID  : {user_id}")
    print(f"  Config   : {config_file}")
    print("")
    print("This ID will be used for all gald3r memory sessions on this machine.")
    print(f"To change it later, edit: {config_file}")
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
