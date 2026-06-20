"""Debug-mode call-stack tracing for the gald3r engine (T432).

When debug mode is OFF (the default) this module is a true no-op: dispatch sites
call ``tracer().activate(...)`` and get back a single shared frozen context
manager whose enter/exit are guarded by one cheap boolean — no time calls, no
string formatting, no contextvar mutation, no allocation per activation.

When ON (``GALD3R_DEBUG=1`` env, or ``DebugTracer.enable(...)`` from the CLI
flags) it tracks a ``contextvars``-based call stack (thread/async-safe) and emits
one trace per skill/operation activation: who triggered it, the trigger type, the
call depth, and elapsed ms — to the terminal, a log file, both, and/or as
newline-delimited JSON.

Instrumentation lives at the *dispatch layer* (adapters/cli.py, adapters/mcp.py),
not inside each system — so adding a system needs no tracing code.
"""
from __future__ import annotations

import contextvars
import json
import os
import sys
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TextIO

# trigger types a caller may declare (free-form is tolerated, these are the canon)
TRIGGER_TYPES = ("command", "rule", "hook", "agent", "sub-skill", "mcp")
# output sinks
OUTPUT_MODES = ("terminal", "file", "both")
# call depth beyond which we warn about possible runaway recursion
DEEP_STACK_THRESHOLD = 10


@dataclass
class DebugContext:
    """One frame on the activation call stack."""
    skill_name: str
    trigger_type: str
    trigger_source: str
    depth: int
    start_ms: float
    parent_skill: Optional[str] = None


# the live call stack, per execution context (thread/async safe)
_STACK: contextvars.ContextVar[List[DebugContext]] = contextvars.ContextVar("gald3r_debug_stack")


def _now_ms() -> float:
    return time.perf_counter() * 1000.0


class _NoOp(AbstractContextManager):
    """Shared, allocation-free context manager used when debug mode is OFF.

    A single instance is reused for every activation; enter/exit do nothing.
    This is the hot path when tracing is disabled — keep it empty."""

    __slots__ = ()

    def __enter__(self) -> "_NoOp":
        return self

    def __exit__(self, *exc) -> bool:
        return False


_NOOP = _NoOp()  # module-level singleton; never reallocated


class _Activation(AbstractContextManager):
    """Live context manager for one activation when debug mode is ON.

    Pushes a DebugContext on enter (emitting the activation trace) and pops it on
    exit (emitting the completion trace with elapsed ms)."""

    __slots__ = ("_tracer", "_ctx", "_token")

    def __init__(self, tracer: "DebugTracer", skill_name: str,
                 trigger_type: str, trigger_source: str):
        self._tracer = tracer
        stack = _STACK.get([])
        parent = stack[-1].skill_name if stack else None
        self._ctx = DebugContext(
            skill_name=skill_name,
            trigger_type=trigger_type,
            trigger_source=trigger_source,
            depth=len(stack) + 1,
            start_ms=_now_ms(),
            parent_skill=parent,
        )
        self._token: Optional[contextvars.Token] = None

    def __enter__(self) -> DebugContext:
        stack = _STACK.get([])
        new_stack = stack + [self._ctx]
        self._token = _STACK.set(new_stack)
        self._tracer._emit_activate(self._ctx)
        if self._ctx.depth > DEEP_STACK_THRESHOLD:
            self._tracer._emit_deep_warning(self._ctx)
        return self._ctx

    def __exit__(self, *exc) -> bool:
        elapsed = _now_ms() - self._ctx.start_ms
        self._tracer._emit_complete(self._ctx, elapsed)
        if self._token is not None:
            _STACK.reset(self._token)
        return False


