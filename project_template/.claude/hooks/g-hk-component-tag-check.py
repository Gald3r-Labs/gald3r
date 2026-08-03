#!/usr/bin/env python3
"""Thin resolver+verb dispatcher for the g-rl-38 subsystem-tagging guard (T318).

Git pre-commit hook: enforce subsystem tagging on staged `.gald3r_sys/` components.
Blocks commits that add new component files to `.gald3r_sys/` without subsystem tagging.

This hook used to hand-roll the staged-file git scan and the tag-presence regex checks
inline (flagged fix-thin by the v3 IP classification alongside T179's hook). That
enforcement logic now lives in the binary as `gald3r lint tag-check` (backed by
`gald3r_core.project.lint.tag_check.lint_tag_check`, wired in `cli/commands/lint_cmd.py`).
This hook is reduced to the same resolver+dispatch pattern already used by
`g-hk-policy-check.py`, `g-hk-agent-worktree-janitor.py`, `g-hk-pre-push.py`, and
`g-hk-pre-tool-call-member-gald3r-guard.py`: resolve the engine via
`_hook_common.resolve_engine_argv`, forward the `-WarnOnly` flag, and propagate the
verb's stdout/stderr/exit code untouched (no output capture -- the child inherits this
process's stdio, so the printed violation report is byte-for-byte identical to the old
inline implementation).

Fail-open when the engine can't be resolved (no `gald3r` binary on PATH / not shipped on
this tier): this is a deliberate, disclosed trade-off matching every other absorbed-verb
hook in this tree (see e.g. `g-hk-policy-check.py`'s docstring) -- before this thin, the
check ran unconditionally (pure git + stdlib, no engine dependency); after, a project
without the compiled binary installed gets no enforcement from this hook. Kept per D-7
("KEPT -- not superseded"; see `.claude/hooks/g-hk-component-tag-check.md`) as the only
enforcement path for g-rl-38 tagging.

Run modes (unchanged):
  - git pre-commit hook (via core.hooksPath): called with no arguments, no stdin
  - Direct check:  python g-hk-component-tag-check.py [-WarnOnly] [-Staged]

Exit codes (unchanged): 0 = pass (allow commit) or engine not resolvable (fail-open),
1 = fail (block commit).

Rule reference: .claude/rules/g-rl-38-component-creation-standards.md
Verb: `gald3r lint tag-check [--root PATH] [--warn-only] [--json]`
(`src/gald3r_core/cli/commands/lint_cmd.py`,
`src/gald3r_core/project/lint/tag_check.py`).
"""
# @subsystems: PROJECT_IDENTITY_SETUP
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
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402


def _resolve_engine_cmd(project_root: Path):
    """Resolve the gald3r engine command prefix (P3 Tier-0, T179/T191).

    Same shared resolver as `g-hk-policy-check.py` -- env var -> PATH -> legacy loose
    resolver -> loud degrade. Returns the command prefix or ``None`` when no engine can be
    found, in which case the hook no-ops (allow the commit -- fail-open).
    """
    return _hook_common.resolve_engine_argv(
        project_root, hook_name="g-hk-component-tag-check"
    )


def _find_project_root() -> Path:
    """Walk up from cwd for a `.gald3r/` ancestor; fall back to `_hook_common`'s
    hook-file-relative resolution.

    T516 (T512 inventory row 10 -- pre-commit component-tag enforcement,
    g-rl-38): applies the shared T512 gitignore-refusal + ambiguity-warning
    walk-up guard (`_hook_common.guarded_walk_up`).
    """
    d = Path.cwd()
    root = _hook_common.guarded_walk_up(
        d, exclude=_hook_common.resolved_global_gald3r_home()
    )
    return root if root is not None else _hook_common.project_root()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enforce subsystem tagging on staged .gald3r_sys components."
    )
    parser.add_argument(
        "-WarnOnly", "--warn-only", dest="warn_only", action="store_true",
        help="Print findings but do not block (exit 0 always)",
    )
    parser.add_argument(
        "-Staged", "--staged", dest="staged", action="store_true",
        help="Explicit staged mode (default when called from git) -- accepted for CLI "
        "compatibility; no-op, since the verb always inspects the git staged index.",
    )
    args = parser.parse_args()

    root = _find_project_root()
    engine = _resolve_engine_cmd(root)
    if engine is None:
        # Engine not installed / not shipped on this tier -- pure no-op (fail-open),
        # matching every other absorbed-verb hook in this tree.
        return 0

    cmd = [*engine, "lint", "tag-check"]
    if args.warn_only:
        cmd.append("--warn-only")

    try:
        # No output capture: the verb's stdout/stderr are this process's own (git invokes
        # this hook with its stdio already connected to the terminal/commit UI), so the
        # printed violation report reaches the same destination the old inline
        # implementation wrote to, byte-for-byte.
        #
        # BUG-574: `stdout`/`stderr` are passed EXPLICITLY (not omitted/None) so Python's
        # Windows subprocess implementation sets STARTUPINFO's STARTF_USESTDHANDLES with
        # this process's own std handles. When omitted, Windows CreateProcess() falls back
        # to ambient/default std-handle inheritance, which reproducibly loses the
        # grandchild's stdout/stderr specifically when this hook itself runs as a NESTED
        # child (e.g. the real `.githooks/pre-commit` dispatcher chain: `sh -> python
        # <this hook> -> gald3r.exe`) -- the exit code still propagates correctly (the
        # commit is still blocked/allowed correctly), but the explanatory violation banner
        # vanished silently, leaving a confusing "commit failed, no output" UX. Live-
        # reproduced end to end via the actual dispatcher chain during BUG-574
        # investigation; explicit stdout=/stderr= reliably restores the banner. No-op on
        # POSIX, where fd inheritance does not depend on this distinction.
        proc = subprocess.run(cmd, timeout=30, stdout=sys.stdout, stderr=sys.stderr)
        return proc.returncode
    except Exception:
        # Fail-open: a broken engine invocation must never block a commit outright beyond
        # what the verb itself would have decided.
        return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, OSError):
        pass
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Never crash the session on unexpected errors -- fail open.
        sys.exit(0)
