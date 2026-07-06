"""Tests for the HYBRID engine resolver (T1642, né T1622) — resolution order + binary-only proof.

Run:  uv run python -m pytest gald3r_core/project_template/.gald3r_sys/scripts/tests/test_gald3r_bin.py -q
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

# Load the sibling module by path (it lives outside any package).
_MOD_PATH = Path(__file__).resolve().parents[1] / "gald3r_bin.py"
_spec = importlib.util.spec_from_file_location("gald3r_bin", _MOD_PATH)
gb = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(gb)  # type: ignore[union-attr]

_EXE = ".exe" if os.name == "nt" else ""


def _mk_project(tmp: Path, *, bundled=False, source=False) -> Path:
    root = tmp / "proj"
    (root / ".gald3r_sys").mkdir(parents=True)
    if bundled:
        bindir = root / ".gald3r_sys" / "bin"
        bindir.mkdir()
        (bindir / f"gald3r{_EXE}").write_text("binary")
    if source:
        eng = root / ".gald3r_sys" / "engine"
        eng.mkdir()
        (eng / "pyproject.toml").write_text("[project]\nname='gald3r'\n")
    return root


def test_env_override_wins(tmp_path, monkeypatch):
    binpath = tmp_path / "custom-gald3r"
    binpath.write_text("x")
    monkeypatch.setenv("GALD3R_BIN", str(binpath))
    monkeypatch.setattr(gb.shutil, "which", lambda _n: "/should/not/be/used")
    root = _mk_project(tmp_path, bundled=True, source=True)
    assert gb.resolve_engine_cmd(root) == [str(binpath)]


def test_path_binary_before_bundled(tmp_path, monkeypatch):
    monkeypatch.delenv("GALD3R_BIN", raising=False)
    monkeypatch.setattr(gb.shutil, "which", lambda _n: "/usr/bin/gald3r")
    root = _mk_project(tmp_path, bundled=True, source=True)
    assert gb.resolve_engine_cmd(root) == ["/usr/bin/gald3r"]


def test_bundled_when_no_path(tmp_path, monkeypatch):
    monkeypatch.delenv("GALD3R_BIN", raising=False)
    monkeypatch.setattr(gb.shutil, "which", lambda _n: None)
    root = _mk_project(tmp_path, bundled=True, source=True)
    expected = str(root / ".gald3r_sys" / "bin" / f"gald3r{_EXE}")
    assert gb.resolve_engine_cmd(root) == [expected]


def test_dev_source_fallback_last(tmp_path, monkeypatch):
    monkeypatch.delenv("GALD3R_BIN", raising=False)
    monkeypatch.setattr(gb.shutil, "which", lambda _n: None)
    root = _mk_project(tmp_path, bundled=False, source=True)
    cmd = gb.resolve_engine_cmd(root)
    assert cmd[:3] == ["uv", "run", "--project"]
    assert cmd[-1] == "gald3r"


def test_binary_only_ship_ignores_source(tmp_path, monkeypatch):
    # A shipped install: source present here only for the test; allow_dev_source=False
    # proves resolution does NOT touch source when a binary path is required.
    monkeypatch.delenv("GALD3R_BIN", raising=False)
    monkeypatch.setattr(gb.shutil, "which", lambda _n: None)
    root = _mk_project(tmp_path, bundled=False, source=True)
    with pytest.raises(gb.EngineNotFoundError):
        gb.resolve_engine_cmd(root, allow_dev_source=False)


def test_not_found_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("GALD3R_BIN", raising=False)
    monkeypatch.setattr(gb.shutil, "which", lambda _n: None)
    root = _mk_project(tmp_path, bundled=False, source=False)
    with pytest.raises(gb.EngineNotFoundError):
        gb.resolve_engine_cmd(root)


def test_find_project_root_walks_up(tmp_path):
    root = _mk_project(tmp_path, bundled=True)
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    assert gb.find_project_root(nested) == root
