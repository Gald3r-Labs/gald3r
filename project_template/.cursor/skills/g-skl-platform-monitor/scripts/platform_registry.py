#!/usr/bin/env python3
"""Shared reader for PLATFORM_REGISTRY.yaml — the single source of truth for the
gald3r platform roster (T516).

This is the ONE place that loads the registry. Both consumers derive from it:
  * check_platform_status.py imports `known_platforms()` (no hardcoded list).
  * check_platform_status.ps1 shells out to this module's CLI (`--list` / `--json`)
    so it never re-implements YAML parsing.

The registry file lives at gald3r_templates/gald3r_core/platforms/PLATFORM_REGISTRY.yaml
in the source repo, and at <root>/.gald3r_sys/platforms/PLATFORM_REGISTRY.yaml (or a
sibling platforms/ tree) in installed projects. `find_registry()` walks up from this
script and probes the known locations; if the file is missing, `known_platforms()`
falls back to a baked-in roster so the tooling degrades gracefully instead of crashing.

CLI:
    python platform_registry.py --list            # one canonical platform name per line
    python platform_registry.py --list --all      # include alias/redundant entries
    python platform_registry.py --list --ready     # only ready (>=80%-working) platforms (T533)
    python platform_registry.py --json            # full registry as JSON
    python platform_registry.py --path            # print the resolved registry path

Readiness (T533): is_ready() / ready_platforms() / readiness_map() derive a
>=80%-working boolean from each entry's existing lifecycle + support_level fields
(ready == lifecycle `active` AND support_level tier1/tier2). The installer's
--all-ready bulk-install set is sourced from ready_platforms(); see
setup_gald3r_project.py.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Baked-in fallback roster (canonical names whose alias_of is null), kept in sync with
# PLATFORM_REGISTRY.yaml. Used ONLY when the registry file cannot be located. This is a
# safe fallback (the tooling still runs), never the primary source.
_FALLBACK_PLATFORMS: List[str] = [
    "cursor", "claude", "copilot", "codex", "antigravity", "windsurf", "gemini",
    "cline", "opencode", "openhands", "kiro", "kiro-cli", "augment", "goose",
    "junie", "openclaw", "qwen", "aider", "mistral", "warp", "replit", "deepcode",
    "trae", "kilo-code", "amp", "codebuddy", "hermes", "kimi", "qoder", "continue",
    "mimo-code", "subq", "roo", "void", "astrbot", "zcode", "zed", "pi",
]

# Readiness derivation (T533) — DERIVED from the existing lifecycle/support_level
# fields, NOT a second source of truth. A platform is "ready" (>=80%-working, safe to
# offer for default/bulk install) when its overlay is a supported, shipped IDE/agent
# target. That means lifecycle must be `active` AND support_level must be tier1/tier2.
# Everything else is installable on demand but not auto-ready: `stub` (capabilities
# untested/all-❓), tier3 weak-but-active overlays, `abandoned`/`off_target` retire
# candidates, and `redundant` aliases (no own overlay).
_READY_LIFECYCLES = frozenset({"active"})
_READY_SUPPORT_LEVELS = frozenset({"tier1", "tier2"})

# Registry locations to probe, relative to candidate roots discovered by walking up.
_REL_REGISTRY_PATHS = (
    Path("gald3r_templates") / "gald3r_core" / "platforms" / "PLATFORM_REGISTRY.yaml",
    Path("gald3r_core") / "platforms" / "PLATFORM_REGISTRY.yaml",
    Path(".gald3r_sys") / "platforms" / "PLATFORM_REGISTRY.yaml",
    Path("platforms") / "PLATFORM_REGISTRY.yaml",
)


def find_registry(start: Optional[Path] = None) -> Optional[Path]:
    """Locate PLATFORM_REGISTRY.yaml by walking up from `start` (default: this file).

    Returns the first existing path, or None if not found.
    """
    here = (start or Path(__file__)).resolve()
    roots = list(here.parents)
    for root in roots:
        for rel in _REL_REGISTRY_PATHS:
            candidate = root / rel
            if candidate.is_file():
                return candidate
    return None


def _load_yaml(text: str) -> dict:
    """Parse the registry. Prefer PyYAML; fall back to a tiny purpose-built parser
    that understands only the flat structure this registry uses (so the tooling works
    even where PyYAML is unavailable)."""
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ImportError:
        return _load_yaml_minimal(text)


def _load_yaml_minimal(text: str) -> dict:
    """Minimal parser for the specific PLATFORM_REGISTRY.yaml layout: a top-level
    `platforms:` list of `- key: value` mappings. Handles scalars, quoted strings,
    `null`, and `>-`/`>` folded blocks. NOT a general YAML parser — only the shapes
    this file uses. Comments (`# ...`) and other top-level scalars are ignored."""
    platforms: List[Dict[str, object]] = []
    lines = text.splitlines()
    i = 0
    in_platforms = False
    current: Optional[Dict[str, object]] = None

    def _scalar(raw: str) -> object:
        raw = raw.strip()
        if raw in ("null", "~", ""):
            return None
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            return raw[1:-1]
        return raw

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Detect the top-level `platforms:` key (no leading indent).
        if not in_platforms:
            if stripped == "platforms:" and not line.startswith(" "):
                in_platforms = True
            i += 1
            continue
        # Inside platforms: skip blank/comment lines.
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            # A new top-level key ends the platforms block.
            break
        if stripped.startswith("- "):
            current = {}
            platforms.append(current)
            stripped = stripped[2:]  # strip the "- "
        if current is None:
            i += 1
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val in (">-", ">", "|", "|-"):
                # Folded/literal block scalar: gather more-indented following lines.
                block: List[str] = []
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if not nxt.strip():
                        j += 1
                        continue
                    nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                    if nxt_indent <= indent:
                        break
                    block.append(nxt.strip())
                    j += 1
                current[key] = " ".join(block)
                i = j
                continue
            current[key] = _scalar(val)
        i += 1

    return {"platforms": platforms}


_CACHE: Optional[dict] = None


def load_registry(start: Optional[Path] = None) -> Optional[dict]:
    """Load and cache the parsed registry, or None if the file is missing."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    path = find_registry(start)
    if path is None:
        return None
    _CACHE = _load_yaml(path.read_text(encoding="utf-8"))
    return _CACHE


