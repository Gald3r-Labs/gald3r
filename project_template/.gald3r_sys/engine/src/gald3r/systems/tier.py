"""Product tier — `gald3r tier show` / `gald3r tier set`. Absorbs the pure half of
custom_scripts/tier_sync.ps1.

The engine ladder is slim < full < controller < maintainer (config.TIERS); the tier lives in
`.gald3r/.identity` as `tier=<value>` and gates which systems activate (e.g. workspace is
controller-tier). This is pure deterministic local file I/O. The script's *other* job — a
dev-only cross-repo template mirror with hardcoded paths, currently dead code — is intentionally
NOT absorbed into the pure engine (it is a maintainer build tool, not a per-project operation).
"""
from __future__ import annotations

import re
from typing import Any, Dict

from gald3r.config import Config, TIERS

# systems that require a minimum tier to activate (kept in sync with the facade gates)
TIER_GATED = {"workspace": "controller"}


class TierSystem:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    @property
    def _identity_path(self):
        return self.cfg.gald3r_dir / ".identity"

    def show(self) -> Dict[str, Any]:
        tier = self.cfg.tier
        idx = TIERS.index(tier)
        return {
            "tier": tier,
            "ladder": TIERS,
            "position": idx,
            "gated": {sys: TIERS.index(tier) >= TIERS.index(req)
                      for sys, req in TIER_GATED.items()},
        }

    def set(self, tier: str) -> Dict[str, Any]:
        tier = tier.lower().strip()
        if tier not in TIERS:
            raise ValueError(f"unknown tier '{tier}'; valid: {', '.join(TIERS)}")
        old = self.cfg.tier
        path = self._identity_path
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []

        replaced = False
        for i, line in enumerate(lines):
            if re.match(r"\s*tier\s*=", line) and not line.lstrip().startswith("#"):
                lines[i] = re.sub(r"(\s*tier\s*=\s*).*", rf"\g<1>{tier}", line)
                replaced = True
                break
        if not replaced:
            lines.append(f"tier={tier}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        # refresh the cached identity so a subsequent .show() reflects the change
        self.cfg.identity["tier"] = tier
        return {"old": old, "new": tier, "path": str(path), "changed": old != tier}
