#!/usr/bin/env python3
"""Shared canonical event core for gald3r hooks (T424).

This is the ONE place gald3r hook behavior is authored. Every platform's
trigger layer (Cursor `hooks.json`, Claude `settings.json`/`hooks.json`,
Kiro CLI agent-JSON `hooks` field, etc.) delegates here so behavior is
identical no matter which harness fired the event.

Architecture (T424 — event-consolidation + shared-core):

1. Canonical event set (`CANONICAL_EVENTS`) — the shared FLOOR of lifecycle
   moments COMMONLY supported across hook-capable platforms. This is a floor,
   NOT a ceiling: every capable platform routes at least these through the one
   core so behavior is identical everywhere. A platform's native events fold
   onto these via `PLATFORM_EVENT_MAP`; a RICHER platform (e.g. Cursor, ~18
   native events) keeps ALL of its events and may register additional concern
   chains — it is never dumbed down to only the canonical set. A WEAKER
   platform wires only the subset it supports and degrades gracefully. The
   floor guarantees cross-platform parity; it does not cap any platform.
2. Per-event concern chain (`CONCERN_CHAIN`) — the ordered list of concern
   hook scripts that run for a canonical event. The existing T1584 Python
   hooks (which import `_hook_common`) ARE those concern handlers; this core
   reuses them rather than reinventing their logic.
3. `dispatch(event)` — reads the harness payload from stdin ONCE, runs every
   concern hook in the chain with that same payload, merges their
   `additional_context`, honors the first blocking verdict, and emits a
   single unified response envelope. Thin per-platform shims and the bundled
   canonical entrypoints (`g-hk-<event>.py`) all call this.

Hooks must never crash the host session: `dispatch` is fully fail-soft and
returns exit 0 (continue) on any unexpected error unless a concern hook
explicitly blocked a tool call (exit 2, tool events only).
"""
# @subsystems: PLATFORM_INTEGRATION
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

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent

# ── Canonical reduced event set (T424 AC0) ──────────────────────────────────
# These are the shared FLOOR (not a ceiling): each is COMMONLY supported across
# hook-capable platforms (see PLATFORM_EVENT_MAP), so every platform routes at
# least these through the core for identical behavior. Strong platforms (Cursor,
# ~18 native events) keep their richer events and may add concern chains; weak
# platforms wire only the subset they support. This is the common denominator
# that guarantees parity, NOT a cap on any platform's capability.
CANONICAL_EVENTS: Dict[str, str] = {
    "session-start": "A new agent session/conversation begins. Context injection point.",
    "session-end": "An agent session terminates. Final cleanup / reflection point.",
    "user-prompt-submit": "The user submits a prompt, before the agent acts on it.",
    "tool-start": "Before a tool/action executes. The blocking guard point.",
    "tool-end": "After a tool/action completes. Post-action reaction point.",
    "stop": "The agent finishes responding to a turn (distinct from session-end).",
}

