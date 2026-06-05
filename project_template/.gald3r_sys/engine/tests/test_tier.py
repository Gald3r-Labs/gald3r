"""Tests for product tier show/set (systems/tier.py) — absorbs tier_sync.ps1 pure half."""
from __future__ import annotations

import pytest

from gald3r.config import TIERS


def test_show_reports_current_tier_and_ladder(project):
    rep = project.tiers.show()
    assert rep["tier"] == "slim" and rep["ladder"] == TIERS and rep["position"] == 0
    assert rep["gated"]["workspace"] is False  # slim < controller


def test_set_persists_to_identity_and_updates_gating(project):
    rep = project.tiers.set("controller")
    assert rep == {"old": "slim", "new": "controller",
                   "path": str(project.config.gald3r_dir / ".identity"), "changed": True}
    # re-read from disk via a fresh facade
    from gald3r.core import Gald3r
    fresh = Gald3r(root=project.config.root)
    assert fresh.tier == "controller"
    assert fresh.tiers.show()["gated"]["workspace"] is True


def test_set_preserves_other_identity_keys(project):
    project.tiers.set("full")
    text = (project.config.gald3r_dir / ".identity").read_text(encoding="utf-8")
    assert "project_name=test_proj" in text and "tier=full" in text


def test_set_rejects_unknown_tier(project):
    with pytest.raises(ValueError):
        project.tiers.set("platinum")


def test_set_same_tier_reports_unchanged(project):
    rep = project.tiers.set("slim")
    assert rep["changed"] is False and rep["new"] == "slim"
