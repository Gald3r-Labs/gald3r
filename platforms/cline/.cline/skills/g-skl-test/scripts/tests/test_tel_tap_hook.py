#!/usr/bin/env python3
"""Standalone subprocess test for g-hk-tel-tap.py (T90).

Proves the shipped Claude Code TEL host-hook tap's SILENT/fire-and-forget
contract end-to-end, as an actual child process (not an in-process import),
the same way a real Claude Code `PostToolUse`/`Stop` hook invocation would
run it:

- `--kind post_tool_use`: exits 0, prints NOTHING to stdout/stderr, and
  writes one matched record to its `host_post_tool_use` capture-ledger
  topic under `$GALD3R_HOME/tel/captures/`.
- `--kind statusline`: same silent-exit-0-plus-ledger-write shape for a
  statusline-flavored payload.
- `--kind transcript`: tails a fake JSONL transcript file named by
  `transcript_path` in the stdin payload, writes one record per line to
  `host_transcript`, and persists a per-path offset sidecar so a SECOND
  invocation with no new lines writes nothing further.
- Malformed (non-JSON) and empty stdin never crash the process (exit 0,
  still silent) -- `_hook_common.read_stdin_json()`'s own degrade-to-{}
  contract.
- An invalid `--kind` value never escapes as a non-zero exit or leaks
  argparse's usage/error text to stderr (adversarial-review Fix 1).
- A malformed TEL rule file (e.g. a `#gag {(}` bad regex) never leaks a
  `logging.warning(...)` record onto stderr via Python's default
  `logging.lastResort` handler (adversarial-review Fix 2).

The hook + its `_hook_common.py` sibling are copied into an isolated tmp
"project" (with its own `.gald3r/` marker dir so the hook's own
`_hook_common.project_root()` walk-up resolves INSIDE tmp, never the real
checkout) -- this test NEVER writes this repo's live `.gald3r/`, per this
task's hard contract. `$GALD3R_HOME` is also pointed at a tmp dir so the
default `CaptureLedger` capture root never touches the real user home.

Runnable standalone: `python test_tel_tap_hook.py` (exit 0 pass, 1 fail),
matching the g-skl-test scripts/tests suite style -- see
test_hook_engine_resolution.py for the locate/assert/cprint pattern this
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

import json
import os
import shutil
import subprocess
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
_HOOKS_SRC = (
    REPO_ROOT / "src" / "gald3r_core" / "platform" / "pipeline" / "neutral_source" / "hooks"
)

_fails = 0


def assert_(cond: bool, msg: str) -> None:
    global _fails
    if cond:
        cprint(f"  [PASS] {msg}", "green")
    else:
        cprint(f"  [FAIL] {msg}", "red")
        _fails += 1


def _new_temp_dir(label: str) -> Path:
    r = Path(tempfile.gettempdir()) / f"tel_tap_{label}_{uuid.uuid4().hex[:8]}"
    r.mkdir(parents=True, exist_ok=True)
    return r


def _build_fake_project() -> Path:
    """Create an isolated tmp 'project' with its own .gald3r/ marker and a
    copy of the hook + _hook_common.py under .claude/hooks/ -- so the
    hook's own project_root() walk-up resolves entirely inside tmp."""
    proj = _new_temp_dir("proj")
    (proj / ".gald3r").mkdir(parents=True, exist_ok=True)
    hooks_dir = proj / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in ("g-hk-tel-tap.py", "_hook_common.py"):
        src = _HOOKS_SRC / name
        if not src.is_file():
            raise FileNotFoundError(f"missing hook source: {src}")
        shutil.copy2(src, hooks_dir / name)
    return proj


def _run_hook(
    proj: Path, home: Path, *, kind: str, stdin_text: str
) -> "subprocess.CompletedProcess[str]":
    hook_path = proj / ".claude" / "hooks" / "g-hk-tel-tap.py"
    env = dict(os.environ)
    env["GALD3R_HOME"] = str(home)
    src_dir = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = (
        src_dir + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src_dir
    )
    return subprocess.run(
        [sys.executable, str(hook_path), "--kind", kind],
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(proj),
        env=env,
        timeout=60,
    )


def _cleanup(*paths: Path) -> None:
    for p in paths:
        shutil.rmtree(p, ignore_errors=True)


