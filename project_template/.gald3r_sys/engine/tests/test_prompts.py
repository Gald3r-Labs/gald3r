"""Tests for the prompt/judgment layer — loading, rendering, provenance, no-execution."""
from __future__ import annotations

import pytest

from gald3r.prompts import PromptAsset, PromptLibrary


def test_library_loads_seed_assets():
    lib = PromptLibrary()
    ids = lib.ids()
    # the migrated judgment families are all present
    for expected in ["persona.norse_pantheon", "role.code_reviewer", "role.qa_engineer",
                     "role.verifier", "rubric.swot", "playbook.plan", "playbook.design",
                     "voice.marketing", "rule.code_reusability"]:
        assert expected in ids, f"missing seed asset {expected}"
    assert len(ids) == len(set(ids)), "duplicate prompt ids"


def test_every_asset_has_provenance_and_body():
    lib = PromptLibrary()
    for a in lib.list():
        assert a.source, f"{a.id} has no source provenance"
        assert a.kind in {"persona", "role", "rubric", "playbook", "voice", "rule"}
        assert len(a.body) > 100, f"{a.id} body suspiciously short"


def test_get_and_kind_filter():
    lib = PromptLibrary()
    persona = lib.get("persona.norse_pantheon")
    assert persona is not None and persona.kind == "persona"
    assert "Odin" in persona.body and "Sindri" in persona.body
    roles = lib.list(kind="role")
    role_ids = {a.id for a in roles}
    assert {"role.code_reviewer", "role.qa_engineer", "role.verifier"} <= role_ids
    assert all(a.kind == "role" for a in roles)


def test_render_unknown_id_raises():
    with pytest.raises(KeyError):
        PromptLibrary().render("role.nonexistent")


def test_render_passthrough_leaves_literal_braces_and_dollars():
    # assets are full of literal {…} and $; with no declared inputs nothing is touched
    body = PromptLibrary().render("role.code_reviewer")
    assert "os.getenv()" in body and "${" not in body


def test_slot_substitution_only_declared():
    a = PromptAsset(id="x", kind="role", title="t",
                    body="Review ${target}. Leave ${undeclared} and {literal} alone.",
                    inputs=["target"], tier="slim", source="test", version=1, path=None)
    out = a.render(target="the diff")
    assert out == "Review the diff. Leave ${undeclared} and {literal} alone."
    with pytest.raises(ValueError):
        a.render()  # missing required input
