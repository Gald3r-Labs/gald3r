#!/usr/bin/env python3
"""Python port of toon_test.ps1 (T1585).

Edge-case round-trip tests for the TOON encoder/decoder (T1384). Imports the
REAL encode_node / decode_block / coerce functions from toon_output.py (no
duplicated logic, per g-rl-04) and asserts ENCODE -> DECODE is lossless for the
edge cases that the in-line VALIDATE smoke-test does not cover.

Standalone: ``python toon_test.py``. Exit 0 = all pass, 1 = one or more failures.
"""
# @subsystems: UI_AND_OUTPUT
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from toon_output import cprint, decode, encode  # noqa: E402


_PASS = 0
_FAIL = 0


def _canon(v: Any) -> str:
    return json.dumps(v, separators=(",", ":"), ensure_ascii=False)


def roundtrip(obj: Any) -> Dict[str, str]:
    """ENCODE then DECODE an arbitrary object; return TOON + canonical JSONs."""
    # wrap in an envelope-like node so top level is always an object
    node = OrderedDict([("data", obj)])
    toon = encode(node)
    decoded = decode(toon)
    return {
        "Toon": toon,
        "SrcJson": _canon(node["data"]),
        "RtJson": _canon(decoded.get("data")),
    }


def test_case(name: str, obj: Any, show_toon: bool = False) -> None:
    """Run one round-trip case and record PASS/FAIL."""
    global _PASS, _FAIL
    r = roundtrip(obj)
    if r["SrcJson"] == r["RtJson"]:
        _PASS += 1
        cprint(f"  PASS  {name}", "green")
    else:
        _FAIL += 1
        cprint(f"  FAIL  {name}", "red")
        print(f"        src: {r['SrcJson']}")
        print(f"        got: {r['RtJson']}")
    if show_toon:
        cprint(f"----TOON----\n{r['Toon']}\n------------", "cyan")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the TOON edge-case suite; exit 0 on all-pass."""
    p = argparse.ArgumentParser(description="TOON edge-case round-trip tests (T1384).")
    p.add_argument("-ShowToon", "--show-toon", dest="show_toon", action="store_true")
    args = p.parse_args(argv)
    show = args.show_toon

    cprint("TOON edge-case round-trip tests", "cyan")

    # 1. Object nested 3+ levels deep
    test_case("nested 3+ levels deep",
              {"a": {"b": {"c": {"d": 42, "label": "deep"}}}}, show)

    # 2. Empty object array -> [] (not null)
    test_case("empty array", {"items": []}, show)

    # 3. Single-element object array -> 1-element array (not scalar)
    test_case("single-element object array",
              {"rows": [{"id": 1, "name": "only"}]}, show)

    # 4. null cell in a tabular row -> None
    test_case("null cell in tabular row",
              {"rows": [{"id": 1, "note": "has"}, {"id": 2, "note": None}]}, show)

    # 5. Pipe-escaped cell -> literal | preserved
    test_case("pipe inside tabular cell",
              {"rows": [{"id": 1, "expr": "a | b", "cmd": "x|y"}]}, show)

    # 6. Empty string value round-trips as "" (scalar AND tabular cell)
    test_case("empty string scalar", {"blank": ""}, show)
    test_case("empty string in tabular cell",
              {"rows": [{"id": 1, "note": ""}]}, show)

    # 7. Numeric-looking string preserved as string, not coerced to int
    test_case("numeric-looking string scalar", {"code": "012"}, show)
    test_case("numeric-looking string in tabular cell",
              {"rows": [{"id": 1, "code": "007", "ver": "1.2"}]}, show)
    # bool-looking string must stay a string too
    test_case("bool-looking string scalar", {"flag": "true"}, show)

    # 8. Real boolean in a tabular cell coerced correctly
    test_case("boolean in tabular cell",
              {"rows": [{"id": 1, "active": True, "locked": False}]}, show)

    # 9. Scalar array with 0 elements -> empty array
    test_case("empty scalar array", {"labels": []}, show)

    # 9b. Non-empty scalar arrays must stay scalar (NOT become tabular) -- the
    #     bug class the PS1 broken Is-Obj hid (T1384).
    test_case("non-empty string scalar array",
              {"labels": ["feature", "bug", "chore"]}, show)
    test_case("numeric scalar array", {"nums": [1, 2, 3]}, show)
    test_case("single-element scalar array", {"one": ["solo"]}, show)

    # Bonus: special characters are SAFE and round-trip bare (T1383)
    test_case("special chars % # ! @ * \\ stay bare",
              {"pct": "87%", "hash": "#tag", "bang": "no!",
               "at": "@user", "star": "a*b", "back": "a\\b"}, show)

    print("")
    cprint(f"Results: {_PASS} passed, {_FAIL} failed",
           "green" if _FAIL == 0 else "red")
    return 1 if _FAIL > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
