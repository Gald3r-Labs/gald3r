#!/usr/bin/env python3
"""Python port of toon_output.ps1 (T1585).

Encode gald3r report JSON as TOON (Token-Oriented Object Notation) and export
(T1382). ENCODE + DECODE + VALIDATE (lossless round-trip) + EXPORT for
g-skl-toon-output. Wraps the standard envelope (version/timestamp/command/
schema/data) around the supplied JSON `data` payload, encodes to TOON,
validates round-trip, and writes a timestamped .toon under the output dir
(g-rl-01).

The encode/decode functions are importable (toon_test.py uses them directly --
the Python equivalent of the PS1 -AsLibrary dot-source mode).
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


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


# ---------- encode helpers ----------
_INT_RX = re.compile(r"^-?\d+$")
_FLOAT_RX = re.compile(r"^-?\d+\.\d+$")


def looks_coercible(s: str) -> bool:
    """True for bare tokens that Coerce() would reinterpret on DECODE.

    A STRING value matching this MUST be quoted so it round-trips as a string,
    not an int/bool/null (e.g. "012" -> 012, "true" -> True would be lossy). (T1384)
    """
    return (s in ("null", "true", "false")
            or bool(_INT_RX.match(s)) or bool(_FLOAT_RX.match(s)))


def need_quote(s: str) -> bool:
    """Quote when grammar/whitespace ambiguity exists.

    Characters %, #, !, @, *, and a lone backslash are SAFE -- none are part of
    the TOON grammar, so they never trigger quoting and round-trip bare. (T1383)
    """
    return (":" in s or "|" in s) or ("\n" in s) or s != s.strip() or s == ""


def _quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _num_str(v: Any) -> str:
    return str(v)


def enc_scalar(v: Any) -> str:
    """Encode one scalar value (null/bool/number/string with minimal quoting)."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num_str(v)
    s = str(v)
    if need_quote(s) or looks_coercible(s):
        return _quote(s)
    return s


def enc_cell(cv: Any) -> str:
    """Encode one TABULAR cell.

    null -> empty cell; "" -> quoted "" (disambiguates "" from null);
    number/bool-looking strings quoted (preserve type); literal pipes escaped \\|. (T1384)
    """
    if cv is None:
        return ""
    if isinstance(cv, bool):
        return "true" if cv else "false"
    if isinstance(cv, (int, float)):
        return _num_str(cv)
    s = str(cv)
    if s == "" or looks_coercible(s):
        return _quote(s)
    return s.replace("|", "\\|")


def is_obj(v: Any) -> bool:
    """True for JSON-object nodes (dicts). The PS1 needed the concrete
    PSCustomObject type check here (T1384); in Python dict is unambiguous."""
    return isinstance(v, dict)


def encode_node(node: Dict[str, Any], indent: int, out: List[str]) -> None:
    """Encode an object node into TOON lines (appended to `out`)."""
    pad = " " * indent
    for k, v in node.items():
        if isinstance(v, list):
            arr = list(v)
            all_obj = len(arr) > 0 and all(is_obj(e) for e in arr)
            if all_obj:
                fields = list(arr[0].keys())
                out.append(f"{pad}{k}[{len(arr)}]{{{','.join(fields)}}}:")
                for rec in arr:
                    cells = [enc_cell(rec.get(f)) for f in fields]
                    out.append(f"{pad}  " + " | ".join(cells))
            else:
                # scalar array (also the empty-array case: yields "k[0]: ")
                items = [enc_scalar(e) for e in arr]
                out.append(f"{pad}{k}[{len(arr)}]: " + ", ".join(items))
        elif is_obj(v):
            out.append(f"{pad}{k}:")
            encode_node(v, indent + 2, out)
        else:
            out.append(f"{pad}{k}: {enc_scalar(v)}")


def encode(node: Dict[str, Any]) -> str:
    """Encode a top-level object to a TOON document string."""
    out: List[str] = []
    encode_node(node, 0, out)
    return "\n".join(out).rstrip()


# ---------- decode ----------
def coerce(s: str) -> Any:
    """Reinterpret a bare decoded token: null/bool/int/float/quoted-string/string."""
    if s == "null":
        return None
    if s == "true":
        return True
    if s == "false":
        return False
    if _INT_RX.match(s):
        return int(s)
    if _FLOAT_RX.match(s):
        return float(s)
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return s


_TABULAR_RX = re.compile(r"^([\w-]+)\[(\d+)\]\{([^}]*)\}:$")
_SCALAR_ARR_RX = re.compile(r"^([\w-]+)\[(\d+)\]:\s*(.*)$")
_KEY_VAL_RX = re.compile(r"^([\w-]+):\s*(.*)$")
_UNESCAPED_PIPE_RX = re.compile(r"(?<!\\)\|")