# ── Platform native event -> canonical event (T424 AC0 machine-readable map) ─
# Source: each platform's PLATFORM_SPEC `## Hook System` section (verified
# 2026-06-18). `pre-commit` is a git-level hook, not an agent-lifecycle event,
# so it is intentionally NOT a canonical event here (handled by the existing
# g-hk-pre-commit git hook). Platforms with no native hook surface (warp, roo,
# replit, subq, aider*, mistral*) are omitted.
PLATFORM_EVENT_MAP: Dict[str, Dict[str, str]] = {
    "cursor": {
        "sessionStart": "session-start",
        "sessionEnd": "session-end",
        "beforeSubmitPrompt": "user-prompt-submit",
        "preToolUse": "tool-start",
        "beforeShellExecution": "tool-start",
        "postToolUse": "tool-end",
        "stop": "stop",
    },
    "claude": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "gemini": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "BeforeTool": "tool-start",
        "AfterTool": "tool-end",
        "AfterAgent": "stop",
    },
    "codex": {
        "SessionStart": "session-start",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "qwen": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "goose": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "openhands": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "augment": {
        "SessionStart": "session-start",
        "SessionEnd": "session-end",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
        "Stop": "stop",
    },
    "copilot": {
        "sessionStart": "session-start",
        "sessionEnd": "session-end",
        "userPromptSubmitted": "user-prompt-submit",
        "preToolUse": "tool-start",
        "postToolUse": "tool-end",
    },
    "windsurf": {
        "pre_user_prompt": "user-prompt-submit",
        "pre_run_command": "tool-start",
        "pre_write_code": "tool-start",
        "post_run_command": "tool-end",
        "post_write_code": "tool-end",
        "post_cascade_response": "stop",
    },
    "kiro-cli": {
        "agentSpawn": "session-start",
        "userPromptSubmit": "user-prompt-submit",
        "preToolUse": "tool-start",
        "postToolUse": "tool-end",
        "stop": "stop",
    },
    "antigravity": {
        "before_model_call": "session-start",
        "before_tool_call": "tool-start",
        "after_tool_call": "tool-end",
        "on_loop_stop": "stop",
    },
    "opencode": {
        "session.created": "session-start",
        "session.deleted": "session-end",
        "tool.execute.before": "tool-start",
        "tool.execute.after": "tool-end",
        "session.idle": "stop",
    },
    "cline": {
        "UserPromptSubmit": "user-prompt-submit",
        "PreToolUse": "tool-start",
        "PostToolUse": "tool-end",
    },
    "junie": {
        "SessionStart": "session-start",
    },
    # Kiro IDE uses a file-event model (.kiro.hook fileEdited/userTriggered)
    # that does not map onto the agent-lifecycle canonical set; its trigger
    # is authored directly as a .kiro.hook file, not via this dispatcher.
}

# ── Canonical event -> ordered concern hook chain (T424 AC1) ────────────────
# Each entry is [basename, *extra_args]. The dispatcher locates `<base>.py`
# (preferred) or `<base>.ps1` (fallback) next to this file and runs it with
# the same stdin payload. This reuses the T1584 Python hooks as the concern
# handlers so behavior is authored once. user-prompt-submit has no concern
# hooks yet — its canonical handler is a clean pass-through that platforms
# can now fire (and future concern hooks register here).
#
# T1624 (WS-A-1) wired the logging chain into the canonical core:
# - g-hk-pre-session-trace  -> session-start (opens the session trace marker)
# - g-hk-post-session-trace -> stop (logs cumulative elapsed) and
#                              session-end --finalize (closes/removes the marker)
# - g-hk-crash-record       -> stop (records one `hook` activation for the stop
#                              chain; zero-overhead no-op unless GALD3R_CRASH_STATS
#                              is enabled)
# - g-hk-graph-update       -> stop (refreshes the muninn graph index; instant
#                              skip when the muninn plugin does not ship)
# The gald3r-internal pre_session/post_session event names are RETIRED (D-8):
# session tracing now rides the canonical session-start/stop events.
#
# T1627 (WS-A-4) wired the vault chain + raw-inbox watcher:
# - g-hk-vault-resolve   -> session-start (resolves vault paths, creates layout)
# - g-hk-vault-migrate   -> session-start with --if-diverged (no-op unless the
#                           local vault diverges from a configured shared vault)
# - g-hk-vault-verify    -> stop (one-line vault structure status banner)
# - raw-inbox-watcher    -> stop with --hook-mode (processes/flags {vault}/raw/
#                           drops; never exits non-zero in hook mode)
# - g-hk-vault-reindex   -> stop (debounced: regenerates _index.yaml + the
#                           OKF-style index.md views only when notes changed)
# Order matters on stop: the watcher routes inbox files into the vault BEFORE
# the reindex runs, so newly ingested notes land in the same regen.
#
# T90 (D001 ratified 2026-07-13) wired the TEL host-CLI hook tap:
# - g-hk-tel-tap --kind post_tool_use -> tool-end (maps Claude Code's
#                                        PostToolUse payload onto the TEL
#                                        normalized stream; SILENT, never
#                                        prints to stdout)
# - g-hk-tel-tap --kind transcript    -> stop (tails the Stop payload's
#                                        transcript_path JSONL for new
#                                        records since the last processed
#                                        offset; also SILENT)
# See gald3r_core.core.tel.host_adapter and g-hk-tel-tap.md for the full
# match/decorate/write-ledger contract both registrations share.
#
# BUG-645 wired g-hk-goal-stop-detect -> stop (goal-mechanism quit-condition
# enforcement -- terminal-state clause + re-invoke ceiling -- mirroring
# g-hk-ggo-stop-detect's own proven pattern, scoped to
# .gald3r/config/ACTIVE_GOAL.md instead of the g-go-go run marker; see that
# hook's own module docstring / .md for the full rationale).
CONCERN_CHAIN: Dict[str, List[List[str]]] = {
    "session-start": [
        ["g-hk-session-start"],
        ["g-hk-pre-session-trace"],
        ["g-hk-vault-resolve"],
        ["g-hk-vault-migrate", "--if-diverged"],
    ],
    "session-end": [
        ["g-hk-session-end"],
        ["g-hk-post-session-trace", "--finalize"],
    ],
    "user-prompt-submit": [],
    "tool-start": [
        ["g-hk-validate-shell"],
        ["g-hk-pre-tool-call-gald3r-guard"],
        ["g-hk-pre-tool-call-prd-freeze"],
        ["g-hk-pre-tool-call-member-gald3r-guard"],
        ["g-hk-policy-check"],
        ["g-hk-pre-tool-call"],
    ],
    "tool-end": [
        ["g-hk-tel-tap", "--kind", "post_tool_use"],
    ],
    "stop": [
        ["g-hk-agent-complete"],
        ["g-hk-nightly-learn"],
        ["g-hk-encoding-normalize", "-Quiet"],
        ["g-hk-ggo-stop-detect"],
        ["g-hk-goal-stop-detect"],
        ["g-hk-post-session-trace"],
        ["g-hk-crash-record", "--component-type", "hook",
         "--component-name", "stop-chain", "--trigger-source", "g_hk_core"],
        ["g-hk-graph-update"],
        ["g-hk-vault-verify"],
        ["raw-inbox-watcher", "--hook-mode"],
        ["g-hk-vault-reindex"],
        ["g-hk-tel-tap", "--kind", "transcript"],
    ],
}

