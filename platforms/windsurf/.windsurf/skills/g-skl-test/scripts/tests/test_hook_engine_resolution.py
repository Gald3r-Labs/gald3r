#!/usr/bin/env python3
"""Unit-style test for _hook_common.resolve_engine_argv (P3 Tier-0, T179/T191).

Proves the shared engine-resolution helper added to
neutral_source/hooks/_hook_common.py resolves the gald3r engine WITHOUT
requiring the loose, gitignored `.gald3r_sys/scripts/gald3r_bin.py` IP
script to be present on disk. That was the bug this task fixes: an install
under the self-contained delivery model never carries that loose script, so
the ~7 hooks that previously shelled out to it directly (build the resolver
path, bail to None if it is not on disk, else dynamically import it) went
silently dormant even when a `gald3r` binary was sitting right there on
PATH -- because the PATH check itself lived inside the absent script.

Resolution order under test:
  1. GALD3R_BIN env var (an existing file) wins over everything else.
  2. `gald3r` on PATH wins over the legacy loose resolver.
  3. The legacy loose `.gald3r_sys/scripts/gald3r_bin.py` resolver is used
     as back-compat only when neither (1) nor (2) resolves anything.
  4. Nothing resolvable -> returns None AND appends one diagnostic line to
     `.gald3r/logs/hook_diag.log` (never stdout) instead of silently
     no-opping forever.

Runnable standalone: `python test_hook_engine_resolution.py` (exit 0 pass,
1 fail), matching the g-skl-test scripts/tests suite style -- see
test_ggo_scheduled_reset_t635.py for the locate/assert/cprint pattern this
file follows.
"""

# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations
# --- gald3r calltrace bootstrap (T268) -- injected; inert unless gald3r call tracing is
# enabled. Strip everywhere: python scripts/inject_calltrace_bootstrap.py --strip
import os as _g3ct_os
_g3ct_home = _g3ct_os.environ.get("GALD3R_HOME") or _g3ct_os.path.join(
    _g3ct_os.path.expanduser("~"), ".gald3r")
_g3ct_env = (_g3ct_os.environ.get("GALD3R_TRACE_CALLS") or "").strip().lower()
if _g3ct_env not in ("", "0", "off", "false", "no") or _g3ct_os.path.isfile(
        _g3ct_os.path.join(_g3ct_home, "calltrace.json")):
    try:
        _g3ct_bs = _g3ct_os.path.join(_g3ct_home, "calltrace_bootstrap.py")
        if _g3ct_os.path.isfile(_g3ct_bs):
            with open(_g3ct_bs, "r", encoding="utf-8") as _g3ct_fh:
                exec(compile(_g3ct_fh.read(), _g3ct_bs, "exec"),
                     {"__g3ct_script__": __file__,
                      "__name__": "_gald3r_calltrace_exec"})
    except Exception:
        pass
# --- end gald3r calltrace bootstrap ---

import importlib.util
import os
import shutil
import stat
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional


def _color_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "gray": "90"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (mirrors the other g-skl-test fixtures)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


def find_repo_root(start: Path) -> Path:
    """Walk up from ``start`` to the nearest ancestor containing .gald3r."""
    d = start
    while True:
        if (d / ".gald3r").is_dir():
            return d
        parent = d.parent
        if parent == d:
            return start
        d = parent


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(SCRIPT_DIR)


def locate_hook_common() -> Optional[Path]:
    """Locate _hook_common.py, preferring the tracked source of truth (T177)
    over the gitignored, regenerated per-platform copies -- same preference
    order as test_ggo_scheduled_reset_t635.py's locate_hook()."""
    for candidate in (
        REPO_ROOT
        / "src"
        / "gald3r_core"
        / "platform"
        / "pipeline"
        / "neutral_source"
        / "hooks"
        / "_hook_common.py",
        REPO_ROOT / ".claude" / "hooks" / "_hook_common.py",
        REPO_ROOT / ".cursor" / "hooks" / "_hook_common.py",
    ):
        if candidate.is_file():
            return candidate
    return None


def load_hook_common():
    """Dynamically import _hook_common.py under a private module name so
    this test never collides with a hook's own `import _hook_common`."""
    path = locate_hook_common()
    if path is None:
        return None
    spec = importlib.util.spec_from_file_location("_hook_common_under_test", str(path))
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_fails = 0


def assert_(cond: bool, msg: str) -> None:
    global _fails
    if cond:
        cprint(f"  [PASS] {msg}", "green")
    else:
        cprint(f"  [FAIL] {msg}", "red")
        _fails += 1


def new_temp_dir() -> Path:
    r = Path(tempfile.gettempdir()) / f"hookcommon_engine_res_{uuid.uuid4().hex[:8]}"
    r.mkdir(parents=True, exist_ok=True)
    return r


