#!/usr/bin/env python3
"""Shared bootstrap for gald3r Python hooks (T1584).

Every ported hook imports this module first. It provides:
- project_root(): locate the gald3r project root from the hook's own location
- bootstrap_engine(): make `gald3r.utils` importable by adding the bundled
  engine source to sys.path when the engine is not installed
- read_stdin_json(): parse the hook payload JSON that Claude Code / Cursor
  pipe to hook commands on stdin (returns {} when absent/malformed)
- resolve_engine_argv(): PATH-first resolution of the gald3r engine command
  argv (env var -> PATH -> legacy loose resolver back-compat -> loud
  degrade). Shared by every hook that used to shell out exclusively to the
  loose, gitignored `.gald3r_sys/scripts/gald3r_bin.py` IP script (P3
  Tier-0, T179/T191) -- see that function's docstring for the full order.

Hooks must never crash the host session: callers wrap main() and exit 0 on
unexpected errors unless the hook's documented purpose is to block.
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

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Windows console-window suppression (BUG-495)
# ---------------------------------------------------------------------------
# Hook processes are (or should be) launched windowless by their host --
# pythonw on Windows for Claude Code's settings.json chains. But on Windows,
# any console-subsystem child (gald3r.exe, git, python) spawned from a
# console-less parent gets a fresh VISIBLE console window unless
# CREATE_NO_WINDOW is set, and an orchestration session fires these chains
# dozens of times a minute -- the observed result was hundreds of
# focus-stealing windows making the desktop unusable. Every ported hook
# imports this module first, so patching Popen once here covers every
# subprocess.run/check_output/Popen call site in every hook on every
# platform overlay. POSIX is untouched (sys.platform guard): there is no
# console-window concept to suppress, and pythonw does not exist on stock
# Linux -- interpreter selection stays the host config's concern. Only
# injected when the caller passed no creationflags of its own: the detach
# spawners (nightly-learn, chat-logger) set DETACHED_PROCESS deliberately
# and must not be second-guessed.
if sys.platform == "win32" and not getattr(subprocess.Popen, "_g3_no_window_patched", False):
    # The discriminator is CONSOLE PRESENCE, not stream redirection (BUG-495
    # second iteration). First cut injected only when the caller redirected
    # BOTH stdout and stderr, to protect deliberate console passthrough
    # (g-hk-component-tag-check's engine spawn -- live-reproduced: blanket
    # injection gave the child its own hidden console, rebinding its std
    # handles away from the parent's and silently swallowing the violation
    # banner). But that rule let partially-redirected spawns
    # (check_output: stdout piped, stderr inherited) keep popping windows
    # under a windowless parent. The truth table is simpler:
    #   - Parent HAS a console (git hook in a terminal): children inherit it;
    #     no new window can pop and passthrough works. Patching is pointless
    #     and risky -> do nothing at all.
    #   - Parent has NO console (pythonw under Claude Code): there is nothing
    #     to inherit -- every non-redirected stream is ALREADY lost into a
    #     fresh visible console. Suppressing that console loses nothing and
    #     kills the window -> inject ALWAYS (unless the caller set its own
    #     creationflags: the detach spawners' DETACHED_PROCESS stays
    #     untouched).
    # Console EXISTENCE is probed via GetConsoleCP(), NOT GetConsoleWindow():
    # a host that spawns its shell with CREATE_NO_WINDOW (Claude Code's Bash
    # tool, VSCode's git UI) gives it a HIDDEN console -- GetConsoleWindow()
    # returns 0 there even though the console exists and std-handle
    # inheritance works perfectly (live-probed: bash-tool python reported
    # window=0 yet its console children have never popped or lost output).
    # GetConsoleCP() returns 0 only when the process has NO console at all
    # (pythonw), which is the only context where injection is safe-and-
    # needed. Checked ONCE at import: console attachment doesn't change
    # over a hook's lifetime.
    import ctypes as _g3_ctypes

    try:
        _g3_has_console = bool(
            _g3_ctypes.WinDLL("kernel32").GetConsoleCP()
        )
    except Exception:
        _g3_has_console = True  # Unknown -> behave like a console parent (no-op).

    if not _g3_has_console:
        _g3_orig_popen_init = subprocess.Popen.__init__

        def _g3_no_window_popen_init(self, *p_args, **p_kwargs):  # noqa: ANN001
            if "creationflags" not in p_kwargs:
                p_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            _g3_orig_popen_init(self, *p_args, **p_kwargs)

        subprocess.Popen.__init__ = _g3_no_window_popen_init  # type: ignore[method-assign]
        subprocess.Popen._g3_no_window_patched = True  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# T516 (T512 inventory rows 8-19) -- shared gitignore/ambiguity resolution
# guard for every hook's `.gald3r/` walk-up resolver (BUG-217 class: a
# gitignored decoy `.gald3r/` closer to the hook than the real, tracked
# project root must never be silently adopted). Extracted here (not
# duplicated per hook) because every hook in this directory already imports
# `_hook_common` first -- this module is the natural, already-established
# shared home for exactly this kind of cross-hook primitive (see
# `resolve_engine_argv`'s own docstring for the same "extract once, every
# hook reuses it" pattern). Deliberately self-contained / stdlib-only, same
# as the rest of this module: hooks must keep working with zero dependency
# on an installed `gald3r_core` package (the self-contained delivery model),
# so this is NOT wired to `gald3r_core.core.gald3r_root_guard` (the sibling
# extraction used by the 7 CORE resolvers in `src/gald3r_core/{core,cli,
# project,server_bridge}`, T512 inventory rows 1-7) even though the guard
# SHAPE below is identical -- see that module's own docstring for why the
# two implementations are deliberately kept separate rather than shared.
# ---------------------------------------------------------------------------
def is_gitignored(path: Path) -> "bool | None":
    """Return whether `path` is gitignored, per `git check-ignore -v`.

    Mirrors `gald3r_core.project.gald3r_integration.identity._is_gitignored`
    (T512) and `gald3r_core.core.gald3r_root_guard.is_gitignored` (T516) --
    the cheap, authoritative test g-rl-02 prescribes for exactly this
    question. Returns `None` (fail-open: callers proceed as if not ignored)
    when the check cannot be performed at all -- `git` not on PATH, `path`
    not inside any git working tree, or the call otherwise failed.
    """
    try:
        result = subprocess.run(  # noqa: S603 -- fixed argv, no shell
            ["git", "check-ignore", "-v", str(path)],
            cwd=str(path.parent),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def resolved_global_gald3r_home() -> "Path | None":
    """Return the resolved global gald3r home `.gald3r` directory, or `None`.

    BUG-426 (stdlib-only port of `gald3r_core.core.gald3r_root_guard
    .resolved_global_gald3r_home` / `identity._resolved_global_gald3r_home`
    -- duplicated rather than imported for the same self-contained-hooks
    reason documented at the top of this section): every real hook
    invocation runs from somewhere nested under the user's home directory,
    so without this exclusion an unbounded walk-up that finds no OTHER
    `.gald3r/` between `start` and the filesystem root would eventually
    reach `~/.gald3r` itself and wrongly adopt (or flag as "ambiguous") the
    user's global gald3r home -- confirmed live on a real dev machine while
    building this guard (`~/.gald3r` genuinely exists there). Never raises;
    returns `None` on any resolution failure so callers skip the exclusion
    rather than crash a hook that must never brick a host session.
    """
    try:
        override = os.environ.get("GALD3R_HOME")
        home = Path(override) if override else (Path.home() / ".gald3r")
        return home.resolve()
    except (OSError, RuntimeError):
        return None


def guarded_walk_up(
    start: Path,
    *,
    marker: str = ".gald3r",
    max_depth: int = 1000,
    exclude: "Path | None" = None,
    ambiguous_candidates: "list | None" = None,
) -> "Path | None":
    """Walk upward from `start` (inclusive) looking for `<dir>/<marker>`.

    T516 guard (same shape as `gald3r_core.core.gald3r_root_guard
    .guarded_walk_up` / `find_gald3r_root`'s T512 fix, commit 3682aa64): a
    candidate whose marker directory is gitignored is refused (never
    adopted; the walk continues upward for the real, tracked root). A
    second, non-gitignored candidate further up than the nearest one is
    reported via `ambiguous_candidates` but the NEAREST candidate still
    wins -- no behavior change for the ordinary single-marker case.
    `exclude` (an optional RESOLVED path, e.g. from
    `resolved_global_gald3r_home()`) is skipped by resolved-path identity,
    same BUG-426 exclusion `find_gald3r_root` applies to the global home.
    """
    candidate = start
    resolved_result: "Path | None" = None
    depth = 0
    while True:
        marker_dir = candidate / marker
        if marker_dir.is_dir():
            is_excluded = False
            if exclude is not None:
                try:
                    is_excluded = marker_dir.resolve() == exclude
                except OSError:
                    is_excluded = False
            if not is_excluded:
                if is_gitignored(marker_dir):
                    pass  # T516: refuse -- never silently adopt a decoy.
                elif resolved_result is None:
                    resolved_result = candidate
                elif ambiguous_candidates is not None:
                    ambiguous_candidates.append(candidate)
        parent = candidate.parent
        if parent == candidate or depth >= max_depth:
            break
        candidate = parent
        depth += 1
    return resolved_result


def project_root() -> Path:
    """Walk up from this file to the directory containing `.gald3r/` or
    `.gald3r_sys/` (hooks live at `<root>/.claude/hooks/` or a platform
    equivalent). Falls back to the current working directory.

    T516 (T512 inventory row 8): the `.gald3r/` half of this check applies
    the shared gitignore-refusal + ambiguity-warning guard above (with the
    BUG-426 global-home exclusion wired in). The `.gald3r_sys/` half is
    deliberately LEFT UNGUARDED for gitignore (but STILL excludes the
    global home by resolved identity): `.gald3r_sys/` is local compiled
    engine data that is normally, intentionally gitignored in a real
    install -- refusing a gitignored `.gald3r_sys/` would break detection
    of every ordinary install rather than catch anything malicious (unlike
    `.gald3r/`, where gitignored is the BUG-217 decoy signature this guard
    exists to catch). Checked as two sequential walks rather than one
    interleaved walk for simplicity; since `.gald3r_sys/` and `.gald3r/`
    are always siblings in a real install, this makes no practical
    difference to which directory is returned.
    """
    here = Path(__file__).resolve().parent
    global_home = resolved_global_gald3r_home()
    gald3r_root = guarded_walk_up(here, marker=".gald3r", exclude=global_home)
    if gald3r_root is not None:
        return gald3r_root
    for d in (here, *here.parents):
        sys_dir = d / ".gald3r_sys"
        if sys_dir.is_dir():
            try:
                # A `.gald3r_sys/` living right next to the global `.gald3r`
                # home (same parent dir) IS that global home's own sibling,
                # not a real project -- same exclusion intent as `exclude`
                # above, but compared by PARENT identity since `.gald3r_sys`
                # and the resolved global-home path never share a name.
                if global_home is not None and sys_dir.resolve().parent == global_home.parent:
                    continue
            except OSError:
                pass
            return d
    return Path.cwd()


def bootstrap_engine() -> bool:
    """Make the `gald3r` package importable.

    Tries the installed package first, then falls back to the engine source
    bundled at `<root>/.gald3r_sys/engine/src`. Returns True when the import
    works — hooks degrade gracefully (pure-stdlib path) when it does not.
    """
    try:
        import gald3r  # noqa: F401

        return True
    except ImportError:
        pass
    engine_src = project_root() / ".gald3r_sys" / "engine" / "src"
    if engine_src.is_dir():
        sys.path.insert(0, str(engine_src))
        try:
            import gald3r  # noqa: F401

            return True
        except ImportError:
            return False
    return False


def read_stdin_json() -> Dict[str, Any]:
    """Read the hook payload JSON from stdin.

    Claude Code and Cursor pipe a JSON object describing the event to hook
    commands. Returns {} for an empty/absent/malformed payload so hooks can
    run standalone (manual invocation, tests) without special-casing.
    """
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError, ValueError):
        return {}


def _default_engine_root() -> Path:
    """Fallback root for resolve_engine_argv() when a caller does not pass
    its own project_root. Most hooks compute project_root differently
    (argparse override, cwd walk-up, etc.) and pass that in to preserve
    their existing behavior; this is only the last-resort default."""
    return project_root()


#: Process-lifetime cache for `resolve_engine_argv()` results (adversarial-
#: panel FIX 8). Every call previously re-did an uncached PATH scan
#: (`shutil.which`) + a fresh `exec_module` of the legacy resolver script on
#: EVERY invocation, even though a long-lived process (a resident daemon, or
#: a single CLI run that touches several hooks) resolves the same
#: `(root, env)` combination repeatedly per tick/session. Keyed on
#: `(root, GALD3R_BIN, PATH)` -- not just `root` -- so a changed env (a test
#: swapping PATH mid-run, or a real env mutation) still gets a fresh
#: resolution instead of a stale cached miss/hit from an earlier call. A
#: plain module-level dict (not `functools.lru_cache` on the `Path` arg
#: alone) because the cache key needs the env fingerprint folded in, which
#: `lru_cache` cannot do without promoting env vars to explicit call
#: arguments at every call site.
_ENGINE_ARGV_CACHE: Dict[tuple, "list[str] | None"] = {}

#: Roots for which the tier-4 "nothing resolvable" diagnostic has already
#: been appended THIS process (adversarial-panel FIX 8) -- previously a
#: fresh line was appended to `hook_diag.log` on every single miss, which is
#: noisy for a long-lived process re-resolving a dormant engine every tick.
#: Tracked separately from `_ENGINE_ARGV_CACHE` (which is env-fingerprinted)
#: because the diagnostic is about the ROOT being dormant, not about one
#: particular env combination -- it must log once per root even if the env
#: changes between misses.
_DIAG_LOGGED_ROOTS: "set[str]" = set()


def _diag_log(root: Path, msg: str) -> None:
    """Append a timestamped line to the shared `.gald3r/logs/hook_diag.log`
    channel (fail-soft; mirrors g-hk-agent-complete.py's ``_diag``).

    Deliberately NEVER stdout: several callers of resolve_engine_argv()
    print a JSON hook response on stdout that Claude Code / Cursor parse
    directly (session-start, policy-check, worktree-janitor), and
    g-hk-wpac-inbox-check's stdout is joined verbatim into the session-start
    `additional_context` banner that reaches model context. A stray
    diagnostic line on stdout in any of those paths would corrupt the JSON
    payload or leak noise straight into the model's context window.
    """
    try:
        logs_dir = Path(root) / ".gald3r" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(logs_dir / "hook_diag.log", "a", encoding="utf-8") as fh:
            fh.write("%s %s\n" % (stamp, msg))
    except OSError:
        pass


def resolve_engine_argv(
    project_root: Path | None = None, *, hook_name: str = "hook"
) -> list[str] | None:
    """Resolve the argv prefix that invokes the gald3r engine (P3 Tier-0, T179/T191).

    Every shipped hook used to build this resolution itself by shelling out
    exclusively to the loose, gitignored `.gald3r_sys/scripts/gald3r_bin.py`
    IP script: build the resolver path, bail to None if it is not on disk,
    else dynamically import it and delegate. Under the self-contained
    delivery model an install ships a *compiled* engine binary and never
    carries that loose script on disk at all -- so every one of those hooks
    silently no-opped even when a `gald3r` binary was sitting right there on
    PATH, because the PATH check itself lived inside the (absent) loose
    script. This helper performs the cheap, zero-IP tiers itself so
    resolution keeps working without the loose script, and only falls back
    to it for legacy back-compat:

        1. ``GALD3R_BIN`` env var -- an explicit path to an existing file
           (escape hatch / CI override).
        2. ``gald3r`` on PATH (``shutil.which``) -- the compiled binary the
           self-contained model relies on as its primary resolution path.
        3. The legacy loose resolver `.gald3r_sys/scripts/gald3r_bin.py`,
           if it is still shipped (older installs, or a dev checkout where
           the engine source is present) -- dynamically imported and
           delegated to for ITS OWN bundled-binary / dev-source fallback
           tiers, exactly as every hook did before this helper existed.
        4. ``None`` -- nothing resolvable. One diagnostic line is appended
           to the shared `.gald3r/logs/hook_diag.log` channel (never
           stdout -- see `_diag_log`) so a dormant gate is discoverable
           instead of silently no-opping forever.

    Args:
        project_root: Root to resolve `.gald3r_sys/` against. Each hook
            computes this differently (argparse override, cwd walk-up,
            etc.); pass the hook's own resolved root to preserve its
            existing behavior. Defaults to `project_root()` (this module's
            hook-file-relative walk) when omitted.
        hook_name: Included in the diagnostic line on a full miss, so
            `.gald3r/logs/hook_diag.log` records which hook degraded.

    Returns:
        A command-prefix ``list[str]`` (e.g. ``["gald3r"]``) ready to have a
        subcommand and args appended before ``subprocess.run``, or ``None``
        when no engine is resolvable -- callers must degrade gracefully and
        must never crash or block on ``None``.

    Never raises: every tier swallows its own filesystem/env/import/exec
    errors and falls through to the next tier.

    Cached per process (adversarial-panel FIX 8, P3): the resolution below
    is repeated at most once per distinct ``(root, GALD3R_BIN, PATH)``
    combination -- see :data:`_ENGINE_ARGV_CACHE`. The function's contract
    (arguments, return type, fail-soft behavior) is unchanged; only repeat
    calls with an IDENTICAL root+env become free.
    """
    root = Path(project_root) if project_root is not None else _default_engine_root()
    root_key = str(root)
    cache_key = (
        root_key,
        os.environ.get("GALD3R_BIN", ""),
        os.environ.get("PATH", ""),
    )
    if cache_key in _ENGINE_ARGV_CACHE:
        return _ENGINE_ARGV_CACHE[cache_key]

    result = _resolve_engine_argv_uncached(root, root_key=root_key, hook_name=hook_name)
    _ENGINE_ARGV_CACHE[cache_key] = result
    return result


def _resolve_engine_argv_uncached(root: Path, *, root_key: str, hook_name: str) -> list[str] | None:
    """The actual (uncached) tiered resolution :func:`resolve_engine_argv` wraps."""
    # 1. Explicit override.
    try:
        override = os.environ.get("GALD3R_BIN", "").strip()
        if override and Path(override).is_file():
            return [override]
    except OSError:
        pass

    # 2. Global binary on PATH -- the self-contained model's primary path.
    try:
        on_path = shutil.which("gald3r")
        if on_path:
            return [on_path]
    except OSError:
        pass

    # 3. Legacy loose resolver back-compat (older installs / dev checkouts).
    resolver = root / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if resolver.is_file():
        try:
            spec = importlib.util.spec_from_file_location("gald3r_bin_hook_common", str(resolver))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
                argv = mod.resolve_engine_cmd(root)
                if argv:
                    return list(argv)
        except Exception:
            pass

    # 4. Nothing resolvable -- loud degrade instead of a silent no-op, but
    # only ONCE per root per process (adversarial-panel FIX 8) -- a
    # long-lived process re-resolving a dormant engine every tick previously
    # appended a fresh diagnostic line every single time.
    if root_key not in _DIAG_LOGGED_ROOTS:
        _DIAG_LOGGED_ROOTS.add(root_key)
        _diag_log(
            root,
            "[%s] gald3r engine not resolved (checked GALD3R_BIN, PATH, legacy "
            ".gald3r_sys/scripts/gald3r_bin.py) -- degrading gracefully" % hook_name,
        )
    return None


# ---------------------------------------------------------------------------
# Detached-spawn single-instance guard (BUG-389)
# ---------------------------------------------------------------------------
#
# Several hooks detach-spawn a background `gald3r ...` job (nightly-learn's
# `gald3r learn nightly`, the chat-logger's `gald3r vault ingest-session`)
# and then return almost instantly -- the spawned job outlives the hook
# process itself. Before BUG-389 neither spawner checked whether a PRIOR
# instance of its own target job was still running, so overlapping Stop
# events (or several concurrent sessions) could stack up duplicate,
# overlapping jobs contending on the same vault/DB and wasting rate-limit
# budget. This is the shared guard both spawners use (g-rl-04 DRY -- exactly
# 2 call sites today, one helper, not two independent implementations).
#
# The guard is a lightweight PID-file lock keyed on the CHILD job's PID, not
# the guarding hook process's own PID: `try_acquire_spawn_lock()` is called
# BEFORE spawning (this immediately claims the lock under the hook's own --
# momentarily live -- PID, closing most of the TOCTOU race between two
# concurrent hook invocations), then `record_spawned_pid()` is called AFTER
# a successful `subprocess.Popen()` to hand the lock off to the actual
# detached child's PID so the guard tracks the child job's real lifetime
# rather than the hook's own near-instant one. A lock recording a PID that
# is no longer alive on this host (a crashed prior job, or one that simply
# finished) is treated as stale and silently reclaimed here -- it can never
# permanently wedge future spawns.


def _win_pid_is_alive(pid: int) -> bool:
    """Windows liveness probe via the Win32 API (stdlib ``ctypes``, no deps).

    ``os.kill(pid, 0)`` is NOT usable as a liveness probe on Windows: signal
    0 there maps to ``CTRL_C_EVENT``, so ``os.kill`` calls
    ``GenerateConsoleCtrlEvent`` and can send a real Ctrl-C to every process
    sharing this console (legacy BUG-199 --
    ``gald3r_core.core.memory.consolidation_lock`` hit this the hard way).
    Uses ``OpenProcess`` + ``GetExitCodeProcess`` instead, mirroring the
    proven pattern in ``gald3r_core.coordination.valkyrie_runtime.lockfile``.
    Any unexpected failure returns True (conservative: never steal a lock we
    cannot prove is stale).
    """
    import ctypes
    from ctypes import wintypes

    still_active = 259
    process_query_limited_information = 0x1000
    error_invalid_parameter = 87  # No such PID -- dead.

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        last_err = ctypes.get_last_error()
        if last_err == error_invalid_parameter:
            return False  # No such PID -- dead -- reclaimable.
        return True  # Exists-but-access-denied, or unknown failure -- assume alive.
    try:
        exit_code = wintypes.DWORD()
        if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return exit_code.value == still_active
        return True  # Query failed but we hold a handle -- conservatively alive.
    finally:
        kernel32.CloseHandle(handle)


def _pid_is_alive(pid: int) -> bool:
    """Cross-platform, conservative liveness probe for the spawn-lock guard.

    Never steals a lock it cannot prove is stale: any unprovable result is
    treated as "alive". On POSIX, signal 0 via ``os.kill`` distinguishes a
    dead PID (``ProcessLookupError``) from a live one (success or
    ``PermissionError``). On Windows, see :func:`_win_pid_is_alive`.
    """
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            return _win_pid_is_alive(pid)
        except OSError:
            return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def _read_lock_pid(lock_path: Path) -> "int | None":
    """Return the PID recorded at ``lock_path``, or ``None`` if absent/unreadable."""
    try:
        raw = lock_path.read_text(encoding="ascii", errors="replace").strip()
        return int(raw)
    except (OSError, ValueError):
        return None


def try_acquire_spawn_lock(lock_path: Path) -> bool:
    """Attempt to claim the single-instance spawn guard at ``lock_path`` (BUG-389).

    Returns ``False`` when a LIVE prior holder is already recorded at
    ``lock_path`` -- callers MUST skip their spawn this invocation (log and
    return normally; never raise). Returns ``True`` when the guard was
    claimed under the calling process's own PID -- either no prior lock
    existed, or the recorded PID is no longer alive (silently reclaimed):
    the caller should proceed to spawn, then call
    :func:`record_spawned_pid` once the child's real PID is known.

    Fails OPEN on any filesystem error writing the lock file (never blocks
    a spawn on a filesystem hiccup) -- this mirrors every other fail-soft
    behavior in these hooks, which must never crash or wedge the host
    session.
    """
    existing_pid = _read_lock_pid(lock_path)
    if existing_pid is not None and _pid_is_alive(existing_pid):
        return False
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(str(os.getpid()), encoding="ascii")
    except OSError:
        return True
    return True


def record_spawned_pid(lock_path: Path, pid: int) -> None:
    """Hand the spawn-lock at ``lock_path`` off to the just-spawned child's PID.

    Best-effort (never raises): a write failure here only means the guard's
    stale-lock reclaim on the NEXT invocation checks liveness against the
    hook's own (already-exited) PID slightly earlier than it would have
    against the child's -- it never blocks or permanently wedges a future
    spawn either way.
    """
    try:
        lock_path.write_text(str(pid), encoding="ascii")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Marker-file agent authorization (BUG-414)
# ---------------------------------------------------------------------------
#
# `g-hk-pre-tool-call-gald3r-guard.py` enforces g-rl-33's ".gald3r/ Folder
# Gate" by refusing Edit/Write calls into the project's live `.gald3r/`
# unless GALD3R_HOOK_BYPASS=1 or GALD3R_ACTIVE_AGENT is set in the hook
# subprocess's OWN environment. That env var can only ever help when it was
# already set in the Claude Code / Cursor HOST process's environment before
# the session started: an agent invoked via the Agent tool (or the main
# coordinator, mid-session) cannot set an env var from inside one tool call
# (its own Bash subprocess/shell) and have it visible to a LATER, separately
# spawned Edit/Write hook subprocess -- each tool call is its own process.
# Every subagent-mediated `.gald3r/` write was therefore falling back to an
# unaudited raw Bash/Python script write instead of the tracked Edit/Write
# tool path, defeating the hook's audit trail (observed repeatedly in this
# repo's own g-go-go run history).
#
# The marker file below is a lightweight, TIME-BOXED, fail-CLOSED escape
# hatch an agent (main coordinator or subagent) can write to itself via a
# plain Bash tool call BEFORE issuing the Edit/Write -- unlike an env var,
# a file write in one subprocess is visible to a LATER subprocess because
# both share the same project's `.gald3r/` filesystem state. `expires_at`
# bounds the blast radius of a marker nobody ever clears (crash, forgotten
# cleanup): it self-expires rather than granting indefinite authorization.
#
# BUG-414 (Phase 2 reopen): an adversarial review of the first cut found two
# live defects, both fixed here:
#
# 1. Fail-OPEN on malformed bytes -- `read_active_agent_marker()`'s
#    `read_text(encoding="utf-8")` only caught `OSError`; non-UTF-8 bytes
#    raise `UnicodeDecodeError` (a `ValueError` subclass, NOT an `OSError`),
#    which propagated uncaught through the guard hook's outer
#    `except Exception` handler and silently ALLOWED the write -- the exact
#    opposite of this module's fail-CLOSED contract. `_parse_marker_file()`
#    below now catches `(OSError, UnicodeDecodeError)` explicitly.
#
# 2. No per-agent binding -- the guard hook only checked truthiness of the
#    marker, so any agent's `clear-active-agent` could wipe any OTHER
#    agent's still-valid marker, and any valid marker set by ANY agent
#    authorized writes from ANY OTHER concurrent process for the full TTL
#    window -- real cross-agent interference in `--swarm` mode. There is NO
#    harness-provided signal of "which process issued this specific
#    Edit/Write call" available to the guard hook (the stdin JSON tool-call
#    event carries no caller-identity field), so TRUE per-process binding is
#    not achievable without a harness change and is deliberately not
#    attempted here. The closest achievable approximation, applied via two
#    concrete mechanisms:
#      (a) **Agent-scoped clear** -- `clear_active_agent_marker(root,
#          agent_id)` only deletes the marker when its own `agent_id` field
#          matches the caller's, so an unrelated agent's clear can no longer
#          wipe someone else's still-valid marker.
#      (b) **Single-use / consume-on-use, made ATOMIC (BUG-414 atomicity
#          rework)** -- the guard hook now calls a single function,
#          `claim_active_agent_marker()`, that claims and validates the
#          marker in one atomic filesystem operation instead of the old
#          separate `read_active_agent_marker()` + `consume_active_agent_
#          marker()` two-step. The two-step version was a TOCTOU race: each
#          guard-hook invocation is a freshly-spawned process, and "read"
#          then "delete" were two independent, unlocked filesystem calls --
#          live-reproduced with 12 concurrent, barrier-synchronized guard-
#          hook subprocesses racing one marker, with up to 12/12 ALL
#          observing it as valid across repeated trials. `claim_active_agent_
#          marker()` uses an atomic rename (`os.replace`) to steal the
#          marker's directory entry: exactly one concurrent caller can win
#          the rename, every other concurrent caller gets `FileNotFoundError`
#          because the OS/filesystem already moved the source out from under
#          them. This makes "claim the marker" and "the marker is gone for
#          everyone else" the SAME atomic step, closing the race window
#          entirely -- of N concurrent invocations, AT MOST ONE can observe
#          the marker as valid. This still collapses the cross-agent
#          piggyback window from the full TTL (up to `ttl_seconds`, default
#          300s) down to a single guard-hook invocation, now with no gap
#          between validation and consumption.


def active_agent_marker_path(root: Path) -> Path:
    """Path to the marker-file authorization token (BUG-414).

    Lives under ``<root>/.gald3r/logs/`` -- already gitignored wholesale via
    ``.gald3r/.gitignore``'s ``logs/`` entry, so this transient authorization
    state can never be accidentally committed.
    """
    return Path(root) / ".gald3r" / "logs" / ".active_agent_marker.json"


def write_active_agent_marker(root: Path, agent_id: str, ttl_seconds: int = 300) -> None:
    """Write a time-boxed marker authorizing ``agent_id`` to write `.gald3r/`.

    Creates ``<root>/.gald3r/logs/`` if it does not yet exist. The marker
    records ``expires_at`` as an absolute epoch-seconds float
    (``time.time() + ttl_seconds``) so :func:`claim_active_agent_marker` can
    treat a stale, forgotten marker as expired without needing to know when
    it was written.

    Fails soft (mirrors :func:`_diag_log`'s posture): never raises on a
    normal filesystem error. Hooks -- and the tiny CLI wrapping this
    function -- must never crash the host session or a Bash tool call.
    """
    marker_path = active_agent_marker_path(root)
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"agent_id": agent_id, "expires_at": time.time() + ttl_seconds}
        marker_path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        pass


def _parse_marker_file(marker_path: Path) -> "Dict[str, Any] | None":
    """Read and schema-validate the marker file, WITHOUT checking expiry.

    Shared by :func:`claim_active_agent_marker` (which additionally checks
    expiry) and :func:`clear_active_agent_marker` (which deliberately does
    NOT check expiry -- an agent must be able to positively confirm removal
    of its own marker even after that marker has already expired).

    Returns the parsed dict (guaranteed to have a non-empty string
    ``agent_id`` and a numeric ``expires_at``) when well-formed, or
    ``None`` (fail CLOSED) for every ambiguous or corrupt case:

    - the marker file does not exist, or cannot be read (``OSError``)
    - the file's bytes are not valid UTF-8 (``UnicodeDecodeError`` -- a
      ``ValueError`` subclass, NOT an ``OSError``; this was BUG-414's
      Phase-2 fail-open regression: the prior version of this check only
      caught ``OSError`` around the ``read_text`` call, so non-UTF-8 bytes
      raised uncaught, propagated through the guard hook's outer
      ``except Exception`` handler, and silently ALLOWED the write)
    - the file's text is not valid JSON, or is JSON but not an object
    - ``agent_id`` is missing, not a string, or empty
    - ``expires_at`` is missing or not a number

    Never raises.
    """
    marker_path = Path(marker_path)
    try:
        raw = marker_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    agent_id = data.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        return None
    expires_at = data.get("expires_at")
    if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
        return None
    return data


def claim_active_agent_marker(root: Path) -> "str | None":
    """Atomically claim, validate, and consume the active-agent marker
    (BUG-414 atomicity rework).

    Replaces the old read-then-consume two-step
    (:func:`read_active_agent_marker` + :func:`consume_active_agent_marker`,
    both removed), which was a TOCTOU race between two separate, unlocked
    filesystem operations -- a read, then later an unconditional unlink --
    with each guard-hook invocation running as its own freshly-spawned
    process. Live-reproduced: 12 concurrent, barrier-synchronized guard-hook
    subprocesses racing one valid marker, with up to 12/12 concurrent
    invocations ALL allowed off the same single marker across repeated
    trials.

    Uses :func:`os.replace` to atomically rename the shared marker path to
    a per-invocation claim path in the SAME directory (same-filesystem
    rename is required for atomicity -- rename across filesystems/volumes
    is not guaranteed atomic). The claim path is unique per call (pid + a
    random token) so concurrent claimers never collide on the DESTINATION;
    only one of them can win the SOURCE. ``os.replace``/rename is atomic
    with respect to other renames of the same source on both POSIX and
    Windows/NTFS: exactly one concurrent caller moves the source away, and
    every other concurrent caller sees ``FileNotFoundError`` because the
    source is already gone by the time their own rename executes -- there
    is no window in which two concurrent callers can both observe the
    source as present and claimable. This makes "claim the marker" and
    "the marker is gone for everyone else" the SAME atomic step, so of N
    concurrent invocations racing the same marker, AT MOST ONE can observe
    it as valid.

    Returns the marker's ``agent_id`` if the claimed file parses as a
    well-formed, unexpired marker (the same validation
    :func:`_parse_marker_file` plus the expiry check already performed for
    the old :func:`read_active_agent_marker`); returns ``None`` (fail
    CLOSED) if no marker existed, a concurrent invocation already claimed
    it, or the claimed file is malformed/expired. In every case the
    temporary claim file is removed before returning -- a claimed marker
    (valid or not) is gone for good, matching the "single use" contract:
    an invalid or expired marker cannot be retried by a later invocation
    either.

    Never raises.
    """
    marker_path = active_agent_marker_path(root)
    claim_path = marker_path.parent / (
        f"{marker_path.name}.claim.{os.getpid()}.{uuid.uuid4().hex}"
    )
    try:
        os.replace(marker_path, claim_path)
    except OSError:
        # Nothing to claim: no marker exists, or a concurrent invocation
        # already won the race and renamed it out from under us.
        return None
    try:
        data = _parse_marker_file(claim_path)
        if data is None:
            return None
        if time.time() >= data["expires_at"]:
            return None
        return data["agent_id"]
    finally:
        try:
            claim_path.unlink()
        except OSError:
            pass


def clear_active_agent_marker(root: Path, agent_id: str) -> bool:
    """Delete the active-agent marker IFF it is well-formed and owned by
    ``agent_id`` (BUG-414 Phase-2, agent-scoped clear).

    Unlike the old unconditional ``clear-active-agent`` behavior, this will
    NOT remove a marker that belongs to a different agent -- closing the
    cross-agent-interference hole where any agent's clear call could
    invalidate any OTHER agent's still-valid authorization.

    Does NOT check expiry (see :func:`_parse_marker_file`): an agent must
    be able to clear its own marker even after it has already expired.

    Returns:
        ``True`` if a marker matching ``agent_id`` was found and deleted.
        ``False`` if the marker was left untouched -- absent, malformed, or
        owned by a different ``agent_id``.

    Never raises (fails soft, mirrors the rest of this module).
    """
    marker_path = active_agent_marker_path(root)
    data = _parse_marker_file(marker_path)
    if data is None:
        return False
    if data.get("agent_id") != agent_id:
        return False
    try:
        marker_path.unlink()
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return True


def _build_active_agent_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="_hook_common.py",
        description=(
            "Marker-file authorization CLI for the .gald3r/ PreToolUse guard "
            "(BUG-414) -- lets an agent (main coordinator or an Agent-tool-"
            "launched subagent) pre-authorize its OWN later Edit/Write calls "
            "to .gald3r/ via a plain Bash tool call, since GALD3R_ACTIVE_AGENT "
            "set inside one tool call's subprocess cannot propagate to a "
            "later, separately spawned hook subprocess. The marker is "
            "SINGLE-USE (BUG-414 Phase-2): the guard hook consumes it on the "
            "first authorized Edit/Write, so `set-active-agent` must be "
            "re-run before each write it should cover. `clear-active-agent` "
            "is AGENT-SCOPED: it only removes a marker owned by the AGENT_ID "
            "you pass, so one agent can no longer invalidate another agent's "
            "still-valid marker."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    set_parser = sub.add_parser(
        "set-active-agent",
        help="Write a time-boxed, single-use marker authorizing AGENT_ID to write .gald3r/.",
    )
    set_parser.add_argument(
        "agent_id", help="Identifier of the authorized agent (e.g. g-qa-engineer)."
    )
    set_parser.add_argument(
        "--ttl",
        dest="ttl_seconds",
        type=int,
        default=300,
        help="Marker lifetime in seconds (default: 300).",
    )

    clear_parser = sub.add_parser(
        "clear-active-agent",
        help="Delete the active-agent marker IFF it is owned by AGENT_ID (idempotent).",
    )
    clear_parser.add_argument(
        "agent_id",
        help="Identifier of the agent whose marker should be cleared (e.g. g-qa-engineer). "
        "A marker owned by a DIFFERENT agent_id is left untouched.",
    )
    return parser


def _active_agent_cli_main(argv: "list[str] | None" = None) -> int:
    args = _build_active_agent_cli_parser().parse_args(argv)
    root = project_root()
    if args.command == "set-active-agent":
        write_active_agent_marker(root, args.agent_id, args.ttl_seconds)
        print(
            "active agent marker set for %r (ttl=%ss) at %s"
            % (args.agent_id, args.ttl_seconds, active_agent_marker_path(root))
        )
        return 0
    if args.command == "clear-active-agent":
        marker_path = active_agent_marker_path(root)
        cleared = clear_active_agent_marker(root, args.agent_id)
        if cleared:
            print(
                "active agent marker cleared for %r at %s"
                % (args.agent_id, marker_path)
            )
        else:
            print(
                "active agent marker left untouched at %s (absent, malformed, "
                "or not owned by %r)" % (marker_path, args.agent_id)
            )
        return 0
    return 2  # pragma: no cover -- argparse `required=True` makes this unreachable


if __name__ == "__main__":
    sys.exit(_active_agent_cli_main())