# ── Concerns invoked INDIRECTLY by a chained concern (T1624, WS-A-5 input) ──
# Hook scripts that ship next to this core and fire through another concern's
# subprocess launch rather than their own CONCERN_CHAIN entry. Machine-readable
# so the hook-parity lint (WS-A-5) can distinguish "chained (indirect)" from
# "orphaned". Key = the chained launcher, values = hook basenames it invokes.
# g-hk-claude-chat-logger is launched by g-hk-agent-complete (stop chain) with
# the discovered transcript path — registering it directly as well would write
# every chat log twice. The launcher resolves it through this map via
# resolve_indirect_concerns() below (T1625 / BUG-133), never by filename.
INDIRECT_CONCERNS: Dict[str, List[str]] = {
    "g-hk-agent-complete": ["g-hk-claude-chat-logger"],
}

# ── Install-directory name -> platform key (T1625 / BUG-133) ────────────────
# Maps the dot-directory a platform ships its gald3r hooks under to the
# platform key used in PLATFORM_EVENT_MAP, so concern hooks can label their
# artifacts (e.g. the chat log's `--platform` slug) without hardcoding a
# platform name. `.agents` is shared by antigravity and the goose plugin
# bundle; detect_platform() disambiguates via the goose bundle's
# `gald3r-hooks` plugin folder.
PLATFORM_INSTALL_DIRS: Dict[str, str] = {
    ".claude": "claude",
    ".cursor": "cursor",
    ".codex": "codex",
    ".gemini": "gemini",
    ".agent": "gemini",
    ".qwen": "qwen",
    ".github": "copilot",
    ".windsurf": "windsurf",
    ".openhands": "openhands",
    ".augment": "augment",
    ".clinerules": "cline",
    ".kiro": "kiro-cli",
    ".opencode": "opencode",
    ".agents": "antigravity",
    ".junie": "junie",
}


