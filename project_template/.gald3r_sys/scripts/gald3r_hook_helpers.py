#!/usr/bin/env python3
"""Python port of gald3r_hook_helpers.ps1 (T1587).

Shared gald3r hook system helpers (Task 600). Pure-function helpers for the
gald3r hook system extensions designed in
``docs/20260506_000000_Cursor_T600_HOOK_SYSTEM_EXTENSIONS.md``.

All helpers are side-effect-free except for INFO-level logging via the module
logger (the PS1 used ``Write-Verbose``). Safe to import from hook scripts —
this is the importable-module equivalent of dot-sourcing the .ps1.

Function surface (PS1 name -> Python name):
  Test-HookToolMatch     -> test_hook_tool_match      (B-3)
  Convert-HookArgSafe    -> convert_hook_arg_safe     (B-6)
  Read-HookEventEnvelope -> read_hook_event_envelope

Run ``python gald3r_hook_helpers.py -RunSelfTest`` (or ``--run-self-test``)
to execute the same smoke test vectors the PS1 ships with.

This module is intentionally pure stdlib — no gald3r engine import needed.
"""
# @subsystems: LOGGING_SYSTEM
from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any, Optional, Sequence

logger = logging.getLogger(__name__)

__all__ = [
    "test_hook_tool_match",
    "convert_hook_arg_safe",
    "read_hook_event_envelope",
]


# -----------------------------------------------------------------------------
# test_hook_tool_match  (AC#2 / B-3)  — PS1: Test-HookToolMatch
# -----------------------------------------------------------------------------

def test_hook_tool_match(tool_name: str, patterns: Optional[Sequence[str]],
                         match_all_on_empty: bool = True) -> bool:
    """Return True if `tool_name` matches at least one of `patterns`.

    Supported pattern syntax ('*' is the only wildcard; matching is
    case-sensitive, exactly like the PS1 -cmatch implementation):
      'bash'            -- exact match
      'bash_*'          -- prefix match
      '*_run'           -- suffix match
      'mcp__*__execute' -- prefix + suffix (any number of '*' is fine)
      '*'               -- match every tool name

    '?' character classes, '**', and '/' segment anchors are NOT supported.

    Args:
        tool_name: Tool identifier produced by the IDE (e.g. 'bash_run').
        patterns: Pattern list; empty/None falls back to `match_all_on_empty`.
        match_all_on_empty: Result when `patterns` is empty (default True —
            "no filter == fire on every tool").
    """
    if not patterns:
        return bool(match_all_on_empty)

    for pattern in patterns:
        if not pattern:
            continue
        # Exact match shortcut (case-sensitive)
        if pattern == tool_name:
            return True
        # Build a literal-anchored regex: '*' -> '.*', everything else escaped.
        # str.split('*') preserves empty leading/trailing segments, matching
        # the PS1 String.Split semantics ('*foo' -> ['', 'foo']).
        regex = "^" + ".*".join(re.escape(seg) for seg in pattern.split("*")) + "$"
        if re.match(regex, tool_name):
            return True
    return False


# -----------------------------------------------------------------------------
# convert_hook_arg_safe  (AC#4 / B-6)  — PS1: Convert-HookArgSafe
# -----------------------------------------------------------------------------

def convert_hook_arg_safe(value: Optional[str], shell: str = "powershell") -> str:
    """Return a shell-safe single-quoted literal for `value`.

    Modes (see §4 of the T600 design doc for the threat model):
      shell='powershell' (default)
        Single-quoted; embedded single quotes doubled; CR/LF replaced with
        '<CR>'/'<LF>' placeholders so multi-line values cannot terminate the
        statement. PowerShell single-quote literals do not interpolate.
      shell='bash'
        Single-quoted; embedded single quotes use the canonical '\\''
        close / escaped-quote / re-open trick. CR/LF pass through (bash
        tolerates multi-line single-quoted argv).

    Args:
        value: String to quote; None becomes ''.
        shell: 'powershell' or 'bash'.

    Raises:
        ValueError: On an unsupported `shell` (PS1 ValidateSet equivalent).
    """
    if value is None:
        value = ""

    if shell == "powershell":
        sanitized = value.replace("\r", "<CR>").replace("\n", "<LF>")
        if sanitized != value:
            logger.info("convert_hook_arg_safe: stripped CR/LF from value")
        escaped = sanitized.replace("'", "''")
        return f"'{escaped}'"
    if shell == "bash":
        escaped = value.replace("'", "'\\''")
        return f"'{escaped}'"
    raise ValueError(f"shell must be 'powershell' or 'bash', got: {shell!r}")


