"""Canonical subscription tiers + role checks (T556, part of T527).

T527 defines four ordered tiers plus an internal gald3r-team role. The evaluator
(T554) needs a single source of truth for "is this principal at least tier X?"
and "does this principal hold role Y?". Everything here is pure: no I/O, no
network, no clock.

Tier ordering (ascending entitlement):

    anonymous < free-logged-in < solo-paid < team-company-paid

The enum (de)serializes to/from its stable string *value* (e.g. ``"solo-paid"``)
so it can live unambiguously in the T553 model and the T555 config file.
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

from enum import Enum
from typing import Iterable, Optional

#: The internal gald3r-team role name (cross-cutting; orthogonal to tier).
ROLE_GALD3R_TEAM = "gald3r-team"


class Tier(str, Enum):
    """Subscription tiers, ordered low→high by entitlement.

    Subclassing ``str`` keeps the value JSON-friendly while the declaration order
    defines the ranking used by :func:`meets_tier`.
    """

    ANONYMOUS = "anonymous"
    FREE_LOGGED_IN = "free-logged-in"
    SOLO_PAID = "solo-paid"
    TEAM_COMPANY_PAID = "team-company-paid"

    @property
    def rank(self) -> int:
        """0-based position in the ascending tier ordering."""
        return _TIER_ORDER.index(self)

    @classmethod
    def from_str(cls, value: str) -> "Tier":
        """Parse a tier from its stable string value.

        Raises:
            ValueError: if ``value`` is not a known tier (no silent default — an
            unknown tier must never be treated as a grant).
        """
        try:
            return cls(value)
        except ValueError as exc:  # re-raise with the valid set for clarity
            valid = ", ".join(t.value for t in _TIER_ORDER)
            raise ValueError(
                f"unknown tier {value!r}; expected one of: {valid}"
            ) from exc


#: Ascending order — the single source of truth for tier ranking.
_TIER_ORDER = (
    Tier.ANONYMOUS,
    Tier.FREE_LOGGED_IN,
    Tier.SOLO_PAID,
    Tier.TEAM_COMPANY_PAID,
)


def meets_tier(principal_tier: Tier, required_tier: Tier) -> bool:
    """Return True when ``principal_tier`` is at least ``required_tier``.

    "At least" uses the ascending ordering above, so e.g. a ``SOLO_PAID``
    principal meets a ``FREE_LOGGED_IN`` requirement but not ``TEAM_COMPANY_PAID``.
    """
    return principal_tier.rank >= required_tier.rank


def has_role(principal_roles: Optional[Iterable[str]], role: str) -> bool:
    """Return True when ``role`` is present in the principal's role collection.

    ``principal_roles`` may be ``None`` (no roles). Matching is exact and
    case-sensitive — roles are stable identifiers, not free text.
    """
    if not principal_roles:
        return False
    return role in set(principal_roles)
