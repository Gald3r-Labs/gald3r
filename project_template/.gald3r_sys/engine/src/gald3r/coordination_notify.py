"""T638 — coordinator-session lifecycle notifications (build + decide; transport-agnostic).

The engine owns the coordinator lifecycle (register / complete / stale-sweep), so it
builds the notification PAYLOAD and decides WHETHER to notify (per-project opt-in/out per
event type + quiet hours). The actual delivery — Slack webhook POST, world_tree mailer —
is injected as a `transport` callable; world_tree wires the real transport + stores the
preferences, tests inject a stub. Pure stdlib, no new deps.

Events: `start` (scope claimed), `end` (scope released), `stale` (no heartbeat 5min).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

EVENTS = ("start", "end", "stale")

# A transport sends one rendered notification on one channel. Returns delivered?.
Transport = Callable[[str, Dict[str, object]], bool]


def build_coordinator_event(event: str, session: Dict[str, object],
                            now: Optional[datetime] = None) -> Dict[str, object]:
    """Construct the notification payload for a coordinator lifecycle event.

    `session` is an `active_coordinators()` row (dict). Payload carries the developer,
    scope, tasks completed, and timestamp (T638 AC).
    """
    if event not in EVENTS:
        raise ValueError(f"event must be one of {EVENTS}")
    n = now or datetime.now(timezone.utc)
    developer = (session.get("display_name") or session.get("coordinator_id") or "unknown")
    scope = session.get("subsystem_scope") or "all"
    tasks_completed = session.get("tasks_completed", session.get("tasks_claimed", 0))
    verb = {"start": "claimed", "end": "released", "stale": "went stale on"}[event]
    text = f"{developer}'s coordinator {verb} scope '{scope}'"
    if event in ("end", "stale"):
        text += f" — {tasks_completed} task(s) completed"
    return {
        "event": event,
        "developer": developer,
        "scope": scope,
        "tasks_completed": tasks_completed,
        "session_id": session.get("session_id", ""),
        "timestamp": n.isoformat(),
        "text": text,
    }


def should_notify(event: str, prefs: Optional[Dict[str, object]]) -> bool:
    """Per-project opt-in/out per event type. Default: notify on `end`+`stale`, not `start`.

    `prefs` shape (all optional): {events: {start: bool, end: bool, stale: bool},
    channels: [...]}. Absent prefs -> the safe defaults above.
    """
    defaults = {"start": False, "end": True, "stale": True}
    if not prefs:
        return defaults.get(event, False)
    ev = prefs.get("events") if isinstance(prefs.get("events"), dict) else None
    if ev is not None and event in ev:
        return bool(ev[event])
    return defaults.get(event, False)


def in_quiet_hours(now: datetime, prefs: Optional[Dict[str, object]]) -> bool:
    """Respect quiet hours if configured. `prefs['quiet_hours'] = [start_h, end_h]` in UTC.

    Supports wrap-around windows (e.g. [22, 7] = 22:00–07:00). Absent -> never quiet.
    """
    if not prefs:
        return False
    qh = prefs.get("quiet_hours")
    if not (isinstance(qh, (list, tuple)) and len(qh) == 2):
        return False
    start_h, end_h = int(qh[0]), int(qh[1])
    h = now.astimezone(timezone.utc).hour
    if start_h == end_h:
        return False
    if start_h < end_h:
        return start_h <= h < end_h
    return h >= start_h or h < end_h  # wrap-around


def notify_coordinator_event(event: str, session: Dict[str, object],
                             prefs: Optional[Dict[str, object]],
                             transport: Transport,
                             now: Optional[datetime] = None) -> Dict[str, object]:
    """Decide + dispatch a coordinator-event notification.

    Returns {sent: bool, reason: str, channels: [...], payload: {...}}. Skips quietly
    when the event is opted out or inside quiet hours (reason explains which).
    """
    n = now or datetime.now(timezone.utc)
    payload = build_coordinator_event(event, session, now=n)
    if not should_notify(event, prefs):
        return {"sent": False, "reason": "opted_out", "channels": [], "payload": payload}
    if in_quiet_hours(n, prefs):
        return {"sent": False, "reason": "quiet_hours", "channels": [], "payload": payload}
    channels: List[str] = list((prefs or {}).get("channels") or ["slack", "email"])
    delivered = [ch for ch in channels if transport(ch, payload)]
    return {"sent": bool(delivered), "reason": "delivered" if delivered else "transport_failed",
            "channels": delivered, "payload": payload}
