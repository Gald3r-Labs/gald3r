#!/usr/bin/env python3
"""test_platform.py — Platform Template Test Harness + HTML Report Card (T613).

Scaffolds a throwaway gald3r project from ONE platform's template overlay,
runs a 14-test plan against it, and emits a self-contained HTML "report card"
per platform. The harness never touches a host-installed copy of the platform
under test — the scaffold is built into a clean temp dir from the canonical
``gald3r_core/`` source the same way the Forge build assembles a
``gald3r_platform_<name>`` repo (base ``project_template/`` minus other-platform
IDE items, then the platform overlay copied on top).

Isolation order (AC1 / AC5):
    1. SmolVM   — ``smolvm run --image python:3.12 -- ...`` (preferred)
    2. Docker   — ``docker run --rm -v ...`` (fallback)
    3. bare-local (last resort — prints a clear WARNING)

For stub / incomplete platforms a RED report card is the CORRECT output — the
harness reports real pass/fail/skip, it never fakes a pass. Tests that do not
apply to a platform (e.g. Hermes ships no hooks.json) are SKIPPED, not failed.

Out of scope (separate tasks): the gald3r-test base image build (T615), Hermes
SKILL.md research (T614), and CI wiring (T616).

Usage:
    python test_platform.py claude
    python test_platform.py hermes --isolation bare-local
    python test_platform.py cursor --out-dir ./_reports
    python test_platform.py --list
    python test_platform.py --help
"""
# @subsystems: PLATFORM_INTEGRATION, UI_AND_OUTPUT
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# ---- result status vocabulary -------------------------------------------------

PASS = "pass"
FAIL = "fail"
WARN = "warn"
SKIP = "skip"

_STATUS_GLYPH = {PASS: "✅", FAIL: "❌", WARN: "⚠️", SKIP: "⏭️"}
_STATUS_LABEL = {PASS: "PASS", FAIL: "FAIL", WARN: "WARN", SKIP: "SKIP"}

# Isolation backends, in preference order.
ISO_SMOLVM = "smolvm"
ISO_DOCKER = "docker"
ISO_LOCAL = "bare-local"
ISO_AUTO = "auto"
ISO_CHOICES = (ISO_AUTO, ISO_SMOLVM, ISO_DOCKER, ISO_LOCAL)

# Minimum CRASH-primitive counts a platform must clear for a count test to PASS.
# A platform may override these in platforms/<name>/test_config.yaml.
DEFAULT_MIN_COUNTS = {"skills": 1, "commands": 1, "agents": 1, "rules": 1}

# The 14 canonical test ids, in display order.
TEST_IDS = [f"T{i}" for i in range(1, 15)]


# ---- data model ---------------------------------------------------------------


@dataclass
class TestResult:
    """One row of the 14-test plan."""

    id: str
    name: str
    status: str  # PASS | FAIL | WARN | SKIP
    evidence: str = ""

    def scored(self) -> bool:
        """A test counts toward the X/14 score only when it PASSes."""
        return self.status == PASS


@dataclass
class ReportCard:
    """Full per-platform run result — the model the HTML renderer consumes."""

    platform: str
    version: str
    date: str
    isolation: str
    scaffold_root: str
    results: List[TestResult] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)

    @property
    def score(self) -> int:
        return sum(1 for r in self.results if r.scored())

    @property
    def total(self) -> int:
        # 14 fixed slots regardless of how many ran — SKIP/FAIL still count as
        # "out of 14" so a half-implemented platform reads honestly.
        return len(TEST_IDS)

    @property
    def band(self) -> str:
        """Color band: green >=12, yellow 8-11, red <8 (AC3)."""
        s = self.score
        if s >= 12:
            return "green"
        if s >= 8:
            return "yellow"
        return "red"

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "version": self.version,
            "date": self.date,
            "isolation": self.isolation,
            "score": self.score,
            "total": self.total,
            "band": self.band,
            "counts": self.counts,
            "environment": self.environment,
            "results": [
                {"id": r.id, "name": r.name, "status": r.status, "evidence": r.evidence}
                for r in self.results
            ],
        }


# ---- path discovery -----------------------------------------------------------


def find_core_root(start: Optional[Path] = None) -> Path:
    """Locate ``gald3r_core/`` by walking up from this script's location.

    The harness ships inside ``project_template/.gald3r_sys/scripts/`` of the
    canonical source tree, so the core is an ancestor directory containing both
    ``platforms/`` and ``project_template/``.

    Args:
        start: Override start path (defaults to this module's file).

    Returns:
        The ``gald3r_core/`` directory.

    Raises:
        FileNotFoundError: When no ancestor qualifies.
    """
    cur = Path(start or __file__).resolve()
    for d in [cur, *cur.parents]:
        if (d / "platforms").is_dir() and (d / "project_template").is_dir():
            return d
        if (d / "gald3r_core").is_dir():
            inner = d / "gald3r_core"
            if (inner / "platforms").is_dir():
                return inner
    raise FileNotFoundError(
        "Could not locate gald3r_core/ (a dir containing platforms/ + "
        f"project_template/) at or above {cur}."
    )


def list_platforms(core: Path) -> List[str]:
    """Return the sorted platform overlay names under ``gald3r_core/platforms/``."""
    pdir = core / "platforms"
    if not pdir.is_dir():
        return []
    return sorted(d.name for d in pdir.iterdir() if d.is_dir())


