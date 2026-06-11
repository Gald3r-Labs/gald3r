"""Tests for gald3r.utils (T1583) — console, fs, process, paths."""
import re
import sys

import pytest

from gald3r.utils import console, fs, paths, process

ANSI = re.compile(r"\x1b\[[0-9;]*m")


# ---- console ----

def test_console_no_color_env_disables_ansi(monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    console.info("hello")
    console.ok("done")
    console.warn("careful")
    out = capsys.readouterr().out
    assert "hello" in out and "done" in out and "careful" in out
    assert not ANSI.search(out)


def test_console_force_color_emits_ansi(monkeypatch, capsys):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    console.ok("colored")
    out = capsys.readouterr().out
    assert ANSI.search(out)
    assert "colored" in out


def test_console_err_goes_to_stderr(monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "1")
    console.err("boom")
    captured = capsys.readouterr()
    assert "boom" in captured.err
    assert "boom" not in captured.out


# ---- fs ----

@pytest.fixture
def tree(tmp_path):
    """Fixture tree: files, nested dirs, an excludable dir and file."""
    src = tmp_path / "src"
    (src / "keep").mkdir(parents=True)
    (src / "skipdir").mkdir()
    (src / "a.txt").write_text("alpha", encoding="utf-8")
    (src / "keep" / "b.md").write_text("bravo", encoding="utf-8")
    (src / "skipdir" / "c.txt").write_text("charlie", encoding="utf-8")
    (src / "skip.log").write_text("delta", encoding="utf-8")
    return src


def test_copy_tree_excludes_dirs_and_files(tree, tmp_path):
    dest = tmp_path / "dest"
    copied = fs.copy_tree(tree, dest, exclude_dirs=["skipdir"], exclude_files=["*.log"])
    assert copied == 2
    assert (dest / "a.txt").read_text(encoding="utf-8") == "alpha"
    assert (dest / "keep" / "b.md").read_text(encoding="utf-8") == "bravo"
    assert not (dest / "skipdir").exists()
    assert not (dest / "skip.log").exists()


def test_copy_tree_exclusion_is_case_insensitive(tree, tmp_path):
    dest = tmp_path / "dest2"
    fs.copy_tree(tree, dest, exclude_dirs=["SKIPDIR"], exclude_files=["SKIP.LOG"])
    assert not (dest / "skipdir").exists()
    assert not (dest / "skip.log").exists()


def test_copy_tree_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        fs.copy_tree(tmp_path / "nope", tmp_path / "dest")


def test_clear_dir_except_git(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".git" / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
    (repo / "sub").mkdir()
    (repo / "sub" / "x.txt").write_text("x", encoding="utf-8")
    (repo / "top.md").write_text("top", encoding="utf-8")
    removed = fs.clear_dir_except_git(repo)
    assert sorted(removed) == ["sub", "top.md"]
    assert (repo / ".git" / "HEAD").exists()
    assert not (repo / "sub").exists()
    assert not (repo / "top.md").exists()


def test_clear_dir_except_git_dry_run(tmp_path, capsys):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "gone.txt").write_text("g", encoding="utf-8")
    removed = fs.clear_dir_except_git(repo, dry_run=True)
    assert removed == ["gone.txt"]
    assert (repo / "gone.txt").exists()
    assert "[DRY]" in capsys.readouterr().out


def test_replace_in_file_tree(tmp_path):
    (tmp_path / "v.md").write_text("version 1.0.0 and v1.0.0", encoding="utf-8")
    (tmp_path / "other.md").write_text("no match here", encoding="utf-8")
    (tmp_path / "bin.md").write_bytes(b"\x00\x01binary-with-md-extension")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "cfg.md").write_text("version 1.0.0", encoding="utf-8")
    n = fs.replace_in_file_tree(
        tmp_path,
        {r"version 1\.0\.0": "version 2.0.0", r"v1\.0\.0": "v2.0.0"},
    )
    assert n == 1
    assert (tmp_path / "v.md").read_text(encoding="utf-8") == "version 2.0.0 and v2.0.0"
    assert (tmp_path / "bin.md").read_bytes().startswith(b"\x00\x01")
    assert (tmp_path / ".git" / "cfg.md").read_text(encoding="utf-8") == "version 1.0.0"


def test_ensure_dir(tmp_path):
    p = fs.ensure_dir(tmp_path / "a" / "b" / "c")
    assert p.is_dir()
    assert fs.ensure_dir(p) == p  # idempotent


# ---- process ----

def test_run_cmd_captures_output():
    r = process.run_cmd([sys.executable, "-c", "print('hi')"])
    assert r.ok and r.returncode == 0
    assert r.stdout.strip() == "hi"


def test_run_cmd_check_raises_on_failure():
    with pytest.raises(process.CommandError) as ei:
        process.run_cmd([sys.executable, "-c", "import sys; sys.exit(3)"])
    assert ei.value.result.returncode == 3


def test_run_cmd_check_false_returns_result():
    r = process.run_cmd([sys.executable, "-c", "import sys; sys.exit(2)"], check=False)
    assert not r.ok and r.returncode == 2


def test_run_cmd_dry_run(capsys):
    r = process.run_cmd(["definitely-not-a-real-binary"], dry_run=True)
    assert r.ok
    assert "[DRY]" in capsys.readouterr().out


def test_run_git_version():
    r = process.run_git(["--version"], check=False)
    assert r.ok
    assert "git version" in r.stdout


def test_run_git_in_temp_repo(tmp_path):
    process.run_git(["init", "-q"], cwd=tmp_path)
    r = process.run_git(["status", "--porcelain"], cwd=tmp_path)
    assert r.ok and r.stdout == ""


# ---- paths ----

def test_temp_file_created_and_cleanable():
    p = paths.temp_file(prefix="t1583_", suffix=".json")
    try:
        assert p.exists()
        assert p.name.startswith("t1583_") and p.suffix == ".json"
    finally:
        p.unlink()


def test_gald3r_root_walks_up(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / ".gald3r").mkdir(parents=True)
    nested = proj / "deep" / "nested"
    nested.mkdir(parents=True)
    assert paths.gald3r_root(nested) == proj
    assert paths.ecosystem_root(nested) == tmp_path


def test_gald3r_root_raises_when_absent(tmp_path):
    # An ancestor of the system temp dir may itself contain .gald3r/ (e.g. a
    # user-home install); the walk-up contract then legitimately resolves there.
    ancestor_hit = next(
        (d for d in [tmp_path, *tmp_path.parents] if (d / ".gald3r").is_dir()), None
    )
    if ancestor_hit is not None:
        assert paths.gald3r_root(tmp_path) == ancestor_hit
    else:
        with pytest.raises(FileNotFoundError):
            paths.gald3r_root(tmp_path)
