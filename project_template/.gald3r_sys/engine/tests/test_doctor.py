"""Tests for the read-only health check (systems/doctor.py)."""
from __future__ import annotations


def _seed_indexes(project):
    gd = project.config.gald3r_dir
    (gd / "tasks" / "open").mkdir(parents=True, exist_ok=True)
    (gd / "TASKS.md").write_text("# TASKS\n", encoding="utf-8")
    (gd / "BUGS.md").write_text("# BUGS\n", encoding="utf-8")


def test_clean_project_scores_high_and_is_read_only(project):
    _seed_indexes(project)
    project.tasks.create(title="real task")            # creates file + index row in sync
    before = (project.config.tasks_md).read_text(encoding="utf-8")
    rep = project.doctor.check()
    assert rep["overall_score"] >= 75
    assert any(s["name"] == "structure" and s["status"] == "PASS" for s in rep["systems"])
    # doctor must not mutate the index
    assert (project.config.tasks_md).read_text(encoding="utf-8") == before


def test_phantom_row_is_flagged(project):
    _seed_indexes(project)
    # index references T1 but no task file exists -> phantom
    (project.config.tasks_md).write_text("# TASKS\n\n- [📋] **T1** ghost\n", encoding="utf-8")
    rep = project.doctor.check()
    tasks = next(s for s in rep["systems"] if s["name"] == "tasks")
    assert tasks["status"] in ("PARTIAL", "FAIL")
    assert any("phantom" in f for f in tasks["failures"])


def test_orphan_file_is_flagged(project):
    _seed_indexes(project)
    project.tasks.create(title="real task")             # writes file + syncs index (T1 in both)
    (project.config.tasks_md).write_text("# TASKS\n", encoding="utf-8")  # wipe index -> orphan
    rep = project.doctor.check()
    tasks = next(s for s in rep["systems"] if s["name"] == "tasks")
    assert any("orphan" in f for f in tasks["failures"])


def test_only_filter_limits_groups(project):
    _seed_indexes(project)
    rep = project.doctor.check(only=["structure"])
    assert {s["name"] for s in rep["systems"]} == {"structure"}


def test_encoding_flags_non_ascii_ps1_without_bom(project):
    (project.config.gald3r_dir / "bad.ps1").write_bytes("Write-Host '📋'\n".encode("utf-8"))  # no BOM
    enc = next(s for s in project.doctor.check(only=["encoding"])["systems"] if s["name"] == "encoding")
    assert enc["status"] == "FAIL" and any("BOM" in f for f in enc["failures"])


def test_encoding_passes_when_non_ascii_ps1_has_bom(project):
    (project.config.gald3r_dir / "good.ps1").write_bytes(b"\xef\xbb\xbf" + "Write-Host '📋'\n".encode("utf-8"))
    enc = next(s for s in project.doctor.check(only=["encoding"])["systems"] if s["name"] == "encoding")
    assert enc["status"] == "PASS"


def test_next_bug_id_counter_is_not_reported_as_phantom(project):
    # regression for the demo-test finding: BUGS.md carries a "## Next Bug ID: BUG-NNN"
    # counter; the doctor must not mistake that next-id for an indexed-but-fileless bug.
    _seed_indexes(project)
    project.bugs.create(title="a genuine logged bug")   # renders BUGS.md incl. the Next-ID line
    bugs = next(s for s in project.doctor.check(only=["bugs"])["systems"] if s["name"] == "bugs")
    assert bugs["status"] == "PASS", bugs["failures"]    # was PARTIAL with phantom [2] before the fix


def test_bug_whose_title_mentions_next_id_is_not_a_false_orphan(project):
    # the meta-case: a bug titled "...'Next Bug ID: BUG-NNN'..." must still be counted — the
    # counter-strip is anchored to the heading, not any line mentioning the text.
    _seed_indexes(project)
    project.bugs.create(title="mis-parses the 'Next Bug ID: BUG-NNN' counter line", severity="medium")
    rep = project.bugs.sync()
    assert rep["orphan"] == [] and rep["phantom"] == []  # sync converges (was orphan [N])
    bugs = next(s for s in project.doctor.check(only=["bugs"])["systems"] if s["name"] == "bugs")
    assert bugs["status"] == "PASS", bugs["failures"]
