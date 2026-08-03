#!/usr/bin/env python3
"""TEL host-CLI hook tap (T90; Claude Code first).

D001 provenance: this hook touches the templates_dev-owned CRASH surface
(it is a NEW concern registered in `g_hk_core.CONCERN_CHAIN`). The D001
gate on this task was RATIFIED by the owner (wrm3) 2026-07-13 -- see
`.gald3r/tasks/open/task090_tel-host-cli-hook-adapters-claude-code-f.md`'s
`## Status History`. Scope stays within T90: this file is additive
(a new concern hook + one new CONCERN_CHAIN registration each for
`tool-end` and `stop`) and does not modify any existing concern hook's
behavior.

Maps three Claude Code host hook event kinds onto the TEL normalized
stream (`.gald3r/specifications_collection/2026-07-09_tel_plan.md`'s task
decomposition table, T90's own row -- "map host hook events onto the TEL
normalized stream as a cleaner-than-PTY tap where hosts offer structure"):

* `post_tool_use` -- the raw `PostToolUse` hook payload (Claude Code's
  canonical `tool-end` event, per `g_hk_core.PLATFORM_EVENT_MAP`), fed
  through the adapter once per invocation.
* `statusline` -- a statusline-shaped payload, fed through once per
  invocation. See "Statusline scope boundary" below -- NOT auto-wired as
  Claude Code's live interactive `statusLine` command by this task.
* `transcript` -- reads `transcript_path` off the stop-event payload,
  tails the JSONL transcript for lines added since the last processed
  offset (persisted per-transcript-path in
  `.gald3r/logs/tel_transcript_offsets.json`), and feeds each NEW raw
  JSONL record through the adapter as its own `transcript` event. No
  per-record filtering/extraction happens here (deliberately -- see the
  module-level "Design choices" note in
  `gald3r_core.core.tel.host_adapter` on gag-suppression being the load-
  bearing noise-reduction mechanism for a host-hook tap, not hardcoded
  hook-side policy): a project that wants to drop routine/sidechain lines
  writes a `#gag` rule for them.

All business logic (matching, decoration, ledger writing) lives in
`gald3r_core.core.tel.host_adapter` (`core/` may never import `platform/`,
so this file only knows Claude Code's payload SHAPES -- reading stdin JSON,
locating `transcript_path`, tailing a JSONL file -- never TEL's rule
engine internals). This file is the thin, host-specific glue only.

CRITICAL -- SILENT / fire-and-forget (HARD contract, per T90's acceptance
criteria): this hook NEVER prints to stdout. Any stdout from a `tool-end`/
`stop` concern hook is folded into `g_hk_core.dispatch()`'s aggregated
`additional_context` response -- a token-injection trap the TEL plan's own
backend-cost table calls out explicitly ("anything a hook prints back into
the conversation (stdout -> context injection) IS tokens"). All
diagnostics go to `.gald3r/logs/hook_diag.log`, never stdout. This hook
also NEVER raises and ALWAYS exits 0 -- a missing engine, a malformed
payload, or an unreadable transcript file degrades to a silent no-op, never
a blocked/crashed host session.

Wired in `g_hk_core.CONCERN_CHAIN["tool-end"]` (`--kind post_tool_use`,
fires from Claude Code's `PostToolUse` via `g-hk-on-tool-end.py`) and
`CONCERN_CHAIN["stop"]` (`--kind transcript`, fires from Claude Code's
`Stop`, which carries `transcript_path`, via `g-hk-on-stop.py`).

Statusline scope boundary: `--kind statusline` is fully supported by this
hook and by `core.tel.host_adapter` for direct/manual invocation, but this
task does NOT register it as Claude Code's actual `statusLine` command
config. That config's contract is fundamentally different from every other
Claude Code hook event -- ITS stdout IS the literal rendered status-bar
text, not something reaching model context -- and this task's own
acceptance criteria require total stdout silence across all three kinds.
Building a real status-bar RENDERER is tel_plan.md's separate, future
`#statusbar`-reads-the-variable-store OUTPUT-direction feature, not this
INPUT tap. Wiring `--kind statusline` into an actual `statusLine` command
is a natural follow-up once that rendering half exists.
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
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

_KINDS = ("post_tool_use", "statusline", "transcript")

#: Sidecar filename tracking, per transcript path, how many JSONL lines
#: have already been processed -- so a long-running session's `stop` event
#: firing repeatedly (once per turn) never reprocesses the whole transcript
#: from line 1 every time.
_OFFSETS_FILENAME = "tel_transcript_offsets.json"


def _diag(root: Path, msg: str) -> None:
    """Append a timestamped line to `.gald3r/logs/hook_diag.log` (fail-soft,
    NEVER stdout -- see this module's own SILENT contract docstring)."""
    try:
        logs_dir = root / ".gald3r" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(logs_dir / "hook_diag.log", "a", encoding="utf-8") as fh:
            fh.write("%s [tel-tap] %s\n" % (stamp, msg))
    except OSError:
        pass


def _import_adapter():
    """Resolve `gald3r_core.core.tel.host_adapter`.

    Tries the live `gald3r_core` package first -- the dev-checkout /
    editable-install path this repo's OWN test suite exercises (this hook
    lives inside `gald3r_core`'s own source tree, so a `uv sync`'d dev
    environment already has it importable). Falls back to the
    installed/frozen `gald3r` engine namespace via
    `_hook_common.bootstrap_engine()`, mirroring `g-hk-crash-record.py`'s
    established `from gald3r import ...` pattern for the eventual renamed/
    self-contained distribution. Returns `None` when neither resolves --
    callers must degrade silently (see module docstring's SILENT contract).
    """
    try:
        # BUG[BUG-531] kind=design_gap: flagged by the new BUG-356
        # neutral_source engine-import IP-leak audit (parity_harness.
        # KNOWN_ENGINE_IMPORT_EXCEPTIONS currently allowlists this exact path
        # pending an owner ruling: ratify this guarded dev-convenience import
        # as permanently allowed, or refactor to always go through
        # bootstrap_engine() below) -- see .gald3r/bugs/open/bug531_*.md
        # (numeric BUG-NNN id pending coordinator flush at time of writing).
        from gald3r_core.core.tel import host_adapter as _adapter

        return _adapter
    except Exception:
        pass
    try:
        if _hook_common.bootstrap_engine():
            from gald3r.core.tel import host_adapter as _adapter  # type: ignore[import-not-found]

            return _adapter
    except Exception:
        pass
    return None


def _read_offsets(path: Path) -> Dict[str, int]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, int] = {}
    for k, v in data.items():
        try:
            out[str(k)] = int(v)
        except (TypeError, ValueError):
            continue
    return out


