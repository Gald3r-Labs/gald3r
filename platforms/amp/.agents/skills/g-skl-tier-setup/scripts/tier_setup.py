#!/usr/bin/env python3
"""Python port of tier_setup.ps1 (T1585).

Non-interactive helper for g-skl-tier-setup SETUP and ENABLE operations.

Produces the same file outputs as the in-chat SETUP flow but from a script,
for CI or unattended installs. Not the primary entry point - prefer the
in-chat agent flow for interactive use.

SETUP mode:
  - Reads a tiers definition from a JSON file (-DefinitionPath)
  - Writes .gald3r/release_profiles/{name}.yaml for each tier
  - Scaffolds template_{name}/ directories with .gitkeep
  - Appends tier_system=enabled and tier_names=[...] to .gald3r/.identity

ENABLE mode (partial - inference only):
  - Reads .gald3r/release_profiles/*.yaml to learn tier names
  - Scans .gald3r/subsystems/*.md and reports inferred min_tier: for each
  - Writes annotations when -Apply is passed; dry-run otherwise
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO


# UTF-8-safe stdio on Windows consoles (the PS1 originals emit Unicode glyphs)
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


def _bootstrap_engine() -> bool:
    """Make ``gald3r.utils`` importable; fall back to the bundled engine source."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for parent in here.parents:
        engine_src = parent / ".gald3r_sys" / "engine" / "src"
        if engine_src.is_dir():
            sys.path.insert(0, str(engine_src))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_ENGINE = _bootstrap_engine()
try:
    from gald3r.utils import console as _console
except ImportError:
    _console = None  # graceful stdlib fallback

_ANSI = {"red": "31", "yellow": "33", "green": "32"}
_ansi_ready = False

RESERVED_TIER_NAMES = ("readme", "all", "none", "default")

# (regex, tier-kind, signal) inference rules, first match wins
INFERENCE_RULES = (
    (r"(?i)docker|docker-compose|container|OKE|kubernetes|localhost:543[23]",
     "docker", "docker"),
    (r"(?i)\bMCP\b|mcp server|mcp_tool|mcp__", "docker", "MCP"),
    (r"(?i)postgres|pgvector|oracle thick|mysql", "docker", "managed-db"),
    (r"(?i)api[_\-]?key|API Key|OPENAI_KEY|ANTHROPIC_|PERPLEXITY_",
     "api-keys", "api-keys"),
    (r"(?i)openai|anthropic|perplexity", "api-keys", "cloud-ai"),
    (r"(?i)vault_location|research/platforms|research/github|ingest[_-]doc"
     r"|crawl4ai|playwright", "api-keys", "vault-network"),
)


def _supports_color(stream: TextIO) -> bool:
    if _console is not None:
        return bool(_console.color_enabled(stream))
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def _say(msg: str = "", color: Optional[str] = None) -> None:
    global _ansi_ready
    code = _ANSI.get((color or "").lower())
    if code and _supports_color(sys.stdout):
        if os.name == "nt" and not _ansi_ready:
            os.system("")
            _ansi_ready = True
        print(f"\x1b[{code}m{msg}\x1b[0m")
    else:
        print(msg)


def test_tier_name(name: str) -> bool:
    """Validate a tier name: lowercase letters/digits/hyphens, 2-20 chars,
    not reserved."""
    if len(name) < 2 or len(name) > 20:
        return False
    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        return False
    if name.lower() in RESERVED_TIER_NAMES:
        return False
    return True


# --- SETUP -------------------------------------------------------------------

