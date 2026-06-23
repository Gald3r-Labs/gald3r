"""Privacy-respecting anonymous product telemetry (install/activation/retention) — T536.

This is the adoption-signal complement to the T538 crash reporter (:mod:`gald3r.crash`).
Where the crash sink reports *defects* the vendor must debug, telemetry reports *anonymous
aggregate adoption*: how many machines installed gald3r, how many activated it (first run),
and whether they keep using it (a daily-active retention ping). It deliberately mirrors the
T538 reporter's proven shape — a sanitizer/anonymizer, a pure-stdlib ``urllib`` sink, an
injectable ``opener`` test seam, and "a send failure NEVER raises into callers".

Owner decision baked in (T536):
    * DEFAULT-ON with an easy one-line opt-out. Unlike the crash reporter (default OFF),
      telemetry sends by default — BUT only when a sink base URL is configured AND the user
      has not opted out. The opt-out is a single flag (``GALD3R_TELEMETRY=off`` env, or
      ``telemetry_enabled: false`` in the per-user ``user_config.json``, or ``opt_out=True``
      passed in). See :func:`resolve_telemetry_config`.
    * STRICTLY ANONYMOUS AGGREGATE. The payload carries NO per-user identifier, NO PII, NO
      file paths / emails / secrets. The only stable id on the wire is a one-way salted hash
      of the machine id (:func:`anonymize_machine_id`) — it cannot be reversed to a machine
      id or a user, and is used solely to de-dupe "unique machines" at the ingest. Every
      free-text field is run through :func:`gald3r.crash.sanitize_text` as defence in depth.

Anonymity guarantees (what is NEVER sent):
    * the raw machine id / user id / email / display name from ``user_config.json``,
    * any file path, home directory, IP, or absolute path,
    * any token / API key / secret,
    * any user content (task text, prompts, file names, ...).

What IS sent (anonymous aggregate only):
    * ``event``           one of install / activation / retention,
    * ``machine_hash``    salted one-way hash of the machine id (de-dup only; not reversible),
    * ``os`` / ``os_version`` / ``arch``   coarse platform (``platform.system()`` etc.),
    * ``app_version``     the engine version,
    * ``platform_template``  the installed platform-template focus (e.g. "claude"), when known,
    * ``occurred_at``     ISO-8601 UTC timestamp.

Fail-soft: like the crash reporter, recording is best-effort and a send error is swallowed —
telemetry must never break, slow, or surface an error to a real run.

Mode-A / stdlib-only: ``urllib`` is lazy-imported only when actually sending, so the engine
adds NO new dependency and there is no import cost on the no-send path.

Backend route convention (mirrors :data:`gald3r.crash.CRASH_SINK_PATH`):
    The world_tree backend self-prefixes ``/diagnostics/*`` under ``API_V1_PREFIX`` (``/api/v1``),
    so this targets ``/api/v1/diagnostics/telemetry`` — the same convention the T538 crash
    route established. NOTE (owner sign-off pending): that backend route does NOT exist yet;
    until it is built a configured send simply gets a 404 and is swallowed (fail-soft). The
    crash route is JWT-gated per-user; anonymous telemetry intentionally does NOT require a
    per-user token, so the sink is sent unauthenticated by default (token optional).
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

import hashlib
import json
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.crash import _sanitize_context, sanitize_text, session_id

# The anonymous events this module reports (T536 AC: install / activation / retention).
EVENT_INSTALL = "install"
EVENT_ACTIVATION = "activation"
EVENT_RETENTION = "retention"
TELEMETRY_EVENTS = (EVENT_INSTALL, EVENT_ACTIVATION, EVENT_RETENTION)

# Append-only JSONL of recorded telemetry events, alongside the crash logs.
TELEMETRY_LOG_NAME = "telemetry_events.jsonl"

# Path on the world_tree backend — same self-prefix + API_V1_PREFIX convention as the
# T538 crash sink (``/api/v1/diagnostics/crash``). See module docstring: route TBD on the
# backend; a configured send 404s and is swallowed until the owner signs off + it is built.
TELEMETRY_SINK_PATH = "/api/v1/diagnostics/telemetry"
DEFAULT_TELEMETRY_TIMEOUT = 5.0

# env knobs — DEFAULT ON with an easy one-line opt-out (the inverse of the crash reporter).
TELEMETRY_ENABLE_ENV = "GALD3R_TELEMETRY"          # "off"/"0"/"false"/"no" => opt out
TELEMETRY_URL_ENV = "GALD3R_TELEMETRY_URL"         # world_tree base URL (no URL => no send)
TELEMETRY_TOKEN_ENV = "GALD3R_TELEMETRY_TOKEN"     # optional bearer (anonymous => usually unset)

# A fixed, public salt for the machine-id hash. This is NOT a secret: a one-way salted
# hash de-dups "unique machines" at ingest without ever sending the reversible machine id.
# The salt only domain-separates the hash so it cannot be cross-referenced with another
# system that happened to hash the same machine id.
_MACHINE_HASH_SALT = "gald3r-telemetry-v1"

_OPT_OUT_VALUES = ("0", "false", "no", "off", "disable", "disabled")


def _now_iso() -> str:
    """ISO-8601 UTC, second precision, trailing Z — matches the crash log style."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def anonymize_machine_id(machine_id: str) -> str:
    """One-way salted hash of a machine id for anonymous de-dup (NOT reversible).

    Returns a short hex digest used solely so the vendor can count *unique machines* and
    *daily-active machines* at the ingest without ever receiving the machine id itself. An
    empty / missing id yields ``""`` (no fabricated identity).
    """
    mid = (machine_id or "").strip()
    if not mid:
        return ""
    digest = hashlib.sha256((_MACHINE_HASH_SALT + ":" + mid).encode("utf-8")).hexdigest()
    return digest[:32]


