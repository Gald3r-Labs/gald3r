#!/usr/bin/env python3
"""Python port of g-hk-session-start.ps1 (T1584).

Session-initialization hook (fires when a new composer conversation is
created). Ensures platform dirs are populated via setup_gald3r_project,
guards against double-application per session, reads and auto-heals
.gald3r/.identity (user_id fallback from the per-user appdata config,
project_id UUID regeneration), then assembles the additional_context
banner: first-time-setup notice, previous-session reflection reminder,
vault context (note count, recent activity, vault structure verification,
stale documentation and raw-inbox counts), TASKS.md archive gate,
HEARTBEAT no_agent watchdog output (T968), cross-project WPAC inbox
summary, and GUARDRAILS.md. Emits a compact JSON response
{"continue": true, "additional_context": ...} and always exits 0.

Vault path resolution is a native port of the retired g-hk-vault-resolve.ps1
(the PS1 dot-sources that helper); the vault status banner is a native port
of the retired g-hk-vault-verify.ps1's Get-Gald3rVaultStatusBanner. The WPAC
inbox check is invoked as a .py sibling; the TASKS.md archive gate was absorbed
into the engine `gald3r task archive-gate` verb (T1665) and is dispatched via
the zero-IP gald3r_bin.py resolver (degrades to no banner when no engine is
installed).
"""
# @subsystems: LOGGING_SYSTEM
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent

SETUP_BANNER = (
    "## GALD3R FIRST-TIME SETUP NEEDED\n"
    "Your gald3r user ID has not been configured yet.\n"
    "\n"
    "**Quick setup:** Edit `.gald3r/.identity` and set `user_id` and "
    "`user_name` to your values.\n"
    "\n"
    "---"
)

# Same (intentionally replicated) path filter as the PS1's Get-MarkdownCount /
# vault note count: excludes paths matching this regex when counting .md files.
OBSIDIAN_FILTER = re.compile(r"\\.obsidian(\|\\)")

IDENTITY_KEYS = (
    "project_id",
    "project_name",
    "user_id",
    "user_name",
    "gald3r_version",
    "vault_location",
)

#: T1649 install nudge — one-time marker written under the project's .gald3r/.
#: Its presence (whatever the content) permanently suppresses the nudge.
INSTALL_NUDGE_MARKER_NAME = ".install_nudge_shown"


def _powershell_exe():
    """Locate a PowerShell executable to run a user-configured HEARTBEAT
    watchdog script that happens to be .ps1 (arbitrary user script, not a
    gald3r-shipped .py/.ps1 twin pair — see _run_watchdogs)."""
    return shutil.which("powershell") or shutil.which("pwsh")


def _run_sibling(base_name, args, cwd=None):
    """Run a sibling hook/script: <base>.py only (T1600 — .ps1 fallback removed).

    Returns a CompletedProcess or None when the .py variant is not runnable.
    """
    py_path = SCRIPT_DIR / (base_name + ".py")
    return _run_script_pair(py_path, args, cwd=cwd)


def _run_script_pair(py_path, args, cwd=None):
    try:
        if py_path is not None and py_path.is_file():
            return subprocess.run(
                [sys.executable, str(py_path)] + list(args),
                capture_output=True, text=True, cwd=cwd,
            )
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def _resolve_engine_cmd(project_root):
    """Resolve the gald3r engine command prefix via the zero-IP resolver.

    The TASKS.md archive gate was absorbed (T1665) into the engine
    `gald3r task archive-gate` verb. Returns the command prefix (e.g.
    ``["gald3r"]``) or ``None`` when the resolver is not shipped (old install)
    or no engine can be found — the caller then degrades to no banner.
    """
    root = Path(project_root)
    resolver_path = root / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver_path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(
            "g_hk_ss_gald3r_bin", str(resolver_path))
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.resolve_engine_cmd(root)
    except Exception:
        return None