def invoke_setup(project_root: Path, profiles_dir: Path, identity_file: Path,
                 definition_path: Optional[str]) -> int:
    if not definition_path:
        _say("ERROR: -DefinitionPath required for SETUP mode.", "red")
        return 1
    def_path = Path(definition_path)
    if not def_path.exists():
        _say(f"ERROR: Definition file not found: {definition_path}", "red")
        return 1

    tiers = json.loads(def_path.read_text(encoding="utf-8-sig"))
    if isinstance(tiers, dict):
        tiers = [tiers]
    if len(tiers) < 1:
        _say("ERROR: Definition must contain at least one tier.", "red")
        return 1

    for tier in tiers:
        if not test_tier_name(str(tier.get("name", ""))):
            _say(f"ERROR: Invalid tier name '{tier.get('name', '')}' — must "
                 "be lowercase letters/digits/hyphens, 2–20 chars, not "
                 "reserved.", "red")
            return 1

    profiles_dir.mkdir(parents=True, exist_ok=True)

    # Build included_tiers cumulatively (tier N includes tiers 1..N)
    names = [str(t["name"]) for t in tiers]

    for i, tier in enumerate(tiers):
        name = str(tier["name"])
        included_tiers = ", ".join(names[:i + 1])

        op_req = tier.get("operational_requirement") or "none"
        prefix = tier.get("tier_prefix") or name[0].upper()
        remote = tier.get("remote") or ""
        destination = tier.get("destination") or "{LOCAL}"
        description = tier.get("description") or f"{name} tier"

        yaml_text = (
            f"name: {name}\n"
            f"tier_prefix: {prefix}\n"
            f"template_dir: template_{name}/\n"
            f"destination: {destination}\n"
            f"remote: {remote}\n"
            f"included_tiers: [{included_tiers}]\n"
            f"operational_requirement: {op_req}\n"
            f"description: \"{description}\"\n"
        )

        out_path = profiles_dir / f"{name}.yaml"
        out_path.write_text(yaml_text, encoding="utf-8", newline="\n")
        _say(f"  wrote {out_path}")

        # Scaffold template directory
        tpl_dir = project_root / f"template_{name}"
        if not tpl_dir.exists():
            tpl_dir.mkdir(parents=True)
            (tpl_dir / ".gitkeep").write_text("", encoding="utf-8")
            _say(f"  scaffolded {tpl_dir} (with .gitkeep)")
        else:
            _say(f"  template_{name}/ already exists — left untouched")

    # Update .gald3r/.identity
    if identity_file.exists():
        lines = [line for line in identity_file.read_text(
            encoding="utf-8-sig").splitlines()
            if not line.startswith("tier_system=")
            and not line.startswith("tier_names=")]
        lines.append("tier_system=enabled")
        lines.append(f"tier_names=[{','.join(names)}]")
        identity_file.write_text("\n".join(lines) + "\n", encoding="utf-8",
                                 newline="\n")
        _say(f"  updated {identity_file}")
    else:
        _say("WARN: .gald3r/.identity not found — create it manually with "
             "tier_system=enabled and tier_names=[...]", "yellow")

    _say("")
    _say("SETUP complete. Next: run this script with -Operation ENABLE to "
         "annotate subsystems.")
    return 0


# --- ENABLE ------------------------------------------------------------------

