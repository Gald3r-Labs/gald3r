#!/usr/bin/env python3
"""Python port of gald3r_compress_memory.ps1 (T1585).

Analyze (and optionally apply) compression of the NON-gald3r sections of memory
files (AGENTS.md / CLAUDE.md / *memory*.md) while strictly preserving
gald3r-managed ranges (T1053).

DRY-RUN by default. Detects ``<!-- gald3r SECTION START -->`` ..
``<!-- gald3r SECTION END -->`` marker pairs and treats everything INSIDE them
as off-limits. Reports per-file token budgets (char/4 proxy) for the protected
vs compressible regions. Apply mode splices an agent-produced compressed body
back in, preserving protected ranges byte-for-byte, and only after explicit
-Confirm.

Safety: in a gald3r SOURCE repo (``.gald3r_sys/`` present and no markers in
the file) the ENTIRE memory file is gald3r-managed, so the script SKIPS it.
"""
# @subsystems: MEMORY_AND_KNOWLEDGE
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


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


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36",
         "white": "37", "gray": "90"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


def get_project_root(explicit: Optional[str]) -> str:
    """Walk up from cwd until .gald3r is found (PS1 semantics: stop at FS root)."""
    if explicit:
        return explicit
    d = Path.cwd()
    while not (d / ".gald3r").exists():
        if d.parent == d:
            break
        d = d.parent
    return str(d)


def est_tokens(s: str) -> int:
    """char/4 token proxy (ceil), matching the PS1 Est-Tokens."""
    if not s:
        return 0
    return int(math.ceil(len(s) / 4.0))


def is_source_repo(root: str) -> bool:
    """True when this is a gald3r SOURCE repo (.gald3r_sys/ present)."""
    return (Path(root) / ".gald3r_sys").exists()


_START_RX = re.compile(r"(?i)<!--.*gald3r.*(section\s+start|begin)")
# The PS1 end-pattern's second alternative (`^.*end\s*-->`) can never match
# after the required prefix, so the effective end marker is `section end`.
_END_RX = re.compile(r"(?i)<!--.*gald3r.*section\s+end")


def find_protected_ranges(lines: Sequence[str]) -> Dict[str, Any]:
    """Return {'protected': [{'start','end'}...], 'hasMarkers': bool} (0-based lines)."""
    ranges: List[Dict[str, int]] = []
    open_idx: Optional[int] = None
    had = False
    for i, l in enumerate(lines):
        if _START_RX.search(l):
            open_idx = i
            had = True
            continue
        if _END_RX.search(l) and open_idx is not None:
            ranges.append({"start": open_idx, "end": i})
            open_idx = None
            had = True
            continue
    if open_idx is not None:  # unterminated -> protect to EOF
        ranges.append({"start": open_idx, "end": len(lines) - 1})
    return {"protected": ranges, "hasMarkers": had}


def analyze_file(file: str, root: str, force: bool) -> "OrderedDict[str, Any]":
    """Per-file dry-run analysis: protected vs compressible token budgets."""
    raw = Path(file).read_text(encoding="utf-8", errors="surrogateescape")
    lines = re.split(r"\r?\n", raw)
    info = find_protected_ranges(lines)
    total_tok = est_tokens(raw)
    result: "OrderedDict[str, Any]" = OrderedDict([
        ("file", file), ("total_tokens", total_tok), ("has_markers", info["hasMarkers"]),
        ("protected_tokens", 0), ("compressible_tokens", 0), ("status", ""), ("note", ""),
    ])
    if not info["hasMarkers"]:
        if is_source_repo(root):
            result["status"] = "skip"
            result["note"] = ("gald3r SOURCE repo + no SECTION markers: entire file is "
                              "gald3r-managed -- nothing safely compressible.")
            result["protected_tokens"] = total_tok
            return result
        if not force:
            result["status"] = "warn"
            result["note"] = ("No gald3r SECTION markers found. In a consumer project this "
                              "usually means an old install. Re-run with -Force to treat "
                              "the whole file as user-compressible.")
            return result
        result["status"] = "compressible"
        result["compressible_tokens"] = total_tok
        result["note"] = ("No markers; -Force: entire file treated as compressible "
                          "(still dry-run unless -Apply).")
        return result

    # markers present: compressible = lines outside protected ranges
    protected_line_set = set()
    for r in info["protected"]:
        protected_line_set.update(range(r["start"], r["end"] + 1))
    prot_tok = 0
    comp_tok = 0
    for i, line in enumerate(lines):
        t = est_tokens(line + "\n")
        if i in protected_line_set:
            prot_tok += t
        else:
            comp_tok += t
    result["protected_tokens"] = prot_tok
    result["compressible_tokens"] = comp_tok
    result["status"] = "compressible"
    result["note"] = (f"{len(info['protected'])} protected gald3r range(s). Compress only "
                      "the compressible region; preserve code blocks + URLs verbatim. "
                      "Target >=30% reduction on the compressible tokens.")
    return result


