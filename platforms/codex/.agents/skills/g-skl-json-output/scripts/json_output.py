#!/usr/bin/env python3
"""Python port of json_output.ps1 (T1585).

SERIALIZE + VALIDATE + EXPORT for g-skl-json-output (T1381). Takes a JSON
string of the schema-specific `data` payload, wraps it with version/timestamp/
command/schema, validates, and writes a timestamped .json under the output dir
(g-rl-01).
"""
# @subsystems: UI_AND_OUTPUT
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
import os
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence


def _bootstrap_engine_utils() -> bool:
    """Make gald3r.utils importable via the installed package.

    T274 (P5-E blocker): the pre-retirement ".gald3r_sys/engine/src" fallback
    walk is removed -- ".gald3r_sys/" is actively purged from every project
    by the deploy pipeline (T335) and never exists in a fresh install, so
    that branch was permanently dead code, not a real fallback.
    """
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        return False


_HAS_UTILS = _bootstrap_engine_utils()


def _color_enabled() -> bool:
    if _HAS_UTILS:
        from gald3r.utils import console
        return console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


def _is_gitignored(path: Path) -> "bool | None":
    """T516: cheap, authoritative gitignore check (same guard shape as T512's
    `find_gald3r_root` fix, commit 3682aa64). `None` (check could not run)
    is treated as fail-open by the caller."""
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


def find_project_root(*, ambiguous_candidates: "list[Path] | None" = None) -> str:
    """Walk up from cwd until .gald3r is found (PS1 semantics: stop at FS root).

    T516 (T512 inventory row 22 -- low blast radius: report output path): a
    candidate whose `.gald3r/` is gitignored is refused (never adopted --
    the walk continues upward for the real, tracked root). A second,
    non-gitignored candidate further up than the nearest one is appended to
    `ambiguous_candidates` (when supplied) but the NEAREST candidate still
    wins -- no behavior change for the ordinary single-`.gald3r/` case.
    """
    d = Path.cwd()
    resolved: Optional[Path] = None
    while True:
        marker = d / ".gald3r"
        if marker.exists():
            if _is_gitignored(marker):
                pass  # T516: refuse -- never silently adopt a decoy.
            elif resolved is None:
                resolved = d
            elif ambiguous_candidates is not None:
                ambiguous_candidates.append(d)
        if d.parent == d:
            break
        d = d.parent
    return str(resolved) if resolved is not None else str(d)


def read_gald3r_version(project_root: str) -> str:
    """Read gald3r_version= from .gald3r/.identity (best effort)."""
    idf = Path(project_root) / ".gald3r" / ".identity"
    if idf.is_file():
        for line in idf.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*gald3r_version=(.+)$", line)
            if m:
                return m.group(1).strip()
    return "unknown"


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Wrap gald3r report data in the standard JSON envelope and export (T1381)."
    )
    p.add_argument("-Command", "--command", dest="command", required=True)
    p.add_argument("-Schema", "--schema", dest="schema", required=True,
                   choices=("status", "review", "backlog"))
    p.add_argument("-DataJson", "--data-json", dest="data_json", required=True)
    p.add_argument("-Topic", "--topic", dest="topic", default=None)
    p.add_argument("-OutDir", "--out-dir", dest="out_dir", default="docs")
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", default=None)
    p.add_argument("-IDE", "--ide", dest="ide", default="Claude")
    p.add_argument("-Compact", "--compact", dest="compact", action="store_true")
    p.add_argument("-Stdout", "--stdout", dest="stdout", action="store_true")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: validate data JSON -> wrap envelope -> export/stdout."""
    args = build_parser().parse_args(argv)
    project_root = args.project_root or find_project_root()
    ver = read_gald3r_version(project_root)

    # VALIDATE: data payload must be valid JSON
    try:
        data: Any = json.loads(args.data_json, object_pairs_hook=OrderedDict)
    except ValueError as exc:
        cprint(f"VALIDATE: FAIL -- data is not valid JSON: {exc}", "red")
        return 1

    envelope: "OrderedDict[str, Any]" = OrderedDict([
        ("gald3r_version", ver),
        ("generated_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("command", args.command),
        ("schema", args.schema),
        ("data", data),
    ])
    if args.compact:
        text = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False)
    else:
        text = json.dumps(envelope, indent=2, ensure_ascii=False)

    # VALIDATE: round-trip parse
    try:
        json.loads(text)
    except ValueError:
        cprint("VALIDATE: FAIL -- envelope did not round-trip.", "red")
        return 1
    cprint(f"VALIDATE: PASS (schema={args.schema}, version={ver})", "green")

    if args.stdout:
        print(text)
        return 0

    topic = args.topic or re.sub(r"[^A-Za-z0-9]+", "_", args.command)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_abs = Path(project_root) / args.out_dir
    out_abs.mkdir(parents=True, exist_ok=True)
    out_file = out_abs / f"{stamp}_{args.ide}_{topic.upper()}.json"
    out_file.write_text(text + "\n", encoding="utf-8")
    cprint(f"EXPORT: {out_file}", "cyan")
    print(out_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
