"""Plugin lifecycle ops — INSTALL / REMOVE / LIST / NEW / CHECK_COMPAT / UPDATE (T663).

The Python/engine reimplementation of the gald3r plugin system designed in ADR-015 /
SS-007 and documented operationally by the `g-skl-plugins` skill. Only the PowerShell
`UPDATE` op shipped historically (`.gald3r_sys/plugins/scripts/update_plugin.ps1`); the
`INSTALL / REMOVE / LIST / NEW / CHECK_COMPAT` scripts were designed-but-never-ported and
the old PS scripts were retired (BUG-128/129/130). This module makes the full lifecycle a
first-class engine surface (single source of truth for the manifest schema, registry, and
the `installed.yaml` ledger) so every adapter (CLI, MCP, Throne, marketplace) calls the
same code path — no copied PowerShell, no forked schema.

A **plugin** is a self-contained, versioned directory under
``.gald3r_sys/plugins/<id>/`` that bundles any subset of gald3r's five component types
(skills, commands, agents, rules, hooks) plus one declarative ``gald3r-plugin.yaml``
manifest. Installing is **additive**: components are copied into the canonical component
dirs and stamped with a ``plugin_source: <id>`` provenance tag; gald3r-core components are
NEVER overwritten (conflict = abort, ADR-015 D6). Lifecycle scripts
(``install.ps1`` / ``uninstall.ps1`` / ``upgrade.ps1``) are data-declared but NEVER
auto-run (ADR-015 D7) — this engine surface deliberately does not execute them.

State files (match the SKILL.md / PS-update contract exactly):

  =====================================================  ===================================
  ``.gald3r_sys/plugins/<id>/gald3r-plugin.yaml``        per-plugin manifest (data-only)
  ``.gald3r_sys/plugins/<id>/``                          versioned, inspectable plugin source
  ``.gald3r_sys/plugins/installed.yaml``                 install ledger (truth for remove/update)
  ``.gald3r_sys/config/plugins.yaml``                    host config (``registry_url:`` override)
  ``.gald3r_sys/VERSION``                                host floor compared to ``gald3r_min_version``
  =====================================================  ===================================

Pure stdlib + ``pyyaml`` (already an engine dependency) + the shared :mod:`gald3r.store`
frontmatter helpers — re-implements nothing that already exists in the engine. Remote
``https://`` registry sources are NOT downloaded by this module (matching the historical
local-path-only behavior on this tree and the engine's no-daemon discipline); a local-path
or already-vendored ``.gald3r_sys/plugins/<id>/`` source is the supported install path.

@subsystems: PLATFORM_INTEGRATION
"""
from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ── component layout (ADR-015 component mapping) ───────────────────────────────

#: plugin subdir -> canonical ``.gald3r_sys/`` target dir. ``skills`` is folder-per-skill
#: (each ``skills/<name>/`` copies whole); the rest are flat files.
COMPONENT_DIRS: Dict[str, str] = {
    "skills": "skills",
    "commands": "commands",
    "agents": "agents",
    "rules": "rules",
    "hooks": "hooks",
}

#: Markdown component types whose copied files get a ``plugin_source:`` frontmatter stamp.
_MARKDOWN_TYPES = ("commands", "agents", "rules")

#: PowerShell component type; gets a ``# plugin_source:`` header-comment stamp.
_PS_TYPE = "hooks"

#: Manifest filename at a plugin root (data-only YAML).
MANIFEST_NAME = "gald3r-plugin.yaml"

#: Install-ledger filename under ``.gald3r_sys/plugins/``.
LEDGER_NAME = "installed.yaml"

#: Host-config filename (``registry_url:`` override) under ``.gald3r_sys/config/``.
HOST_CONFIG_NAME = "plugins.yaml"

#: Default registry URL (informational; remote fetch is not performed by this engine).
DEFAULT_REGISTRY_URL = (
    "https://raw.githubusercontent.com/gald3r/plugin-registry/main/registry.json"
)

#: A valid plugin id: kebab-case, must match the dir name + ledger key (ADR-015).
_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: Lenient SemVer (``X``, ``X.Y``, ``X.Y.Z`` with optional ``-pre`` / ``+build``).
_SEMVER_RE = re.compile(r"^\d+(?:\.\d+){0,2}(?:[-+].*)?$")


