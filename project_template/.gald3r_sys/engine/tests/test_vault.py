"""Tests for VaultSystem — routing, the tags-not-topics invariant, reindex, lint."""
from __future__ import annotations

import pytest
import yaml

from gald3r.store import split_doc


def test_ingest_routes_by_type_and_reindexes(project):
    n = project.vault.ingest("Cursor Agent Mode", type="platform_doc",
                             source="https://docs.cursor.com/", tags=["cursor", "ide"],
                             ingestion_type="crawl", date_="2026-06-03")
    assert n.rel == "research/platforms/cursor-agent-mode.md"
    fm, _ = split_doc(n.path.read_text(encoding="utf-8"))
    assert fm["tags"] == ["cursor", "ide"] and fm["type"] == "platform_doc"

    idx = yaml.safe_load(project.config.gald3r_dir.joinpath("vault/_index.yaml").read_text(encoding="utf-8"))
    assert len(idx["notes"]) == 1
    assert idx["notes"][0]["path"] == "research/platforms/cursor-agent-mode.md"
    assert idx["notes"][0]["tags"] == ["cursor", "ide"]

    home = project.config.gald3r_dir.joinpath("vault/index.md").read_text(encoding="utf-8")
    assert "Total notes: 1" in home
    assert "[[research/platforms/cursor-agent-mode|Cursor Agent Mode]]" in home


def test_topics_is_migrated_to_tags(project):
    # D021: an incoming `topics:` must never reach disk — it becomes `tags:`.
    n = project.vault.ingest("Legacy note here", type="article", source="x",
                             topics=["legacy", "thing"])
    fm, _ = split_doc(n.path.read_text(encoding="utf-8"))
    assert "topics" not in fm
    assert fm["tags"] == ["legacy", "thing"]


def test_log_is_appended(project):
    project.vault.ingest("First note title", type="article", source="a", tags=["t"])
    project.vault.ingest("Second note title", type="concept", source="b", tags=["t"])
    log = project.config.gald3r_dir.joinpath("vault/log.md").read_text(encoding="utf-8")
    assert log.count("| ingest |") == 2
    assert "research/articles/first-note-title.md" in log
    assert "knowledge/concepts/second-note-title.md" in log


def test_list_filter_and_get(project):
    project.vault.ingest("Alpha article x", type="article", source="a", tags=["t"])
    project.vault.ingest("Beta concept y", type="concept", source="b", tags=["t"])
    assert len(project.vault.list()) == 2
    assert len(project.vault.list(type="concept")) == 1
    got = project.vault.get("beta-concept-y")
    assert got is not None and got.type == "concept"


def test_lint_flags_missing_tags_and_legacy_topics(project):
    # write a note straight to disk with a legacy key + empty tags, bypassing ingest
    bad = project.config.gald3r_dir / "vault/research/articles/bad.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        '---\ndate: 2026-06-03\ntype: article\ningestion_type: manual\n'
        'source: x\ntitle: "Bad note"\ntopics: []\n---\n# Bad\n',
        encoding="utf-8",
    )
    issues = project.vault.lint()
    kinds = {i["issue"] for i in issues}
    assert any("legacy 'topics:'" in k for k in kinds)
    assert any("empty tags" in k for k in kinds)


def test_ingest_rejects_short_title(project):
    with pytest.raises(ValueError):
        project.vault.ingest("ab", type="article", source="x", tags=["t"])
