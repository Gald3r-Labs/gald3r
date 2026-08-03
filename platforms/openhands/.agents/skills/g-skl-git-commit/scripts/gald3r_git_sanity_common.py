#!/usr/bin/env python3
"""Python port of gald3r_git_sanity_common.ps1 (T1585).

Shared patterns/helpers for gald3r git sanity (pre-commit + push gate).
Import from hooks/scripts instead of dot-sourcing the .ps1:

    from gald3r_git_sanity_common import get_gald3r_secret_patterns

Repository root is resolved by the caller (git rev-parse).
"""
# @subsystems: RELEASE_AND_VERSIONING
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

from typing import List

# Mirrors Get-Gald3rSecretPatterns in gald3r_git_sanity_common.ps1 exactly.
SECRET_PATTERNS: List[str] = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"Bearer\s+[a-zA-Z0-9._\-]{20,}",
    r"AKIA[A-Z0-9]{16}",
    r"password\s*=\s*\S+",
    r"api_key\s*=\s*\S+",
    r"secret_key\s*=\s*\S+",
    r"private_key\s*=\s*\S+",
    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
]


def get_gald3r_secret_patterns() -> List[str]:
    """Return the shared secret-detection regex patterns (copy, not the list)."""
    return list(SECRET_PATTERNS)