class PluginError(Exception):
    """Raised when a plugin op cannot proceed (bad manifest, conflict, missing source)."""


# ── manifest + compat (the schema is here; nothing else redefines it) ──────────


def _parse_semver(v: Optional[str]) -> tuple:
    """Parse a lenient SemVer into a comparable ``(major, minor, patch)`` tuple.

    Mirrors :func:`gald3r.systems.upgrade._parse_semver` so the engine orders plugin
    versions the same way it orders its own. Tolerant of pre-release / build suffixes.
    """
    if not v:
        return (0, 0, 0)
    main = str(v).split("+")[0].split("-")[0]
    out: List[int] = []
    for part in main.split("."):
        digits = ""
        for ch in part:
            if ch.isdigit():
                digits += ch
            else:
                break
        out.append(int(digits) if digits else 0)
    while len(out) < 3:
        out.append(0)
    return (out[0], out[1], out[2])


def load_manifest(plugin_dir: Path) -> Dict[str, Any]:
    """Read + parse ``<plugin_dir>/gald3r-plugin.yaml`` into a dict.

    Raises :class:`PluginError` when the manifest is missing or not a YAML mapping. Does
    NOT validate field semantics — that is :func:`check_compat`'s job.
    """
    manifest = Path(plugin_dir) / MANIFEST_NAME
    if not manifest.is_file():
        raise PluginError(f"no {MANIFEST_NAME} in {plugin_dir}")
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8-sig"))
    except yaml.YAMLError as e:
        raise PluginError(f"malformed {MANIFEST_NAME} in {plugin_dir}: {e}") from e
    if not isinstance(data, dict):
        raise PluginError(f"{MANIFEST_NAME} in {plugin_dir} is not a YAML mapping")
    return data


def validate_manifest(manifest: Dict[str, Any]) -> List[str]:
    """Validate a manifest dict against the ADR-015 schema. Returns a list of reasons.

    Empty list == the manifest is schema-valid. Hard-required fields are ``id`` + ``version``
    (mirrors the historical validator's minimal check); ``id`` must be kebab-case and
    ``version`` / ``gald3r_min_version`` must be SemVer. ``components`` (when present) must
    name only known component types.
    """
    reasons: List[str] = []
    pid = manifest.get("id")
    if not pid:
        reasons.append("missing required field: id")
    elif not _ID_RE.match(str(pid)):
        reasons.append(f"id '{pid}' is not kebab-case (a-z, 0-9, single hyphens)")
    ver = manifest.get("version")
    if not ver:
        reasons.append("missing required field: version")
    elif not _SEMVER_RE.match(str(ver)):
        reasons.append(f"version '{ver}' is not SemVer")
    floor = manifest.get("gald3r_min_version")
    if floor is not None and not _SEMVER_RE.match(str(floor)):
        reasons.append(f"gald3r_min_version '{floor}' is not SemVer")
    components = manifest.get("components")
    if components is not None:
        if not isinstance(components, dict):
            reasons.append("components must be a mapping of component-type -> [files]")
        else:
            for ctype in components:
                if ctype not in COMPONENT_DIRS:
                    reasons.append(
                        f"unknown component type '{ctype}' "
                        f"(expected one of {sorted(COMPONENT_DIRS)})"
                    )
    return reasons


# ── the system ─────────────────────────────────────────────────────────────────