def _write_offsets(path: Path, offsets: Dict[str, int]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(offsets, separators=(",", ":")), encoding="utf-8")
    except OSError:
        pass


def _new_transcript_records(root: Path, transcript_path: str) -> List[Dict[str, Any]]:
    """Read every JSONL line appended to *transcript_path* since the last
    persisted offset, parse each as one transcript record, advance the
    offset, and return the parsed records (malformed lines skipped). Any
    I/O failure (missing file, unreadable, corrupt offsets sidecar) returns
    an empty list rather than raising -- fail-open, matches every other
    helper in this file."""
    records: List[Dict[str, Any]] = []
    try:
        tpath = Path(transcript_path)
        if not tpath.is_file():
            return records
        lines = tpath.read_text(encoding="utf-8", errors="replace").splitlines()
        offsets_path = root / ".gald3r" / "logs" / _OFFSETS_FILENAME
        offsets = _read_offsets(offsets_path)
        key = str(tpath.resolve())
        start = offsets.get(key, 0)
        if start < 0 or start > len(lines):
            start = 0  # transcript rotated/truncated since last run -- reprocess
        for raw in lines[start:]:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
        offsets[key] = len(lines)
        _write_offsets(offsets_path, offsets)
    except Exception:
        return records
    return records


class _SilentArgumentParser(argparse.ArgumentParser):
    """`argparse.ArgumentParser` whose `error()` never writes anything.

    The stock `ArgumentParser.error()` prints a usage line + error message
    to `sys.stderr` and THEN calls `sys.exit(2)` -- both halves violate
    this hook's SILENT / ALWAYS-exits-0 contract (module docstring) on an
    invalid `--kind` value (e.g. a hyphen typo like `post-tool-use`).
    Overriding `error()` itself -- rather than only catching the
    `SystemExit` it raises -- is required because the base class's stderr
    write happens INSIDE `error()`, before `SystemExit` is even raised;
    catching the exception in `main()` alone would still leak the usage
    text to stderr first. This override skips the printing entirely and
    raises `SystemExit(2)` directly; `main()` catches it and falls back to
    the same safe default `--kind` the parser itself uses for a bare
    invocation.
    """

    def error(self, message: str) -> None:
        raise SystemExit(2)


