from __future__ import annotations

import pytest

from gald3r.core import Gald3r


def _make_project(tmp_path, tier: str) -> Gald3r:
    gd = tmp_path / ".gald3r"
    gd.mkdir()
    (gd / ".identity").write_text(
        f"project_name=test_proj\ngald3r_version=1.10.0\ntier={tier}\n", encoding="utf-8"
    )
    return Gald3r(root=tmp_path)


@pytest.fixture
def project(tmp_path):
    """A throwaway gald3r project rooted at tmp_path with a minimal .gald3r/ (slim tier)."""
    return _make_project(tmp_path, "slim")


@pytest.fixture
def controller_project(tmp_path):
    """A throwaway gald3r project at controller tier (unlocks workspace.*)."""
    return _make_project(tmp_path, "controller")