def _run_engine(engine_cmd, args, cwd=None):
    """Run a resolved engine command prefix + args, capturing output.

    Returns a CompletedProcess or None on failure (fail-open — a missing or
    erroring engine must never break session start).
    """
    try:
        return subprocess.run(
            list(engine_cmd) + list(args),
            capture_output=True, text=True, cwd=cwd,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def parse_identity_file(path, extra_keys=()):
    """Parse KEY=VALUE lines from a .gald3r/.identity file."""
    identity = {k: "" for k in IDENTITY_KEYS}
    for k in extra_keys:
        identity.setdefault(k, "")
    try:
        if path.is_file():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"^(\w+)=(.*)$", line)
                if m:
                    identity[m.group(1)] = m.group(2).strip()
    except OSError:
        pass
    return identity


def _replace_identity_value(identity_file, key, value):
    """Regex-replace `key=...` in the identity file (matches PS1 -replace)."""
    try:
        content = identity_file.read_text(encoding="utf-8")
        content = re.sub(key + "=.*", lambda _m: "%s=%s" % (key, value), content)
        identity_file.write_text(content, encoding="utf-8")  # -NoNewline parity
    except OSError:
        pass


def _markdown_count(path):
    """Port of Get-MarkdownCount (including the original path filter)."""
    if not path.is_dir():
        return 0
    count = 0
    try:
        for p in path.rglob("*.md"):
            if OBSIDIAN_FILTER.search(str(p)):
                continue
            if p.is_file():
                count += 1
    except OSError:
        pass
    return count


# BUG-209/BUG-210: an unexpanded identity placeholder (e.g. the shipped default
# ``repos_location={LOCAL_REPOS}``, or any ``{TOKEN}`` setup never filled) must be
# treated as "use local", never as a real path. Matches the ``{LOCAL}`` vault
# sentinel plus ANY ``{ALL_CAPS_OR_ident}`` token so the two spellings can never
# diverge into a filesystem side effect again.
_PLACEHOLDER_RE = re.compile(r"^\{[A-Za-z0-9_]+\}$")


def _is_local_sentinel(value):
    """True when a location value means "use the local fallback".

    That is: empty/None, the canonical ``{LOCAL}`` sentinel, or any still-
    unexpanded ``{PLACEHOLDER}`` token (BUG-209/BUG-210).
    """
    if not value:
        return True
    v = value.strip()
    return v == "{LOCAL}" or bool(_PLACEHOLDER_RE.match(v))


def _path_writable(path_str):
    """Port of Test-Gald3rPathWritable: mkdir -Force + write probe.

    BUG-209: never mkdir an unexpanded ``{PLACEHOLDER}`` path — that is what
    materialized a literal ``{LOCAL_REPOS}`` directory in project roots. Such a
    value is rejected up front (callers route it to the local fallback instead).
    """
    if not path_str or _PLACEHOLDER_RE.match(str(path_str).strip()):
        return False
    try:
        p = Path(path_str)
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".gald3r_write_probe.tmp"
        probe.write_text("", encoding="utf-8")
        try:
            probe.unlink()
        except OSError:
            pass
        return True
    except OSError:
        return False


def _env_setting(env_path, keys):
    """Port of Get-EnvSetting: first matching line per key, first non-empty."""
    if not env_path.is_file():
        return None
    try:
        lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for key in keys:
        pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=\s*(.+)$")
        for line in lines:
            m = pattern.match(line)
            if m:
                value = m.group(1).strip().strip('"').strip("'")
                if value:
                    return value
                break  # first match per key only; empty value -> next key
    return None


