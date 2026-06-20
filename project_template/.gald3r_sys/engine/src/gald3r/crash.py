"""CRASH activation tracking — datetime invocation statistics (T433).

CRASH = the five gald3r extension-point types: **C**ommands, **R**ules, **A**gents,
**S**kills, **H**ooks. This module records *which* of those are actually invoked,
*when* (ISO-8601), and *what triggered* them — to a single append-only JSONL log —
and computes usage statistics from it: most-active, least-active, never-activated,
and "declares intent but never fired" (rules with ``fires_on:`` / skills with
``activate_for:`` that have zero activations).

It is the historical-stats complement to the real-time call-stack tracer in
:mod:`gald3r.debug` (T432). When both are active they write in the SAME event: the
``CrashTracker`` hooks ``DebugTracer._emit_activate`` so one activation produces both
a live debug trace AND a persisted JSONL record (AC #11).

Feasibility (honest scope — see SKILL/README + T433 handoff):
    Claude Code / Cursor / other IDE harnesses do NOT emit a discrete lifecycle
    event for *every* "rule activation" or "skill activation". Only certain events
    fire (session start, pre-tool-use, agent/subagent complete, stop). What this
    module CAN faithfully record is:
      * every Command dispatched through the engine CLI/MCP (instrumented at the
        dispatch layer via the debug tracer — exact),
      * any Skill/Agent/Hook/Rule activation that a hook OR an agent explicitly
        reports by calling ``record_activation(...)`` (the manual/heuristic path).
    Rule "activation" in particular has no harness event; rules are always-loaded
    context, so a faithful "rule fired" signal must be reported explicitly by the
    component that consumed the rule. The never-activated / should-be-called
    detector turns that gap into a *positive* signal: components in the registry
    with zero JSONL records are surfaced rather than silently assumed-active.

Zero overhead when disabled: ``record_activation`` short-circuits on a single env
read when ``GALD3R_CRASH_STATS`` is unset / ``off`` and no explicit enable was done.
"""
from __future__ import annotations

import json
import os
import platform
import re
import traceback
import uuid
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# the five CRASH component types
COMPONENT_TYPES = ("command", "rule", "agent", "skill", "hook")

# env var that controls output mode (see resolve_mode); "off"/unset == disabled
ENV_VAR = "GALD3R_CRASH_STATS"
MODE_OFF = "off"
MODE_RESPONSE = "show_in_response"
MODE_LOG = "show_in_log"
MODE_TERMINAL = "show_in_terminal"
OUTPUT_MODES = (MODE_OFF, MODE_RESPONSE, MODE_LOG, MODE_TERMINAL)

# log file (append-only JSONL) under .gald3r/logs/
LOG_NAME = "crash_activations.jsonl"

# registry roots to scan for installed components, relative to the project root.
# Both IDE-installed folders (.cursor/.claude/.agent...) and the canonical
# template source are tolerated; whichever exist are scanned.
_REGISTRY_GLOBS: Tuple[Tuple[str, str], ...] = (
    # (component_type, glob relative to project root)
    ("skill", ".cursor/skills/*/SKILL.md"),
    ("skill", ".claude/skills/*/SKILL.md"),
    ("rule", ".cursor/rules/*.md"),
    ("rule", ".cursor/rules/*.mdc"),
    ("rule", ".claude/rules/*.md"),
    ("command", ".cursor/commands/*.md"),
    ("command", ".claude/commands/*.md"),
    ("agent", ".cursor/agents/*.md"),
    ("agent", ".claude/agents/*.md"),
    ("hook", ".cursor/hooks/*.ps1"),
    ("hook", ".claude/hooks/*.ps1"),
)

# intent-metadata keys that mark a component as "should be called" (T433)
_FIRES_ON = re.compile(r"^\s*fires_on\s*:", re.M)
_ACTIVATE_FOR = re.compile(r"^\s*activate_for\s*:", re.M)


def _now_iso() -> str:
    """ISO-8601 UTC, second precision, trailing Z — matches the hook log style."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_mode(env: Optional[Dict[str, str]] = None) -> str:
    """Resolve the output mode from ``GALD3R_CRASH_STATS``.

    Unset / empty / unknown / ``off`` => MODE_OFF (tracking disabled, zero overhead).
    """
    env = env if env is not None else os.environ
    val = (env.get(ENV_VAR) or "").strip().lower()
    if val in (MODE_RESPONSE, MODE_LOG, MODE_TERMINAL):
        return val
    return MODE_OFF


@dataclass
class ActivationRecord:
    """One CRASH activation event — the exact JSONL line schema (T433 AC #2)."""
    component_type: str
    component_name: str
    activated_at: str
    session_id: str
    trigger_source: str
    elapsed_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_type": self.component_type,
            "component_name": self.component_name,
            "activated_at": self.activated_at,
            "session_id": self.session_id,
            "trigger_source": self.trigger_source,
            "elapsed_ms": self.elapsed_ms,
        }


