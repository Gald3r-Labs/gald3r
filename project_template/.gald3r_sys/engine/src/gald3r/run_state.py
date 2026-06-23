"""Active agent-run detection (T585).

During a multi-agent / autopilot run (g-go-go, g-go-code, swarm), each agent
that creates a task or bug must NOT write directly to `tasks/open/` +
regenerate the index — concurrent writers race on the next id and collide
(observed live 2026-06-20: intake handed drafts 573-584, colliding with
just-completed tasks). Instead, creation routes to `tasks/inbox/` /
`bugs/inbox/` as an id-less draft, and the hot-inbox intake (the single
ID-assigning authority) assigns real ids atomically at each iteration
boundary.

This module is the one place that answers "is an agent run active?" so the
create paths and the orchestration layer agree. Pure stdlib, never raises.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

#: Env override — set to "1"/"true" to force run-active (orchestrators that
#: do not maintain ggo_run_state.json can still opt task/bug creation into the
#: inbox path). Set to "0"/"false" to force-disable even if the marker is hot.
_ENV_FLAG = "GALD3R_AGENT_RUN"

#: Marker file written by the g-go-go orchestrator: `{"active": true, ...}`.
_RUN_STATE_REL = ("logs", "ggo_run_state.json")


def _env_override() -> "bool | None":
    """Return the forced state from the env flag, or None when unset/blank."""
    raw = os.environ.get(_ENV_FLAG)
    if raw is None or not raw.strip():
        return None
    return raw.strip().lower() in ("1", "true", "yes", "on")


def is_agent_run_active(gald3r_dir: Path) -> bool:
    """True when a multi-agent / autopilot run is in progress.

    Resolution order (first decisive wins):
      1. ``GALD3R_AGENT_RUN`` env flag (explicit override, either direction).
      2. ``.gald3r/logs/ggo_run_state.json`` with a truthy ``active`` field.

    Args:
        gald3r_dir: The project's ``.gald3r`` directory.

    Returns:
        True if creation should route to the inbox; False otherwise. Never
        raises — a missing/garbled marker reads as "not active".
    """
    override = _env_override()
    if override is not None:
        return override
    marker = Path(gald3r_dir).joinpath(*_RUN_STATE_REL)
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(data.get("active", False)) if isinstance(data, dict) else False