def detect_platform(script_dir: Optional[Path] = None) -> str:
    """Resolve the platform key for the install a hook is running from.

    Resolution order: the ``GALD3R_HOOK_PLATFORM`` env override (must be a
    PLATFORM_EVENT_MAP key), then the nearest ancestor directory of
    ``script_dir`` (default: this core's directory) whose name maps via
    PLATFORM_INSTALL_DIRS. Falls back to ``"claude"`` — the unified chat
    logger's own default — when nothing matches.
    """
    env = (os.environ.get("GALD3R_HOOK_PLATFORM") or "").strip().lower()
    if env in PLATFORM_EVENT_MAP:
        return env
    here = Path(script_dir) if script_dir is not None else SCRIPT_DIR
    part_names = [here.name] + [p.name for p in here.parents]
    for name in part_names:
        platform = PLATFORM_INSTALL_DIRS.get(name)
        if platform is None:
            continue
        if platform == "antigravity" and "gald3r-hooks" in part_names:
            return "goose"
        return platform
    return "claude"


# ── Codex apply_patch payload normalization (T426 / BUG-370 stage 2) ───────
# BUG-370 stage 1 (T425) wired Codex's real `.codex/hooks.json` mechanism
# directly to the shared canonical entrypoints (`g-hk-on-<event>.py` ->
# `dispatch()`), on the documented assumption that Codex's harness already
# constructs the exact `{tool_name, tool_input}` dict shape every concern
# hook expects -- true for ordinary tools, but NOT for `apply_patch`, whose
# real wire shape was independently re-verified for this fix (2026-07-18)
# directly against Codex's OWN upstream Rust source (never assumed from
# OpenCode's fork, despite a superficially similar patch-header grammar):
#
#   * `codex-rs/core/src/tools/hook_names.rs`'s `HookToolName::apply_patch()`
#     -- "The serialized name remains `apply_patch` ... `Write` and `Edit`
#     are accepted as matcher ALIASES [selection only], never the payload
#     value." I.e. the real `tool_name` on the wire is the literal lowercase
#     `"apply_patch"` -- it does NOT match the Claude-Code-shaped
#     `"ApplyPatch"` already present in every concern hook's `WRITE_TOOLS`
#     list, so the guard's `if tool not in WRITE_TOOLS: return _allow()`
#     gate silently no-ops for every Codex apply_patch call today, before
#     PATH_KEYS is even considered.
#   * `codex-rs/core/src/tools/handlers/apply_patch.rs`'s
#     `pre_tool_use_payload()` builds `tool_input` as literally
#     `serde_json::json!({ "command": command })`, where `command` is the
#     raw patch-body text the model passed as the tool call argument (NOT a
#     shell/heredoc-wrapped invocation -- `apply_patch_payload_command()` in
#     the same file pulls it straight from `ToolPayload::Custom { input }`).
#     There is no discrete path key at all, matching OpenCode's own
#     pre-BUG-369 gap, but under a different field name (`command`, not
#     `patchText`) -- confirmed by reading the real handler source, not
#     assumed from the field-name coincidence with Bash's `tool_input.command`
#     docs prose (https://learn.chatgpt.com/docs/hooks, the redirect target
#     of https://developers.openai.com/codex/hooks: "Bash and `apply_patch`
#     use `tool_input.command`").
#   * `codex-rs/apply-patch/src/parser.rs`'s `BEGIN_PATCH_MARKER` /
#     `END_PATCH_MARKER` / `ADD_FILE_MARKER` / `DELETE_FILE_MARKER` /
#     `UPDATE_FILE_MARKER` / `MOVE_TO_MARKER` constants confirm the header
#     grammar (`"*** Begin Patch"`, `"*** Add File: "`, `"*** Delete File: "`,
#     `"*** Update File: "`, `"*** Move to: "`, `"*** End Patch"`) is
#     byte-for-byte the same convention BUG-369 already parsed for
#     OpenCode's `apply_patch.ts` (both apparently descended from the
#     original Codex CLI naming, per this task's own scope note) -- so the
#     same line-oriented `.startswith(...)`/slice/`.strip()` extraction
#     mirrors both real parsers correctly without a reinvented regex header
#     grammar. (Lenient-mode legacy heredoc wrapping --
#     `"<<'EOF'\\n*** Begin Patch\\n...*** End Patch\\nEOF\\n"`, documented in
#     the same `parser.rs` for old GPT-4.1-style `local_shell` tool calls --
#     is harmless to this line-scan: the extra heredoc marker lines simply
#     never match any of the four header prefixes.)
#
# Per BUG-370's task text and the "concern hooks stay platform-agnostic"
# precedent BUG-367/368/369 already established for OpenCode's generated
# plugin, this normalization is Codex-gated (via `detect_platform()`, which
# already exists in this shared dispatch CORE for unrelated reasons -- the
# chat logger's `--platform` slug) and lives HERE, never inside
# `g-hk-pre-tool-call-gald3r-guard.py` or its `tool-start` siblings (the PRD
# freeze gate, the workspace-member guard): it renames `tool_name` to the
# already-existing Claude-Code-shaped `"ApplyPatch"` WRITE_TOOLS entry (no
# new vocabulary added to any concern hook) and injects a `file_path` key
# alongside the untouched original `command` key, mirroring exactly how
# BUG-368/369 added `file_path` alongside OpenCode's untouched `filePath`/
# `patchText`.
_CODEX_APPLY_PATCH_TOOL_NAME = "apply_patch"
_CODEX_APPLY_PATCH_COMMAND_KEY = "command"
_CODEX_APPLY_PATCH_CLAUDE_SHAPED_TOOL_NAME = "ApplyPatch"
_CODEX_APPLY_PATCH_PATH_KEY = "file_path"

