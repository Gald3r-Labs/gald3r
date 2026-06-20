"""Per-user ``user_config.json`` schema + read/write/ensure helper (T558).

One small JSON file, created and managed identically by templates, Throne, and the
Agent, lives in the unified per-user home (T530 / T557 :func:`gald3r.home.resolve_home`)
and identifies the human + their machine. It reuses the ``memory_setup_user`` field
shape and feeds logged-in state to the entitlement core (T527).

Schema (``user-config-v1``):

    user_id       str            stable per-user id (generated if missing)
    display_name  str            human-friendly name (defaults to "" until set)
    email         str | None     optional contact (never required)
    machine_id    str            stable per-machine id (generated if missing)

This module is pure I/O over an explicitly passed path — no UI, no network, no
auth. It **fails loud** on corrupt JSON (no silent reset that would lose identity).
"""
# @subsystems: PROJECT_IDENTITY_SETUP, MEMORY_AND_KNOWLEDGE
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

from gald3r import home

SCHEMA_VERSION = "user-config-v1"

#: The canonical config filename inside the per-user home.
USER_CONFIG_FILENAME = "user_config.json"

_ALLOWED_FIELDS = {"user_id", "display_name", "email", "machine_id", "schema_version"}


class UserConfigError(ValueError):
    """Raised when user_config.json cannot be read/validated."""


@dataclass
class UserConfig:
    """The validated user_config.json record."""

    user_id: str
    machine_id: str
    display_name: str = ""
    email: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.user_id, str) or not self.user_id.strip():
            raise UserConfigError("user_id must be a non-empty string")
        if not isinstance(self.machine_id, str) or not self.machine_id.strip():
            raise UserConfigError("machine_id must be a non-empty string")
        if not isinstance(self.display_name, str):
            raise UserConfigError("display_name must be a string")
        if self.email is not None and not isinstance(self.email, str):
            raise UserConfigError("email must be a string or null")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "email": self.email,
            "machine_id": self.machine_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserConfig":
        if not isinstance(data, dict):
            raise UserConfigError("user_config must be a JSON object")
        unknown = set(data) - _ALLOWED_FIELDS
        if unknown:
            raise UserConfigError(f"user_config has unknown field(s): {sorted(unknown)}")
        for required in ("user_id", "machine_id"):
            if required not in data:
                raise UserConfigError(f"user_config missing required field: {required}")
        return cls(
            user_id=data["user_id"],
            machine_id=data["machine_id"],
            display_name=data.get("display_name", ""),
            email=data.get("email"),
        )


def default_config_path(env: dict, platform_name: str) -> Path:
    """Return the canonical user_config.json path inside the T557 per-user home."""
    return home.resolve_home(env, platform_name) / USER_CONFIG_FILENAME


def read(path: Union[str, Path]) -> UserConfig:
    """Read + validate user_config.json. Raises UserConfigError on missing/corrupt."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise UserConfigError(f"cannot read user_config at {p}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UserConfigError(f"user_config at {p} is not valid JSON: {exc}") from exc
    return UserConfig.from_dict(data)


def write(path: Union[str, Path], config: UserConfig) -> Path:
    """Write ``config`` to ``path`` (creating parent dirs). Returns the path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(config.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return p


def ensure(path: Union[str, Path]) -> UserConfig:
    """Return the config at ``path``, creating it with generated ids if missing.

    Idempotent: if a valid file already exists it is returned unchanged (never
    overwritten). A corrupt existing file raises (no silent reset) rather than
    clobbering whatever identity might be recoverable there.
    """
    p = Path(path)
    if p.exists():
        return read(p)
    config = UserConfig(
        user_id=uuid.uuid4().hex,
        machine_id=uuid.uuid4().hex,
    )
    write(p, config)
    return config
