"""Tests for FeatureSystem and PrdSystem (flat folder-backed, via _base)."""
from __future__ import annotations

import pytest


# ---- features ----

def test_feature_create_and_index(project):
    a = project.features.create(title="First feature here", priority="high")
    b = project.features.create(title="Second feature here")
    assert a.id == "feat-001" and b.id == "feat-002"
    assert a.status == "staging"
    assert a.path.parent.name == "features"          # flat (no status subfolder)
    md = project.config.gald3r_dir.joinpath("FEATURES.md").read_text(encoding="utf-8")
    assert "### Staging" in md and "**feat-001**" in md
    assert "Next feat ID**: feat-003" in md


def test_feature_promote_groups_in_index(project):
    f = project.features.create(title="Promotable feature here")
    project.features.update(f.id, status="shipped")
    md = project.config.gald3r_dir.joinpath("FEATURES.md").read_text(encoding="utf-8")
    shipped, _, staging = md.partition("### Committed")
    assert "**feat-001**" in shipped            # appears under ### Shipped
    assert project.features.get("feat-001").status == "shipped"


# ---- prds ----

def test_prd_create(project):
    p = project.prds.create(title="First PRD document here")
    assert p.id == "PRD-001" and p.status == "draft"
    md = project.config.gald3r_dir.joinpath("PRDS.md").read_text(encoding="utf-8")
    assert "| PRD-001 |" in md and "Next PRD ID**: PRD-002" in md


def test_prd_freeze_blocks_updates(project):
    p = project.prds.create(title="A PRD to be frozen here")
    project.prds.update(p.id, status="released")        # draft -> released (allowed)
    assert project.prds.get(p.id).status == "released"
    with pytest.raises(PermissionError):                 # now immutable (C-019)
        project.prds.update(p.id, title="Sneaky retitle attempt")
    with pytest.raises(PermissionError):
        project.prds.update(p.id, status="draft")


def test_prd_status_validation(project):
    with pytest.raises(ValueError):
        project.prds.create(title="Bad status PRD here", status="bogus")