def decode_block(lines: Sequence[str], idx: List[int], indent: int) -> "OrderedDict[str, Any]":
    """Recursive-descent decode over an array of lines, by indentation."""
    obj: "OrderedDict[str, Any]" = OrderedDict()
    while idx[0] < len(lines):
        line = lines[idx[0]]
        if line.strip() == "":
            idx[0] += 1
            continue
        cur_indent = len(line) - len(line.lstrip(" "))
        if cur_indent < indent:
            break
        if cur_indent > indent:
            break
        t = line.strip()

        m = _TABULAR_RX.match(t)  # tabular array
        if m:
            key, n, fields = m.group(1), int(m.group(2)), m.group(3).split(",")
            idx[0] += 1
            rows: List["OrderedDict[str, Any]"] = []
            r = 0
            while r < n and idx[0] < len(lines):
                # Split on UNESCAPED pipes only (escaped content pipes are \|).
                # Robust to trailing-space loss on the document TrimEnd. (T1384)
                cells = _UNESCAPED_PIPE_RX.split(lines[idx[0]].lstrip())
                rec: "OrderedDict[str, Any]" = OrderedDict()
                for c, field in enumerate(fields):
                    cell = cells[c].strip().replace("\\|", "|") if c < len(cells) else ""
                    rec[field.strip()] = None if cell == "" else coerce(cell)
                rows.append(rec)
                idx[0] += 1
                r += 1
            obj[key] = rows
            continue

        m = _SCALAR_ARR_RX.match(t)  # scalar array
        if m:
            raw = m.group(3)
            if raw.strip():
                vals = [coerce(p.strip()) for p in raw.split(",")]
            else:
                vals = []
            obj[m.group(1)] = vals
            idx[0] += 1
            continue

        m = _KEY_VAL_RX.match(t)  # key: value | nested
        if m:
            key, val = m.group(1), m.group(2)
            if val == "":
                idx[0] += 1
                obj[key] = decode_block(lines, idx, indent + 2)
            else:
                obj[key] = coerce(val)
                idx[0] += 1
            continue

        idx[0] += 1  # unrecognized; skip
    return obj


def decode(toon: str) -> "OrderedDict[str, Any]":
    """Decode a TOON document string into nested OrderedDicts/lists."""
    return decode_block(re.split(r"\r?\n", toon), [0], 0)


# ---------- project helpers ----------
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


def _canon_json(v: Any) -> str:
    return json.dumps(v, separators=(",", ":"), ensure_ascii=False)


# ---------- CLI ----------
def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Encode gald3r report JSON as TOON and export (T1382)."
    )
    p.add_argument("-Command", "--command", dest="command", default=None)
    p.add_argument("-Schema", "--schema", dest="schema", default=None)
    p.add_argument("-DataJson", "--data-json", dest="data_json", default=None)
    p.add_argument("-Topic", "--topic", dest="topic", default=None)
    p.add_argument("-OutDir", "--out-dir", dest="out_dir", default="docs")
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", default=None)
    p.add_argument("-IDE", "--ide", dest="ide", default="Claude")
    p.add_argument("-Compare", "--compare", dest="compare", action="store_true")
    p.add_argument("-Stdout", "--stdout", dest="stdout", action="store_true")
    p.add_argument("-AsLibrary", "--as-library", dest="as_library", action="store_true",
                   help="No-op in Python: import this module instead (kept for interface parity).")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: encode -> validate round-trip -> (compare) -> export/stdout."""
    args = build_parser().parse_args(argv)
    if args.as_library:
        return 0  # functions are importable; nothing to run

    if not args.command or not args.schema or not args.data_json:
        print("toon_output.py requires -Command, -Schema, and -DataJson "
              "(omit them only with -AsLibrary).", file=sys.stderr)
        return 2
    if args.schema not in ("status", "review", "backlog"):
        print(f"Invalid -Schema '{args.schema}' (expected: status|review|backlog).",
              file=sys.stderr)
        return 2

    project_root = args.project_root or find_project_root()
    ver = read_gald3r_version(project_root)

    try:
        data = json.loads(args.data_json, object_pairs_hook=OrderedDict)
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

    toon = encode(envelope)

    # VALIDATE: lossless round-trip (compare data payloads as canonical JSON)
    decoded = decode(toon)
    src_json = _canon_json(envelope["data"])
    rt_json = _canon_json(decoded.get("data"))
    if src_json != rt_json:
        cprint("VALIDATE: WARN -- round-trip differs (lossy on this payload).", "yellow")
    else:
        cprint(f"VALIDATE: PASS -- lossless round-trip (schema={args.schema}, version={ver})",
               "green")

    if args.compare:
        json_chars = len(json.dumps(envelope, indent=2, ensure_ascii=False))
        toon_chars = len(toon)
        pct = round(100 * (json_chars - toon_chars) / json_chars, 1)
        cprint(f"COMPARE: JSON={json_chars} chars  TOON={toon_chars} chars  "
               f"({pct}% smaller than JSON)", "cyan")

    if args.stdout:
        print(toon)
        return 0

    topic = args.topic or re.sub(r"[^A-Za-z0-9]+", "_", args.command)
    out_abs = Path(project_root) / args.out_dir
    out_abs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_abs / f"{stamp}_{args.ide}_{topic.upper()}.toon"
    out_file.write_text(toon + "\n", encoding="utf-8")
    cprint(f"EXPORT: {out_file}", "cyan")
    print(out_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
