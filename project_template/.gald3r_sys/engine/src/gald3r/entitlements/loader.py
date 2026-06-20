"""Feature-flag config format + loader (T555, part of T527).

The on-disk source of truth for the entitlement registry is a single JSON file:

    {
      "version": 1,
      "entitlements": [
        {
          "feature_id": "themes.export",
          "tier": "solo-paid",
          "allowlist": [],
          "enabled": true,
          "audience_window": {"start": null, "end": null}
        }
      ]
    }

* ``version`` (int, required) — schema version; only ``1`` is understood today.
* ``entitlements`` (list, required) — zero or more records in the T553 shape.

The loader is *pure with respect to its input*: :func:`load_config_text` takes the
raw text/bytes (testable without a filesystem), and :func:`load_config` is a thin
path wrapper. It **fails closed**: any malformed input, unknown field, missing
required field, duplicate feature_id, or empty file raises :class:`ConfigError`.
There are no silent defaults that would grant access.
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from gald3r.entitlements.model import Entitlement, EntitlementError

#: The only config schema version this loader understands.
SUPPORTED_VERSION = 1


class ConfigError(ValueError):
    """Raised when a flag-config file/text cannot be loaded into valid records."""


def load_config_text(text: Union[str, bytes]) -> Dict[str, Entitlement]:
    """Parse flag-config text/bytes → ``{feature_id: Entitlement}`` (fail closed).

    Raises:
        ConfigError: empty input, invalid JSON, wrong top-level shape, unsupported
            version, a record that fails T553 validation, or a duplicate feature_id.
    """
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ConfigError(f"config is not valid UTF-8: {exc}") from exc
    if not text.strip():
        raise ConfigError("config is empty")

    try:
        doc: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config is not valid JSON: {exc}") from exc

    if not isinstance(doc, dict):
        raise ConfigError("config root must be a JSON object")
    unknown = set(doc) - {"version", "entitlements"}
    if unknown:
        raise ConfigError(f"config has unknown top-level field(s): {sorted(unknown)}")
    if "version" not in doc:
        raise ConfigError("config missing required field: version")
    if doc["version"] != SUPPORTED_VERSION:
        raise ConfigError(
            f"unsupported config version {doc['version']!r}; expected {SUPPORTED_VERSION}"
        )
    if "entitlements" not in doc:
        raise ConfigError("config missing required field: entitlements")
    records = doc["entitlements"]
    if not isinstance(records, list):
        raise ConfigError("config 'entitlements' must be a list")

    registry: Dict[str, Entitlement] = {}
    for i, raw in enumerate(records):
        try:
            ent = Entitlement.from_dict(raw)
        except EntitlementError as exc:
            raise ConfigError(f"entitlements[{i}]: {exc}") from exc
        if ent.feature_id in registry:
            raise ConfigError(f"entitlements[{i}]: duplicate feature_id {ent.feature_id!r}")
        registry[ent.feature_id] = ent
    return registry


def load_config(path: Union[str, Path]) -> Dict[str, Entitlement]:
    """Read a flag-config file from ``path`` → ``{feature_id: Entitlement}``.

    Raises:
        ConfigError: if the file is missing/unreadable or its contents are invalid
            (see :func:`load_config_text`).
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read config file {p}: {exc}") from exc
    return load_config_text(text)