# -----------------------------------------------------------------------------
# read_hook_event_envelope  (companion to AC#1 / B-2)  — PS1: Read-HookEventEnvelope
# -----------------------------------------------------------------------------

def read_hook_event_envelope(inline_json: Optional[str] = None) -> Optional[Any]:
    """Parse the gald3r hook event envelope.

    Sources, in order of precedence: `inline_json` (useful for tests), the
    ``GALD3R_HOOK_EVENT`` environment variable, then the file named by
    ``GALD3R_HOOK_EVENT_FILE`` (for environments where env-var size is
    constrained).

    Returns:
        The parsed JSON value (dict/list/...), or None when no envelope is
        available or the JSON is malformed.
    """
    json_text: Optional[str] = None

    if inline_json:
        json_text = inline_json
    elif os.environ.get("GALD3R_HOOK_EVENT"):
        json_text = os.environ["GALD3R_HOOK_EVENT"]
    else:
        event_file = os.environ.get("GALD3R_HOOK_EVENT_FILE", "")
        if event_file and os.path.exists(event_file):
            with open(event_file, "r", encoding="utf-8-sig") as fh:
                json_text = fh.read()

    if not json_text:
        return None
    try:
        return json.loads(json_text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.info("read_hook_event_envelope: failed to parse JSON: %s", exc)
        return None


# -----------------------------------------------------------------------------
# Self-test (same vectors as the PS1 -RunSelfTest block)
# -----------------------------------------------------------------------------

def _run_self_test() -> int:
    failed = 0

    def assert_eq(name: str, got: Any, want: Any) -> None:
        nonlocal failed
        if got == want:
            print(f"ok    {name}")
        else:
            print(f"FAIL  {name}\n  got:  {got}\n  want: {want}")
            failed += 1

    # test_hook_tool_match
    assert_eq("match prefix bash_*",
              test_hook_tool_match("bash_run", ["bash_*"]), True)
    assert_eq("no match bash vs bash_*",
              test_hook_tool_match("bash", ["bash_*"]), False)
    assert_eq("OR file_*",
              test_hook_tool_match("file_read", ["bash_*", "file_*"]), True)
    assert_eq("empty patterns -> true",
              test_hook_tool_match("whatever", []), True)
    assert_eq("empty patterns + match_all_on_empty=False -> false",
              test_hook_tool_match("whatever", [], match_all_on_empty=False), False)
    assert_eq("mcp middle wildcard",
              test_hook_tool_match("mcp__chrome-devtools__click",
                                   ["mcp__*__click"]), True)
    assert_eq("case sensitive",
              test_hook_tool_match("Bash_run", ["bash_*"]), False)
    assert_eq("star matches all",
              test_hook_tool_match("anything", ["*"]), True)

    # convert_hook_arg_safe
    assert_eq("ps simple", convert_hook_arg_safe("hello", "powershell"), "'hello'")
    assert_eq("ps single quote", convert_hook_arg_safe("it's", "powershell"),
              "'it''s'")
    assert_eq("ps dollar paren literal",
              convert_hook_arg_safe("$(whoami)", "powershell"), "'$(whoami)'")
    assert_eq("bash simple", convert_hook_arg_safe("hello", "bash"), "'hello'")
    assert_eq("bash single quote", convert_hook_arg_safe("it's", "bash"),
              "'it'\\''s'")
    assert_eq("bash semicolon", convert_hook_arg_safe("; rm -rf /", "bash"),
              "'; rm -rf /'")

    if failed > 0:
        print(f"\n{failed} test(s) failed")
        return 1
    print("\nAll tests passed.")
    return 0


if __name__ == "__main__":
    if any(a in ("-RunSelfTest", "--run-self-test") for a in sys.argv[1:]):
        sys.exit(_run_self_test())
    print(__doc__)
    print("Pass -RunSelfTest (or --run-self-test) to run the smoke test vectors.")