def _is_opt_out(value: Optional[str]) -> bool:
    """True when an env/config string represents an explicit opt-out."""
    return (value or "").strip().lower() in _OPT_OUT_VALUES


@dataclass
class TelemetryConfig:
    """Resolved telemetry config (T536). DEFAULT ON: ``enabled`` is True UNLESS the user
    opted out — but a send only happens when a ``base_url`` is also present (no URL => the
    event is still recorded locally, nothing is sent)."""

    opt_out: bool
    base_url: str
    token: str = ""
    source: str = "agent"

    @property
    def enabled(self) -> bool:
        """Telemetry is on by default; only an explicit opt-out turns it off."""
        return not self.opt_out

    @property
    def can_send(self) -> bool:
        """A network send is possible only when enabled AND a sink URL is configured."""
        return bool(self.enabled and self.base_url)


def resolve_telemetry_config(
    env: Optional[Dict[str, str]] = None,
    *,
    source: str = "agent",
    opt_out: Optional[bool] = None,
) -> TelemetryConfig:
    """Build a :class:`TelemetryConfig` from the environment (DEFAULT ON).

    Opt-out precedence (any one disables sending):
      1. explicit ``opt_out=True`` argument (e.g. resolved from ``user_config.json``),
      2. ``GALD3R_TELEMETRY`` env set to a falsey value (``off``/``0``/``false``/``no``).

    ``base_url`` comes from ``GALD3R_TELEMETRY_URL`` (no URL => nothing is sent, the event
    is only recorded locally). ``token`` is optional — anonymous telemetry does not require
    a per-user bearer, but one is honored if configured.
    """
    env = env if env is not None else os.environ
    env_opt_out = _is_opt_out(env.get(TELEMETRY_ENABLE_ENV))
    return TelemetryConfig(
        opt_out=bool(opt_out) or env_opt_out,
        base_url=(env.get(TELEMETRY_URL_ENV) or "").strip().rstrip("/"),
        token=(env.get(TELEMETRY_TOKEN_ENV) or "").strip(),
        source=source,
    )


