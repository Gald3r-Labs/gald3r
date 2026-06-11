#!/usr/bin/env python3
"""Python port of manage_user_profile.ps1 (T1585).

Manage the gald3r user settings profile (T1036).

CLI helper for the two-layer gald3r user profile system:
  Layer 1 (global):       %APPDATA%/gald3r/user_profile.yaml  (Windows)
  Layer 2 (per-project):  <project>/.gald3r/.user_prefs.yaml  (gitignored)

SECURITY: The profile never stores plaintext API key values.
api_keys entries hold only environment variable names and optional keychain IDs.

Actions:
  get             - Show the current effective profile (merges global + project prefs)
  set             - Update a single field (dot-path) in the global profile
  validate-keys   - Check whether each API key env var is set and non-empty
  migrate         - Migrate from legacy %APPDATA%/gald3r/user_config.json to user_profile.yaml
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Tuple


# UTF-8-safe stdio on Windows consoles (the PS1 originals emit Unicode glyphs)
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _bootstrap_engine() -> bool:
    """Make ``gald3r.utils`` importable; fall back to the bundled engine source."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for parent in here.parents:
        engine_src = parent / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()
try:
    from gald3r.utils import console as _console
except ImportError:
    _console = None  # graceful stdlib fallback

try:
    import yaml as _pyyaml  # optional dependency
except ImportError:
    _pyyaml = None

_ANSI = {"cyan": "36", "green": "32", "yellow": "33", "red": "31",
         "gray": "37", "darkgray": "90", "white": "97"}
_ansi_ready = False


def _supports_color(stream: TextIO) -> bool:
    if _console is not None:
        return bool(_console.color_enabled(stream))
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def _say(msg: str = "", color: Optional[str] = None,
         stream: Optional[TextIO] = None) -> None:
    """Write-Host replacement with optional foreground color."""
    global _ansi_ready
    stream = stream or sys.stdout
    code = _ANSI.get((color or "").lower())
    if code and _supports_color(stream):
        if os.name == "nt" and not _ansi_ready:
            os.system("")  # flip the Windows console into VT mode
            _ansi_ready = True
        print(f"\x1b[{code}m{msg}\x1b[0m", file=stream)
    else:
        print(msg, file=stream)


def _warn(msg: str) -> None:
    _say(f"WARNING: {msg}", "yellow", sys.stderr)


# ---------------------------------------------------------------------------
# Minimal YAML subset (fallback when PyYAML is absent)
# ---------------------------------------------------------------------------

def _parse_scalar(s: str) -> Any:
    s = s.strip()
    if not s:
        return ""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "~"):
        return None
    if s == "[]":
        return []
    if s == "{}":
        return {}
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [_parse_scalar(p) for p in inner.split(",")]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _yaml_parse_fallback(text: str) -> Any:
    """Indentation-based parser for the profile schema this script writes."""
    rows: List[Tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        rows.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))
    idx = 0

    def block(indent: int) -> Any:
        nonlocal idx
        if idx >= len(rows):
            return {}
        if rows[idx][1].startswith("- "):
            out_list: List[Any] = []
            while (idx < len(rows) and rows[idx][0] >= indent
                   and rows[idx][1].startswith("- ")):
                item_indent, item_text = rows[idx]
                body = item_text[2:].strip()
                if ":" in body and not body.startswith(("'", '"')):
                    rows[idx] = (item_indent + 2, body)
                    out_list.append(block(item_indent + 2))
                else:
                    out_list.append(_parse_scalar(body))
                    idx += 1
            return out_list
        out: Dict[str, Any] = {}
        while idx < len(rows) and rows[idx][0] >= indent:
            row_indent, text_row = rows[idx]
            if row_indent > indent or text_row.startswith("- "):
                break
            key, _, rest = text_row.partition(":")
            key = key.strip().strip("'\"")
            idx += 1
            rest = rest.strip()
            if rest:
                out[key] = _parse_scalar(rest)
            elif idx < len(rows) and rows[idx][0] > indent:
                out[key] = block(rows[idx][0])
            else:
                out[key] = {}
        return out

    return block(rows[0][0] if rows else 0)