def resolve_vault(project_root):
    """Native port of g-hk-vault-resolve.ps1.

    Returns dict with vault_path, repos_path, messages (list of notices).
    """
    identity = parse_identity_file(
        project_root / ".gald3r" / ".identity", extra_keys=("repos_location",)
    )
    env_path = project_root / ".env"
    vault_local = project_root / ".gald3r" / "vault"
    repos_local = project_root / ".gald3r" / "repos"
    messages = []

    vault_location = identity.get("vault_location") or _env_setting(
        env_path, ["GALD3R_VAULT_LOCATION", "GALD3R_KNOWLEDGE_WELL_PATH"]
    )
    repos_location = identity.get("repos_location") or _env_setting(
        env_path, ["GALD3R_REPOS_LOCATION"]
    )

    if _is_local_sentinel(vault_location):
        vault_path = vault_local
    elif _path_writable(vault_location):
        vault_path = Path(vault_location)
    else:
        vault_path = vault_local
        messages.append(
            "Shared vault unavailable; writing to local fallback at "
            "`.gald3r/vault/`."
        )

    if _is_local_sentinel(repos_location):
        repos_path = repos_local
    elif _path_writable(repos_location):
        repos_path = Path(repos_location)
    else:
        repos_path = repos_local
        messages.append(
            "Configured repos mirror unavailable; using local `.gald3r/repos/`."
        )

    for p in (vault_local, repos_local, vault_path, repos_path):
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    local_md = _markdown_count(vault_local)
    if vault_path != vault_local and local_md > 0:
        messages.append(
            "Local vault contains %d markdown files while a shared vault is "
            "configured. Consider running migration." % local_md
        )

    project_name = identity.get("project_name")
    if not project_name or project_name == "{project_name}":
        project_name = project_root.name

    project_dir = vault_path / "projects" / project_name
    for p in (project_dir, project_dir / "sessions", project_dir / "decisions"):
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    return {"vault_path": vault_path, "repos_path": repos_path, "messages": messages}


def vault_status_banner(project_root):
    """Native port of g-hk-vault-verify.ps1 Get-Gald3rVaultStatusBanner."""
    try:
        research_subdirs = ("articles", "github", "harvests", "papers",
                            "platforms", "videos")
        identity_path = project_root / ".gald3r" / ".identity"
        if not identity_path.exists():
            return ""

        vault_location = ""
        for line in identity_path.read_text(encoding="utf-8",
                                            errors="replace").splitlines():
            m = re.match(r"^\s*vault_location\s*=\s*(.+)$", line)
            if m:
                vault_location = m.group(1).strip().strip('"').strip("'")
                break

        if not vault_location or vault_location == "{LOCAL}":
            return ""

        if not Path(vault_location).exists():
            return ("- Vault at `%s`: NOT FOUND -- run `@g-vault init` to "
                    "build the vault structure" % vault_location)

        research_root = Path(vault_location) / "research"
        missing = []
        if not research_root.exists():
            missing.append("research/")
        else:
            for sub in research_subdirs:
                if not (research_root / sub).exists():
                    missing.append("research/" + sub + "/")

        if missing:
            return ("- Vault at `%s`: PARTIAL (missing: %s) -- run "
                    "`@g-vault init` to create the missing folders"
                    % (vault_location, ", ".join(missing)))
        return "- Vault at `%s`: OK" % vault_location
    except (OSError, ValueError):
        return ""