#: Real header-line prefixes, verbatim from `codex-rs/apply-patch/src/
#: parser.rs`'s own marker constants (trailing space included, matching that
#: source exactly) -- never a reinvented grammar.
_CODEX_APPLY_PATCH_HEADER_PREFIXES: List[str] = [
    "*** Add File: ",
    "*** Delete File: ",
    "*** Update File: ",
    "*** Move to: ",
]

#: Fail-safe fallback (mirrors BUG-369's own "fail safe, not fail open" AC):
#: when the patch body contains NO recognized header line at all (malformed
#: / unrecognized shape), this broader scan still catches a literal
#: ``.gald3r/``-containing path token appearing anywhere else in the body,
#: so an unparseable patch can never silently allow a real ``.gald3r/``
#: target just because the strict header scan found nothing to anchor on.
_CODEX_APPLY_PATCH_GALD3R_SUBSTRING_RE = re.compile(r"""([^\s"'`]*\.gald3r/[^\s"'`]*)""")


def _extract_codex_apply_patch_header_paths(command: str) -> List[str]:
    """Pull every recognized header-line path out of a Codex ``apply_patch``
    ``tool_input.command`` body, mirroring ``codex-rs/apply-patch/src/
    parser.rs``'s own line-oriented marker-prefix convention exactly."""
    paths: List[str] = []
    for line in command.splitlines():
        for prefix in _CODEX_APPLY_PATCH_HEADER_PREFIXES:
            if line.startswith(prefix):
                candidate = line[len(prefix):].strip()
                if candidate:
                    paths.append(candidate)
                break
    return paths


def _pick_codex_apply_patch_path(command: Any) -> Optional[str]:
    """Choose the single path to surface as ``file_path`` for a Codex
    ``apply_patch`` call. When the patch touches multiple files, whichever
    header path resolves under ``.gald3r/`` wins over an earlier, unrelated
    one (the shared containment check only ever inspects one path field, so
    silently picking a non-``.gald3r/`` path first would defeat the guard on
    a multi-file patch) -- mirrors ``pickApplyPatchPath()``'s OpenCode
    precedent (BUG-369) exactly, adapted to Codex's real header set."""
    if not isinstance(command, str):
        return None
    header_paths = _extract_codex_apply_patch_header_paths(command)
    for candidate in header_paths:
        if ".gald3r/" in candidate.replace("\\", "/"):
            return candidate
    if header_paths:
        return header_paths[0]
    # Fail-safe: no recognized header line at all.
    match = _CODEX_APPLY_PATCH_GALD3R_SUBSTRING_RE.search(command)
    return match.group(1) if match else None


