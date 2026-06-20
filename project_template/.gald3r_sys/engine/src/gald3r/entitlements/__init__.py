"""Server-authoritative entitlement / feature-flag core (T527).

GUI-free, dependency-free building blocks the T527 epic composes into the paywall:

* :mod:`gald3r.entitlements.tiers`      — canonical tier enum + role checks (T556)
* :mod:`gald3r.entitlements.model`      — typed entitlement record + JSON (T553)
* :mod:`gald3r.entitlements.loader`     — on-disk flag-config format + loader (T555)
* :mod:`gald3r.entitlements.evaluator`  — pure allow/deny decision function (T554)

"engine enforces; client advises" (T491): the same pure evaluator backs both the
Throne UX gate and the Agent runtime gate, so nothing here touches the network,
the filesystem (beyond an explicitly passed path/bytes), or any UI.
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

from gald3r.entitlements.tiers import Tier, has_role, meets_tier
from gald3r.entitlements.model import Entitlement, AudienceWindow, EntitlementError
from gald3r.entitlements.evaluator import Decision, Principal, evaluate
from gald3r.entitlements.loader import load_config, load_config_text, ConfigError

__all__ = [
    "Tier",
    "has_role",
    "meets_tier",
    "Entitlement",
    "AudienceWindow",
    "EntitlementError",
    "Decision",
    "Principal",
    "evaluate",
    "load_config",
    "load_config_text",
    "ConfigError",
]