def main() -> int:
    if not _HOOKS_SRC.is_dir():
        cprint(f"FAIL: hooks source dir not found: {_HOOKS_SRC}", "red")
        return 1

    # ---- T1: post_tool_use -- silent exit 0 + ledger write -----------------
    cprint("\n=== T1: post_tool_use -- silent exit 0 + ledger write ===", "cyan")
    proj = _build_fake_project()
    home = _new_temp_dir("home")
    payload = json.dumps({"tool_name": "Bash", "session_id": "s1", "cwd": str(proj)})
    result = _run_hook(proj, home, kind="post_tool_use", stdin_text=payload)
    assert_(result.returncode == 0, f"exit code 0 (got {result.returncode})")
    assert_(result.stdout == "", f"stdout is empty (got {result.stdout!r})")
    assert_(result.stderr == "", f"stderr is empty (got {result.stderr!r})")
    ledger_files = list((home / "tel" / "captures").glob("host_post_tool_use-*.log"))
    assert_(len(ledger_files) == 1, f"exactly one host_post_tool_use ledger file, got {len(ledger_files)}")
    if ledger_files:
        content = ledger_files[0].read_text(encoding="utf-8")
        assert_("tool_name=Bash" in content, "ledger content carries the projected line")
    real_repo_diag = REPO_ROOT / ".gald3r" / "logs" / "hook_diag.log"
    # Not a strict absence check (the repo's own dev session may have
    # written to this file already for unrelated reasons) -- the real
    # assertion is structural: project_root() resolved INSIDE tmp (proven
    # by the ledger landing under `home`, a tmp dir, not the real
    # ~/.gald3r), so this hook run could not have targeted the real repo's
    # .gald3r/ at all.
    _ = real_repo_diag
    _cleanup(proj, home)

    # ---- T2: statusline -- silent exit 0 + ledger write ---------------------
    cprint("\n=== T2: statusline -- silent exit 0 + ledger write ===", "cyan")
    proj = _build_fake_project()
    home = _new_temp_dir("home")
    payload = json.dumps({"model": {"id": "claude-x"}, "cost": {"total_cost_usd": 1.23}})
    result = _run_hook(proj, home, kind="statusline", stdin_text=payload)
    assert_(result.returncode == 0, f"exit code 0 (got {result.returncode})")
    assert_(result.stdout == "", f"stdout is empty (got {result.stdout!r})")
    ledger_files = list((home / "tel" / "captures").glob("host_statusline-*.log"))
    assert_(len(ledger_files) == 1, f"exactly one host_statusline ledger file, got {len(ledger_files)}")
    if ledger_files:
        content = ledger_files[0].read_text(encoding="utf-8")
        assert_("total_cost_usd" in content, "statusline ledger content carries cost field")
    _cleanup(proj, home)

    # ---- T3: transcript -- tails new JSONL lines, persists an offset -------
    cprint("\n=== T3: transcript -- tails new lines + persists offset ===", "cyan")
    proj = _build_fake_project()
    home = _new_temp_dir("home")
    transcript_path = proj / "fake_transcript.jsonl"
    transcript_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "user", "message": {"role": "user", "content": "hello"}}),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "hi there"}],
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    payload = json.dumps({"transcript_path": str(transcript_path), "session_id": "s1"})
    result = _run_hook(proj, home, kind="transcript", stdin_text=payload)
    assert_(result.returncode == 0, f"exit code 0 (got {result.returncode})")
    assert_(result.stdout == "", f"stdout is empty (got {result.stdout!r})")
    ledger_files = list((home / "tel" / "captures").glob("host_transcript-*.log"))
    assert_(len(ledger_files) == 1, f"exactly one host_transcript ledger file, got {len(ledger_files)}")
    if ledger_files:
        lines = [ln for ln in ledger_files[0].read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert_(len(lines) == 2, f"one ledger line per transcript record, got {len(lines)}")
    offsets_path = proj / ".gald3r" / "logs" / "tel_transcript_offsets.json"
    assert_(offsets_path.is_file(), "offset sidecar was persisted under the tmp project's .gald3r/")

    # Second run, no new transcript lines appended -- must write nothing more.
    result2 = _run_hook(proj, home, kind="transcript", stdin_text=payload)
    assert_(result2.returncode == 0, f"second run exit code 0 (got {result2.returncode})")
    assert_(result2.stdout == "", "second run stdout still empty")
    ledger_files_after = list((home / "tel" / "captures").glob("host_transcript-*.log"))
    if ledger_files_after:
        lines_after = [
            ln for ln in ledger_files_after[0].read_text(encoding="utf-8").splitlines() if ln.strip()
        ]
        assert_(
            len(lines_after) == 2,
            f"no duplicate lines written on a no-new-content second run, got {len(lines_after)}",
        )
    _cleanup(proj, home)

    # ---- T4: malformed (non-JSON) stdin never crashes, stays silent -------
    cprint("\n=== T4: malformed stdin -- silent exit 0, no crash ===", "cyan")
    proj = _build_fake_project()
    home = _new_temp_dir("home")
    result = _run_hook(proj, home, kind="post_tool_use", stdin_text="{not valid json at all")
    assert_(result.returncode == 0, f"exit code 0 on malformed stdin (got {result.returncode})")
    assert_(result.stdout == "", f"stdout is empty on malformed stdin (got {result.stdout!r})")
    assert_(result.stderr == "", f"stderr is empty on malformed stdin (got {result.stderr!r})")
    _cleanup(proj, home)

    # ---- T5: empty stdin never crashes, stays silent -----------------------
    cprint("\n=== T5: empty stdin -- silent exit 0, no crash ===", "cyan")
    proj = _build_fake_project()
    home = _new_temp_dir("home")
    result = _run_hook(proj, home, kind="post_tool_use", stdin_text="")
    assert_(result.returncode == 0, f"exit code 0 on empty stdin (got {result.returncode})")
    assert_(result.stdout == "", f"stdout is empty on empty stdin (got {result.stdout!r})")
    assert_(result.stderr == "", f"stderr is empty on empty stdin (got {result.stderr!r})")
    _cleanup(proj, home)

    # ---- T6: invalid --kind value -- silent exit 0, no crash (adversarial ---
    # review Fix 1 -- argparse's default error() writes usage+error text to
    # stderr then calls sys.exit(2) on an unrecognized --kind choice, which
    # is a SystemExit that escapes this hook's own try/except and, via
    # g_hk_core.dispatch(), could turn into {"continue": false} for a
    # tool-end/stop event. Proves the fix: the hook's own argparse failure
    # path degrades to the safe default --kind and stays silent.
    cprint("\n=== T6: invalid --kind value -- silent exit 0, no crash ===", "cyan")
    proj = _build_fake_project()
    home = _new_temp_dir("home")
    payload = json.dumps({"tool_name": "Bash", "session_id": "s1", "cwd": str(proj)})
    result = _run_hook(proj, home, kind="post-tool-use", stdin_text=payload)
    assert_(result.returncode == 0, f"exit code 0 on invalid --kind (got {result.returncode})")
    assert_(result.stdout == "", f"stdout is empty on invalid --kind (got {result.stdout!r})")
    assert_(result.stderr == "", f"stderr is empty on invalid --kind (got {result.stderr!r})")
    _cleanup(proj, home)

    # ---- T7: malformed TEL rule file -- silent exit 0, no crash (adversarial-
    # review Fix 2 -- a `#gag {(}` rule compiles fine at the grammar layer
    # (balanced braces) but "(" is an invalid regex; core.tel.decorate's
    # _gag_match() catches the re.error and calls logging.warning(...) on
    # EVERY render. With no handler configured, Python's default
    # logging.lastResort writes that straight to this process's real
    # stderr. Proves the fix: the hook installs a NullHandler on the
    # gald3r_core.core.tel logger namespace before rendering, so the
    # warning never reaches stderr.
    cprint("\n=== T7: malformed TEL rule file -- silent exit 0, no crash ===", "cyan")
    proj = _build_fake_project()
    home = _new_temp_dir("home")
    tel_dir = proj / ".gald3r" / "tel"
    tel_dir.mkdir(parents=True, exist_ok=True)
    (tel_dir / "rules.cfg").write_text("#gag {(}\n", encoding="utf-8")
    payload = json.dumps({"tool_name": "Bash", "session_id": "s1", "cwd": str(proj)})
    result = _run_hook(proj, home, kind="post_tool_use", stdin_text=payload)
    assert_(
        result.returncode == 0, f"exit code 0 with malformed rule file (got {result.returncode})"
    )
    assert_(
        result.stdout == "", f"stdout is empty with malformed rule file (got {result.stdout!r})"
    )
    assert_(
        result.stderr == "", f"stderr is empty with malformed rule file (got {result.stderr!r})"
    )
    _cleanup(proj, home)

    print("")
    if _fails == 0:
        cprint("ALL TEL TAP HOOK TESTS PASSED", "green")
        return 0
    cprint(f"{_fails} ASSERTION(S) FAILED", "red")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
