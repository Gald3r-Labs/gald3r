#!/usr/bin/env python3
"""Canonical `tool-start` event entrypoint (T424).

Thin trigger shim: delegates to the shared canonical event core
(`g_hk_core.dispatch`). Contains NO business logic. This is the canonical
blocking guard point — the core returns exit code 2 when a concern hook
blocks the tool call (honored by Cursor preToolUse / kiro-cli preToolUse).
"""
# @subsystems: PLATFORM_INTEGRATION
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g_hk_core  # noqa: E402

if __name__ == "__main__":
    sys.exit(g_hk_core.dispatch("tool-start"))