def all_entries(start: Optional[Path] = None) -> List[Dict[str, object]]:
    """Every registry entry (including alias/redundant), or [] if missing."""
    reg = load_registry(start)
    if not reg:
        return []
    return list(reg.get("platforms") or [])


def known_platforms(include_aliases: bool = False, start: Optional[Path] = None) -> List[str]:
    """The canonical roster. By default excludes alias/redundant entries (alias_of set).

    Falls back to the baked-in roster if the registry file cannot be located.
    """
    entries = all_entries(start)
    if not entries:
        return list(_FALLBACK_PLATFORMS)
    names: List[str] = []
    for e in entries:
        name = e.get("name")
        if not name:
            continue
        if not include_aliases and e.get("alias_of"):
            continue
        names.append(str(name))
    return names


def overlay_dirs(start: Optional[Path] = None) -> List[str]:
    """The set of overlay_dir values for non-alias entries (the ship roster)."""
    out: List[str] = []
    for e in all_entries(start):
        if e.get("alias_of"):
            continue
        od = e.get("overlay_dir")
        if od:
            out.append(str(od))
    return out


def is_ready(entry: Dict[str, object]) -> bool:
    """Derive the readiness flag (>=80%-working) for one registry entry (T533).

    A readiness boolean is DERIVED from the entry's existing `lifecycle` and
    `support_level` fields — the registry stays the single source of truth. Ready
    means a supported, shipped IDE/agent overlay: lifecycle `active` AND
    support_level tier1/tier2. Aliases, stubs, tier3 weak-but-active overlays, and
    abandoned/off_target retire candidates are NOT ready (still installable, just not
    offered for the default/bulk set).
    """
    if entry.get("alias_of"):
        return False
    lifecycle = str(entry.get("lifecycle") or "").strip().lower()
    support_level = str(entry.get("support_level") or "").strip().lower()
    return lifecycle in _READY_LIFECYCLES and support_level in _READY_SUPPORT_LEVELS


def readiness_map(start: Optional[Path] = None) -> Dict[str, bool]:
    """{canonical platform name: ready?} for every non-alias entry (T533)."""
    out: Dict[str, bool] = {}
    for e in all_entries(start):
        if e.get("alias_of"):
            continue
        name = e.get("name")
        if not name:
            continue
        out[str(name)] = is_ready(e)
    return out


def ready_platforms(start: Optional[Path] = None) -> List[str]:
    """Canonical names of the ready (>=80%-working) platforms only (T533).

    Falls back to the full baked-in roster if the registry cannot be located, so the
    installer still has a usable default set when the file is missing.
    """
    entries = all_entries(start)
    if not entries:
        return list(_FALLBACK_PLATFORMS)
    return [name for name, ready in readiness_map(start).items() if ready]


def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read the gald3r platform registry (single source of truth, T516)."
    )
    parser.add_argument("--list", action="store_true",
                        help="Print one canonical platform name per line.")
    parser.add_argument("--all", action="store_true",
                        help="With --list, include alias/redundant entries.")
    parser.add_argument("--ready", action="store_true",
                        help="With --list, print only ready (>=80%%-working) platforms.")
    parser.add_argument("--json", action="store_true",
                        help="Print the full registry as JSON.")
    parser.add_argument("--path", action="store_true",
                        help="Print the resolved registry file path (or NONE).")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.path:
        p = find_registry()
        print(str(p) if p else "NONE")
        return 0
    if args.json:
        reg = load_registry() or {"platforms": []}
        print(json.dumps(reg, indent=2, ensure_ascii=False))
        return 0
    # default + --list: print the roster (optionally only the ready subset)
    if args.ready:
        for name in ready_platforms():
            print(name)
        return 0
    for name in known_platforms(include_aliases=args.all):
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
