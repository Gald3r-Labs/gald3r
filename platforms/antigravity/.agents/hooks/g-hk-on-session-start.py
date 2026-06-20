#!/usr/bin/env python3
"""Canonical `session-start` event entrypoint (T424).

Thin trigger shim: delegates to the shared canonical event core
(`g_hk_core.dispatch`). Contains NO business logic — behavior lives in the
core and the concern chain it runs. Platform triggers point here so every
harness fires the SAME shared core.
"""
# @subsystems: PLATFORM_INTEGRATION
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g_hk_core  # noqa: E402

if __name__ == "__main__":
    sys.exit(g_hk_core.dispatch("session-start"))