_EXE_SUFFIX = ".cmd" if os.name == "nt" else ""


def write_fake_gald3r_on_path(path_dir: Path, marker: str) -> Path:
    """Create a fake `gald3r` executable in path_dir that shutil.which() can
    find -- content is irrelevant, only its resolved path is asserted on."""
    path_dir.mkdir(parents=True, exist_ok=True)
    exe = path_dir / f"gald3r{_EXE_SUFFIX}"
    if os.name == "nt":
        exe.write_text("@echo %s\r\n" % marker, encoding="utf-8")
    else:
        exe.write_text("#!/bin/sh\necho %s\n" % marker, encoding="utf-8")
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return exe


def write_legacy_resolver(project_root: Path, argv_literal: str) -> Path:
    """Write a mock `.gald3r_sys/scripts/gald3r_bin.py` exposing
    resolve_engine_cmd(project_root) -> [argv_literal], mirroring the real
    (untracked, gitignored) IP script's public contract closely enough for
    resolve_engine_argv()'s back-compat tier to exercise it."""
    scripts_dir = project_root / ".gald3r_sys" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    resolver = scripts_dir / "gald3r_bin.py"
    resolver.write_text(
        "def resolve_engine_cmd(project_root=None):\n    return [%r]\n" % argv_literal,
        encoding="utf-8",
    )
    return resolver


class EnvSandbox:
    """Save/restore PATH and GALD3R_BIN around a test so cases never leak
    into each other or depend on the host machine's real PATH/engine state."""

    def __init__(self, path_value: Optional[str], gald3r_bin: Optional[str]):
        self._path_value = path_value
        self._gald3r_bin = gald3r_bin
        self._saved: dict = {}

    def __enter__(self):
        self._saved["PATH"] = os.environ.get("PATH")
        self._saved["GALD3R_BIN"] = os.environ.get("GALD3R_BIN")
        if self._path_value is not None:
            os.environ["PATH"] = self._path_value
        if self._gald3r_bin is not None:
            os.environ["GALD3R_BIN"] = self._gald3r_bin
        else:
            os.environ.pop("GALD3R_BIN", None)
        return self

    def __exit__(self, *exc):
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        return False


def _cleanup(*paths: Path) -> None:
    for p in paths:
        shutil.rmtree(p, ignore_errors=True)


def _paths_equal(actual: Optional[list], expected: Path) -> bool:
    """Case-insensitive, single-element argv-vs-Path comparison.

    Windows filesystems are case-insensitive, and shutil.which() resolves a
    bare command name by appending each PATHEXT extension verbatim (e.g.
    `.CMD`) regardless of the on-disk file's actual casing (e.g. `.cmd`) --
    both name the same file, so a strict string == would spuriously fail."""
    if not actual or len(actual) != 1:
        return False
    return str(Path(actual[0])).casefold() == str(expected).casefold()


