#!/usr/bin/env python3
"""Python port of json_output.ps1 (T1585).

SERIALIZE + VALIDATE + EXPORT for g-skl-json-output (T1381). Takes a JSON
string of the schema-specific `data` payload, wraps it with version/timestamp/
command/schema, validates, and writes a timestamped .json under the output dir
(g-rl-01).
"""
# @subsystems: UI_AND_OUTPUT
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence


def _bootstrap_engine_utils() -> bool:
    """Make gald3r.utils importable: installed package, else walk up to .gald3r_sys/engine/src."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        cand = parent / ".gald3r_sys" / "engine" / "src"
        if (cand / "gald3r" / "utils" / "__init__.py").is_file():
            sys.path.insert(0, str(cand))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
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


def find_project_root() -> str:
    """Walk up from cwd until .gald3r is found (PS1 semantics: stop at FS root)."""
    d = Path.cwd()
    while not (d / ".gald3r").exists():
        if d.parent == d:
            break
        d = d.parent
    return str(d)


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