def _run_watchdogs(project_root):
    """HEARTBEAT no_agent watchdog (T968). Returns terminal banner text."""
    banner = ""
    heartbeat_file = project_root / ".gald3r" / "config" / "HEARTBEAT.md"
    if not heartbeat_file.is_file():
        return banner
    raw = heartbeat_file.read_text(encoding="utf-8", errors="replace")

    blocks = re.split(r"(?m)^\s*-\s+id:\s*", raw)[1:]
    for block in blocks:
        # no_agent flag — only true entries are watchdogs.
        if not re.search(r"(?m)^\s*no_agent:\s*true\s*$", block):
            continue

        m = re.search(r"(?m)^\s*script:\s*[\"']?([^\"'\r\n]+?)[\"']?\s*$", block)
        script_rel = m.group(1).strip() if m else None
        if not script_rel:
            continue

        output_channel = "terminal"
        m = re.search(r"(?m)^\s*output:\s*[\"']?(\w+)[\"']?\s*$", block)
        if m:
            output_channel = m.group(1).strip().lower()

        entry_id = block.split("\n", 1)[0].strip().strip("\"'")
        if not entry_id:
            entry_id = script_rel

        script_path = (Path(script_rel) if os.path.isabs(script_rel)
                       else project_root / script_rel)
        if not script_path.exists():
            continue

        # Run the script directly and capture stdout only. Failures are
        # swallowed so a broken watchdog never blocks session start.
        stdout = ""
        try:
            sp = str(script_path)
            if sp.lower().endswith(".ps1"):
                exe = _powershell_exe()
                if not exe:
                    continue
                cmd = [exe, "-NoProfile", "-ExecutionPolicy", "Bypass",
                       "-File", sp]
            elif sp.lower().endswith(".py"):
                cmd = [sys.executable, sp]
            else:
                cmd = [sp]
            res = subprocess.run(cmd, capture_output=True, text=True,
                                 cwd=str(project_root))
            stdout = res.stdout or ""
        except (OSError, subprocess.SubprocessError):
            stdout = ""

        # Silent on empty stdout — the whole point of watchdog mode.
        if not stdout or stdout.strip() == "":
            continue

        stdout = stdout.rstrip()
        if output_channel == "log":
            try:
                wd_log_dir = project_root / ".gald3r" / "logs"
                wd_log_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                wd_log_file = wd_log_dir / ("watchdog_%s.log" % entry_id)
                with open(wd_log_file, "a", encoding="utf-8") as fh:
                    fh.write("## %s\n%s\n\n" % (stamp, stdout))
            except OSError:
                pass
        else:
            banner += "## Watchdog: %s\n%s\n\n" % (entry_id, stdout)

    if banner:
        banner += "---\n"
    return banner


# ── One-time install nudge (T1649 — prompt, not force) ──────────────────────


def _install_home_default():
    """Zero-IP mirror of gald3r.home.resolve_install_home's default order.

    The engine SOURCE does not ship (T1645), so this hook cannot import
    ``gald3r.home`` — it replicates only the tiny path resolution
    (``GALD3R_HOME`` env var, else the per-OS default) needed for the
    best-effort Throne probe. No engine logic lives here.
    """
    override = os.environ.get("GALD3R_HOME", "").strip()
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", "").strip()
        parent = Path(base) if base else Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        parent = Path.home() / "Library" / "Application Support"
    else:
        xdg = os.environ.get("XDG_DATA_HOME", "").strip()
        parent = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return parent / "gald3r"


def _throne_present():
    """Best-effort Throne probe: ``gald3r install throne`` caches the
    downloaded installer under ``<install-home>/cache/throne`` — any file
    there means the user has (at least) fetched Throne. Absence just means
    the one-time nudge mentions it; this is a soft offer, never a gate."""
    try:
        cache = _install_home_default() / "cache" / "throne"
        return cache.is_dir() and any(p.is_file() for p in cache.iterdir())
    except OSError:
        return False