def _normalize_codex_apply_patch_event(raw_stdin: str) -> str:
    """Codex-gated normalization (T426 / BUG-370 stage 2) -- see the module
    comment block above for the full investigation and rationale. Returns
    *raw_stdin* completely UNCHANGED whenever the detected platform is not
    Codex, the payload does not parse as a JSON object, or `tool_name` is
    not the real Codex `apply_patch` value -- deliberately narrow, and never
    raises (any parse failure is treated as "nothing to normalize", not an
    error), matching this whole module's fail-soft contract."""
    if detect_platform() != "codex":
        return raw_stdin
    try:
        event = json.loads(raw_stdin)
    except (json.JSONDecodeError, ValueError, TypeError):
        return raw_stdin
    if not isinstance(event, dict):
        return raw_stdin
    if event.get("tool_name") != _CODEX_APPLY_PATCH_TOOL_NAME:
        return raw_stdin
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return raw_stdin

    normalized_input = dict(tool_input)
    command = tool_input.get(_CODEX_APPLY_PATCH_COMMAND_KEY)
    path = _pick_codex_apply_patch_path(command)
    if path is not None:
        normalized_input[_CODEX_APPLY_PATCH_PATH_KEY] = path

    normalized_event = dict(event)
    normalized_event["tool_name"] = _CODEX_APPLY_PATCH_CLAUDE_SHAPED_TOOL_NAME
    normalized_event["tool_input"] = normalized_input
    try:
        return json.dumps(normalized_event)
    except (TypeError, ValueError):
        return raw_stdin


def _resolve_script(base_name: str, script_dir: Path) -> Optional[Path]:
    """Resolve a hook basename to a shipped script, preferring .py over .ps1."""
    for suffix in (".py", ".ps1"):
        candidate = script_dir / (base_name + suffix)
        if candidate.is_file():
            return candidate
    return None


def resolve_indirect_concerns(
    launcher: str, script_dir: Optional[Path] = None
) -> List[Path]:
    """Resolve the shipped scripts a launcher invokes indirectly (T1625).

    Looks up INDIRECT_CONCERNS — the same machine-readable map the WS-A-5
    hook-parity lint consumes — and resolves each basename next to
    ``script_dir`` (default: this core's directory) via _resolve_script.
    Concern scripts that do not ship in this install are omitted; callers
    MUST emit a visible warning when the list comes back empty (BUG-133:
    a missing logger must never be a silent no-op).
    """
    here = Path(script_dir) if script_dir is not None else SCRIPT_DIR
    resolved: List[Path] = []
    for base in INDIRECT_CONCERNS.get(launcher, []):
        path = _resolve_script(base, here)
        if path is not None:
            resolved.append(path)
    return resolved


def _read_raw_stdin() -> str:
    """Read the raw harness payload once so it can be re-fed to each concern."""
    try:
        if sys.stdin.isatty():
            return ""
        return sys.stdin.read() or ""
    except (OSError, ValueError):
        return ""


def _locate(base_name: str):
    """Resolve a concern hook to a runnable command, preferring .py over .ps1."""
    path = _resolve_script(base_name, SCRIPT_DIR)
    if path is None:
        return None
    if path.suffix == ".py":
        return [sys.executable, str(path)]
    import shutil

    exe = shutil.which("powershell") or shutil.which("pwsh")
    if exe:
        return [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                str(path)]
    return None


def _is_block(payload: Dict[str, Any], returncode: int) -> bool:
    """Detect a blocking verdict from a concern hook's response/exit code."""
    if returncode == 2:
        return True
    if payload.get("continue") is False:
        return True
    decision = str(payload.get("decision", "")).lower()
    if decision in ("block", "deny"):
        return True
    perm = payload.get("permission")
    if isinstance(perm, dict) and str(perm.get("decision", "")).lower() == "deny":
        return True
    return False


def _run_concern(cmd: List[str], extra_args: List[str], raw_stdin: str):
    """Run one concern hook with the shared payload; return (payload, rc)."""
    try:
        res = subprocess.run(
            cmd + list(extra_args),
            input=raw_stdin,
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
        )
    except (OSError, subprocess.SubprocessError):
        return {}, 0
    payload: Dict[str, Any] = {}
    out = (res.stdout or "").strip()
    if out:
        try:
            parsed = json.loads(out)
            if isinstance(parsed, dict):
                payload = parsed
        except (json.JSONDecodeError, ValueError):
            # Non-JSON stdout is treated as additional_context text.
            payload = {"additional_context": out}
    return payload, res.returncode