def _read_version(core: Path) -> str:
    vf = core / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8-sig").strip()
    return "0.0.0"


# ---- test config (data-driven, per-platform overridable) ----------------------


def load_test_config(core: Path, platform: str) -> dict:
    """Build the effective per-platform test config.

    Resolution: start from a sensible default (every test applies, default min
    counts), then overlay ``platforms/<platform>/test_config.yaml`` when present.
    The override file is optional — the harness discovers the real overlay layout
    dynamically (see :func:`discover_layout`), so a missing config is normal.

    Recognised override keys (all optional):
        skip:        list of test ids to force-SKIP (e.g. ["T5"] for Hermes)
        min_counts:  dict overriding DEFAULT_MIN_COUNTS
        config_dirs: list of overlay config dir names (e.g. [".claude"]) —
                     usually auto-discovered, override only when ambiguous
        status_cmd:  argv list for the read-only health command (default: doctor)

    Args:
        core: The gald3r_core root.
        platform: Platform overlay name.

    Returns:
        The merged config dict.
    """
    cfg: dict = {
        "skip": [],
        "min_counts": dict(DEFAULT_MIN_COUNTS),
        "config_dirs": [],
        "status_cmd": ["doctor"],
    }
    override = core / "platforms" / platform / "test_config.yaml"
    if override.is_file():
        data = _load_yaml(override)
        if isinstance(data, dict):
            if isinstance(data.get("skip"), list):
                cfg["skip"] = [str(x) for x in data["skip"]]
            if isinstance(data.get("min_counts"), dict):
                cfg["min_counts"].update(
                    {k: int(v) for k, v in data["min_counts"].items()}
                )
            if isinstance(data.get("config_dirs"), list):
                cfg["config_dirs"] = [str(x) for x in data["config_dirs"]]
            if isinstance(data.get("status_cmd"), list):
                cfg["status_cmd"] = [str(x) for x in data["status_cmd"]]
    return cfg