# ---- session id -------------------------------------------------------------

_SESSION_ID: Optional[str] = None


def session_id() -> str:
    """The gald3r session id if exported by the harness, else a per-process UUID.

    Honors ``GALD3R_SESSION_ID`` / ``CURSOR_CONVERSATION_ID`` when present so a
    JSONL record can be correlated with debug logs / chat transcripts.
    """
    global _SESSION_ID
    if _SESSION_ID is not None:
        return _SESSION_ID
    sid = (os.environ.get("GALD3R_SESSION_ID")
           or os.environ.get("CURSOR_CONVERSATION_ID")
           or "")
    _SESSION_ID = sid.strip() or f"proc-{uuid.uuid4().hex[:12]}"
    return _SESSION_ID


# ---- log path ---------------------------------------------------------------

def log_path(root: Optional[Path] = None) -> Path:
    base = Path(root) if root is not None else Path.cwd()
    return base / ".gald3r" / "logs" / LOG_NAME


# ---- recording (the hot path) ----------------------------------------------

def record_activation(
    component_type: str,
    component_name: str,
    *,
    trigger_source: str = "",
    elapsed_ms: Optional[float] = None,
    root: Optional[Path] = None,
    force: bool = False,
) -> Optional[ActivationRecord]:
    """Append one activation record to ``crash_activations.jsonl``.

    Returns the written record, or ``None`` when tracking is disabled (the hot path
    short-circuits on a single env read so there is zero overhead when off — AC #10).
    Pass ``force=True`` to record regardless of mode (used by tests / explicit
    instrumentation that wants a record even with the env var unset).
    """
    if not force and resolve_mode() == MODE_OFF:
        return None

    ctype = component_type.strip().lower()
    rec = ActivationRecord(
        component_type=ctype if ctype in COMPONENT_TYPES else ctype,
        component_name=component_name,
        activated_at=_now_iso(),
        session_id=session_id(),
        trigger_source=trigger_source,
        elapsed_ms=elapsed_ms,
    )
    try:
        p = log_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
    except OSError:
        # Never let activation tracking break a real run.
        return None
    return rec


# ---- reset (archive + start fresh) ------------------------------------------

def reset_log(root: Optional[Path] = None) -> Optional[Path]:
    """Archive the current JSONL to ``crash_activations_YYYYMMDD_HHMMSS.jsonl`` and
    start fresh (AC: ``--crash-stats-reset``). Returns the archive path, or ``None``
    when there was nothing to archive."""
    p = log_path(root)
    if not p.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = p.with_name(f"crash_activations_{ts}.jsonl")
    p.rename(archive)
    return archive


# ---- reading + stats --------------------------------------------------------

def read_records(root: Optional[Path] = None) -> List[ActivationRecord]:
    """Stream the JSONL into ActivationRecord objects. Skips malformed lines."""
    p = log_path(root)
    out: List[ActivationRecord] = []
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
        out.append(ActivationRecord(
            component_type=str(d.get("component_type", "")),
            component_name=str(d.get("component_name", "")),
            activated_at=str(d.get("activated_at", "")),
            session_id=str(d.get("session_id", "")),
            trigger_source=str(d.get("trigger_source", "")),
            elapsed_ms=d.get("elapsed_ms"),
        ))
    return out


@dataclass
class ComponentStat:
    component_name: str
    component_type: str
    count: int
    last_activated: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_name": self.component_name,
            "component_type": self.component_type,
            "count": self.count,
            "last_activated": self.last_activated,
        }