def _fmt_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "''"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or s != s.strip() or any(c in s for c in ":#{}[]'\""):
        return "'" + s.replace("'", "''") + "'"
    return s


def _yaml_dump_fallback(data: Any, indent: int = 0) -> str:
    pad = " " * indent
    lines: List[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                if v:
                    lines.append(f"{pad}{k}:")
                    lines.append(_yaml_dump_fallback(v, indent + 2))
                else:
                    lines.append(f"{pad}{k}: {{}}")
            elif isinstance(v, list):
                if v:
                    lines.append(f"{pad}{k}:")
                    lines.append(_yaml_dump_fallback(v, indent + 2))
                else:
                    lines.append(f"{pad}{k}: []")
            else:
                lines.append(f"{pad}{k}: {_fmt_scalar(v)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    first = False
                    if isinstance(v, (dict, list)) and v:
                        lines.append(f"{prefix}{k}:")
                        lines.append(_yaml_dump_fallback(v, indent + 4))
                    else:
                        empty = "{}" if isinstance(v, dict) else "[]" \
                            if isinstance(v, list) else _fmt_scalar(v)
                        lines.append(f"{prefix}{k}: {empty}")
            else:
                lines.append(f"{pad}- {_fmt_scalar(item)}")
    return "\n".join(lines)


def yaml_loads(text: str) -> Any:
    if _pyyaml is not None:
        return _pyyaml.safe_load(text)
    return _yaml_parse_fallback(text)


def yaml_dumps(data: Any) -> str:
    if _pyyaml is not None:
        return _pyyaml.safe_dump(data, default_flow_style=False, sort_keys=False,
                                  allow_unicode=True)
    return _yaml_dump_fallback(data) + "\n"


# ---------------------------------------------------------------------------
# Helpers (parity with the PS1 functions)
# ---------------------------------------------------------------------------

def get_appdata_dir() -> Path:
    """%APPDATA% with the same fallback the PS1 used ($HOME/AppData/Roaming)."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata)
    return Path.home() / "AppData" / "Roaming"


def get_global_profile_path() -> Path:
    return get_appdata_dir() / "gald3r" / "user_profile.yaml"


def get_project_prefs_path(project_root: str) -> Path:
    return Path(project_root) / ".gald3r" / ".user_prefs.yaml"


def read_yaml_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8-sig")
        data = yaml_loads(content)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError) as exc:
        _warn(f"Could not read YAML at {path}: {exc}")
        return None


def write_yaml_file(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_dumps(data), encoding="utf-8")


def get_now_iso() -> str:
    # Parity with the PS1: local time formatted with a literal Z suffix.
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


def new_default_profile() -> Dict[str, Any]:
    now = get_now_iso()
    return {
        "schema_version": 2,
        "user_id": str(uuid.uuid4()),
        "display_name": "",
        "email": "",
        "created_at": now,
        "updated_at": now,
        "api_keys": {},
        "mcp_servers": {},
        "personality": {
            "theme": "silicon_valley",
            "primary_character": "random",
            "animation_enabled": True,
            "emoji_density": "normal",
        },
        "skill_packs": [],
        "plugins": [],
        "updates": {
            "check_frequency": "24h",
            "auto_upgrade": False,
            "notify_in_agent": True,
            "notify_in_throne": True,
            "skip_versions": [],
        },
    }


def set_dot_path(data: Dict[str, Any], path: str, new_value: Any) -> None:
    parts = path.split(".")
    obj = data
    for key in parts[:-1]:
        if key not in obj or not isinstance(obj[key], dict):
            obj[key] = {}
        obj = obj[key]
    obj[parts[-1]] = new_value


def coerce_value(raw: str) -> Any:
    """Map CLI strings to bool/int/dict like the PS1's [object]$Value."""
    s = raw.strip()
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    if s.startswith(("{", "[")):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
    return raw


def _env_ref(ref: Any) -> str:
    return str(ref.get("env_var", "")) if isinstance(ref, dict) else str(ref)


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def invoke_get(project_path: Optional[str]) -> int:
    global_path = get_global_profile_path()
    _say(f"Global profile: {global_path}")

    glob = read_yaml_file(global_path)
    if glob is None:
        _warn(f"Global profile not found at {global_path}")
        _say("Run with -Action migrate to create from legacy config, or:")
        _say("  manage_user_profile.py -Action set -Field display_name "
             "-Value YourName -Apply")
        return 0

    prefs: Optional[Dict[str, Any]] = None
    if project_path:
        prefs_path = get_project_prefs_path(project_path)
        _say(f"Project prefs: {prefs_path}")
        prefs = read_yaml_file(prefs_path)
        if prefs:
            _say("(Project prefs loaded — overrides apply)")

    _say("")
    _say("=== Effective Profile ===", "cyan")

    _say("Identity:")
    _say(f"  user_id:      {glob.get('user_id', '')}")
    _say(f"  display_name: {glob.get('display_name', '')}")
    _say(f"  email:        {glob.get('email', '')}")

    _say("")
    _say("Personality:")
    personality = glob.get("personality") or {}
    if project_path and prefs and prefs.get("personality"):
        personality = prefs["personality"]
        _say("  (project override active)")
    _say(f"  theme:             {personality.get('theme', '')}")
    _say(f"  primary_character: {personality.get('primary_character', '')}")
    _say(f"  animation_enabled: {personality.get('animation_enabled', '')}")
    _say(f"  emoji_density:     {personality.get('emoji_density', '')}")

    _say("")
    _say("API Keys (env-var references — never values):")
    api_keys = glob.get("api_keys") or {}
    if api_keys:
        for name, ref in api_keys.items():
            env_var = _env_ref(ref)
            is_set = bool(os.environ.get(env_var))
            status = "[OK]" if is_set else "[MISSING]"
            _say(f"  {name} → {env_var} {status}",
                 "green" if is_set else "red")
    else:
        _say("  (none configured)")

    _say("")
    _say("MCP Servers:")
    mcp_servers: Dict[str, Any] = dict(glob.get("mcp_servers") or {})
    if project_path and prefs and prefs.get("mcp_servers"):
        for key, val in prefs["mcp_servers"].items():
            mcp_servers[key] = val
        _say("  (project MCP overrides active)")
    if mcp_servers:
        for name, entry in mcp_servers.items():
            url = entry.get("url", "") if isinstance(entry, dict) else entry
            _say(f"  {name} → {url}")
    else:
        _say("  (none configured)")

    skill_packs = glob.get("skill_packs") or []
    _say("")
    _say(f"Skill Packs ({len(skill_packs)}):")
    for sp in skill_packs:
        if isinstance(sp, dict):
            state = "enabled" if sp.get("enabled") else "disabled"
            _say(f"  {sp.get('id', '')} [{state}]")
        else:
            _say(f"  {sp}")

    updates = glob.get("updates") or {}
    _say("")
    _say("Updates:")
    _say(f"  check_frequency: {updates.get('check_frequency', '')}")
    _say(f"  auto_upgrade:    {updates.get('auto_upgrade', '')}")
    _say(f"  notify_in_agent: {updates.get('notify_in_agent', '')}")
    return 0


def invoke_set(field: Optional[str], value: Optional[str],
               project_path: Optional[str], apply: bool) -> int:
    if not field:
        _say("ERROR: -Field is required for the 'set' action.", "red", sys.stderr)
        return 1
    if value is None:
        _say("ERROR: -Value is required for the 'set' action.", "red", sys.stderr)
        return 1
    new_value = coerce_value(value)

    if project_path:
        path = get_project_prefs_path(project_path)
        _say(f"Scope: project prefs → {path}")
        data = read_yaml_file(path)
        if data is None:
            # Bootstrap minimal project prefs
            identity_path = Path(project_path) / ".gald3r" / ".identity"
            project_id = ""
            if identity_path.exists():
                for line in identity_path.read_text(
                        encoding="utf-8-sig").splitlines():
                    if line.startswith("project_id="):
                        project_id = line.split("=", 1)[1].strip()
                        break
            data = {"schema_version": 1, "project_id": project_id}
        set_dot_path(data, field, new_value)
        if apply:
            write_yaml_file(path, data)
            _say(f"Written: {path}", "green")
        else:
            _say(f"(Dry-run) Would write to: {path}", "yellow")
            _say(f"  Field: {field} = {value}")
    else:
        path = get_global_profile_path()
        _say(f"Scope: global profile → {path}")
        data = read_yaml_file(path)
        if data is None:
            data = new_default_profile()
            _say("Global profile not found — creating with defaults.")
        set_dot_path(data, field, new_value)
        data["updated_at"] = get_now_iso()
        if apply:
            write_yaml_file(path, data)
            _say(f"Written: {path}", "green")
        else:
            _say(f"(Dry-run) Would write to: {path}", "yellow")
            _say(f"  Field: {field} = {value}")
            _say("Pass -Apply to write.")
    return 0


def invoke_validate_keys() -> int:
    global_path = get_global_profile_path()
    glob = read_yaml_file(global_path)
    if glob is None:
        _warn(f"No global profile at {global_path}")
        return 0
    api_keys = glob.get("api_keys") or {}
    if not api_keys:
        _say("No API keys configured in profile.")
        return 0
    _say("API Key Validation:", "cyan")
    ok = 0
    missing = 0
    for name, ref in api_keys.items():
        env_var = _env_ref(ref)
        if os.environ.get(env_var):
            _say(f"  [OK]      {name} → {env_var}", "green")
            ok += 1
        else:
            _say(f"  [MISSING] {name} → {env_var}", "red")
            missing += 1
    _say("")
    _say(f"{ok}/{ok + missing} keys present.")
    return 0


def invoke_migrate(apply: bool) -> int:
    legacy_path = get_appdata_dir() / "gald3r" / "user_config.json"
    target_path = get_global_profile_path()

    if not legacy_path.exists():
        _warn(f"Legacy config not found at: {legacy_path}")
        _say("Nothing to migrate.")
        return 0

    legacy = json.loads(legacy_path.read_text(encoding="utf-8-sig"))

    now = get_now_iso()
    profile = new_default_profile()
    profile["user_id"] = legacy.get("user_id") or str(uuid.uuid4())
    profile["display_name"] = legacy.get("user_name") or ""
    profile["email"] = legacy.get("email") or ""
    profile["created_at"] = legacy.get("created_at") or now
    profile["updated_at"] = now

    _say("Migration plan:", "cyan")
    _say(f"  Source: {legacy_path}")
    _say(f"  Target: {target_path}")
    _say(f"  user_id:      {profile['user_id']}")
    _say(f"  display_name: {profile['display_name']}")
    _say(f"  email:        {profile['email']}")

    if apply:
        if target_path.exists():
            _warn(f"Target already exists: {target_path}")
            _warn("Overwrite? Press Ctrl+C to cancel, or wait 5 seconds "
                  "to continue...")
            time.sleep(5)
        write_yaml_file(target_path, profile)
        _say(f"Migration complete: {target_path}", "green")
    else:
        _say("")
        _say(f"(Dry-run) Would write to: {target_path}", "yellow")
        _say("Pass -Apply to execute migration.")
    return 0


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage the gald3r user settings profile (T1036).")
    parser.add_argument("-Action", "--action", dest="action", required=True,
                        type=str.lower,
                        choices=["get", "set", "validate-keys", "migrate"],
                        help="Profile operation to perform")
    parser.add_argument("-Field", "--field", dest="field", default=None,
                        help="Dot-path field for 'set' (e.g. personality.theme)")
    parser.add_argument("-Value", "--value", dest="value", default=None,
                        help="New value for 'set' (string/bool/int/JSON object)")
    parser.add_argument("-ProjectPath", "--project-path", dest="project_path",
                        default=None,
                        help="Project directory for per-project prefs scope")
    parser.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                        help="Actually write changes (default: dry-run)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "get":
        return invoke_get(args.project_path)
    if args.action == "set":
        return invoke_set(args.field, args.value, args.project_path, args.apply)
    if args.action == "validate-keys":
        return invoke_validate_keys()
    return invoke_migrate(args.apply)


if __name__ == "__main__":
    sys.exit(main())