class DebugTracer:
    """Holds debug-mode state and emits traces. One instance is the module
    singleton; ``tracer()`` returns it. When ``enabled`` is False, ``activate``
    returns the shared no-op CM and nothing is computed."""

    def __init__(self) -> None:
        self.enabled: bool = False
        self.output_mode: str = "terminal"
        self.json_mode: bool = False
        # None => resolve sys.stdout live at write time (so test capture / stream
        # redirection done after enable() is still honored). An explicit stream
        # (passed to enable) pins the sink.
        self._stream: Optional[TextIO] = None
        self._log_path: Optional[Path] = None
        self._fh: Optional[TextIO] = None

    # ---- lifecycle ----
    def enable(self, output_mode: str = "terminal", json_mode: bool = False,
               root: Optional[Path] = None, stream: Optional[TextIO] = None) -> None:
        """Turn debug mode on. ``output_mode`` is terminal|file|both; ``json_mode``
        emits NDJSON instead of human lines; ``root`` is the project root used to
        place the file log under ``.gald3r/logs/``."""
        self.enabled = True
        self.output_mode = output_mode if output_mode in OUTPUT_MODES else "terminal"
        self.json_mode = json_mode
        if stream is not None:
            self._stream = stream
        if self.output_mode in ("file", "both"):
            self._open_log(root)

    def disable(self) -> None:
        """Turn debug mode off and close any open log file. Resets the call stack."""
        self.enabled = False
        if self._fh is not None:
            try:
                self._fh.close()
            finally:
                self._fh = None
        self._log_path = None
        self._stream = None
        _STACK.set([])

    def configure_from_env(self) -> None:
        """Enable from environment if ``GALD3R_DEBUG`` is truthy. Honors
        ``GALD3R_DEBUG_OUTPUT`` (terminal|file|both) and ``GALD3R_DEBUG_JSON``."""
        flag = os.environ.get("GALD3R_DEBUG", "").strip().lower()
        if flag in ("1", "true", "yes", "on"):
            out = os.environ.get("GALD3R_DEBUG_OUTPUT", "terminal").strip().lower()
            js = os.environ.get("GALD3R_DEBUG_JSON", "").strip().lower() in ("1", "true", "yes", "on")
            self.enable(output_mode=out, json_mode=js)

    def _open_log(self, root: Optional[Path]) -> None:
        try:
            base = Path(root) if root is not None else Path.cwd()
            logs_dir = base / ".gald3r" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._log_path = logs_dir / f"debug_{ts}.log"
            self._fh = open(self._log_path, "a", encoding="utf-8", newline="\n")
        except OSError:
            # If the log can't be opened, degrade to terminal rather than crash the run.
            self._fh = None
            self.output_mode = "terminal"

    @property
    def log_path(self) -> Optional[Path]:
        return self._log_path

    # ---- the dispatch hook ----
    def activate(self, skill_name: str, trigger_type: str = "command",
                 trigger_source: str = "") -> AbstractContextManager:
        """Return a context manager wrapping one skill/operation activation.

        Hot path: when disabled, return the shared no-op CM with zero work."""
        if not self.enabled:
            return _NOOP
        return _Activation(self, skill_name, trigger_type, trigger_source)

    # ---- emission (only reached when enabled) ----
    def _write(self, line: str) -> None:
        if self.output_mode in ("terminal", "both"):
            print(line, file=self._stream if self._stream is not None else sys.stdout)
        if self.output_mode in ("file", "both") and self._fh is not None:
            self._fh.write(line + "\n")
            self._fh.flush()

    def _chain(self) -> str:
        """The current call-stack chain, e.g.
        ``Command(@g-status) → Skill(g-skl-status) → Operation(SYNC_CHECK)``."""
        stack = _STACK.get([])
        parts = []
        for c in stack:
            label = {
                "command": "Command",
                "operation": "Operation",
                "mcp": "Mcp",
            }.get(c.trigger_type, "Skill")
            src = c.trigger_source or c.skill_name
            parts.append(f"{label}({src})")
        return " → ".join(parts)

    def _emit_activate(self, c: DebugContext) -> None:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if self.json_mode:
            self._write(json.dumps({
                "event": "skill_activate",
                "skill": c.skill_name,
                "trigger_type": c.trigger_type,
                "trigger_source": c.trigger_source,
                "depth": c.depth,
                "ts_ms": round(c.start_ms, 3),
            }, ensure_ascii=False))
        else:
            indent = "  " * (c.depth - 1)
            self._write(
                f"{indent}[DEBUG SKILL] {c.skill_name} triggered by "
                f"{c.trigger_type}:{c.trigger_source} at {ts} (depth={c.depth})"
            )
            self._write(f"{indent}              chain: {self._chain()}")

    def _emit_deep_warning(self, c: DebugContext) -> None:
        if self.json_mode:
            self._write(json.dumps({
                "event": "deep_stack_warning",
                "skill": c.skill_name,
                "depth": c.depth,
            }, ensure_ascii=False))
        else:
            indent = "  " * (c.depth - 1)
            self._write(
                f"{indent}[DEBUG WARN] Deep call stack (depth={c.depth}): possible recursion"
            )

    def _emit_complete(self, c: DebugContext, elapsed_ms: float) -> None:
        if self.json_mode:
            self._write(json.dumps({
                "event": "skill_complete",
                "skill": c.skill_name,
                "trigger_type": c.trigger_type,
                "trigger_source": c.trigger_source,
                "depth": c.depth,
                "ts_ms": round(_now_ms(), 3),
                "elapsed_ms": round(elapsed_ms, 3),
            }, ensure_ascii=False))
        else:
            indent = "  " * (c.depth - 1)
            self._write(
                f"{indent}[DEBUG DONE]  {c.skill_name} ({elapsed_ms:.2f} ms)"
            )


_TRACER = DebugTracer()
# Pick up GALD3R_DEBUG at import so the env-var path works even without CLI flags.
_TRACER.configure_from_env()


def tracer() -> DebugTracer:
    """The module-singleton tracer. Dispatch sites call ``tracer().activate(...)``."""
    return _TRACER