def _silence_tel_logging() -> None:
    """Install a `logging.NullHandler()` on the `gald3r_core.core.tel`
    logger namespace (with `propagate = False`) before this hook makes any
    adapter/render call.

    `core.tel.decorate`'s `_gag_match`/highlight/subs/trigger match paths
    (and sibling `core/tel/*` modules, e.g. `grammar.py`'s rule-file
    parser) call `logging.warning(...)` when a project's TEL rule file has
    a malformed regex (e.g. `#gag {(}`) -- on EVERY render, not once. With
    no handler configured anywhere in that logger's ancestor chain,
    Python's default `logging.lastResort` handler writes those WARNING+
    records straight to this process's real `sys.stderr`, contradicting
    this file's own SILENT contract (module docstring). The suppression
    lives HERE, at the shipping hook boundary, rather than inside
    `core/tel/*` itself, so every OTHER caller of the tel engine (e.g. the
    interactive `cli/render.py` TUI path, which legitimately wants those
    warnings surfaced) is unaffected -- see `core.tel.host_adapter`'s
    module docstring for the corresponding contract note.

    `propagate = False` on this SAME logger is required, not optional: a
    child logger (e.g. `gald3r_core.core.tel.decorate`) with no handler of
    its own still walks up to this `NullHandler` via
    `logging.Logger.callHandlers`, but that walk continues PAST it to the
    root logger (and `lastResort`) unless the logger holding the handler
    also has `propagate = False`.
    """
    try:
        tel_logger = logging.getLogger("gald3r_core.core.tel")
        tel_logger.addHandler(logging.NullHandler())
        tel_logger.propagate = False
    except Exception:
        pass


def main() -> int:
    _silence_tel_logging()

    parser = _SilentArgumentParser(add_help=False)
    parser.add_argument("--kind", choices=_KINDS, default="post_tool_use")
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        # An invalid --kind (or any other argparse parse failure) must
        # never escape this hook as a non-zero exit -- see module
        # docstring's SILENT / ALWAYS-exits-0 contract. Fall back to the
        # same safe default --kind the parser itself uses for a bare
        # invocation.
        args = argparse.Namespace(kind="post_tool_use")

    root = _hook_common.project_root()
    payload = _hook_common.read_stdin_json()

    try:
        adapter = _import_adapter()
        if adapter is None:
            _diag(root, "TEL adapter unavailable (engine not resolved) -- skipping tap")
            return 0

        pipeline = adapter.build_host_pipeline(root)
        if pipeline is None:
            return 0  # GALD3R_TEL_DISABLE, or nothing to resolve -- nothing to do

        if args.kind == "transcript":
            transcript_path = payload.get("transcript_path")
            if not transcript_path:
                return 0
            for record in _new_transcript_records(root, str(transcript_path)):
                adapter.handle_host_event("transcript", record, pipeline=pipeline)
        else:
            adapter.handle_host_event(args.kind, payload, pipeline=pipeline)
    except Exception as exc:  # pragma: no cover -- belt-and-suspenders, never crash
        _diag(root, "tap error: %s" % exc)

    return 0  # ALWAYS 0 -- fire-and-forget, never blocks the host session


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session -- and this one must
        # never print anything, not even the "{}" envelope other concern
        # hooks use (see module docstring's SILENT contract).
        sys.exit(0)
