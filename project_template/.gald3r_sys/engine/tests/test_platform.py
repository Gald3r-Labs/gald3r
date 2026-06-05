"""Tests for platform capability reporting (systems/platform.py)."""
from __future__ import annotations

import pytest

MATRIX = """# Matrix
| Platform | Hooks | Rules | Skills | Commands | MCP | Engine tier | Rules ext |
|---|---|---|---|---|---|---|---|
| cursor | ✅ | ✅ | ✅ | ✅ | ✅ | MCP (L2) | .mdc |
| aider | ⚠ | ✅ | ❌ | ⚠ | ❌ | CLI (L1) | .md |
| subq | ❌ | ❌ | ❌ | ❌ | ❌ | files-only (L0) | — |
"""


def _matrix(project):
    (project.config.gald3r_dir / "PLATFORM_CAPABILITY_MATRIX.md").write_text(MATRIX, encoding="utf-8")


def test_status_all_parses_matrix_and_summarizes_by_tier(project):
    _matrix(project)
    rep = project.platform.status()
    assert rep["summary"]["total"] == 3
    assert rep["summary"]["MCP (L2)"] == 1 and rep["summary"]["CLI (L1)"] == 1
    cursor = next(r for r in rep["rows"] if r["platform"] == "cursor")
    assert cursor["MCP"] == "✅" and cursor["Rules ext"] == ".mdc"


def test_status_single_platform_filters(project):
    _matrix(project)
    rep = project.platform.status(platform="aider")
    assert len(rep["rows"]) == 1 and rep["rows"][0]["platform"] == "aider"


def test_unknown_platform_raises(project):
    _matrix(project)
    with pytest.raises(KeyError):
        project.platform.status(platform="nonsuch")


def test_missing_matrix_raises(project):
    with pytest.raises(FileNotFoundError):
        project.platform.status()
