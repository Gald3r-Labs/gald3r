#!/usr/bin/env python3
"""Python port of gald3r_git_sanity_common.ps1 (T1585).

Shared patterns/helpers for gald3r git sanity (pre-commit + push gate).
Import from hooks/scripts instead of dot-sourcing the .ps1:

    from gald3r_git_sanity_common import get_gald3r_secret_patterns

Repository root is resolved by the caller (git rev-parse).
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

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