# ── Events where a concern hook's blocking verdict is session-halting ──────
# (BUG-199) A blocking verdict (rc==2 or an equivalent JSON payload caught by
# _is_block()) is only allowed to turn into continue:false / a process exit
# code 2 for events in this set -- exactly the set the exit-code branch at
# the bottom of dispatch() already used before this fix existed (Cursor
# preToolUse, kiro-cli preToolUse exit 2). Every OTHER canonical event (stop,
# tool-end, session-*, ...) never hard-blocks a harness turn/session either
# way: a blocking verdict there is caught and folded into additional_context
# instead of being dropped, per this same set being reused for both the
# JSON continue/reason fields and the exit code below.
TOOL_BLOCKING_EVENTS: Tuple[str, ...] = ("tool-start",)


def dispatch(event: str) -> int:
    """Run the concern chain for a canonical event; emit a unified envelope.

    Returns the process exit code (2 when a tool event was blocked, else 0).
    """
    if event not in CANONICAL_EVENTS:
        # Unknown event — never block, just continue.
        print(json.dumps({"continue": True}, separators=(",", ":")))
        return 0

    raw_stdin = _read_raw_stdin()
    # T426 / BUG-370 stage 2: normalize Codex's raw apply_patch payload
    # (lowercase tool_name, patch-body-only tool_input) to the Claude-Code-
    # shaped vocabulary every WRITE_TOOLS/PATH_KEYS-consuming concern hook
    # already reads, BEFORE it is fed to any of them -- see the Codex-gated
    # normalization block above `_resolve_script()` for the full rationale.
    # Only tool_name/tool_input-bearing events are relevant; the function
    # itself is also a safe no-op for every other event/platform/tool.
    if event in ("tool-start", "tool-end"):
        raw_stdin = _normalize_codex_apply_patch_event(raw_stdin)
    context_parts: List[str] = []
    blocked = False
    block_reason = ""

    for entry in CONCERN_CHAIN.get(event, []):
        base_name = entry[0]
        extra_args = entry[1:]
        cmd = _locate(base_name)
        if cmd is None:
            continue
        payload, rc = _run_concern(cmd, extra_args, raw_stdin)
        ctx = payload.get("additional_context")
        if isinstance(ctx, str) and ctx.strip():
            context_parts.append(ctx.strip())
        if not blocked and _is_block(payload, rc):
            blocked = True
            block_reason = str(
                payload.get("reason")
                or payload.get("block_reason")
                or ("%s blocked the %s event" % (base_name, event))
            )

    # BUG[BUG-199] kind=code (fixed): continue:false/reason must only carry a
    # blocking verdict for the SAME event set that already hard-blocks via
    # exit code (TOOL_BLOCKING_EVENTS, defined above dispatch()) — previously
    # this was unconditional, so rc==2 from a tool-end/stop concern hook
    # halted the session via the printed JSON even though its own exit code
    # was 0. A blocking verdict on any other event is caught and folded into
    # additional_context instead of being silently dropped. See
    # .gald3r/bugs/open/bug199_g-hk-core-dispatch-treats-rc-2-from-any.md
    tool_blocking = blocked and event in TOOL_BLOCKING_EVENTS
    if blocked and not tool_blocking and block_reason:
        context_parts.append(
            "[non-blocking event %r caught a concern-hook blocking verdict]: %s"
            % (event, block_reason)
        )

    response: Dict[str, Any] = {"continue": not tool_blocking}
    if context_parts:
        response["additional_context"] = "\n\n".join(context_parts)
    if tool_blocking and block_reason:
        response["reason"] = block_reason

    print(json.dumps(response, separators=(",", ":")))
    # Only tool events use exit-code blocking (Cursor preToolUse, kiro-cli
    # preToolUse exit 2). Lifecycle events never hard-block via exit code.
    if tool_blocking:
        return 2
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        # No event given: print the canonical event list as JSON (introspection).
        print(json.dumps({"canonical_events": list(CANONICAL_EVENTS.keys())},
                         separators=(",", ":")))
        return 0
    return dispatch(argv[0])


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session.
        try:
            print(json.dumps({"continue": True}, separators=(",", ":")))
        except Exception:
            pass
        sys.exit(0)