class PluginSystem:
    """Plugin lifecycle ops for one project, attached to the facade as ``g.plugins``.

    All ops resolve paths under ``<root>/.gald3r_sys/``. The class owns the manifest schema,
    the ``installed.yaml`` ledger, and the compat gate; every public op returns a plain dict
    the CLI / MCP render directly. No op executes lifecycle scripts (ADR-015 D7).
    """

    def __init__(self, config):
        self.config = config
        self.root = config.root
        self.sys_dir = self.root / ".gald3r_sys"
        self.plugins_dir = self.sys_dir / "plugins"
        self.ledger_path = self.plugins_dir / LEDGER_NAME

    # ---- host version (compat floor) ----
    @property
    def host_version(self) -> str:
        """The host framework version (``.gald3r_sys/VERSION``), or the project's identity
        version as a fallback. This is the floor ``gald3r_min_version`` is compared against."""
        vf = self.sys_dir / "VERSION"
        if vf.is_file():
            txt = vf.read_text(encoding="utf-8-sig").strip()
            if txt:
                return txt
        return self.config.gald3r_rel_version

    # ---- ledger I/O ----
    def _read_ledger(self) -> Dict[str, Any]:
        """Read ``installed.yaml`` -> ``{<id>: {version, source, installed_at, components}}``."""
        if not self.ledger_path.is_file():
            return {}
        try:
            data = yaml.safe_load(self.ledger_path.read_text(encoding="utf-8-sig"))
        except yaml.YAMLError as e:
            raise PluginError(f"malformed {LEDGER_NAME}: {e}") from e
        if not isinstance(data, dict):
            return {}
        plugins = data.get("plugins")
        return plugins if isinstance(plugins, dict) else {}

    def _write_ledger(self, plugins: Dict[str, Any]) -> None:
        """Write ``installed.yaml`` deterministically (LF, no BOM), matching the PS shape."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        lines = ["# gald3r plugin install ledger (installed.yaml) -- ADR-015", "plugins:"]
        if not plugins:
            lines.append("  {}")
        for pid in sorted(plugins):
            entry = plugins[pid] or {}
            lines.append(f"  {pid}:")
            for key in ("version", "source", "installed_at"):
                if entry.get(key) is not None:
                    lines.append(f"    {key}: {entry[key]}")
            comps = entry.get("components") or {}
            if comps:
                lines.append("    components:")
                for ctype in sorted(comps):
                    items = comps[ctype] or []
                    lines.append(f"      {ctype}:")
                    for it in items:
                        lines.append(f"        - {it}")
        text = "\n".join(lines) + "\n"
        with open(self.ledger_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    # ---- registry config ----
    def _registry_url(self) -> str:
        """Resolve the configured registry URL (``plugins.yaml registry_url:`` or default)."""
        cfg = self.sys_dir / "config" / HOST_CONFIG_NAME
        if cfg.is_file():
            try:
                data = yaml.safe_load(cfg.read_text(encoding="utf-8-sig"))
            except yaml.YAMLError:
                data = None
            if isinstance(data, dict) and data.get("registry_url"):
                return str(data["registry_url"])
        return DEFAULT_REGISTRY_URL

    # ---- component inventory + provenance ----
    @staticmethod
    def _inventory(plugin_dir: Path) -> Dict[str, List[str]]:
        """Scan a plugin source dir for the components it actually ships (by file/dir name).

        skills -> the names of ``skills/<name>/`` subdirs; the rest -> the filenames under
        ``<type>/``. This is the authoritative component set (the manifest's ``components:``
        is informational; the files on disk are what install copies, ADR-015).
        """
        out: Dict[str, List[str]] = {}
        for ctype, _ in COMPONENT_DIRS.items():
            src = plugin_dir / ctype
            if not src.is_dir():
                continue
            if ctype == "skills":
                names = sorted(d.name for d in src.iterdir() if d.is_dir())
            else:
                names = sorted(f.name for f in src.iterdir() if f.is_file())
            if names:
                out[ctype] = names
        return out

    def _canonical_target(self, ctype: str, name: str) -> Path:
        """The canonical ``.gald3r_sys/<type>/<name>`` path a component is copied to."""
        return self.sys_dir / COMPONENT_DIRS[ctype] / name

    @staticmethod
    def _has_provenance(path: Path, plugin_id: str) -> bool:
        """True when ``path`` (file or skill dir) still carries this plugin's provenance tag.

        For a skill dir, the tag lives in its ``SKILL.md``. Removal only deletes files that
        still carry the matching ``plugin_source:`` so gald3r-core + other plugins' files
        are never touched (ADR-015 D6).
        """
        target = path / "SKILL.md" if path.is_dir() else path
        if not target.is_file():
            return False
        try:
            text = target.read_text(encoding="utf-8-sig")
        except OSError:
            return False
        return bool(re.search(rf"plugin_source:\s*{re.escape(plugin_id)}\b", text))

    @staticmethod
    def _stamp_provenance(path: Path, ctype: str, plugin_id: str) -> None:
        """Stamp ``plugin_source: <id>`` into a freshly-copied component (idempotent)."""
        if ctype == "skills":
            target = path / "SKILL.md"
        else:
            target = path
        if not target.is_file():
            return
        text = target.read_text(encoding="utf-8-sig")
        if re.search(rf"plugin_source:\s*{re.escape(plugin_id)}\b", text):
            return  # already stamped
        if ctype == _PS_TYPE:
            stamp = f"# plugin_source: {plugin_id}\n"
            lines = text.splitlines(keepends=True)
            # insert after a leading shebang / first comment block, else at top
            idx = 0
            for i, ln in enumerate(lines[:15]):
                if ln.lstrip().startswith("#"):
                    idx = i + 1
                else:
                    break
            lines.insert(idx, stamp)
            new = "".join(lines)
        else:  # markdown: add to frontmatter if present, else prepend a frontmatter block
            m = re.match(r"^(﻿?---\r?\n)(.*?)(\r?\n---\r?\n)(.*)$", text, re.S)
            if m:
                new = m.group(1) + m.group(2) + f"\nplugin_source: {plugin_id}" + m.group(3) + m.group(4)
            else:
                new = f"---\nplugin_source: {plugin_id}\n---\n\n" + text
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)

    # ---- source resolution ----
    def _resolve_source(self, source: str) -> Path:
        """Resolve an INSTALL ``source`` to a local plugin dir (containing a manifest).

        Accepts an absolute/relative local path to a plugin dir, or a versioned subdir
        ``<source>/<version>`` is NOT auto-descended here (the caller passes the concrete
        dir). Remote ``https://`` sources are rejected — this engine does not fetch (matching
        the local-path-only behavior on this tree). Raises :class:`PluginError` otherwise.
        """
        s = str(source)
        if s.startswith(("http://", "https://")):
            raise PluginError(
                f"remote source not supported by the engine installer: {s}. "
                "Vendor the plugin under .gald3r_sys/plugins/<id>/ or pass a local path."
            )
        cand = Path(s)
        if not cand.is_absolute():
            cand = (self.root / cand).resolve()
        if not cand.is_dir():
            raise PluginError(f"source is not a directory: {cand}")
        if not (cand / MANIFEST_NAME).is_file():
            raise PluginError(f"no {MANIFEST_NAME} at source: {cand}")
        return cand

    # ================= OPERATIONS =================

    # ---- CHECK_COMPAT ----
    def check_compat(self, plugin_dir: Path) -> Dict[str, Any]:
        """Validate a plugin's manifest against the schema + the host compat floor.

        Returns ``{"ok": bool, "id", "version", "gald3r_min_version", "host_version",
        "reasons": [...]}``. ``ok`` is True only when the manifest is schema-valid AND
        ``gald3r_min_version`` (if set) <= the host VERSION. Each failure is a clear reason
        string. Never raises for a present-but-invalid manifest (the reasons carry the
        verdict); only a missing/unreadable manifest raises (via :func:`load_manifest`).
        """
        manifest = load_manifest(plugin_dir)
        reasons = validate_manifest(manifest)
        floor = manifest.get("gald3r_min_version")
        host = self.host_version
        if floor and _parse_semver(str(floor)) > _parse_semver(host):
            reasons.append(
                f"requires gald3r >= {floor} but host is {host} (gald3r_min_version floor)"
            )
        return {
            "ok": not reasons,
            "id": manifest.get("id"),
            "version": manifest.get("version"),
            "gald3r_min_version": floor,
            "host_version": host,
            "reasons": reasons,
        }

    # ---- INSTALL ----
    def install(self, source: str, *, dry_run: bool = False) -> Dict[str, Any]:
        """Install a plugin from a local source dir into the project (idempotent).

        Flow: resolve source -> validate manifest + compat -> conflict-abort against
        gald3r-core (D6) -> copy components into the canonical dirs + stamp ``plugin_source:``
        -> record the ``installed.yaml`` ledger entry. Re-installing the same id+version is a
        no-op (``status="already_installed"``); installing a different version re-materializes
        (REMOVE-then-copy of this plugin's own files). NEVER auto-runs ``install.ps1`` (D7).

        Args:
            source: A local path to a plugin dir holding a ``gald3r-plugin.yaml``.
            dry_run: Plan only — validate + report the component plan, write nothing.

        Returns a result dict: ``{ok, status, id, version, components, conflicts, reasons,
        dry_run}``.
        """
        src = self._resolve_source(source)
        compat = self.check_compat(src)
        if not compat["ok"]:
            return {
                "ok": False, "status": "incompatible", "id": compat["id"],
                "version": compat["version"], "components": {}, "conflicts": [],
                "reasons": compat["reasons"], "dry_run": dry_run,
            }
        manifest = load_manifest(src)
        pid = str(manifest["id"])
        version = str(manifest["version"])
        if pid != src.name and not str(source).startswith(("http://", "https://")):
            # ADR-015: id MUST match the plugin dir name. A vendored dir named after the id
            # is the norm; a mismatched local path is a manifest/layout error.
            return {
                "ok": False, "status": "id_dir_mismatch", "id": pid, "version": version,
                "components": {}, "conflicts": [],
                "reasons": [f"manifest id '{pid}' != source dir name '{src.name}'"],
                "dry_run": dry_run,
            }
        inventory = self._inventory(src)

        ledger = self._read_ledger()
        existing = ledger.get(pid)
        if existing and str(existing.get("version")) == version:
            return {
                "ok": True, "status": "already_installed", "id": pid, "version": version,
                "components": existing.get("components", {}), "conflicts": [],
                "reasons": [], "dry_run": dry_run,
            }

        # D6 conflict-abort: a canonical target that exists but is NOT owned by this plugin
        # (no matching plugin_source:) is a gald3r-core or other-plugin file -> abort.
        conflicts: List[str] = []
        for ctype, names in inventory.items():
            for name in names:
                target = self._canonical_target(ctype, name)
                if target.exists() and not self._has_provenance(target, pid):
                    conflicts.append(f"{ctype}/{name}")
        if conflicts:
            return {
                "ok": False, "status": "conflict", "id": pid, "version": version,
                "components": inventory, "conflicts": sorted(conflicts),
                "reasons": [f"would overwrite non-plugin component(s): {sorted(conflicts)}"],
                "dry_run": dry_run,
            }

        if dry_run:
            return {
                "ok": True, "status": "planned", "id": pid, "version": version,
                "components": inventory, "conflicts": [], "reasons": [], "dry_run": True,
            }

        # If a different version of this plugin is installed, clear its old files first
        # (re-materialize). Safe: only removes files still carrying this plugin's provenance.
        if existing:
            self._remove_components(pid, existing.get("components", {}))

        copied = self._copy_components(src, pid, inventory)
        ledger[pid] = {
            "version": version,
            "source": str(source),
            "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "components": copied,
        }
        self._write_ledger(ledger)
        return {
            "ok": True, "status": "installed", "id": pid, "version": version,
            "components": copied, "conflicts": [], "reasons": [], "dry_run": False,
        }

    def _copy_components(self, src: Path, pid: str, inventory: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Copy a plugin's components into the canonical dirs + stamp provenance."""
        copied: Dict[str, List[str]] = {}
        for ctype, names in inventory.items():
            for name in names:
                source_path = src / ctype / name
                target = self._canonical_target(ctype, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                if ctype == "skills":
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(source_path, target)
                else:
                    shutil.copy2(source_path, target)
                self._stamp_provenance(target, ctype, pid)
                copied.setdefault(ctype, []).append(name)
        return copied

    # ---- REMOVE ----
    def remove(self, plugin_id: str, *, dry_run: bool = False) -> Dict[str, Any]:
        """Uninstall a plugin cleanly (ledger + component files). Safe on a missing plugin.

        Uses ``installed.yaml`` as the record of truth (D4). Deletes only component files
        that still carry this plugin's ``plugin_source:`` provenance, so gald3r-core and
        other plugins' files are never touched (D6). Removing an absent plugin is a no-op
        (``status="not_installed"``). NEVER auto-runs ``uninstall.ps1`` (D7).

        Returns ``{ok, status, id, removed, skipped, dry_run}`` where ``removed`` lists the
        canonical paths deleted and ``skipped`` lists owned-by-ledger files that were left in
        place because their provenance no longer matched (modified/replaced after install).
        """
        pid = str(plugin_id)
        ledger = self._read_ledger()
        entry = ledger.get(pid)
        if entry is None:
            return {"ok": True, "status": "not_installed", "id": pid,
                    "removed": [], "skipped": [], "dry_run": dry_run}
        components = entry.get("components", {}) or {}
        if dry_run:
            planned, skipped = self._plan_remove(pid, components)
            return {"ok": True, "status": "planned", "id": pid,
                    "removed": planned, "skipped": skipped, "dry_run": True}
        removed, skipped = self._remove_components(pid, components)
        del ledger[pid]
        self._write_ledger(ledger)
        return {"ok": True, "status": "removed", "id": pid,
                "removed": removed, "skipped": skipped, "dry_run": False}

    def _plan_remove(self, pid: str, components: Dict[str, List[str]]):
        """Compute (would-remove, would-skip) without touching disk."""
        planned: List[str] = []
        skipped: List[str] = []
        for ctype, names in components.items():
            if ctype not in COMPONENT_DIRS:
                continue
            for name in names:
                target = self._canonical_target(ctype, name)
                rel = f"{COMPONENT_DIRS[ctype]}/{name}"
                if target.exists() and self._has_provenance(target, pid):
                    planned.append(rel)
                elif target.exists():
                    skipped.append(rel)  # exists but provenance no longer matches
        return planned, skipped

    def _remove_components(self, pid: str, components: Dict[str, List[str]]):
        """Delete this plugin's provenance-owned component files. Returns (removed, skipped)."""
        removed: List[str] = []
        skipped: List[str] = []
        for ctype, names in components.items():
            if ctype not in COMPONENT_DIRS:
                continue
            for name in names:
                target = self._canonical_target(ctype, name)
                rel = f"{COMPONENT_DIRS[ctype]}/{name}"
                if not target.exists():
                    continue
                if not self._has_provenance(target, pid):
                    skipped.append(rel)  # modified/replaced post-install -> preserve
                    continue
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                removed.append(rel)
        return removed, skipped

    # ---- LIST ----
    def list(self) -> Dict[str, Any]:
        """List installed plugins (ledger) with id, version, source, and components.

        Each entry also carries a live ``compat`` verdict re-derived from the plugin's
        on-disk manifest when its source dir is still present under ``.gald3r_sys/plugins/``
        (so a host upgrade that breaks a floor surfaces here). Returns
        ``{registry_url, installed: [ {id, version, source, installed_at, components,
        compat} ]}``.
        """
        ledger = self._read_ledger()
        installed: List[Dict[str, Any]] = []
        for pid in sorted(ledger):
            entry = ledger[pid] or {}
            compat: Optional[Dict[str, Any]] = None
            src_dir = self.plugins_dir / pid
            if (src_dir / MANIFEST_NAME).is_file():
                try:
                    c = self.check_compat(src_dir)
                    compat = {"ok": c["ok"], "reasons": c["reasons"]}
                except PluginError as e:
                    compat = {"ok": False, "reasons": [str(e)]}
            installed.append({
                "id": pid,
                "version": entry.get("version"),
                "source": entry.get("source"),
                "installed_at": entry.get("installed_at"),
                "components": entry.get("components", {}),
                "compat": compat,
            })
        return {"registry_url": self._registry_url(), "installed": installed}

    # ---- NEW ----
    def new(self, plugin_id: str, *, name: str = "", author: str = "",
            subsystem: str = "PLATFORM_INTEGRATION", force: bool = False) -> Dict[str, Any]:
        """Scaffold a new plugin skeleton under ``.gald3r_sys/plugins/<id>/`` from a template.

        Creates the plugin dir with a starter ``gald3r-plugin.yaml`` (data-only, with ``id`` +
        ``version`` + the inherited ``default_subsystem``), a ``CHANGELOG.md``, and empty
        component subdirs (skills/commands/agents/rules/hooks). Refuses to clobber an existing
        non-empty dir unless ``force=True``. Returns ``{ok, id, path, created, reasons}``.
        """
        pid = str(plugin_id)
        if not _ID_RE.match(pid):
            return {"ok": False, "id": pid, "path": None, "created": [],
                    "reasons": [f"id '{pid}' is not kebab-case (a-z, 0-9, single hyphens)"]}
        plugin_dir = self.plugins_dir / pid
        if plugin_dir.exists() and any(plugin_dir.iterdir()) and not force:
            return {"ok": False, "id": pid, "path": str(plugin_dir), "created": [],
                    "reasons": [f"plugin dir already exists and is non-empty: {plugin_dir} "
                                "(pass force=True to overwrite)"]}
        plugin_dir.mkdir(parents=True, exist_ok=True)
        created: List[str] = []

        manifest_text = (
            f"# gald3r-plugin.yaml\n"
            f"id: {pid}\n"
            f"version: 0.1.0\n"
            f"name: {name or pid}\n"
            f"description: TODO describe what this plugin ships.\n"
            f"author: {author or 'unknown'}\n"
            f"license: MIT\n"
            f"gald3r_min_version: {self.host_version}\n"
            f"default_subsystem: {subsystem}\n"
            f"components: {{}}\n"
        )
        (plugin_dir / MANIFEST_NAME).write_text(manifest_text, encoding="utf-8", newline="\n")
        created.append(MANIFEST_NAME)

        changelog = (
            f"# Changelog — {name or pid}\n\n"
            "All notable changes to this plugin are documented here (Keep a Changelog).\n\n"
            "## [0.1.0]\n\n### Added\n- Initial scaffold.\n"
        )
        (plugin_dir / "CHANGELOG.md").write_text(changelog, encoding="utf-8", newline="\n")
        created.append("CHANGELOG.md")

        for ctype in COMPONENT_DIRS:
            sub = plugin_dir / ctype
            sub.mkdir(parents=True, exist_ok=True)
            (sub / ".gitkeep").write_text("", encoding="utf-8", newline="\n")
            created.append(f"{ctype}/.gitkeep")

        return {"ok": True, "id": pid, "path": str(plugin_dir),
                "created": created, "reasons": []}

    # ---- UPDATE ----
    def update(self, plugin_id: str, *, source: Optional[str] = None,
               force: bool = False, dry_run: bool = False) -> Dict[str, Any]:
        """Re-apply / move an installed plugin to a newer (or forced) version from a source.

        The Python equivalent of the historical ``update_plugin.ps1`` for local sources:
        validate + compat-check the source, compare versions against the ledger, and (unless
        ``dry_run``) re-materialize via :meth:`install` (which removes this plugin's stale
        files then copies the new ones and rewrites the ledger). ``source`` defaults to the
        already-vendored ``.gald3r_sys/plugins/<id>/`` dir. ``force=True`` re-installs even
        when already at the source version.

        Returns ``{ok, status, id, from_version, to_version, components, reasons, dry_run}``.
        """
        pid = str(plugin_id)
        ledger = self._read_ledger()
        entry = ledger.get(pid)
        if entry is None:
            return {"ok": False, "status": "not_installed", "id": pid,
                    "from_version": None, "to_version": None, "components": {},
                    "reasons": [f"plugin '{pid}' is not installed"], "dry_run": dry_run}
        from_version = str(entry.get("version"))
        src = self._resolve_source(source) if source else (self.plugins_dir / pid)
        if not (src / MANIFEST_NAME).is_file():
            return {"ok": False, "status": "no_source", "id": pid,
                    "from_version": from_version, "to_version": None, "components": {},
                    "reasons": [f"no source manifest for '{pid}' (looked at {src})"],
                    "dry_run": dry_run}
        compat = self.check_compat(src)
        if not compat["ok"]:
            return {"ok": False, "status": "incompatible", "id": pid,
                    "from_version": from_version, "to_version": compat["version"],
                    "components": {}, "reasons": compat["reasons"], "dry_run": dry_run}
        to_version = str(compat["version"])
        same = _parse_semver(to_version) == _parse_semver(from_version)
        if same and not force:
            return {"ok": True, "status": "up_to_date", "id": pid,
                    "from_version": from_version, "to_version": to_version,
                    "components": entry.get("components", {}), "reasons": [], "dry_run": dry_run}
        if dry_run:
            inventory = self._inventory(src)
            return {"ok": True, "status": "planned", "id": pid,
                    "from_version": from_version, "to_version": to_version,
                    "components": inventory, "reasons": [], "dry_run": True}
        res = self.install(str(src), dry_run=False)
        status = "forced" if (same and force) else "updated"
        return {"ok": res["ok"], "status": status if res["ok"] else res["status"],
                "id": pid, "from_version": from_version, "to_version": to_version,
                "components": res.get("components", {}),
                "reasons": res.get("reasons", []), "dry_run": False}