def _engine_missing(project_root):
    """True only on a REAL gald3r_bin.py resolver miss (EngineNotFoundError).

    Delegates to the shipped zero-IP resolver so the nudge can never drift
    from the actual resolution order (GALD3R_BIN env var -> PATH -> bundled
    binary -> dev source). Any probe failure — resolver not shipped (old
    install), import error — returns False: silence over noise.
    """
    resolver_path = project_root / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver_path.is_file():
        return False
    try:
        spec = importlib.util.spec_from_file_location(
            "g_hk_nudge_gald3r_bin", str(resolver_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        not_found = getattr(mod, "EngineNotFoundError", None)
        if not_found is None:
            return False
        try:
            mod.resolve_engine_cmd(project_root)
            return False
        except not_found:
            return True
    except Exception:
        return False


def _install_nudge_banner(project_root):
    """T1649 — one-time, non-blocking install nudge (prompt, not force).

    When the compiled gald3r engine binary is missing (a real resolver miss;
    dev checkouts with engine source never trigger) and/or Throne is not
    detected, emit ONE banner pointing at ``g-install-agent`` /
    ``g-install-throne``, then drop a marker file in ``.gald3r/`` so the
    nudge never repeats for this project. The zero-engine SKILL.full.md
    fallback keeps working either way — the banner says so explicitly.
    Never blocks: banner-only, and if the marker cannot be persisted the
    nudge stays silent rather than risk repeating forever.
    """
    marker = project_root / ".gald3r" / INSTALL_NUDGE_MARKER_NAME
    try:
        if marker.exists():
            return ""
    except OSError:
        return ""

    # Pre-T1642 installs do not ship the resolver (and may not carry the
    # g-install-* commands the nudge points at) — stay silent entirely.
    resolver_path = project_root / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver_path.is_file():
        return ""

    engine_missing = _engine_missing(project_root)
    throne_missing = not _throne_present()
    if not engine_missing and not throne_missing:
        return ""

    lines = ["## Unlock the Engine-Backed Experience"]
    if engine_missing:
        lines.append(
            "- The compiled gald3r engine binary was not found (resolver "
            "miss). Run **`g-install-agent`** to install the signed Gald3r "
            "Agent binary from the public releases."
        )
    if throne_missing:
        lines.append(
            "- Gald3r Throne (the desktop app) was not detected. Run "
            "**`g-install-throne`** to install it."
        )
    lines.append(
        "Nothing is broken: skills keep working in the file-first "
        "SKILL.full.md fallback mode without them. This is a one-time "
        "notice — it will not be shown again for this project."
    )
    banner = "\n".join(lines) + "\n\n---\n"

    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({
            "shown_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "engine_missing": engine_missing,
            "throne_missing": throne_missing,
            "task": "T1649",
        }, indent=2) + "\n", encoding="utf-8")
    except OSError:
        # Cannot persist the dismissal -> do not show the nudge at all
        # ("never repeats" outranks "always shown once").
        return ""
    return banner


def main():
    parser = argparse.ArgumentParser(
        description="gald3r session-start hook (Python port of "
                    "g-hk-session-start.ps1)")
    parser.parse_known_args()

    # ── Ensure platform dirs are populated from canonical root ──────────────
    try:
        root = SCRIPT_DIR.parent.parent
        _run_script_pair(
            root / "setup_gald3r_project.py",
            ["-Platform", "cursor", "-Quiet"],
        )
    except Exception:
        pass

    # ── Idempotency guard ────────────────────────────────────────────────────
    if os.environ.get("GALD3R_HK_SESSION_START_APPLIED") == "1":
        print(json.dumps({
            "continue": True,
            "additional_context":
                "[SKIP] g-hk-session-start already applied this session",
        }, separators=(",", ":")))
        return 0
    os.environ["GALD3R_HK_SESSION_START_APPLIED"] = "1"

    _hook_common.read_stdin_json()  # drain stdin payload (unused, parity)

    project_root = Path.cwd()

    # ── Read .identity file ──────────────────────────────────────────────────
    identity_file = project_root / ".gald3r" / ".identity"
    identity = parse_identity_file(identity_file)
    setup_needed = False

    # ── User identity resolution ─────────────────────────────────────────────
    user_id = identity.get("user_id", "")
    if not user_id or user_id == "{SETUP_NEEDED}":
        appdata = os.environ.get("APPDATA")
        if appdata:
            app_data_config = Path(appdata) / "gald3r" / "user_config.json"
        else:
            app_data_config = (Path(os.environ.get("HOME", str(Path.home())))
                               / ".config" / "gald3r" / "user_config.json")
        if app_data_config.is_file():
            try:
                app_cfg = json.loads(app_data_config.read_text(encoding="utf-8"))
                cfg_uid = app_cfg.get("user_id")
                if cfg_uid and cfg_uid != "SETUP_NEEDED":
                    user_id = cfg_uid
                    _replace_identity_value(identity_file, "user_id", user_id)
            except (OSError, ValueError):
                pass
        if not user_id or user_id == "SETUP_NEEDED":
            setup_needed = True

    # ── .project_id auto-heal ────────────────────────────────────────────────
    project_id = identity.get("project_id", "")
    uuid_pattern = (r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
    if not re.match(uuid_pattern, project_id or ""):
        project_id = str(uuid.uuid4())
        _replace_identity_value(identity_file, "project_id", project_id)

    # ── Build context message ────────────────────────────────────────────────
    setup_banner = SETUP_BANNER if setup_needed else ""

    reflection_banner = ""
    reflection_file = project_root / ".gald3r" / "logs" / "pending_reflection.json"
    if reflection_file.exists():
        try:
            refl_data = json.loads(reflection_file.read_text(encoding="utf-8"))
            session_size = 0
            if refl_data.get("loop_count"):
                session_size = int(refl_data["loop_count"])
            if session_size >= 5:
                reflection_banner = (
                    "## Previous Session Reminder\n"
                    "Your last session had %d turns. Consider running "
                    "**`@g-status`** to review where things stand.\n"
                    "\n"
                    "---" % session_size
                )
        except (OSError, ValueError, TypeError):
            pass
        try:
            reflection_file.unlink()
        except OSError:
            pass

    vault = resolve_vault(project_root)
    vault_path = vault["vault_path"]
    repos_path = vault["repos_path"]
    vault_messages = vault["messages"]

    vault_note_count = _markdown_count(vault_path)

    recent_vault_activity = "none yet"
    vault_log_path = vault_path / "log.md"
    if vault_log_path.is_file():
        try:
            headings = [l for l in vault_log_path.read_text(
                encoding="utf-8", errors="replace").splitlines()
                if re.match(r"^## ", l)]
            if headings:
                recent_vault_activity = re.sub(r"^##\s*", "", headings[-1])
        except OSError:
            pass

    # BUG-132 fix: interpolate the resolved vault/repos paths (the PS1
    # interpolates $VaultPath/$ReposPath; the backtick escapes were a PS1
    # rendering bug). Trailing newline added to match the PS1 here-string,
    # which terminates the recent-activity line before the vault-verify line.
    vault_banner = (
        "## Vault Context\n"
        "- Vault path: %s\n"
        "- Repos path: %s\n"
        "- Notes: %d\n"
        "- Recent activity: %s\n"
        % (vault_path, repos_path, vault_note_count, recent_vault_activity)
    )

    # ── Vault existence / structure verification (T1456) ────────────────────
    try:
        status_line = vault_status_banner(project_root)
        if status_line:
            vault_banner += status_line + "\n"
    except Exception:
        pass

    # ── Stale documentation check ────────────────────────────────────────────
    stale_doc_banner = ""
    try:
        index_path = vault_path / "research" / "platforms" / "_index.yaml"
        if index_path.is_file():
            today = datetime.now()
            stale_count = 0
            for line in index_path.read_text(encoding="utf-8",
                                             errors="replace").splitlines():
                m = re.search(r"next_refresh:\s*(\d{4}-\d{2}-\d{2})", line)
                if m:
                    try:
                        refresh_date = datetime.strptime(m.group(1), "%Y-%m-%d")
                        if refresh_date < today:
                            stale_count += 1
                    except ValueError:
                        pass
            if stale_count > 0:
                stale_doc_banner = (
                    "- \U0001F4DA %d documentation note(s) overdue for "
                    "refresh — run `@g-ingest-docs REFRESH_STALE`\n"
                    % stale_count
                )
    except Exception:
        pass

    if stale_doc_banner:
        vault_banner += stale_doc_banner

    if vault_messages:
        vault_banner += "\n"
        for message in vault_messages:
            vault_banner += "- Notice: %s\n" % message

    vault_banner += "\n---\n"

    # ── Vault raw inbox check ────────────────────────────────────────────────
    try:
        raw_path = vault_path / "raw"
        if raw_path.is_dir():
            raw_files = [p for p in raw_path.iterdir()
                         if p.is_file() and p.name != "README.md"]
            if raw_files:
                vault_banner += (
                    "- \U0001F4E5 %d file(s) in vault raw/ inbox — drop "
                    "processed via `@g-vault-process-inbox` (planned) or "
                    "route manually via `g-skl-ingest-*`\n" % len(raw_files)
                )
    except Exception:
        pass

    # ── TASKS.md archive gate ────────────────────────────────────────────────
    # The gald3r_tasks_archive_gate.py skill script was absorbed into the engine
    # `gald3r task archive-gate` verb (T1665, v3 IP round). Exit codes are
    # parity-locked: 0 clean, 1 warn (>=900), 2 breach (>1200), 3 error. A
    # missing engine (old install / no binary) degrades to no banner.
    archive_gate_banner = ""
    try:
        engine = _resolve_engine_cmd(project_root)
        gate_exit = 0
        if engine is not None:
            res = _run_engine(
                engine,
                ["task", "archive-gate", "--check-only",
                 "--project-root", str(project_root)],
            )
            gate_exit = res.returncode if res is not None else 0
        if gate_exit == 2:
            archive_gate_banner = (
                "WARNING: TASKS.md ARCHIVE GATE: file exceeds 1200 lines. "
                "Run: gald3r task archive-gate --apply to archive terminal "
                "tasks.\n---\n"
            )
        elif gate_exit == 1:
            archive_gate_banner = (
                "WARNING: TASKS.md approaching archive threshold (>=900 "
                "lines). Consider: gald3r task archive-gate --apply\n---\n"
            )
    except Exception:
        pass

    # ── HEARTBEAT no_agent watchdog (T968) ───────────────────────────────────
    watchdog_banner = ""
    try:
        watchdog_banner = _run_watchdogs(project_root)
    except Exception:
        watchdog_banner = ""

    # ── Cross-project INBOX check ────────────────────────────────────────────
    inbox_banner = ""
    try:
        res = _run_sibling("g-hk-wpac-inbox-check",
                           ["-ProjectRoot", str(project_root)])
        if res is not None and res.stdout and res.stdout.strip():
            # PS1 interpolates the output-line array → lines join with spaces.
            inbox_banner = "%s\n---\n" % " ".join(res.stdout.splitlines())
    except Exception:
        pass

    # ── One-time install nudge (T1649 — prompt, not force) ──────────────────
    nudge_banner = ""
    try:
        nudge_banner = _install_nudge_banner(project_root)
    except Exception:
        nudge_banner = ""

    additional_context = (
        setup_banner + reflection_banner + vault_banner
        + archive_gate_banner + watchdog_banner + inbox_banner + nudge_banner
        + "gald3r task management system is active. Check .gald3r/TASKS.md "
          "for current tasks."
    )

    # ── Append GUARDRAILS if present ─────────────────────────────────────────
    guardrails_file = project_root / "GUARDRAILS.md"
    if guardrails_file.is_file():
        try:
            guardrails = guardrails_file.read_text(encoding="utf-8",
                                                   errors="replace")
            additional_context = "%s\n\n---\n\n%s" % (additional_context,
                                                      guardrails)
        except OSError:
            pass

    # ── Response ─────────────────────────────────────────────────────────────
    print(json.dumps({
        "continue": True,
        "additional_context": additional_context,
    }, separators=(",", ":")))
    return 0


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
