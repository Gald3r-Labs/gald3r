#!/usr/bin/env python3
"""Canonical `stop` event entrypoint (T424).

Thin trigger shim: delegates to the shared canonical event core
(`g_hk_core.dispatch`). Contains NO business logic. Fires when the agent
finishes responding to a turn (distinct from `session-end`).
"""
# @subsystems: PLATFORM_INTEGRATION
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g_hk_core  # noqa: E402

if __name__ == "__main__":
    sys.exit(g_hk_core.dispatch("stop"))