def build_event_payload(
    *,
    event: str,
    source: str,
    machine_id: Optional[str] = None,
    app_version: Optional[str] = None,
    platform_template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the STRICTLY ANONYMOUS telemetry payload (T536).

    No per-user identifier, no PII, no paths. The only stable id is the one-way salted
    machine hash (de-dup only). Every free-text field — including any ``context`` values
    and the ``platform_template`` — is run through :func:`gald3r.crash.sanitize_text`
    (paths/emails/secrets) as defence in depth, so even a mis-supplied value cannot leak.
    """
    return {
        "event": event if event in TELEMETRY_EVENTS else event,
        "source": source,
        "machine_hash": anonymize_machine_id(machine_id or ""),
        "os": platform.system(),
        "os_version": platform.release(),
        "arch": platform.machine(),
        "app_version": app_version or _app_version(),
        "platform_template": (
            sanitize_text(platform_template) if platform_template else None
        ),
        "occurred_at": _now_iso(),
        "context": _sanitize_context(context),
    }


def _app_version() -> str:
    try:
        from gald3r import __version__

        return __version__
    except Exception:  # pragma: no cover - version import is best-effort
        return "unknown"


def telemetry_log_path(root: Optional[Path] = None) -> Path:
    base = Path(root) if root is not None else Path.cwd()
    return base / ".gald3r" / "logs" / TELEMETRY_LOG_NAME


def send_to_sink(
    payload: Dict[str, Any],
    config: TelemetryConfig,
    *,
    timeout: float = DEFAULT_TELEMETRY_TIMEOUT,
    opener: Optional[Any] = None,
) -> bool:
    """POST an already-built anonymous payload to the world_tree telemetry sink.

    Returns True on a 2xx, False otherwise. NEVER raises — a network/HTTP failure (including
    a 404 while the backend route is still TBD) must not break the run. ``opener`` is the
    test seam: a callable ``(url, data, headers, timeout) -> int`` (the HTTP status) that
    bypasses the network, mirroring :func:`gald3r.crash.report_to_sink`'s ``opener``.
    """
    if not config.can_send:
        return False
    url = config.base_url + TELEMETRY_SINK_PATH
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # Anonymous telemetry does not require a per-user token; honor one only if configured.
    if config.token:
        headers["Authorization"] = f"Bearer {config.token}"
    try:
        if opener is not None:
            status_code = opener(url, data, headers, timeout)
        else:
            # Lazy stdlib import — only paid when actually sending (no import cost off-path).
            import urllib.error
            import urllib.request

            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - http(s) only
                    status_code = resp.status
            except urllib.error.HTTPError as e:
                status_code = e.code
    except Exception:  # noqa: BLE001 - telemetry must never break the run
        return False
    return 200 <= int(status_code) < 300


@dataclass
class TelemetryRecord:
    """One telemetry event — JSONL schema for ``telemetry_events.jsonl`` (T536)."""

    event: str
    source: str
    machine_hash: str
    os: str
    os_version: str
    arch: str
    app_version: str
    occurred_at: str
    platform_template: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "source": self.source,
            "machine_hash": self.machine_hash,
            "os": self.os,
            "os_version": self.os_version,
            "arch": self.arch,
            "app_version": self.app_version,
            "platform_template": self.platform_template,
            "occurred_at": self.occurred_at,
            "context": self.context,
        }


def record_event(
    event: str,
    *,
    machine_id: Optional[str] = None,
    app_version: Optional[str] = None,
    platform_template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    config: Optional[TelemetryConfig] = None,
    source: str = "agent",
    opener: Optional[Any] = None,
) -> bool:
    """Record an anonymous telemetry event locally + (DEFAULT ON) send it to the vendor sink.

    Always appends a sanitized local ``telemetry_events.jsonl`` record (so a project keeps a
    transparent, inspectable copy of exactly what telemetry would send). Then — UNLESS the
    user opted out — POSTs the anonymized aggregate payload when a sink URL is configured.
    Returns True iff the remote send was accepted (2xx); False when opted out, unconfigured,
    or the send failed. NEVER raises — telemetry must never break a run.

    The payload is STRICTLY ANONYMOUS: see :func:`build_event_payload`. ``machine_id`` is
    hashed one-way before it ever leaves the machine; the raw id is never sent.
    """
    cfg = config if config is not None else resolve_telemetry_config(source=source)
    payload = build_event_payload(
        event=event,
        source=cfg.source,
        machine_id=machine_id,
        app_version=app_version,
        platform_template=platform_template,
        context=context,
    )
    rec = TelemetryRecord(
        event=payload["event"],
        source=payload["source"],
        machine_hash=payload["machine_hash"],
        os=payload["os"],
        os_version=payload["os_version"],
        arch=payload["arch"],
        app_version=payload["app_version"],
        occurred_at=payload["occurred_at"],
        platform_template=payload["platform_template"],
        context=payload["context"],
    )
    try:
        p = telemetry_log_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
    except OSError:
        pass  # local logging failure must not block the send nor the run

    if not cfg.can_send:
        return False
    return send_to_sink(payload, cfg, opener=opener)


def record_install(
    *,
    machine_id: Optional[str] = None,
    app_version: Optional[str] = None,
    platform_template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    config: Optional[TelemetryConfig] = None,
    source: str = "agent",
    opener: Optional[Any] = None,
) -> bool:
    """Record the anonymous INSTALL event (first install on this machine)."""
    return record_event(
        EVENT_INSTALL,
        machine_id=machine_id,
        app_version=app_version,
        platform_template=platform_template,
        context=context,
        root=root,
        config=config,
        source=source,
        opener=opener,
    )


def record_activation(
    *,
    machine_id: Optional[str] = None,
    app_version: Optional[str] = None,
    platform_template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    config: Optional[TelemetryConfig] = None,
    source: str = "agent",
    opener: Optional[Any] = None,
) -> bool:
    """Record the anonymous ACTIVATION event (first meaningful run)."""
    return record_event(
        EVENT_ACTIVATION,
        machine_id=machine_id,
        app_version=app_version,
        platform_template=platform_template,
        context=context,
        root=root,
        config=config,
        source=source,
        opener=opener,
    )


def record_retention(
    *,
    machine_id: Optional[str] = None,
    app_version: Optional[str] = None,
    platform_template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    config: Optional[TelemetryConfig] = None,
    source: str = "agent",
    opener: Optional[Any] = None,
) -> bool:
    """Record the anonymous RETENTION event (e.g. a daily-active ping)."""
    return record_event(
        EVENT_RETENTION,
        machine_id=machine_id,
        app_version=app_version,
        platform_template=platform_template,
        context=context,
        root=root,
        config=config,
        source=source,
        opener=opener,
    )


def read_records(root: Optional[Path] = None) -> List[TelemetryRecord]:
    """Stream ``telemetry_events.jsonl`` into TelemetryRecord objects (skips bad lines)."""
    p = telemetry_log_path(root)
    out: List[TelemetryRecord] = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        out.append(TelemetryRecord(
            event=str(d.get("event", "")),
            source=str(d.get("source", "")),
            machine_hash=str(d.get("machine_hash", "")),
            os=str(d.get("os", "")),
            os_version=str(d.get("os_version", "")),
            arch=str(d.get("arch", "")),
            app_version=str(d.get("app_version", "")),
            occurred_at=str(d.get("occurred_at", "")),
            platform_template=d.get("platform_template"),
            context=d.get("context") or {},
        ))
    return out