def scan_registry(root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Scan installed component folders → ``{component_name: {type, intent}}``.

    ``intent`` is True when the component declares ``fires_on:`` (rules) or
    ``activate_for:`` (skills) — the "should be called" intent metadata (T433).
    Names are the file/dir stem (e.g. ``g-skl-tasks``, ``g-rl-00-always``), so they
    line up with how an agent / hook would name the component in a JSONL record.
    """
    base = Path(root) if root is not None else Path.cwd()
    registry: Dict[str, Dict[str, Any]] = {}
    for ctype, pattern in _REGISTRY_GLOBS:
        for path in base.glob(pattern):
            if path.name == "SKILL.md":
                name = path.parent.name           # skill folder name
            else:
                name = path.stem                  # rule/command/agent/hook stem
            intent = False
            try:
                text = path.read_text(encoding="utf-8-sig", errors="replace")
                if ctype == "rule" and _FIRES_ON.search(text):
                    intent = True
                elif ctype == "skill" and _ACTIVATE_FOR.search(text):
                    intent = True
            except OSError:
                text = ""
            # First sighting wins for type; later IDE copies don't downgrade intent.
            entry = registry.setdefault(name, {"type": ctype, "intent": False})
            entry["intent"] = entry["intent"] or intent
    return registry


def compute_stats(root: Optional[Path] = None) -> Dict[str, Any]:
    """Aggregate the JSONL + registry into a stats payload (O(n) over records).

    Keys:
      ``total_activations``, ``by_type`` (Counter), ``per_component`` (list of
      ComponentStat dicts, count-desc), ``most_active`` (top 10), ``least_active``
      (count>0, asc), ``never_activated`` (registry names with 0 records),
      ``should_be_called`` (intent-declaring registry names with 0 records).
    """
    records = read_records(root)
    registry = scan_registry(root)

    counts: Counter = Counter()
    last_seen: Dict[str, str] = {}
    type_of: Dict[str, str] = {}
    by_type: Counter = Counter()
    for r in records:
        counts[r.component_name] += 1
        by_type[r.component_type] += 1
        type_of.setdefault(r.component_name, r.component_type)
        # activated_at is ISO-8601 Z → lexical max == chronological max
        if r.activated_at >= last_seen.get(r.component_name, ""):
            last_seen[r.component_name] = r.activated_at

    per_component: List[ComponentStat] = []
    for name, cnt in counts.items():
        per_component.append(ComponentStat(
            component_name=name,
            component_type=registry.get(name, {}).get("type") or type_of.get(name, "unknown"),
            count=cnt,
            last_activated=last_seen.get(name, ""),
        ))
    per_component.sort(key=lambda s: (-s.count, s.component_name))

    invoked = set(counts.keys())
    never_activated = sorted(n for n in registry if n not in invoked)
    should_be_called = sorted(
        n for n, meta in registry.items()
        if meta.get("intent") and n not in invoked
    )

    most_active = [s.to_dict() for s in per_component[:10]]
    least_active = [s.to_dict() for s in sorted(
        (s for s in per_component if s.count > 0),
        key=lambda s: (s.count, s.component_name),
    )]

    return {
        "total_activations": len(records),
        "by_type": dict(by_type),
        "per_component": [s.to_dict() for s in per_component],
        "most_active": most_active,
        "least_active": least_active,
        "never_activated": never_activated,
        "should_be_called": should_be_called,
        "registry_size": len(registry),
    }


# ---- rendering --------------------------------------------------------------

def render_report(stats: Dict[str, Any], *, when: Optional[str] = None) -> str:
    """The full markdown stats report (written to crash_stats_YYYYMMDD.md)."""
    when = when or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    by_type = stats.get("by_type", {})
    type_line = " | ".join(
        f"{t.capitalize()}s: {by_type.get(t, 0)}" for t in COMPONENT_TYPES
    )
    lines: List[str] = [
        "# CRASH Activation Stats",
        "",
        f"_Generated {when} — {stats.get('total_activations', 0)} activation(s) across "
        f"{stats.get('registry_size', 0)} known component(s)._",
        "",
        f"**By type:** {type_line}",
        "",
        "## Most Active (top 10)",
        "",
    ]
    most = stats.get("most_active", [])
    if most:
        lines.append("| Component | Type | Count | Last Activated |")
        lines.append("|---|---|---|---|")
        for s in most:
            lines.append(
                f"| {s['component_name']} | {s['component_type']} | {s['count']} "
                f"| {s['last_activated'] or '—'} |"
            )
    else:
        lines.append("_(no activations recorded yet)_")
    lines += ["", "## Least Active (>0 calls)", ""]
    least = stats.get("least_active", [])
    if least:
        lines.append("| Component | Type | Count | Last Activated |")
        lines.append("|---|---|---|---|")
        for s in least:
            lines.append(
                f"| {s['component_name']} | {s['component_type']} | {s['count']} "
                f"| {s['last_activated'] or '—'} |"
            )
    else:
        lines.append("_(no activations recorded yet)_")

    lines += ["", "## Never Activated", ""]
    never = stats.get("never_activated", [])
    if never:
        for n in never:
            lines.append(f"- {n}")
    else:
        lines.append("_(every known component has been activated at least once)_")

    should = stats.get("should_be_called", [])
    if should:
        lines += ["", "## Should Be Called But Isn't", "",
                  "_These components declare intent (`fires_on:` / `activate_for:`) "
                  "but have 0 activations._", ""]
        for n in should:
            lines.append(f"- ⚠️ {n}")

    return "\n".join(lines) + "\n"


def render_signature(stats: Dict[str, Any]) -> str:
    """Compact 3-5 line summary for response-signature / log / terminal modes."""
    by_type = stats.get("by_type", {})
    type_line = " | ".join(
        f"{t.capitalize()}s: {by_type.get(t, 0)}" for t in COMPONENT_TYPES
    )
    top = stats.get("most_active", [])[:3]
    top_line = " ".join(f"{s['component_name']}({s['count']})" for s in top) or "—"
    never_n = len(stats.get("never_activated", []))
    should = stats.get("should_be_called", [])
    out = [
        "---",
        f"CRASH stats: {type_line}",
        f"Top: {top_line}",
        f"Never invoked: {never_n} component(s)",
    ]
    if should:
        out.append(f"Should-be-called but idle: {len(should)} ({', '.join(should[:3])})")
    return "\n".join(out)


def write_report(root: Optional[Path] = None, *, stats: Optional[Dict[str, Any]] = None) -> Path:
    """Compute (if needed) and write the dated markdown report. Returns its path."""
    stats = stats if stats is not None else compute_stats(root)
    base = Path(root) if root is not None else Path.cwd()
    logs_dir = base / ".gald3r" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out = logs_dir / f"crash_stats_{datetime.now().strftime('%Y%m%d')}.md"
    out.write_text(render_report(stats), encoding="utf-8", newline="\n")
    return out


# ---- T432 debug integration (same-event recording, AC #11) ------------------

class CrashTracker:
    """Bridges the live debug tracer (T432) to the historical JSONL recorder.

    When attached, every ``DebugTracer`` activation also persists a CRASH record —
    so a single command dispatch produces BOTH a real-time debug trace and a
    durable JSONL line in the same event (AC #11). Detaching restores the original
    emit so the debug path is untouched when CRASH stats are off.
    """

    def __init__(self, root: Optional[Path] = None):
        self.root = root
        self._tracer = None
        self._orig_emit = None

    def attach(self, tracer_obj) -> "CrashTracker":
        """Wrap ``tracer_obj._emit_activate`` so it also records to JSONL."""
        if self._orig_emit is not None:
            return self  # already attached
        self._tracer = tracer_obj
        self._orig_emit = tracer_obj._emit_activate

        def _emit_and_record(ctx):  # ctx is a debug.DebugContext
            self._orig_emit(ctx)
            # A CLI command dispatch is trigger_type "command"; map to CRASH "command".
            ctype = "command" if ctx.trigger_type == "command" else "skill"
            record_activation(
                ctype,
                ctx.skill_name,
                trigger_source=ctx.trigger_source,
                root=self.root,
                force=True,
            )

        tracer_obj._emit_activate = _emit_and_record  # type: ignore[assignment]
        return self

    def detach(self) -> None:
        if self._tracer is not None and self._orig_emit is not None:
            self._tracer._emit_activate = self._orig_emit  # type: ignore[assignment]
        self._tracer = None
        self._orig_emit = None


# ---- T562: local error-capture wrapper -------------------------------------
#
# Extends the local-only CRASH/debug machinery (T433/T511) with an error-capture
# wrapper for the Agent Python harness: it catches an unhandled exception, writes a
# structured LOCAL record (stack, app version, OS, anonymized context), and re-raises
# so the original failure still propagates. There is NO remote sink — that stays in
# the T538 epic. All file paths in the record are sanitized so no user path leaks.

#: Append-only JSONL of captured errors, alongside the activation log.
ERROR_LOG_NAME = "crash_errors.jsonl"

# Patterns scrubbed from any captured text (stack frames, messages, context):
#   * connection-string credentials  scheme://user:password@host  (T578)
#   * Windows drive paths  C:\Users\me\...   /  C:/Users/me/...
#   * POSIX home/abs paths /home/me/...  /Users/me/...  /root/...  + generic
#     absolute paths /etc/..., /srv/..., /usr/..., /app/... (T578)
#   * email addresses
#   * secrets / tokens / API keys (T538) — SECURITY-CRITICAL once the reporter can
#     send text off the machine. T562's local capture did not send anywhere, so
#     secret scrubbing only becomes load-bearing with the T538 remote sink. Scrub
#     well-known key shapes (sk-/ghp_/ghs_/AKIA/Bearer ...) AND any
#     ``name=value`` / ``"name": "value"`` pair whose name looks like a secret.
#
# SHARED CONTRACT (T538 + T576 + T578): this scrub list + ordering is mirrored,
# rule-for-rule, by the Throne frontend ``crashReportLogic.anonymize``
# (gald3r_throne/src/lib/crashReportLogic.ts) and the Throne Rust panic-hook
# ``crash_report::sanitize::sanitize_text`` (gald3r_throne/src-tauri). Any change
# here MUST be applied to all three so the Agent + client redact identically.

# Connection-string inline credentials (T578): scheme://user:password@host. An
# EXPLICIT rule (not a path-regex side effect) — runs FIRST so the password is
# redacted whole before any path/token rule can partially eat it. Requires the
# ``user:password`` userinfo (both halves) so a plain ``scheme://host`` URL is
# untouched; only the credentials are replaced, the scheme + ``@host`` survive.
_CONN_STRING_CRED_RE = re.compile(
    r"([A-Za-z][A-Za-z0-9+.\-]*://)([^/?#@\s:]+:[^/?#@\s]+)@"
)
_WIN_PATH_RE = re.compile(r"[A-Za-z]:[\\/][^\s'\"]+")
_POSIX_PATH_RE = re.compile(r"(?<![\w.])/(?:home|Users|root|tmp|var|opt|mnt|media)/[^\s'\":]+")
# Generic absolute POSIX path (T578): broadens coverage beyond the home allow-list
# above to /etc, /srv, /usr, /app, ... — anything that looks like an absolute path
# with >=2 segments. The ``(?<![\w.])`` lookbehind + the 2-segment minimum guard
# against over-redaction: ``a/b`` fractions (first / preceded by a word char) and
# ``scheme://host/path`` URLs (slash preceded by a word char) are NOT matched.
_POSIX_ABS_PATH_RE = re.compile(r"(?<![\w.])/[A-Za-z0-9._-]+/[^\s'\":]+")
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

# Well-known opaque token shapes (OpenAI/GitHub/Anthropic/AWS/JWT-ish/long hex).
_TOKEN_RE = re.compile(
    r"\b("
    r"sk-[A-Za-z0-9_-]{16,}"           # OpenAI-style
    r"|gh[pousr]_[A-Za-z0-9]{20,}"     # GitHub PAT / server / OAuth / refresh
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"   # Slack
    r"|AKIA[0-9A-Z]{16}"               # AWS access key id
    r"|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}"  # JWT
    r"|[A-Fa-f0-9]{40,}"               # long hex (sha/aws-secret-ish)
    r")\b"
)
# ``Authorization: Bearer <token>`` / ``token <token>``.
_BEARER_RE = re.compile(r"(?i)\b(bearer|token)\s+[A-Za-z0-9._\-]{8,}")
# key=value / "key": "value" where key names a credential.
_SECRET_KV_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|passwd|pwd|auth|credential|access[_-]?key)"
    r"(\s*[=:]\s*)"
    r"(\"[^\"]+\"|'[^']+'|[^\s,}'\"]+)"
)

_PATH_PLACEHOLDER = "<path>"
_EMAIL_PLACEHOLDER = "<redacted-email>"
_SECRET_PLACEHOLDER = "<redacted-secret>"


def sanitize_text(text: str) -> str:
    """Scrub filesystem paths, emails, and secrets/tokens from ``text``.

    Anonymization (T562 paths/emails + T538 secrets/tokens). SECURITY-CRITICAL:
    the T538 remote reporter calls this on every field BEFORE sending — a token
    that survives here is a token that leaves the machine.
    """
    if not text:
        return text
    # Connection-string creds FIRST (T578) — redact the password whole before any
    # path/token rule can partially consume it; keep the scheme + @host.
    text = _CONN_STRING_CRED_RE.sub(
        lambda m: m.group(1) + _SECRET_PLACEHOLDER + "@", text
    )
    text = _WIN_PATH_RE.sub(_PATH_PLACEHOLDER, text)
    text = _POSIX_PATH_RE.sub(_PATH_PLACEHOLDER, text)
    text = _POSIX_ABS_PATH_RE.sub(_PATH_PLACEHOLDER, text)  # broaden coverage (T578)
    text = _EMAIL_RE.sub(_EMAIL_PLACEHOLDER, text)
    # Secrets last (after paths) so a key embedded in a path is still caught.
    text = _SECRET_KV_RE.sub(lambda m: m.group(1) + m.group(2) + _SECRET_PLACEHOLDER, text)
    text = _BEARER_RE.sub(lambda m: m.group(1) + " " + _SECRET_PLACEHOLDER, text)
    text = _TOKEN_RE.sub(_SECRET_PLACEHOLDER, text)
    return text


def _sanitize_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a copy of ``context`` with all string values sanitized."""
    if not context:
        return {}
    out: Dict[str, Any] = {}
    for key, value in context.items():
        if isinstance(value, str):
            out[key] = sanitize_text(value)
        elif isinstance(value, (list, tuple)):
            out[key] = [sanitize_text(v) if isinstance(v, str) else v for v in value]
        else:
            out[key] = value
    return out


@dataclass
class ErrorRecord:
    """One captured error — the JSONL line schema for ``crash_errors.jsonl`` (T562)."""

    error_type: str
    message: str
    stack: str
    app_version: str
    os: str
    occurred_at: str
    session_id: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "stack": self.stack,
            "app_version": self.app_version,
            "os": self.os,
            "occurred_at": self.occurred_at,
            "session_id": self.session_id,
            "context": self.context,
        }


def error_log_path(root: Optional[Path] = None) -> Path:
    base = Path(root) if root is not None else Path.cwd()
    return base / ".gald3r" / "logs" / ERROR_LOG_NAME


def _app_version() -> str:
    try:
        from gald3r import __version__

        return __version__
    except Exception:  # pragma: no cover - version import is best-effort
        return "unknown"


def build_error_record(
    exc: BaseException,
    *,
    context: Optional[Dict[str, Any]] = None,
    app_version: Optional[str] = None,
) -> ErrorRecord:
    """Build a sanitized :class:`ErrorRecord` from an exception (no I/O)."""
    stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return ErrorRecord(
        error_type=type(exc).__name__,
        message=sanitize_text(str(exc)),
        stack=sanitize_text(stack),
        app_version=app_version or _app_version(),
        os=f"{platform.system()} {platform.release()}".strip(),
        occurred_at=_now_iso(),
        session_id=session_id(),
        context=_sanitize_context(context),
    )


def record_error(
    exc: BaseException,
    *,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    app_version: Optional[str] = None,
) -> Optional[ErrorRecord]:
    """Append a structured, sanitized error record to ``crash_errors.jsonl``.

    Returns the record written, or ``None`` if the log could not be written (error
    capture must never mask the original failure). Unlike activation tracking this
    is NOT gated by an env var — a crash is always worth a local record.
    """
    rec = build_error_record(exc, context=context, app_version=app_version)
    try:
        p = error_log_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
    except OSError:
        return None
    return rec


def read_error_records(root: Optional[Path] = None) -> List[ErrorRecord]:
    """Stream ``crash_errors.jsonl`` into ErrorRecord objects (skips bad lines)."""
    p = error_log_path(root)
    out: List[ErrorRecord] = []
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
        out.append(ErrorRecord(
            error_type=str(d.get("error_type", "")),
            message=str(d.get("message", "")),
            stack=str(d.get("stack", "")),
            app_version=str(d.get("app_version", "")),
            os=str(d.get("os", "")),
            occurred_at=str(d.get("occurred_at", "")),
            session_id=str(d.get("session_id", "")),
            context=d.get("context") or {},
        ))
    return out


@contextmanager
def capture_errors(
    *,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    app_version: Optional[str] = None,
) -> Iterator[None]:
    """Context manager that captures an unhandled exception then RE-RAISES it.

    Wrap an Agent harness entry point so any unhandled error is persisted to a
    structured local record before propagating::

        with capture_errors(context={"phase": "harness_main"}):
            run_harness()
    """
    try:
        yield
    except BaseException as exc:  # noqa: BLE001 - we re-raise after logging
        record_error(exc, context=context, root=root, app_version=app_version)
        raise


def error_captured(
    *,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    app_version: Optional[str] = None,
):
    """Decorator form of :func:`capture_errors` for harness entry-point functions."""

    def _decorator(func):
        def _wrapped(*args, **kwargs):
            with capture_errors(context=context, root=root, app_version=app_version):
                return func(*args, **kwargs)

        _wrapped.__name__ = getattr(func, "__name__", "wrapped")
        _wrapped.__doc__ = func.__doc__
        return _wrapped

    return _decorator


# ---- T538: opt-in remote vendor reporting ----------------------------------
#
# Extends the T562 LOCAL error capture into OPTIONAL remote vendor reporting: when
# explicitly opted in AND configured, a captured error (or an AC3 failure /
# "wasted-token" event) is ALSO POSTed — already anonymized — to the world_tree
# crash sink (T538 backend ``POST /api/v1/diagnostics/crash``) so the VENDOR can
# debug defects in THEIR OWN code that affect users.
#
# Design guarantees:
#   * DEFAULT OFF + DISCLOSED. Remote reporting requires BOTH an explicit opt-in
#     (``GALD3R_CRASH_REPORT`` truthy / ``opt_in=True``) AND a sink URL + token.
#     Absent either, nothing leaves the machine — the local JSONL is still written.
#   * SINGLE DEPENDENCY. Pure stdlib ``urllib`` (lazy-imported only when actually
#     sending) — the engine adds NO new dependency. An injectable ``opener`` is the
#     test seam (mirrors ``systems/upgrade.py::version_check``), so tests assert the
#     exact outbound payload with ZERO network I/O.
#   * ANONYMIZE BEFORE SEND. Every text field on the wire goes through
#     :func:`sanitize_text` / :func:`_sanitize_context` (paths/emails/secrets) — the
#     reporter NEVER sends a raw stack/message/context.
#   * NEVER MASKS THE FAILURE. Any send error is swallowed; remote reporting must
#     not break the run nor the original exception propagation.

#: Append-only JSONL of captured AC3 failure / wasted-token events.
EVENT_LOG_NAME = "crash_events.jsonl"

# env knobs (all OFF by default — disclosed opt-in)
REPORT_ENABLE_ENV = "GALD3R_CRASH_REPORT"        # truthy => remote reporting allowed
REPORT_URL_ENV = "GALD3R_CRASH_REPORT_URL"       # world_tree base URL
REPORT_TOKEN_ENV = "GALD3R_CRASH_REPORT_TOKEN"   # JWT bearer (the existing auth)

# Path on the world_tree backend (T538 route self-prefix + API_V1_PREFIX).
CRASH_SINK_PATH = "/api/v1/diagnostics/crash"
DEFAULT_REPORT_TIMEOUT = 5.0

# AC3 event kinds the reporter understands. ``crash``/``error`` come from the
# T562 capture path; the rest are failure / "wasted-token" signals.
EVENT_KINDS = ("crash", "error", "loop_failure", "tool_error", "wasted_token")

_TRUTHY = ("1", "true", "yes", "on")


def _env_truthy(name: str, env: Optional[Dict[str, str]] = None) -> bool:
    env = env if env is not None else os.environ
    return (env.get(name) or "").strip().lower() in _TRUTHY


@dataclass
class ReportConfig:
    """Resolved remote-reporting config (T538). ``enabled`` requires ALL of:
    explicit opt-in, a sink URL, and a token — else nothing is ever sent."""

    opt_in: bool
    base_url: str
    token: str
    source: str = "agent_harness"

    @property
    def enabled(self) -> bool:
        return bool(self.opt_in and self.base_url and self.token)


def resolve_report_config(
    env: Optional[Dict[str, str]] = None, *, source: str = "agent_harness"
) -> ReportConfig:
    """Build a :class:`ReportConfig` from the environment (all default OFF)."""
    env = env if env is not None else os.environ
    return ReportConfig(
        opt_in=_env_truthy(REPORT_ENABLE_ENV, env),
        base_url=(env.get(REPORT_URL_ENV) or "").strip().rstrip("/"),
        token=(env.get(REPORT_TOKEN_ENV) or "").strip(),
        source=source,
    )


def build_report_payload(
    *,
    kind: str,
    source: str,
    error_type: Optional[str] = None,
    message: Optional[str] = None,
    stack: Optional[str] = None,
    app_version: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the ANONYMIZED crash-sink JSON body (T538 schema ``CrashReportIn``).

    Every free-text field is scrubbed here (defence in depth even if the caller
    passed already-sanitized values). ``opt_in`` is hard-set True — the route
    rejects opt_in=false, and a payload only reaches here on the opted-in path.
    """
    return {
        "source": source,
        "kind": kind if kind in EVENT_KINDS else kind,
        "error_type": error_type,
        "message": sanitize_text(message) if message else None,
        "stack": sanitize_text(stack) if stack else None,
        "app_version": app_version or _app_version(),
        "os": f"{platform.system()} {platform.release()}".strip(),
        "session_id": session_id(),
        "opt_in": True,
        "context": _sanitize_context(context),
    }


def report_to_sink(
    payload: Dict[str, Any],
    config: ReportConfig,
    *,
    timeout: float = DEFAULT_REPORT_TIMEOUT,
    opener: Optional[Any] = None,
) -> bool:
    """POST an already-built payload to the world_tree crash sink (T538 AC2).

    Returns True on a 2xx, False otherwise. NEVER raises — a network/HTTP failure
    must not break the run. ``opener`` is the test seam: a callable
    ``(url, data, headers, timeout) -> int`` (the HTTP status) that bypasses the
    network, mirroring ``systems/upgrade.py::version_check``'s ``opener``.
    """
    if not config.enabled:
        return False
    url = config.base_url + CRASH_SINK_PATH
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {config.token}",
    }
    try:
        if opener is not None:
            status_code = opener(url, data, headers, timeout)
        else:
            # Lazy stdlib import — only paid when actually sending (hot-path safe).
            import urllib.error
            import urllib.request

            req = urllib.request.Request(
                url, data=data, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - http(s) only
                    status_code = resp.status
            except urllib.error.HTTPError as e:
                status_code = e.code
    except Exception:  # noqa: BLE001 - reporting must never break the run
        return False
    return 200 <= int(status_code) < 300


@dataclass
class EventRecord:
    """One AC3 failure / "wasted-token" event — JSONL schema for crash_events.jsonl."""

    kind: str
    source: str
    message: str
    occurred_at: str
    session_id: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "message": self.message,
            "occurred_at": self.occurred_at,
            "session_id": self.session_id,
            "context": self.context,
        }


def event_log_path(root: Optional[Path] = None) -> Path:
    base = Path(root) if root is not None else Path.cwd()
    return base / ".gald3r" / "logs" / EVENT_LOG_NAME


def report_error(
    exc: BaseException,
    *,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    app_version: Optional[str] = None,
    config: Optional[ReportConfig] = None,
    source: str = "agent_harness",
    opener: Optional[Any] = None,
) -> bool:
    """Capture an error LOCALLY (always) then OPTIONALLY report it remotely (T538).

    Always writes the local ``crash_errors.jsonl`` record (T562). When remote
    reporting is opted-in AND configured, also POSTs the anonymized payload to the
    vendor sink. Returns True iff a remote report was accepted (2xx); False when
    reporting is off/unconfigured or the send failed (the local record is written
    either way). NEVER raises.
    """
    rec = record_error(exc, context=context, root=root, app_version=app_version)
    cfg = config if config is not None else resolve_report_config(source=source)
    if not cfg.enabled:
        return False
    payload = build_report_payload(
        kind="error",
        source=cfg.source,
        error_type=rec.error_type if rec else type(exc).__name__,
        message=rec.message if rec else str(exc),
        stack=rec.stack if rec else None,
        app_version=app_version,
        context=context,
    )
    return report_to_sink(payload, cfg, opener=opener)


def record_event(
    kind: str,
    message: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    root: Optional[Path] = None,
    config: Optional[ReportConfig] = None,
    source: str = "agent_harness",
    app_version: Optional[str] = None,
    opener: Optional[Any] = None,
) -> bool:
    """Record an AC3 failure / "wasted-token" signal locally + optionally remote.

    These are NOT exceptions — they are loop failures, tool errors, and
    wasted-token events the VENDOR needs to debug defects in their code (AC3).
    Always appends a sanitized local ``crash_events.jsonl`` record; when remote
    reporting is opted-in + configured, also POSTs it. Returns True iff remotely
    accepted. NEVER raises.
    """
    safe_msg = sanitize_text(message)
    safe_ctx = _sanitize_context(context)
    evt = EventRecord(
        kind=kind if kind in EVENT_KINDS else kind,
        source=source,
        message=safe_msg,
        occurred_at=_now_iso(),
        session_id=session_id(),
        context=safe_ctx,
    )
    try:
        p = event_log_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(evt.to_dict(), ensure_ascii=False) + "\n")
    except OSError:
        pass  # local logging failure must not block remote reporting nor the run

    cfg = config if config is not None else resolve_report_config(source=source)
    if not cfg.enabled:
        return False
    payload = build_report_payload(
        kind=evt.kind,
        source=cfg.source,
        message=safe_msg,
        app_version=app_version,
        context=context,
    )
    return report_to_sink(payload, cfg, opener=opener)


def read_event_records(root: Optional[Path] = None) -> List[EventRecord]:
    """Stream ``crash_events.jsonl`` into EventRecord objects (skips bad lines)."""
    p = event_log_path(root)
    out: List[EventRecord] = []
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
        out.append(EventRecord(
            kind=str(d.get("kind", "")),
            source=str(d.get("source", "")),
            message=str(d.get("message", "")),
            occurred_at=str(d.get("occurred_at", "")),
            session_id=str(d.get("session_id", "")),
            context=d.get("context") or {},
        ))
    return out