def apply_mode(file: str, compressed_file: str) -> int:
    """Verify protected ranges are byte-identical, then write the compressed file."""
    raw = Path(file).read_text(encoding="utf-8", errors="surrogateescape")
    lines = re.split(r"\r?\n", raw)
    info = find_protected_ranges(lines)
    if not info["hasMarkers"]:
        print("ERROR: Refusing to apply: no gald3r SECTION markers -- cannot guarantee "
              "protected-range preservation.", file=sys.stderr)
        return 2
    # The apply path requires the agent to supply the FULL new file with protected
    # ranges intact; we verify the protected ranges are byte-identical before writing.
    new_raw = Path(compressed_file).read_text(encoding="utf-8", errors="surrogateescape")
    new_lines = re.split(r"\r?\n", new_raw)
    new_info = find_protected_ranges(new_lines)
    orig_prot = ["\n".join(lines[r["start"]:r["end"] + 1]) for r in info["protected"]]
    new_prot = ["\n".join(new_lines[r["start"]:r["end"] + 1]) for r in new_info["protected"]]
    if "\n--\n".join(orig_prot) != "\n--\n".join(new_prot):
        print("ERROR: Refusing to apply: protected gald3r range(s) differ between original "
              "and compressed file. No write performed.", file=sys.stderr)
        return 3
    Path(file).write_text(new_raw, encoding="utf-8", errors="surrogateescape")
    cprint(f"APPLIED: {file} (protected gald3r ranges verified byte-identical)", "green")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Compress the NON-gald3r sections of memory files, preserving "
                    "gald3r-managed ranges (T1053)."
    )
    p.add_argument("-Path", "--path", dest="path", default=None,
                   help="Specific file; omitted = scan AGENTS.md + CLAUDE.md in -ProjectRoot")
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", default=None)
    p.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                   help="default off = dry-run")
    p.add_argument("-CompressedFile", "--compressed-file", dest="compressed_file",
                   default=None, help="apply mode: agent-produced compressed body")
    p.add_argument("-Confirm", "--confirm", dest="confirm", action="store_true",
                   help="required for -Apply (no silent file writes)")
    p.add_argument("-Force", "--force", dest="force", action="store_true",
                   help="consumer project with no markers: allow whole-file compress")
    p.add_argument("-Json", "--json", dest="json", action="store_true")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: dry-run analysis report, or guarded apply."""
    args = build_parser().parse_args(argv)
    root = get_project_root(args.project_root)

    targets: List[str] = []
    if args.path:
        p = args.path
        targets = [p if Path(p).is_absolute() else str(Path(root) / p)]
    else:
        for n in ("AGENTS.md", "CLAUDE.md"):
            cand = Path(root) / n
            if cand.is_file():
                targets.append(str(cand))

    if not targets:
        cprint("No memory files found (AGENTS.md/CLAUDE.md).", "yellow")
        return 0

    # APPLY mode (single file + compressed body) --------------------------------
    if args.apply:
        if not args.confirm:
            print("ERROR: Apply mode requires -Confirm (no silent writes to tracked "
                  "memory files).", file=sys.stderr)
            return 2
        if not args.path or not args.compressed_file:
            print("ERROR: Apply mode requires -Path <file> and -CompressedFile "
                  "<agent-compressed-body>.", file=sys.stderr)
            return 2
        return apply_mode(targets[0], args.compressed_file)

    # DRY-RUN report -------------------------------------------------------------
    reports = [analyze_file(f, root, args.force) for f in targets]
    if args.json:
        print(json.dumps(reports, indent=2))
        return 0

    cprint("g-skl-compress-memory -- DRY RUN (no files modified)", "cyan")
    for r in reports:
        cprint(f"\n  {r['file']}", "white")
        print(f"    status={r['status']}  total~{r['total_tokens']} tok  "
              f"protected~{r['protected_tokens']}  compressible~{r['compressible_tokens']}")
        if r["compressible_tokens"] > 0:
            saved = int(math.ceil(r["compressible_tokens"] * 0.30))
            cprint(f"    target: >=30% of {r['compressible_tokens']} compressible tokens "
                   f"(~{saved} tok saved)", "cyan")
        cprint(f"    {r['note']}", "gray")
    cprint("\nTo compress: run the g-skl-compress-memory skill on the compressible region, "
           "then apply with -Apply -CompressedFile <new-full-file> -Confirm.", "cyan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