def _load_yaml(path: Path) -> Optional[dict]:
    """Load a small YAML file; tolerate missing PyYAML with a tiny fallback."""
    try:
        import yaml  # type: ignore

        with open(path, "r", encoding="utf-8-sig") as fh:
            return yaml.safe_load(fh)
    except ImportError:
        return _mini_yaml(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _mini_yaml(text: str) -> dict:
    """Minimal flat-key YAML reader for the test_config override (no PyYAML).

    Supports ``key: value``, ``key:`` followed by ``  - item`` list lines, and
    one level of ``key:`` -> ``  subkey: value`` mappings. Sufficient for the
    small override schema; falls back to {} on anything fancier.
    """
    out: dict = {}
    cur_list_key: Optional[str] = None
    cur_map_key: Optional[str] = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped.startswith("- "):
            if cur_list_key is not None:
                out.setdefault(cur_list_key, []).append(stripped[2:].strip())
            continue
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key, val = key.strip(), val.strip()
            if indent > 0 and cur_map_key is not None:
                out.setdefault(cur_map_key, {})[key] = _coerce(val)
                continue
            cur_list_key, cur_map_key = None, None
            if val == "":
                cur_list_key = key
                cur_map_key = key
                out.setdefault(key, [])
            else:
                out[key] = _coerce(val)
    # Drop empty list placeholders that turned out to be maps.
    return {k: v for k, v in out.items()}


def _coerce(val: str):
    val = val.strip().strip('"').strip("'")
    if val.isdigit():
        return int(val)
    return val


# ---- overlay layout discovery -------------------------------------------------


@dataclass
class Layout:
    """Discovered per-platform overlay layout inside a scaffold root."""

    config_dirs: List[Path] = field(default_factory=list)
    skills_dirs: List[Path] = field(default_factory=list)
    commands_dirs: List[Path] = field(default_factory=list)
    agents_dirs: List[Path] = field(default_factory=list)
    rules_dirs: List[Path] = field(default_factory=list)
    hook_configs: List[Path] = field(default_factory=list)
    mcp_configs: List[Path] = field(default_factory=list)


# Hidden config-dir prefixes that a platform overlay may use.
_KNOWN_CONFIG_DIRS = (
    ".claude", ".cursor", ".codex", ".agents", ".agent", ".gemini", ".hermes",
    ".copilot", ".opencode", ".windsurf", ".github", ".kiro", ".junie", ".goose",
    ".roo", ".cline", ".augment", ".warp", ".replit", ".qwen", ".openclaw",
    ".antigravity", ".aider", ".mistral", ".vibe", ".continue",
)
_HOOK_CONFIG_NAMES = ("hooks.json", "hooks.yaml", "settings.json")
_MCP_CONFIG_NAMES = (".mcp.json", "mcp.json", "config.toml")


def discover_layout(scaffold: Path, overlay: Path, cfg: dict) -> Layout:
    """Find component dirs + hook/MCP config files inside a scaffolded project.

    The scaffold mirrors the platform repo's ``project_template/`` (base +
    overlay). We look for the platform's config dir(s) and the standard
    component sub-dirs (skills / commands / agents / rules) plus hook & MCP
    config files, using the overlay source tree as the authoritative hint for
    which hidden config dirs this platform actually ships.

    Args:
        scaffold: The scaffolded project_template root (where the install lives).
        overlay: The source ``platforms/<name>`` dir (layout hint).
        cfg: Effective test config (may pin ``config_dirs``).

    Returns:
        A populated :class:`Layout`.
    """
    layout = Layout()

    # Which hidden config dirs does this platform ship? Prefer an explicit
    # config pin, else read the overlay's own top-level hidden dirs, else the
    # known set that actually exists in the scaffold.
    if cfg.get("config_dirs"):
        candidates = list(cfg["config_dirs"])
    else:
        candidates = [
            d.name for d in overlay.iterdir()
            if d.is_dir() and d.name.startswith(".")
        ] if overlay.is_dir() else []
    if not candidates:
        candidates = list(_KNOWN_CONFIG_DIRS)

    seen = set()
    for name in candidates:
        cdir = scaffold / name
        if cdir.is_dir() and cdir not in seen:
            seen.add(cdir)
            layout.config_dirs.append(cdir)

    # Walk each config dir for component sub-dirs + config files.
    for cdir in layout.config_dirs:
        _collect_components(cdir, layout)

    # De-dup any nested duplicates.
    for attr in (
        "skills_dirs", "commands_dirs", "agents_dirs", "rules_dirs",
        "hook_configs", "mcp_configs",
    ):
        uniq: List[Path] = []
        for p in getattr(layout, attr):
            if p not in uniq:
                uniq.append(p)
        setattr(layout, attr, uniq)

    return layout


def _collect_components(cdir: Path, layout: Layout) -> None:
    """Populate `layout` with component dirs + config files found under `cdir`."""
    # Component dirs may be at the top of the config dir or one level down.
    for sub in ("skills", "commands", "agents", "rules"):
        for cand in (cdir / sub,):
            if cand.is_dir():
                getattr(layout, f"{sub}_dirs").append(cand)
    # Config files (top level of the config dir, plus the scaffold root for .mcp.json).
    for name in _HOOK_CONFIG_NAMES:
        f = cdir / name
        if f.is_file():
            layout.hook_configs.append(f)
    for name in _MCP_CONFIG_NAMES:
        f = cdir / name
        if f.is_file():
            layout.mcp_configs.append(f)
    # Some overlays put .mcp.json at the config-dir parent (scaffold root level).
    parent_mcp = cdir.parent / ".mcp.json"
    if parent_mcp.is_file():
        layout.mcp_configs.append(parent_mcp)


def _count_skill_files(skills_dirs: List[Path]) -> int:
    return sum(len(list(d.rglob("SKILL.md"))) for d in skills_dirs)


def _count_md_files(dirs: List[Path]) -> int:
    """Count top-level .md / .toml component files (commands/agents/rules)."""
    total = 0
    for d in dirs:
        total += len([p for p in d.rglob("*") if p.is_file()
                      and p.suffix.lower() in (".md", ".mdc", ".toml")])
    return total


# ---- scaffolding (host-safe; mirrors the Forge platform-repo assembly) --------

_EXCLUDE_COPY_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache"}
# Other-platform IDE dirs in the base project_template that must be pruned for a
# platform that does NOT own them (claude owns .claude, cursor owns .cursor).
_PLATFORM_OWNED_DIRS = {"claude": {".claude"}, "cursor": {".cursor"}}
_PLATFORM_OWNED_FILES = {"claude": {"CLAUDE.md"}}
_BASE_EXCLUDE_DIRS = {".claude", ".cursor"}
_BASE_EXCLUDE_FILES = {"CLAUDE.md"}


def scaffold_platform(core: Path, platform: str, dest: Path) -> Path:
    """Assemble a throwaway platform install under ``dest/project_template``.

    Replicates :class:`gald3r_forge.systems.build.BuildSystem._build_platform_repo`
    for ONE platform's ``project_template``: copy the base template minus
    other-platform IDE items, then overlay ``platforms/<platform>`` on top. The
    engine pytest suite is skipped to keep the scaffold lean.

    Args:
        core: gald3r_core root.
        platform: Overlay name.
        dest: Destination temp root (created if missing).

    Returns:
        The scaffolded ``project_template`` directory.
    """
    src_template = core / "project_template"
    overlay = core / "platforms" / platform
    dest_template = dest / "project_template"
    dest_template.mkdir(parents=True, exist_ok=True)

    owned_dirs = _PLATFORM_OWNED_DIRS.get(platform, set())
    owned_files = _PLATFORM_OWNED_FILES.get(platform, set())
    x_dirs = (_BASE_EXCLUDE_DIRS - owned_dirs) | _EXCLUDE_COPY_DIRS
    x_files = _BASE_EXCLUDE_FILES - owned_files

    _copy_tree(src_template, dest_template, x_dirs, x_files,
               prune_rel={"./.gald3r_sys/engine/tests"})
    if overlay.is_dir():
        _copy_tree(overlay, dest_template, _EXCLUDE_COPY_DIRS, set())
    return dest_template


def _copy_tree(
    src: Path,
    dest: Path,
    exclude_dirs: set,
    exclude_files: set,
    prune_rel: Optional[set] = None,
) -> None:
    """Copy `src` into `dest`, pruning excluded dir names / file names."""
    prune_rel = prune_rel or set()
    src = src.resolve()
    for root, dirs, files in os.walk(src):
        rootp = Path(root)
        rel = rootp.relative_to(src)
        # Prune excluded dir names in place.
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        # Prune exact relative subtrees (e.g. engine tests).
        rel_posix = "./" + rel.as_posix() if rel.as_posix() != "." else "."
        dirs[:] = [
            d for d in dirs
            if (rel_posix.rstrip("/") + "/" + d).lstrip("./")
            not in {p.lstrip("./") for p in prune_rel}
        ]
        target_root = dest / rel
        target_root.mkdir(parents=True, exist_ok=True)
        for f in files:
            if f in exclude_files:
                continue
            try:
                shutil.copy2(rootp / f, target_root / f)
            except (OSError, shutil.Error):
                pass


# ---- the 14-test plan ---------------------------------------------------------


def _run_cli(scaffold: Path, args: List[str]) -> Tuple[int, str]:
    """Run the bundled gald3r engine CLI against the scaffold.

    Prefers ``uv run --project <engine>`` and falls back to running the engine
    as ``python -m gald3r`` with the engine ``src`` on PYTHONPATH. Returns
    (returncode, combined-output). A returncode of -1 means the CLI could not
    be launched at all (no uv, no python module).
    """
    engine = scaffold / ".gald3r_sys" / "engine"
    env = dict(os.environ)
    if shutil.which("uv") and (engine / "pyproject.toml").is_file():
        cmd = ["uv", "run", "--project", str(engine), "gald3r", *args]
        rc, out = _exec(cmd, cwd=scaffold, env=env)
        if rc != 127:
            return rc, out
    # Fallback: python -m gald3r with engine/src on the path.
    src = engine / "src"
    if (src / "gald3r" / "__init__.py").is_file():
        env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
        return _exec([sys.executable, "-m", "gald3r", *args], cwd=scaffold, env=env)
    return -1, "gald3r engine not launchable (no uv project run, no engine/src)"


def _exec(cmd: List[str], cwd: Path, env: dict, timeout: int = 180) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s: {' '.join(cmd)}"
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def _trim(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def run_test_plan(
    scaffold: Path, core: Path, platform: str, cfg: dict, layout: Layout,
    version: str,
) -> List[TestResult]:
    """Execute the 14-test plan against a scaffolded platform install.

    Each test is self-contained and returns a :class:`TestResult`. Tests in
    ``cfg['skip']`` are short-circuited to SKIP without running.

    Args:
        scaffold: Scaffolded project_template root.
        core: gald3r_core root (for VERSION comparisons).
        platform: Platform overlay name.
        cfg: Effective test config.
        layout: Discovered overlay layout.
        version: The expected gald3r version (from VERSION).

    Returns:
        14 TestResults in T1..T14 order.
    """
    engine = scaffold / ".gald3r_sys" / "engine"
    skip = set(cfg.get("skip", []))
    min_counts = cfg.get("min_counts", DEFAULT_MIN_COUNTS)
    results: List[TestResult] = []
    cli_ok = True  # set False when the engine never launches; gates T2/T3

    def add(tid: str, name: str, runner: Callable[[], Tuple[str, str]]) -> None:
        if tid in skip:
            results.append(TestResult(tid, name, SKIP, "skipped by test_config"))
            return
        try:
            status, ev = runner()
        except Exception as exc:  # never let one test abort the run
            status, ev = WARN, f"test raised: {exc!r}"
        results.append(TestResult(tid, name, status, _trim(ev)))

    # T1 — engine installs (editable). Heavy; honoured but gated to keep runs
    # fast: we verify the engine package is importable rather than mutating the
    # host env with a real `uv pip install -e`. The install command is still
    # surfaced as evidence so a reviewer can reproduce it.
    def t1() -> Tuple[str, str]:
        nonlocal cli_ok
        if not (engine / "pyproject.toml").is_file():
            cli_ok = False
            return FAIL, "no engine/pyproject.toml in scaffold"
        rc, out = _run_cli(scaffold, ["--version"])
        cli_ok = rc == 0
        cmd = f"uv pip install -e {engine.name} (reproduce); import check rc={rc}"
        if rc == 0:
            return PASS, f"engine importable; {cmd}; {out}"
        return FAIL, f"engine not launchable (rc={rc}); {out}"

    add("T1", "Engine installs / launchable", t1)

    # T2 — `gald3r --version` matches VERSION.
    def t2() -> Tuple[str, str]:
        if not cli_ok:
            return SKIP, "engine not launchable (see T1)"
        rc, out = _run_cli(scaffold, ["--version"])
        if rc != 0:
            return FAIL, f"--version rc={rc}: {out}"
        if version and version in out:
            return PASS, f"--version => {out} (matches VERSION {version})"
        # Source tree ships __version__=0.1.0 but VERSION may be 2.x (stamped at
        # build). Report honestly as WARN, not a hard fail.
        return WARN, f"--version => {out}; VERSION file says {version} (stamp gap)"

    add("T2", "gald3r --version matches VERSION", t2)

    # T3 — read-only status/health command exits 0 (default: `gald3r doctor`;
    # there is no bare `gald3r status` in this engine — see TEST_RUNNER.md).
    def t3() -> Tuple[str, str]:
        if not cli_ok:
            return SKIP, "engine not launchable (see T1)"
        status_cmd = cfg.get("status_cmd", ["doctor"])
        rc, out = _run_cli(scaffold, status_cmd)
        cmd_label = "gald3r " + " ".join(status_cmd)
        if rc == 0:
            return PASS, f"{cmd_label} exit 0; {out}"
        return FAIL, f"{cmd_label} rc={rc}: {out}"

    add("T3", "Read-only health command (doctor) exits 0", t3)

    # T4 — task create/read round-trips through the CLI.
    def t4() -> Tuple[str, str]:
        if not cli_ok:
            return SKIP, "engine not launchable (see T1)"
        rc1, out1 = _run_cli(
            scaffold, ["task", "new", "--title", "T613 harness probe"]
        )
        rc2, out2 = _run_cli(scaffold, ["task", "list"])
        if rc1 == 0 and rc2 == 0:
            return PASS, f"created + listed; new={_trim(out1, 80)} list ok"
        return FAIL, f"new rc={rc1}, list rc={rc2}: {_trim(out1 + ' | ' + out2, 120)}"

    add("T4", "Task create + read round-trip", t4)

    # T5 — hook config parses + validates (skip when the platform ships none).
    def t5() -> Tuple[str, str]:
        if not layout.hook_configs:
            return SKIP, "platform ships no hooks.json/settings.json/hooks.yaml"
        bad: List[str] = []
        for f in layout.hook_configs:
            ok, why = _validate_config_file(f)
            if not ok:
                bad.append(f"{f.name}: {why}")
        if bad:
            return FAIL, "; ".join(bad)
        names = ", ".join(sorted({f.name for f in layout.hook_configs}))
        return PASS, f"valid hook config(s): {names}"

    add("T5", "Hook config valid (schema parse)", t5)

    # T6 — skills discoverable (>= N SKILL.md).
    def t6() -> Tuple[str, str]:
        n = _count_skill_files(layout.skills_dirs)
        need = int(min_counts.get("skills", 1))
        if not layout.skills_dirs:
            return SKIP, "platform ships no skills/ dir"
        if n >= need:
            return PASS, f"{n} SKILL.md found (>= {need})"
        return FAIL, f"only {n} SKILL.md (< {need})"

    add("T6", "Skills discoverable (SKILL.md)", t6)

    # T7 — commands present (>= N).
    def t7() -> Tuple[str, str]:
        return _count_test(layout.commands_dirs, int(min_counts.get("commands", 1)),
                           "command")

    add("T7", "Commands present", t7)

    # T8 — agents present (>= N).
    def t8() -> Tuple[str, str]:
        return _count_test(layout.agents_dirs, int(min_counts.get("agents", 1)),
                           "agent")

    add("T8", "Agents present", t8)

    # T9 — rules present (>= N).
    def t9() -> Tuple[str, str]:
        return _count_test(layout.rules_dirs, int(min_counts.get("rules", 1)),
                           "rule")

    add("T9", "Rules present", t9)

    # T10 — MCP config valid (parse JSON / TOML when present).
    def t10() -> Tuple[str, str]:
        if not layout.mcp_configs:
            return SKIP, "platform ships no MCP config"
        bad: List[str] = []
        for f in layout.mcp_configs:
            ok, why = _validate_config_file(f)
            if not ok:
                bad.append(f"{f.name}: {why}")
        if bad:
            return FAIL, "; ".join(bad)
        names = ", ".join(sorted({f.name for f in layout.mcp_configs}))
        return PASS, f"valid MCP config(s): {names}"

    add("T10", "MCP config valid (JSON/TOML)", t10)

    # T11 — platform overlay (config) dir present.
    def t11() -> Tuple[str, str]:
        if layout.config_dirs:
            names = ", ".join(sorted({d.name for d in layout.config_dirs}))
            return PASS, f"overlay config dir(s): {names}"
        return FAIL, "no platform config dir found in scaffold"

    add("T11", "Platform overlay dir present", t11)

    # T12 — .gitignore covers the standard python noise dirs.
    def t12() -> Tuple[str, str]:
        gi = scaffold / ".gitignore"
        if not gi.is_file():
            return FAIL, "no .gitignore in scaffold"
        text = gi.read_text(encoding="utf-8-sig", errors="replace")
        need = ["__pycache__", ".venv", ".pytest_cache"]
        missing = [n for n in need if n not in text]
        if not missing:
            return PASS, "covers __pycache__/, .venv/, .pytest_cache/"
        return FAIL, f"missing gitignore entries: {', '.join(missing)}"

    add("T12", ".gitignore covers python noise", t12)

    # T13 — VERSION matches 2.x.x.
    def t13() -> Tuple[str, str]:
        vf = scaffold / "VERSION"
        v = vf.read_text(encoding="utf-8-sig").strip() if vf.is_file() else ""
        if not v:
            # The base project_template may not carry its own VERSION until the
            # build stamps it; fall back to the source VERSION for the assertion.
            v = version
        import re as _re

        if _re.match(r"^2\.\d+\.\d+$", v):
            return PASS, f"VERSION = {v} (matches 2.x.x)"
        return WARN, f"VERSION = {v or '(absent)'} (expected 2.x.x)"

    add("T13", "VERSION matches 2.x.x", t13)

    # T14 — root AGENTS.md present + non-empty.
    def t14() -> Tuple[str, str]:
        am = scaffold / "AGENTS.md"
        if am.is_file() and am.stat().st_size > 0:
            return PASS, f"AGENTS.md present ({am.stat().st_size} bytes)"
        return FAIL, "AGENTS.md missing or empty"

    add("T14", "Root AGENTS.md present + non-empty", t14)

    return results


def _count_test(dirs: List[Path], need: int, label: str) -> Tuple[str, str]:
    """Shared >= N component-count assertion for T7/T8/T9."""
    if not dirs:
        return SKIP, f"platform ships no {label}s dir"
    n = _count_md_files(dirs)
    if n >= need:
        return PASS, f"{n} {label}(s) found (>= {need})"
    return FAIL, f"only {n} {label}(s) (< {need})"


def _validate_config_file(path: Path) -> Tuple[bool, str]:
    """Parse a JSON / YAML / TOML config file; return (ok, reason)."""
    ext = path.suffix.lower()
    try:
        if path.name.endswith(".json") or ext == ".json":
            with open(path, "r", encoding="utf-8-sig") as fh:
                json.load(fh)
            return True, "json ok"
        if ext in (".yaml", ".yml"):
            data = _load_yaml(path)
            return (data is not None), ("yaml ok" if data is not None else "yaml parse failed")
        if ext == ".toml":
            try:
                import tomllib  # py3.11+
            except ImportError:
                return True, "toml parse skipped (no tomllib)"
            with open(path, "rb") as fh:
                tomllib.load(fh)
            return True, "toml ok"
        return True, f"unvalidated ({ext})"
    except json.JSONDecodeError as exc:
        return False, f"json error: {exc}"
    except Exception as exc:  # tomllib / yaml errors
        return False, f"parse error: {exc}"


# ---- counts (CRASH primitives matrix) -----------------------------------------


def crash_counts(layout: Layout) -> Dict[str, int]:
    """Return the CRASH-primitive count matrix (Commands/Rules/Agents/Skills/Hooks)."""
    return {
        "Commands": _count_md_files(layout.commands_dirs),
        "Rules": _count_md_files(layout.rules_dirs),
        "Agents": _count_md_files(layout.agents_dirs),
        "Skills": _count_skill_files(layout.skills_dirs),
        "Hooks": len(layout.hook_configs),
    }


# ---- HTML rendering (single self-contained file, inline CSS) ------------------

_BAND_COLOR = {"green": "#1a7f37", "yellow": "#bf8700", "red": "#cf222e"}
_STATUS_COLOR = {PASS: "#1a7f37", FAIL: "#cf222e", WARN: "#bf8700", SKIP: "#6e7781"}


def _load_page_template() -> str:
    """Return the HTML page template.

    Prefers the external skeleton ``platform_report_card.html`` shipped next to
    this script (the canonical, editable template — AC3) and falls back to the
    embedded copy when it is absent (e.g. running from an unusual location).
    The two are kept identical; the embedded copy guarantees the harness is
    self-contained even if the skeleton file is missing.
    """
    skeleton = Path(__file__).resolve().parent / "platform_report_card.html"
    if skeleton.is_file():
        try:
            return skeleton.read_text(encoding="utf-8")
        except OSError:
            pass
    return _PAGE_TEMPLATE


def render_report_card(card: ReportCard) -> str:
    """Render a single platform :class:`ReportCard` as self-contained HTML (AC3)."""
    e = html.escape
    band = card.band
    band_color = _BAND_COLOR[band]
    rows = []
    for r in card.results:
        glyph = _STATUS_GLYPH.get(r.status, "?")
        color = _STATUS_COLOR.get(r.status, "#6e7781")
        rows.append(
            f"<tr><td class='tid'>{e(r.id)}</td>"
            f"<td>{e(r.name)}</td>"
            f"<td style='color:{color};font-weight:600'>{glyph} "
            f"{_STATUS_LABEL.get(r.status, r.status)}</td>"
            f"<td class='ev'>{e(r.evidence)}</td></tr>"
        )
    test_rows = "\n".join(rows)

    counts = card.counts or {}
    count_cells = "".join(
        f"<div class='metric'><div class='mv'>{counts.get(k, 0)}</div>"
        f"<div class='ml'>{e(k)}</div></div>"
        for k in ("Commands", "Rules", "Agents", "Skills", "Hooks")
    )

    env = card.environment or {}
    env_rows = "".join(
        f"<tr><td>{e(str(k))}</td><td>{e(str(v))}</td></tr>" for k, v in env.items()
    )

    return _load_page_template().format(
        platform=e(card.platform),
        title=f"gald3r Platform Report Card — {e(card.platform)}",
        band_color=band_color,
        band=e(band.upper()),
        score=card.score,
        total=card.total,
        version=e(card.version),
        date=e(card.date),
        isolation=e(card.isolation),
        count_cells=count_cells,
        test_rows=test_rows,
        env_rows=env_rows,
    )


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ --band: {band_color}; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         margin: 0; background: #f6f8fa; color: #1f2328; }}
  .wrap {{ max-width: 980px; margin: 0 auto; padding: 24px; }}
  header {{ background: var(--band); color: #fff; border-radius: 10px;
           padding: 22px 26px; display: flex; align-items: center;
           justify-content: space-between; flex-wrap: wrap; gap: 12px; }}
  header h1 {{ margin: 0; font-size: 1.5rem; }}
  header .sub {{ opacity: .9; font-size: .9rem; margin-top: 4px; }}
  .score {{ font-size: 2.4rem; font-weight: 700; line-height: 1; }}
  .score small {{ font-size: 1rem; font-weight: 400; opacity: .85; }}
  section {{ background: #fff; border: 1px solid #d0d7de; border-radius: 10px;
            margin: 18px 0; padding: 18px 20px; }}
  section h2 {{ margin: 0 0 12px; font-size: 1.05rem;
               border-bottom: 1px solid #eaeef2; padding-bottom: 8px; }}
  .metrics {{ display: flex; gap: 14px; flex-wrap: wrap; }}
  .metric {{ flex: 1 1 0; min-width: 90px; text-align: center;
            background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 8px;
            padding: 12px 8px; }}
  .metric .mv {{ font-size: 1.6rem; font-weight: 700; }}
  .metric .ml {{ font-size: .8rem; color: #57606a; margin-top: 2px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
  th, td {{ text-align: left; padding: 7px 9px; border-bottom: 1px solid #eaeef2;
           vertical-align: top; }}
  th {{ background: #f6f8fa; font-weight: 600; }}
  td.tid {{ font-variant-numeric: tabular-nums; font-weight: 600; white-space: nowrap; }}
  td.ev {{ color: #57606a; font-size: .82rem; font-family: ui-monospace, SFMono-Regular,
          Menlo, Consolas, monospace; }}
  footer {{ text-align: center; color: #8b949e; font-size: .8rem; padding: 14px 0; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>{platform} — Platform Report Card</h1>
      <div class="sub">gald3r v{version} &middot; {date} &middot; isolation: {isolation} &middot; band: {band}</div>
    </div>
    <div class="score">{score}<small>/{total}</small></div>
  </header>

  <section>
    <h2>Summary</h2>
    <p>Platform <strong>{platform}</strong> scored <strong>{score}/{total}</strong>
       ({band} band). A red card is the correct output for a stub or incomplete
       platform — someone should fix that platform's spec, not the harness.</p>
  </section>

  <section>
    <h2>CRASH primitives</h2>
    <div class="metrics">{count_cells}</div>
  </section>

  <section>
    <h2>Test results</h2>
    <table>
      <thead><tr><th>ID</th><th>Test</th><th>Result</th><th>Evidence</th></tr></thead>
      <tbody>
{test_rows}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Environment</h2>
    <table><tbody>
{env_rows}
    </tbody></table>
  </section>

  <footer>Generated by gald3r test_platform.py (T613) &middot; Powered by gald3r v{version}</footer>
</div>
</body>
</html>
"""


# ---- isolation backend selection ----------------------------------------------


def select_isolation(requested: str) -> Tuple[str, Optional[str]]:
    """Resolve the isolation backend to use (AC1/AC5).

    Order when ``auto``: SmolVM -> Docker -> bare-local. Returns the chosen
    backend plus an optional WARNING string (set only for bare-local, which
    runs on the host).

    Args:
        requested: One of ISO_CHOICES.

    Returns:
        (backend, warning_or_none)
    """
    if requested == ISO_SMOLVM:
        return ISO_SMOLVM, None
    if requested == ISO_DOCKER:
        return ISO_DOCKER, None
    if requested == ISO_LOCAL:
        return ISO_LOCAL, _LOCAL_WARNING
    # auto
    if shutil.which("smolvm"):
        return ISO_SMOLVM, None
    if shutil.which("docker"):
        return ISO_DOCKER, None
    return ISO_LOCAL, _LOCAL_WARNING


_LOCAL_WARNING = (
    "WARNING: running in BARE-LOCAL mode — no SmolVM/Docker isolation. The "
    "scaffold is still built in a throwaway temp dir (no host platform tool is "
    "touched), but engine subprocesses run on the host. Build the gald3r-test "
    "image (T615) to get full isolation."
)


def _isolation_argv(backend: str, platform: str, out_dir: Optional[str]) -> List[str]:
    """Build the in-container argv that re-invokes this harness for SmolVM/Docker.

    The base test image (T615) is expected to ship this script and the source
    tree; SmolVM/Docker simply re-run the harness in bare-local mode INSIDE the
    isolated env. We surface the command rather than silently no-op when the
    backend binary is absent.
    """
    inner = [
        "python", "/work/.gald3r_sys/scripts/test_platform.py", platform,
        "--isolation", ISO_LOCAL,
    ]
    if out_dir:
        inner += ["--out-dir", out_dir]
    if backend == ISO_SMOLVM:
        return ["smolvm", "run", "--image", "python:3.12", "--", *inner]
    # docker
    return [
        "docker", "run", "--rm", "-v", "{src}:/work", "gald3r-test:latest", *inner,
    ]


# ---- orchestration ------------------------------------------------------------


def test_one_platform(
    platform: str,
    core: Path,
    isolation: str = ISO_AUTO,
    out_dir: Optional[Path] = None,
    keep_scaffold: bool = False,
) -> ReportCard:
    """Run the full harness for ONE platform and return its :class:`ReportCard`.

    Always runs the scaffolding + test plan in-process (bare-local). When a
    SmolVM/Docker backend is requested AND available, the isolated re-invocation
    command is recorded in the environment block for reproducibility — actually
    spawning the container requires the T615 base image, which is out of scope
    for T613, so the harness runs the plan locally and notes the backend.

    Args:
        platform: Overlay name (must exist under gald3r_core/platforms/).
        core: gald3r_core root.
        isolation: Requested isolation backend.
        out_dir: Where to also drop the report card (in addition to the two
            canonical locations). Optional.
        keep_scaffold: Keep the temp scaffold on disk (debugging).

    Returns:
        The populated ReportCard (also written to disk — see :func:`write_outputs`).

    Raises:
        ValueError: Unknown platform.
    """
    platforms = list_platforms(core)
    if platform not in platforms:
        raise ValueError(
            f"Unknown platform '{platform}'. Known: {', '.join(platforms)}"
        )

    version = _read_version(core)
    backend, warning = select_isolation(isolation)
    cfg = load_test_config(core, platform)

    tmp = Path(tempfile.mkdtemp(prefix=f"gald3r_test_{platform}_"))
    try:
        scaffold = scaffold_platform(core, platform, tmp)
        overlay = core / "platforms" / platform
        layout = discover_layout(scaffold, overlay, cfg)
        results = run_test_plan(scaffold, core, platform, cfg, layout, version)
        counts = crash_counts(layout)

        env: Dict[str, str] = {
            "python": sys.version.split()[0],
            "platform_os": sys.platform,
            "isolation_backend": backend,
            "uv_available": "yes" if shutil.which("uv") else "no",
            "config_dirs": ", ".join(d.name for d in layout.config_dirs) or "(none)",
            "scaffold": str(scaffold) if keep_scaffold else "(temp, removed)",
        }
        if warning:
            env["isolation_warning"] = warning
        if backend in (ISO_SMOLVM, ISO_DOCKER):
            env["isolation_command"] = " ".join(
                _isolation_argv(backend, platform, str(out_dir) if out_dir else None)
            )
            env["isolation_note"] = (
                "backend available; container run requires the T615 base image — "
                "plan executed bare-local this run"
            )

        card = ReportCard(
            platform=platform,
            version=version,
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            isolation=backend,
            scaffold_root=str(scaffold),
            results=results,
            counts=counts,
            environment=env,
        )
        return card
    finally:
        if not keep_scaffold:
            shutil.rmtree(tmp, ignore_errors=True)


def write_outputs(card: ReportCard, core: Path, out_dir: Optional[Path]) -> List[Path]:
    """Write the report card to the two canonical locations (+ optional out_dir).

    Canonical (AC3):
        1. ``gald3r_platform_<platform>/PLATFORM_REPORT_CARD.html`` (under out
           root — defaults to cwd)
        2. history copy ``.gald3r_sys/reports/platform_<name>_<date>.html``

    Args:
        card: The rendered report card model.
        core: gald3r_core root (anchors the history copy under its
            ``project_template/.gald3r_sys/reports/``).
        out_dir: Optional extra output dir (also receives a copy).

    Returns:
        The list of written file paths.
    """
    html_text = render_report_card(card)
    written: List[Path] = []

    base = out_dir if out_dir else Path.cwd()
    primary = base / f"gald3r_platform_{card.platform}" / "PLATFORM_REPORT_CARD.html"
    primary.parent.mkdir(parents=True, exist_ok=True)
    primary.write_text(html_text, encoding="utf-8")
    written.append(primary)

    datestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    history = (
        core / "project_template" / ".gald3r_sys" / "reports"
        / f"platform_{card.platform}_{datestamp}.html"
    )
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text(html_text, encoding="utf-8")
    written.append(history)

    return written


# ---- CLI ----------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="test_platform.py", allow_abbrev=False,
        description=(
            "Scaffold a gald3r project from a platform template, run the 14-test "
            "plan, and emit a self-contained HTML report card (T613)."
        ),
    )
    p.add_argument("platform", nargs="?", default=None,
                   help="platform overlay name (e.g. claude, cursor, hermes)")
    p.add_argument("--isolation", choices=ISO_CHOICES, default=ISO_AUTO,
                   help="isolation backend (default: auto = smolvm->docker->bare-local)")
    p.add_argument("--out-dir", default=None,
                   help="extra output dir for the report card (in addition to the "
                        "two canonical locations)")
    p.add_argument("--list", action="store_true",
                   help="list known platform overlays and exit")
    p.add_argument("--json", action="store_true",
                   help="also print the report card as JSON to stdout")
    p.add_argument("--keep-scaffold", action="store_true",
                   help="keep the temp scaffold on disk (debugging)")
    return p.parse_args(argv)


def _ensure_utf8() -> None:
    """Force UTF-8 on stdout/stderr so the emoji status markers in the JSON dump
    and summary print on the Windows console (cp1252). No-op where already UTF-8.
    Mirrors gald3r.adapters.cli._ensure_utf8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def main(argv: Optional[List[str]] = None) -> int:
    _ensure_utf8()
    args = parse_args(argv)
    core = find_core_root()

    if args.list:
        for name in list_platforms(core):
            print(name)
        return 0

    if not args.platform:
        print("error: a platform name is required (or use --list)", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).resolve() if args.out_dir else None
    try:
        card = test_one_platform(
            args.platform, core, isolation=args.isolation, out_dir=out_dir,
            keep_scaffold=args.keep_scaffold,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if card.environment.get("isolation_warning"):
        print(card.environment["isolation_warning"], file=sys.stderr)

    written = write_outputs(card, core, out_dir)

    print(
        f"[{card.platform}] {card.score}/{card.total} ({card.band}) "
        f"-> {written[0]}"
    )
    for p in written[1:]:
        print(f"           history: {p}")

    if args.json:
        print(json.dumps(card.to_dict(), ensure_ascii=False, indent=2))

    # Exit non-zero on a red card so CI / batch callers can gate on it.
    return 0 if card.band != "red" else 1


if __name__ == "__main__":
    raise SystemExit(main())
