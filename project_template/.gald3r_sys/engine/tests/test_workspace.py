"""Tests for WorkspaceSystem — tier gate, topology, the INBOX conflict gate, manifest VALIDATE."""
from __future__ import annotations

import pytest
import yaml

# minimal valid Workspace-Control manifest (matches the PARSE_MANIFEST/VALIDATE contract)
_GOOD_MANIFEST = """\
schema:
  name: gald3r_workspace_control_manifest
  version: 1.1.0
workspace:
  id: "proj-1"
  display_name: "Test Workspace"
  lifecycle_status: active
  owner_repository_id: "proj-1"
  bootstrap_member_ids:
    - "proj-1"
  source_of_truth:
    canonical_machine_registry: .gald3r/linking/workspace_manifest.yaml
repositories: []
controlled_members:
  expected_count: 0
  repository_ids: []
routing_policy:
  default: controller
wpac_relationship:
  role: standalone
"""


def _write_manifest(project, text):
    p = project.config.gald3r_dir / "linking/workspace_manifest.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---- tier gate ----

def test_workspace_is_controller_tier(project):
    # `project` fixture is slim → facade must refuse
    with pytest.raises(PermissionError):
        _ = project.workspace


def test_workspace_unlocked_at_controller(controller_project):
    assert controller_project.workspace is not None


# ---- topology ----

def test_topology_roundtrip(controller_project):
    ws = controller_project.workspace
    ws.set_role("parent")
    ws.add_child("child_app", project_path="/x/child_app", project_id="c1")
    ws.add_sibling("sister_lib")
    topo = ws.read_topology()
    assert topo["role"] == "parent"
    assert topo["children"][0]["project_name"] == "child_app"
    assert topo["siblings"][0]["project_name"] == "sister_lib"
    assert "last_updated" in topo
    # written frontmatter is valid nested YAML on disk
    raw = (controller_project.config.gald3r_dir / "linking/topology.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(raw.split("---")[1])
    assert fm["children"][0]["project_id"] == "c1"


def test_topology_rejects_bad_role_and_dupes(controller_project):
    ws = controller_project.workspace
    with pytest.raises(ValueError):
        ws.set_role("overlord")
    ws.add_child("dup")
    with pytest.raises(ValueError):
        ws.add_child("dup")


# ---- inbox / conflict gate ----

def test_inbox_conflict_gate(controller_project):
    ws = controller_project.workspace
    assert ws.has_conflicts() is False
    ws.add_item("CONFLICT", "parent_proj", "schema collision on TASKS.md", when="2026-06-03")
    ws.add_item("REQUEST", "child_proj", "please bump shared lib", when="2026-06-03")
    assert ws.has_conflicts() is True
    conflicts = ws.conflicts()
    assert len(conflicts) == 1
    assert conflicts[0].from_project == "parent_proj"
    assert len(ws.list_items()) == 2


def test_inbox_resolve_archives(controller_project):
    ws = controller_project.workspace
    ws.add_item("CONFLICT", "parent_proj", "blocking conflict", when="2026-06-03")
    ws.resolve("blocking conflict", "rebased onto parent schema", when="2026-06-04")
    assert ws.has_conflicts() is False
    resolved = ws.list_items("RESOLVED")
    assert len(resolved) == 1 and resolved[0].done is True
    assert "rebased onto parent schema" in resolved[0].text


def test_inbox_rejects_bad_section(controller_project):
    with pytest.raises(ValueError):
        controller_project.workspace.add_item("BOGUS", "x", "y")


# ---- manifest VALIDATE / status ----

def test_manifest_validate_passes_on_good_stub(controller_project):
    _write_manifest(controller_project, _GOOD_MANIFEST)
    ws = controller_project.workspace
    assert ws.validate_manifest() == []
    st = ws.status()
    assert st["valid"] is True and st["active"] is False
    assert st["summary"] == "inactive / current repository only"


def test_manifest_validate_catches_missing_keys(controller_project):
    bad = "schema:\n  name: x\nworkspace:\n  id: p1\nrepositories: []\n"
    _write_manifest(controller_project, bad)
    errs = controller_project.workspace.validate_manifest()
    assert any("controlled_members" in e for e in errs)
    assert any("workspace.display_name" in e for e in errs)
    assert any("canonical_machine_registry" in e for e in errs)


def test_manifest_status_active_with_members(controller_project):
    text = _GOOD_MANIFEST.replace(
        "controlled_members:\n  expected_count: 0\n  repository_ids: []",
        "controlled_members:\n  expected_count: 2\n  repository_ids:\n    - m1\n    - m2",
    )
    _write_manifest(controller_project, text)
    st = controller_project.workspace.status()
    assert st["active"] is True and st["member_count"] == 2
    assert controller_project.workspace.member_list() == ["m1", "m2"]


def test_status_without_manifest(controller_project):
    st = controller_project.workspace.status()
    assert st["active"] is False and st["valid"] is False