def invoke_enable(project_root: Path, profiles_dir: Path,
                  subsystems_dir: Path, apply: bool) -> int:
    if not profiles_dir.exists():
        _say("ERROR: .gald3r/release_profiles/ not found — run SETUP first.",
             "red")
        return 1
    if not subsystems_dir.exists():
        _say("ERROR: .gald3r/subsystems/ not found — no subsystems to "
             "annotate.", "red")
        return 1

    # Parse tiers
    tier_list: List[Dict[str, Any]] = []
    for profile in sorted(profiles_dir.glob("*.yaml")):
        content = profile.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r"(?m)^name:\s*(.+)$", content)
        name = m.group(1).strip() if m else profile.stem
        m = re.search(r"(?m)^operational_requirement:\s*(.+)$", content)
        op_req = m.group(1).strip() if m else "none"
        included_count = 0
        m = re.search(r"(?m)^included_tiers:\s*\[([^\]]+)\]", content)
        if m:
            included_count = len(m.group(1).split(","))
        tier_list.append({"name": name, "op_req": op_req,
                          "included_count": included_count})

    # Sort ascending by included_tiers count (lowest tier first)
    tier_list.sort(key=lambda t: t["included_count"])
    default_tier = tier_list[0]["name"]
    api_keys_tier = next((t["name"] for t in tier_list
                          if t["op_req"] == "api-keys"), None)
    docker_tier = next((t["name"] for t in tier_list
                        if t["op_req"] == "docker"), None)

    if not api_keys_tier:
        api_keys_tier = tier_list[-1]["name"]
    if not docker_tier:
        docker_tier = tier_list[-1]["name"]

    tier_for = {"docker": docker_tier, "api-keys": api_keys_tier}

    _say("Tier list (lowest -> highest): "
         + " -> ".join(t["name"] for t in tier_list))
    _say(f"Default tier (no signals):     {default_tier}")
    _say(f"API-keys tier:                 {api_keys_tier}")
    _say(f"Docker tier:                   {docker_tier}")
    _say("")

    results: List[Dict[str, Any]] = []

    for spec in sorted(subsystems_dir.glob("*.md")):
        content = spec.read_text(encoding="utf-8-sig", errors="replace")
        inferred = default_tier
        signals: List[str] = []

        for pattern, tier_kind, signal in INFERENCE_RULES:
            if re.search(pattern, content):
                inferred = tier_for[tier_kind]
                signals.append(signal)
                break

        # Check existing min_tier
        existing: Optional[str] = None
        m = re.search(r"(?m)^min_tier:\s*(\S+)", content)
        if m:
            existing = m.group(1).strip()

        results.append({
            "file": spec.name,
            "existing": existing,
            "inferred": inferred,
            "signals": ",".join(signals),
            "will_change": existing != inferred,
        })

    _say("Inference results:")
    for r in results:
        if r["existing"] is None:
            label = "NEW"
        elif r["will_change"]:
            label = f"CHANGE {r['existing']}->{r['inferred']}"
        else:
            label = f"OK ({r['existing']})"
        sig = f"[{r['signals']}]" if r["signals"] else ""
        _say(f"  {str(r['file']).ljust(48)} {label} {sig}")

    if not apply:
        _say("")
        _say("Dry run. Pass -Apply to write min_tier: annotations.")
        return 0

    # Apply annotations
    written = 0
    for r in results:
        if not r["will_change"] and r["existing"]:
            continue
        path = subsystems_dir / str(r["file"])
        content = path.read_text(encoding="utf-8-sig", errors="replace")

        if re.search(r"(?m)^min_tier:\s*\S+", content):
            content = re.sub(r"(?m)^min_tier:\s*\S+",
                             f"min_tier: {r['inferred']}", content)
        else:
            # Insert after 'name:' line (CRLF parity with the PS1)
            content = re.sub(r"(?m)(^name:\s*.+$)",
                             "\\1\r\nmin_tier: " + str(r["inferred"]),
                             content, count=1)

        path.write_text(content, encoding="utf-8", newline="")
        written += 1

    _say("")
    _say(f"Wrote {written} subsystem annotations.")

    # Run tier sync if available: prefer .py sibling, else pwsh the .ps1
    sync_base = project_root / "custom_scripts" / "platform_parity_sync"
    sync_py = sync_base.with_suffix(".py")
    sync_ps1 = sync_base.with_suffix(".ps1")
    if sync_py.exists():
        _say("Running platform_parity_sync.py -TierSync...")
        subprocess.run([sys.executable, str(sync_py), "-TierSync"])
    elif sync_ps1.exists():
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if shell:
            _say("Running platform_parity_sync.ps1 -TierSync...")
            subprocess.run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass",
                            "-File", str(sync_ps1), "-TierSync"])
        else:
            _say("WARN: PowerShell not available — tier sync skipped.",
                 "yellow")
    else:
        _say("WARN: custom_scripts/platform_parity_sync.ps1 not found — "
             "tier sync skipped.", "yellow")
    return 0


# --- Main ----------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Non-interactive helper for g-skl-tier-setup SETUP and "
                    "ENABLE operations.")
    parser.add_argument("-Operation", "--operation", dest="operation",
                        required=True, type=str.upper,
                        choices=["SETUP", "ENABLE"],
                        help="SETUP | ENABLE")
    parser.add_argument("-DefinitionPath", "--definition-path",
                        dest="definition_path", default=None,
                        help="Path to a JSON file describing tiers "
                             "(SETUP only)")
    parser.add_argument("-Apply", "--apply", dest="apply",
                        action="store_true",
                        help="ENABLE only — actually write min_tier: "
                             "annotations")
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root",
                        default=None,
                        help="Optional project root path override")
    args = parser.parse_args(argv)

    if args.project_root:
        project_root = Path(args.project_root)
    else:
        # Parity with the PS1: five directories up from the scripts folder.
        here = Path(__file__).resolve().parent
        project_root = (here / ".." / ".." / ".." / ".." / "..").resolve()

    if not (project_root / ".gald3r").exists():
        _say(f"ERROR: .gald3r/ not found at {project_root} — run @g-setup "
             "first.", "red")
        return 1

    profiles_dir = project_root / ".gald3r" / "release_profiles"
    identity_file = project_root / ".gald3r" / ".identity"
    subsystems_dir = project_root / ".gald3r" / "subsystems"

    if args.operation == "SETUP":
        return invoke_setup(project_root, profiles_dir, identity_file,
                            args.definition_path)
    return invoke_enable(project_root, profiles_dir, subsystems_dir,
                         args.apply)


if __name__ == "__main__":
    sys.exit(main())
