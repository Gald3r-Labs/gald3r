"""Pure server-side feature-flag evaluator (T554, part of T527).

``evaluate(feature_id, principal, registry, now=...)`` is the single decision
function both surfaces call ("engine enforces; client advises", T491). It is
pure: identical inputs always yield an identical :class:`Decision`. There is no
I/O and no implicit clock — audience-window checks use the injected ``now``.

Decision precedence (first match wins):

    1. unknown_feature   — feature_id not in the registry
    2. kill_switched     — entitlement.enabled is False (global off; highest gate)
    3. outside_window    — ``now`` is outside the audience window
    4. not_in_allowlist  — allowlist is non-empty and the principal is not on it
    5. denied_by_tier    — principal's tier is below the required tier
    6. allowed           — all gates passed
"""
# @subsystems: SECURITY_AND_COMPLIANCE, AGENT_ORCHESTRATION
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Mapping, Optional

from gald3r.entitlements.model import Entitlement
from gald3r.entitlements.tiers import Tier, has_role

# Stable decision reason codes (used by callers + tests; do not rename casually).
REASON_ALLOWED = "allowed"
REASON_UNKNOWN_FEATURE = "unknown_feature"
REASON_KILL_SWITCHED = "kill_switched"
REASON_OUTSIDE_WINDOW = "outside_window"
REASON_NOT_IN_ALLOWLIST = "not_in_allowlist"
REASON_DENIED_BY_TIER = "denied_by_tier"


@dataclass(frozen=True)
class Principal:
    """The actor a decision is made about — tier + roles + a stable account id.

    ``account_id`` is matched against an entitlement's allowlist. ``roles`` carries
    cross-cutting roles (e.g. the internal gald3r-team role); see :func:`has_role`.
    """

    tier: Tier
    account_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Decision:
    """The result of an evaluation: allow/deny + a stable reason code.

    A pure value object — role checks live on the principal via
    :func:`gald3r.entitlements.tiers.has_role`, not here.
    """

    allowed: bool
    reason: str
    feature_id: str


def evaluate(
    feature_id: str,
    principal: Principal,
    registry: Mapping[str, Entitlement],
    *,
    now: Optional[datetime] = None,
) -> Decision:
    """Decide whether ``principal`` may use ``feature_id`` given ``registry``.

    Args:
        feature_id: The feature being requested.
        principal: The actor (tier / account_id / roles).
        registry: Mapping of feature_id → :class:`Entitlement`.
        now: Injected current time for audience-window checks. Defaults to
            ``datetime.now(timezone.utc)`` only as a convenience for callers that
            do not gate on windows; pass it explicitly for deterministic results.

    Returns:
        A :class:`Decision` (allow/deny + stable reason code).
    """
    ent = registry.get(feature_id)
    if ent is None:
        return Decision(False, REASON_UNKNOWN_FEATURE, feature_id)

    if not ent.enabled:
        return Decision(False, REASON_KILL_SWITCHED, feature_id)

    if now is None:
        now = datetime.now(timezone.utc)
    if not ent.audience_window.is_open and not ent.audience_window.contains(now):
        return Decision(False, REASON_OUTSIDE_WINDOW, feature_id)

    if ent.allowlist and (
        principal.account_id is None or principal.account_id not in ent.allowlist
    ):
        return Decision(False, REASON_NOT_IN_ALLOWLIST, feature_id)

    if principal.tier.rank < ent.tier.rank:
        return Decision(False, REASON_DENIED_BY_TIER, feature_id)

    return Decision(True, REASON_ALLOWED, feature_id)


def principal_has_role(principal: Principal, role: str) -> bool:
    """Thin helper mirroring tiers.has_role for principals (used by callers)."""
    return has_role(principal.roles, role)
