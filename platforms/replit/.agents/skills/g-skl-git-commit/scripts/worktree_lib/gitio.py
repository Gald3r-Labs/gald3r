"""Git/process IO, path, time, and text helpers for the worktree port.

Python port of gald3r_worktree.ps1 (T1585) — shared helper layer.

Prefers the gald3r engine utils (``gald3r.utils.process``) when importable;
falls back to a minimal local subprocess wrapper so the script never
hard-fails on import.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:  # engine utils (T1583) — preferred transport
    from gald3r.utils.process import run_cmd as _engine_run_cmd

    _ENGINE_UTILS_AVAILABLE = True
except ImportError:  # minimal local fallback — keep the script importable
    _engine_run_cmd = None
    _ENGINE_UTILS_AVAILABLE = False


class WorktreeError(RuntimeError):
    """Operational failure — mirrors a PS1 ``throw`` (CLI exits 1)."""


# ---------------------------------------------------------------------------
# Process / git wrappers (PS1 Invoke-Git)
# ---------------------------------------------------------------------------

def run_process(args: Sequence[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a command and capture output. Never raises on non-zero exit.

    Returns:
        (returncode, stdout, stderr)
    """
    if _ENGINE_UTILS_AVAILABLE:
        res = _engine_run_cmd(list(args), cwd=cwd, check=False)
        return res.returncode, res.stdout, res.stderr
    proc = subprocess.run(
        [str(a) for a in args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def invoke_git(repo: str, args: Sequence[str]) -> str:
    """Run ``git -C <repo> <args>``; raise WorktreeError on failure.

    Mirrors the PS1 Invoke-Git contract: stderr progress noise never aborts;
    only a non-zero exit code is a failure.
    """
    rc, out, err = run_process(["git", "-C", str(repo), *[str(a) for a in args]])
    if rc != 0:
        merged = "\n".join(part for part in (out.strip(), err.strip()) if part)
        raise WorktreeError(f"git {' '.join(str(a) for a in args)} failed in {repo}: {merged}")
    return out


def git_exit_code(repo: str, args: Sequence[str]) -> int:
    """Run a git command and return only its exit code (PS1 ``& git ...; $LASTEXITCODE``)."""
    rc, _out, _err = run_process(["git", "-C", str(repo), *[str(a) for a in args]])
    return rc


# ---------------------------------------------------------------------------
# Path helpers (PS1 Test-PathInside / GetFullPath)
# ---------------------------------------------------------------------------

def full_path(path: str) -> str:
    """Absolute, normalized path — equivalent of [System.IO.Path]::GetFullPath."""
    return os.path.abspath(str(path))


def path_inside(child: str, parent: str) -> bool:
    """True when `child` is inside (or equals) `parent`.

    Case-insensitive ordinal comparison, exactly like the PS1 Test-PathInside.
    """
    c = full_path(child).rstrip("\\/").lower()
    p = full_path(parent).rstrip("\\/").lower()
    return c == p or c.startswith(p + os.sep)


def strings_equal_ci(a: Optional[str], b: Optional[str]) -> bool:
    """Case-insensitive string equality, mirroring the PowerShell -eq operator."""
    return (str(a) if a is not None else "").lower() == (str(b) if b is not None else "").lower()


def is_blank(value: Optional[str]) -> bool:
    """[string]::IsNullOrWhiteSpace equivalent."""
    return value is None or not str(value).strip()


# ---------------------------------------------------------------------------
# Safe segment (PS1 ConvertTo-SafeSegment)
# ---------------------------------------------------------------------------

_RESERVED_NAMES = re.compile(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])$")


def safe_segment(value: Optional[str]) -> str:
    """Sanitize a value into a filesystem/branch-safe lowercase segment."""
    if is_blank(value):
        return "unknown"
    safe = re.sub(r"[^a-z0-9._-]+", "-", str(value).lower())
    safe = re.sub(r"\.{2,}", ".", safe)
    safe = safe.strip("-").strip(".")
    if not safe.strip():
        return "unknown"
    if safe.endswith(".lock"):
        safe = safe[: -len(".lock")] + "-lock"
    if _RESERVED_NAMES.match(safe):
        safe = "x-" + safe
    if len(safe) > 48:
        safe = safe[:48].strip("-").strip(".")
    return safe


def short_suffix() -> str:
    """First 8 hex chars of a fresh GUID (PS1 Get-ShortSuffix)."""
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Time helpers (PS1 (Get-Date).ToUniversalTime().ToString("o") and parses)
# ---------------------------------------------------------------------------

_EXTRA_FRACTION = re.compile(r"(\.\d{6})\d+")


def utc_now() -> datetime:
    """Current aware UTC time."""
    return datetime.now(timezone.utc)


def iso_o(dt: datetime) -> str:
    """Round-trip ISO-8601 UTC timestamp, matching .NET's "o" format shape."""
    dt = dt.astimezone(timezone.utc)
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}.{dt.microsecond:06d}0Z"


def parse_datetime(raw: Any, assume_utc: bool) -> Optional[datetime]:
    """Parse an ISO-8601-ish timestamp; return an aware UTC datetime or None.

    Args:
        raw: The stored timestamp value (string or None).
        assume_utc: How to interpret a value without timezone info — True
            mirrors the PS1 AssumeUniversal path (lock manifests); False
            mirrors a plain [datetime] cast (local-time assumption).
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    s = _EXTRA_FRACTION.sub(r"\1", s)
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc) if assume_utc else dt.astimezone()
    return dt.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# File helpers (atomic temp+rename writes, JSON metadata IO)
# ---------------------------------------------------------------------------

def atomic_write_text(path: Path, content: str) -> None:
    """Write `content` via a sibling temp file + atomic rename (PS1 Move-Item -Force)."""
    tmp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Read a JSON file; return None on any read/parse failure (PS1 try/ConvertFrom-Json)."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Serialize metadata to disk (PS1 ConvertTo-Json | Set-Content -Encoding UTF8)."""
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def regex_count(pattern: str, text: str) -> int:
    """Count multiline regex matches (PS1 [regex]::Matches(...).Count)."""
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def collapse_newlines(text: str) -> str:
    """Collapse internal newlines to single spaces (queue item normalization)."""
    return re.sub(r"\r?\n", " ", text)


def resolve_owner(owner: Optional[str]) -> str:
    """Default owner resolution: USERNAME, then USER, then 'agent' (PS1 param block)."""
    if not is_blank(owner):
        return str(owner)
    for var in ("USERNAME", "USER"):
        value = os.environ.get(var)
        if not is_blank(value):
            return str(value)
    return "agent"


def as_list(value: Optional[Sequence[str]]) -> List[str]:
    """Normalize an optional sequence to a concrete list."""
    return list(value) if value else []
