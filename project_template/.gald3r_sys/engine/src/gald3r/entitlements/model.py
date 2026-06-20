"""Typed entitlement record + JSON (de)serialization (T553, part of T527).

One entitlement answers: *who* may use *which* feature, gated by tier, an explicit
allowlist, a global kill-switch, and an optional time-boxed audience window. The
field shape reconciles T524's ``(feature_id -> tier + allowlist + on/off +
audience window)`` registry sketch:

    feature_id       str            stable feature key
    tier             Tier           minimum tier required (T556)
    allowlist        list[str]      when non-empty, restricts the feature to these
                                    principal/account ids (early-access mode); the
                                    tier floor still applies. Empty = tier-only.
    enabled          bool           global on/off kill-switch (False = denied to all)
    audience_window  AudienceWindow optional [start, end) availability window

Pure data + validation only — no UI, no network, no clock. The evaluator (T554)
applies these fields; the loader (T555) builds these from disk.
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from gald3r.entitlements.tiers import Tier


class EntitlementError(ValueError):
    """Raised when an entitlement record fails validation / deserialization."""


def _parse_dt(value: Any, label: str) -> Optional[datetime]:
    """Parse an ISO-8601 string (or pass through a datetime) → datetime | None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise EntitlementError(f"{label} must be an ISO-8601 string, got {type(value).__name__}")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise EntitlementError(f"{label} is not a valid ISO-8601 datetime: {value!r}") from exc


@dataclass(frozen=True)
class AudienceWindow:
    """An optional ``[start, end)`` availability window (either side may be open).

    ``None`` on a side means "no bound" (open-ended). A window with ``start > end``
    is invalid and rejected at construction.
    """

    start: Optional[datetime] = None
    end: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.start is not None and self.end is not None and self.start > self.end:
            raise EntitlementError(
                f"audience_window start ({self.start.isoformat()}) is after end "
                f"({self.end.isoformat()})"
            )

    def contains(self, now: datetime) -> bool:
        """True when ``now`` falls inside ``[start, end)`` (open sides always pass)."""
        if self.start is not None and now < self.start:
            return False
        if self.end is not None and now >= self.end:
            return False
        return True

    @property
    def is_open(self) -> bool:
        """True when there is no bound at all (always-available window)."""
        return self.start is None and self.end is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AudienceWindow":
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise EntitlementError("audience_window must be an object with start/end")
        unknown = set(data) - {"start", "end"}
        if unknown:
            raise EntitlementError(f"audience_window has unknown field(s): {sorted(unknown)}")
        return cls(
            start=_parse_dt(data.get("start"), "audience_window.start"),
            end=_parse_dt(data.get("end"), "audience_window.end"),
        )


_ALLOWED_FIELDS = {"feature_id", "tier", "allowlist", "enabled", "audience_window"}


@dataclass(frozen=True)
class Entitlement:
    """A single server-authoritative feature entitlement record."""

    feature_id: str
    tier: Tier
    allowlist: List[str] = field(default_factory=list)
    enabled: bool = True
    audience_window: AudienceWindow = field(default_factory=AudienceWindow)

    def __post_init__(self) -> None:
        if not isinstance(self.feature_id, str) or not self.feature_id.strip():
            raise EntitlementError("feature_id must be a non-empty string")
        if not isinstance(self.tier, Tier):
            raise EntitlementError("tier must be a Tier")
        if not isinstance(self.enabled, bool):
            raise EntitlementError("enabled must be a bool")
        if not isinstance(self.allowlist, list) or any(
            not isinstance(x, str) for x in self.allowlist
        ):
            raise EntitlementError("allowlist must be a list of strings")
        if not isinstance(self.audience_window, AudienceWindow):
            raise EntitlementError("audience_window must be an AudienceWindow")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain JSON-friendly dict (round-trips with from_dict)."""
        return {
            "feature_id": self.feature_id,
            "tier": self.tier.value,
            "allowlist": list(self.allowlist),
            "enabled": self.enabled,
            "audience_window": self.audience_window.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entitlement":
        """Build a validated Entitlement from a dict; raise EntitlementError on any
        unknown/missing required field (fail closed — no silent grant defaults)."""
        if not isinstance(data, dict):
            raise EntitlementError("entitlement record must be an object")
        unknown = set(data) - _ALLOWED_FIELDS
        if unknown:
            raise EntitlementError(f"unknown field(s): {sorted(unknown)}")
        if "feature_id" not in data:
            raise EntitlementError("missing required field: feature_id")
        if "tier" not in data:
            raise EntitlementError("missing required field: tier")
        tier_raw = data["tier"]
        try:
            tier = tier_raw if isinstance(tier_raw, Tier) else Tier.from_str(tier_raw)
        except ValueError as exc:
            raise EntitlementError(str(exc)) from exc
        return cls(
            feature_id=data["feature_id"],
            tier=tier,
            allowlist=list(data.get("allowlist", [])),
            enabled=data.get("enabled", True),
            audience_window=AudienceWindow.from_dict(data.get("audience_window")),
        )