def main() -> int:
    mod = load_hook_common()
    if mod is None:
        cprint(f"FAIL: _hook_common.py not found under {REPO_ROOT}", "red")
        return 1
    if not hasattr(mod, "resolve_engine_argv"):
        cprint("FAIL: _hook_common.resolve_engine_argv is missing", "red")
        return 1

    # ---- T1: GALD3R_BIN env var wins over PATH and the legacy resolver ----
    cprint("\n=== T1: GALD3R_BIN env var wins ===", "cyan")
    root = new_temp_dir()
    path_dir = new_temp_dir()
    fake_on_path = write_fake_gald3r_on_path(path_dir, "PATH_BINARY")
    write_legacy_resolver(root, "LEGACY_RESOLVER_BINARY")
    explicit_bin = root / "explicit_gald3r_bin.exe"
    explicit_bin.write_text("", encoding="utf-8")
    with EnvSandbox(path_value=str(path_dir), gald3r_bin=str(explicit_bin)):
        result = mod.resolve_engine_argv(root, hook_name="test-t1")
    assert_(_paths_equal(result, explicit_bin), f"GALD3R_BIN wins: got {result!r}")
    _cleanup(root, path_dir)

    # ---- T2: env unset, fake gald3r on PATH -> PATH wins over legacy resolver
    cprint("\n=== T2: PATH wins (env unset, legacy resolver also present) ===", "cyan")
    root = new_temp_dir()
    path_dir = new_temp_dir()
    fake_on_path = write_fake_gald3r_on_path(path_dir, "PATH_BINARY")
    write_legacy_resolver(root, "LEGACY_RESOLVER_BINARY")
    with EnvSandbox(path_value=str(path_dir), gald3r_bin=None):
        result = mod.resolve_engine_argv(root, hook_name="test-t2")
    assert_(_paths_equal(result, fake_on_path), f"PATH wins over legacy resolver: got {result!r}")
    _cleanup(root, path_dir)

    # ---- T3: nothing resolvable -> None + loud diagnostic (never silent) ----
    cprint("\n=== T3: nothing resolvable -> None + diagnostic logged ===", "cyan")
    root = new_temp_dir()
    empty_path_dir = new_temp_dir()
    with EnvSandbox(path_value=str(empty_path_dir), gald3r_bin=None):
        result = mod.resolve_engine_argv(root, hook_name="test-t3-miss")
    assert_(result is None, f"no engine resolvable -> None: got {result!r}")
    diag_log = root / ".gald3r" / "logs" / "hook_diag.log"
    assert_(diag_log.is_file(), "diagnostic log file was created (loud degrade, not silent)")
    if diag_log.is_file():
        diag_text = diag_log.read_text(encoding="utf-8", errors="replace")
        assert_("test-t3-miss" in diag_text, "diagnostic line names the calling hook")
        assert_("not resolved" in diag_text, "diagnostic line explains the miss")
    _cleanup(root, empty_path_dir)

    # ---- T4: legacy resolver back-compat used when PATH/env absent --------
    cprint("\n=== T4: legacy resolver used when PATH/env absent (back-compat) ===", "cyan")
    root = new_temp_dir()
    empty_path_dir = new_temp_dir()
    write_legacy_resolver(root, "LEGACY_RESOLVER_BINARY")
    with EnvSandbox(path_value=str(empty_path_dir), gald3r_bin=None):
        result = mod.resolve_engine_argv(root, hook_name="test-t4")
    assert_(
        result == ["LEGACY_RESOLVER_BINARY"], f"legacy resolver back-compat used: got {result!r}"
    )
    _cleanup(root, empty_path_dir)

    # ---- T5: process-lifetime cache keys on (root, GALD3R_BIN, PATH) -- no
    # stale hit when the env changes for the SAME root (P3, adversarial-
    # panel FIX 8) --------------------------------------------------------
    cprint("\n=== T5: cache keys on (root, GALD3R_BIN, PATH) -- no stale hit ===", "cyan")
    root = new_temp_dir()
    path_dir_a = new_temp_dir()
    path_dir_b = new_temp_dir()
    fake_a = write_fake_gald3r_on_path(path_dir_a, "FAKE_A")
    fake_b = write_fake_gald3r_on_path(path_dir_b, "FAKE_B")
    with EnvSandbox(path_value=str(path_dir_a), gald3r_bin=None):
        result_a = mod.resolve_engine_argv(root, hook_name="test-t5-a")
    assert_(_paths_equal(result_a, fake_a), f"first PATH resolves fake_a: got {result_a!r}")
    with EnvSandbox(path_value=str(path_dir_b), gald3r_bin=None):
        # Same root, DIFFERENT PATH -- must resolve fresh, not return a
        # stale cache hit for fake_a from the call just above.
        result_b = mod.resolve_engine_argv(root, hook_name="test-t5-b")
    assert_(
        _paths_equal(result_b, fake_b),
        f"changed PATH (same root) resolves fake_b, not a stale cached fake_a: got {result_b!r}",
    )
    _cleanup(root, path_dir_a, path_dir_b)

    # ---- T6: the miss diagnostic is logged ONCE per process per root, even
    # across calls with a DIFFERENT (still-missing) env fingerprint (P3,
    # adversarial-panel FIX 8) ---------------------------------------------
    cprint("\n=== T6: miss diagnostic logged once per root (not once per env) ===", "cyan")
    root = new_temp_dir()
    empty_path_dir_1 = new_temp_dir()
    empty_path_dir_2 = new_temp_dir()
    with EnvSandbox(path_value=str(empty_path_dir_1), gald3r_bin=None):
        mod.resolve_engine_argv(root, hook_name="test-t6-first")
    with EnvSandbox(path_value=str(empty_path_dir_2), gald3r_bin=None):
        # A DIFFERENT (still empty) PATH -> a distinct cache key, so this
        # call actually re-runs resolution rather than being served from
        # T6's first cache entry -- proves the once-per-root diagnostic
        # dedup is independent of the argv-result cache, not just a side
        # effect of it.
        mod.resolve_engine_argv(root, hook_name="test-t6-second")
    diag_log = root / ".gald3r" / "logs" / "hook_diag.log"
    assert_(diag_log.is_file(), "diagnostic log created on first miss")
    if diag_log.is_file():
        lines = [
            ln
            for ln in diag_log.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.strip()
        ]
        assert_(
            len(lines) == 1,
            f"exactly one diagnostic line for this root across 2 distinct-env misses, "
            f"got {len(lines)}",
        )
    _cleanup(root, empty_path_dir_1, empty_path_dir_2)

    print("")
    if _fails == 0:
        cprint("ALL HOOK ENGINE RESOLUTION TESTS PASSED", "green")
        return 0
    cprint(f"{_fails} ASSERTION(S) FAILED", "red")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
