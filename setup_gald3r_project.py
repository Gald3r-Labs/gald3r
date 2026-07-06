#!/usr/bin/env python3
"""Python port of setup_gald3r_project.ps1 (T1586).

gald3r Installer — installs gald3r into a target project.

Default (no --platform):
    Installs Cursor + Claude Code — copies project_template/ as-is.

--platform <name> (T533 — multi-select):
    Installs one or more platforms. Repeat the flag (--platform a --platform b),
    pass a comma list (--platform a,b,c), use --platforms a b c, or bulk-install
    with --all (every overlay) / --all-ready (the registry's derived >=80%-working
    set). Copies project_template/ once (the shared brain, keeping the .cursor and/or
    .claude config for any selected tier1 IDEs) then overlays platforms/<name>/ for
    every selected non-tier1 platform. A single --platform x still works exactly as
    before (back-compat).

Usage:
    python setup_gald3r_project.py                                       # Cursor + Claude (prompts)
    python setup_gald3r_project.py --target-path "C:/MyProject"          # same, no prompt
    python setup_gald3r_project.py --target-path X --platform windsurf   # Windsurf only
    python setup_gald3r_project.py --target-path X --platform windsurf --platform goose  # both
    python setup_gald3r_project.py --target-path X --platform cursor,claude,windsurf      # comma list
    python setup_gald3r_project.py --target-path X --all-ready           # every ready platform
    python setup_gald3r_project.py --target-path X --all                 # every overlay
    python setup_gald3r_project.py --target-path X --dry-run             # preview only
    python setup_gald3r_project.py --target-path X --force               # skip confirmations
    python setup_gald3r_project.py --non-interactive --name MyProj --tier full --platform cursor

Both --kebab-case and -PascalCase spellings are accepted for every flag
(e.g. ``-TargetPath``, ``-DryRun``) to mirror the PowerShell parameter surface.
"""
# @subsystems: PROJECT_IDENTITY_SETUP

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# -- Engine utils bootstrap ------------------------------------------------------
# At setup time the bundled engine may not be importable yet (it ships inside the
# template we are about to copy). Add both the template-source location (next to
# this script) and the installed location (relative to the CWD = target project)
# to sys.path, then import gald3r.utils with a pure-stdlib fallback.


def _bootstrap_engine_imports() -> None:
    """Add candidate engine src/ directories to sys.path (T1583 utils)."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "project_template" / ".gald3r_sys" / "engine" / "src",
        Path.cwd() / ".gald3r_sys" / "engine" / "src",
    ]
    for cand in candidates:
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


_bootstrap_engine_imports()

try:
    from gald3r.utils import console as _console
    from gald3r.utils import fs as _fs
except ImportError:  # graceful pure-stdlib fallback
    _console = None
    _fs = None

try:
    # Shared install-home -> identity inheritance + vault auto-provision (T476).
    # Single engine implementation reused by agent (this installer) AND throne.
    from gald3r import provision as _provision
except ImportError:  # engine not importable at bootstrap -> plain placeholder fill
    _provision = None


def _load_platform_registry():
    """Import the shared platform_registry reader by file path (T533).

    The registry reader is the single source of truth for the platform roster and the
    DERIVED readiness flag (PLATFORM_REGISTRY.yaml, T516/T533). It ships inside
    project_template/ as a skill script, so it is imported here by path rather than as
    an installed package. Returns the module, or None if it cannot be located/imported
    (callers then fall back to the platforms/ directory listing).
    """
    import importlib.util

    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "project_template" / ".claude" / "skills"
        / "g-skl-platform-monitor" / "scripts" / "platform_registry.py",
        script_dir / "project_template" / ".cursor" / "skills"
        / "g-skl-platform-monitor" / "scripts" / "platform_registry.py",
    ]
    for cand in candidates:
        if not cand.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location("platform_registry", cand)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except (OSError, ImportError, SyntaxError):
            continue
    return None


_registry = _load_platform_registry()

# -- Repo identity ---------------------------------------------------------------
# gald3r:          REQUIRE_PLATFORM = False -> default = Cursor + Claude Code
# <template_adv>:  REQUIRE_PLATFORM = True  -> must pick a platform
REQUIRE_PLATFORM = False

TIER_DEFAULT = "full"

_COLORS = {
    "cyan": "\x1b[36m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "darkgray": "\x1b[90m",
    "red": "\x1b[31m",
}
_RESET = "\x1b[0m"


def _color_enabled() -> bool:
    """Return True when ANSI color should be emitted (NO_COLOR/FORCE_COLOR/tty)."""
    if _console is not None:
        return _console.color_enabled(sys.stdout)
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


def cprint(msg: str, color: str = "") -> None:
    """Print `msg`, wrapped in an ANSI color when the terminal supports it.

    Args:
        msg: Text to print.
        color: Key in _COLORS (mirrors Write-Host -ForegroundColor); empty = plain.
    """
    if color and _color_enabled():
        print(f"{_COLORS[color]}{msg}{_RESET}")
    else:
        print(msg)


def ensure_dir(path: Path) -> Path:
    """Create `path` (and parents) if missing; return it (engine fs or stdlib)."""
    if _fs is not None:
        return _fs.ensure_dir(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ask(prompt: str, default: str, non_interactive: bool) -> str:
    """Prompt the user with a ``[default]`` hint, or auto-answer in CI mode.

    Args:
        prompt: Prompt text (without the default hint).
        default: Value used when the user presses Enter or in non-interactive mode.
        non_interactive: When True, emit an ``[AUTO]`` line and return `default`.

    Returns:
        The entered (or defaulted) value, stripped.
    """
    if non_interactive:
        print(f"[AUTO] {prompt}: {default}")
        return default
    hint = f" [{default}]" if default else ""
    answer = input(f"{prompt}{hint}: ").strip()
    return answer if answer else default


def confirm(prompt: str, non_interactive: bool) -> bool:
    """Ask a y/N question; auto-answers ``y`` (with an ``[AUTO]`` line) in CI mode.

    Args:
        prompt: Question text (``(y/N)`` is appended).
        non_interactive: When True, auto-confirm.

    Returns:
        True when the user answered yes.
    """
    if non_interactive:
        print(f"[AUTO] {prompt} (y/N): y")
        return True
    answer = input(f"{prompt} (y/N): ").strip()
    return bool(re.match(r"^[Yy]", answer))


def copy_layer(
    source_dir: Path,
    target_dir: Path,
    skip_top_dirs: Sequence[str] = (),
    protected: Sequence[str] = (),
    dry_run: bool = False,
) -> int:
    """Copy every file under `source_dir` into `target_dir` (PS1 ``Copy-Layer``).

    Args:
        source_dir: Layer root to copy from.
        target_dir: Project root to copy into.
        skip_top_dirs: Top-level entry names to skip entirely.
        protected: Top-level entry names whose EXISTING destination files are
            never overwritten (new files are still added).
        dry_run: When True nothing is written; files are only counted.

    Returns:
        Number of files copied (or that would be copied).
    """
    skip = {d.casefold() for d in skip_top_dirs}
    prot = {d.casefold() for d in protected}
    count = 0
    for root, dirs, files in os.walk(source_dir):
        root_p = Path(root)
        if root_p == source_dir:
            dirs[:] = [d for d in dirs if d.casefold() not in skip]
        rel_root = root_p.relative_to(source_dir)
        for name in files:
            rel = rel_root / name
            top = rel.parts[0]
            if top.casefold() in skip:
                continue
            dest = target_dir / rel
            if top.casefold() in prot and dest.exists():
                continue
            if not dry_run:
                ensure_dir(dest.parent)
                shutil.copy2(root_p / name, dest)
            count += 1
    return count


def write_identity(
    target: Path, project_id: str, project_name: str, tier: str, dry_run: bool
) -> bool:
    """Fill ``.gald3r/.identity``, inheriting install-home defaults (T476).

    Substitutes ``{project_id}`` / ``{project_name}`` and sets a ``tier=`` key,
    then layers in the centralized install-home identity defaults so org/brand/
    vault-path/provider prefs pre-populate the new identity (the cascade is
    install-home defaults -> existing identity -> these per-project values). The
    project_id/project_name/tier chosen here are the per-project overrides and win.
    Secrets are never written (the shared merge strips secret-looking keys). When
    the engine is not importable at bootstrap, falls back to the plain placeholder
    fill (still functional, just no inheritance). Also auto-provisions the shared
    ``gald3r_vault`` at the resolved location. A pre-existing, already-initialized
    identity (no ``{project_id}`` placeholder) is left untouched.

    Args:
        target: Project root containing ``.gald3r/``.
        project_id: UUID4 string for this project (T1453 behavior).
        project_name: Human project name.
        tier: Template tier label (e.g. slim/full/adv).
        dry_run: When True only print the planned write.

    Returns:
        True when the identity file was written (or would be, in dry-run).
    """
    ident = target / ".gald3r" / ".identity"
    if dry_run:
        print(f"[DRY] would write {ident} "
              f"(project_id={project_id}, project_name={project_name}, tier={tier}); "
              f"inherit install-home defaults + auto-provision gald3r_vault")
        return True
    if not ident.is_file():
        cprint(f"  Identity file not found at {ident} -- skipped.", "yellow")
        return False
    text = ident.read_text(encoding="utf-8")
    if "{project_id}" not in text:
        cprint("  Identity already initialized -- left unchanged.", "darkgray")
        return False
    new = text.replace("{project_id}", project_id)
    new = new.replace("{project_name}", project_name)
    # BUG-210: the shipped identity default `repos_location={LOCAL_REPOS}` has no
    # expander and the session-start hook only understood the `{LOCAL}` sentinel,
    # so the raw token leaked to disk (materializing a literal `{LOCAL_REPOS}/`
    # dir — BUG-209). Normalize the legacy token to the canonical `{LOCAL}`
    # sentinel here so no fresh install ever writes the dead placeholder, even if
    # an older template (or an inherited default) still carries it.
    new = new.replace("repos_location={LOCAL_REPOS}", "repos_location={LOCAL}")
    if re.search(r"^tier=.*$", new, re.MULTILINE):
        new = re.sub(r"^tier=.*$", f"tier={tier}", new, flags=re.MULTILINE)
    else:
        if not new.endswith("\n"):
            new += "\n"
        new += f"tier={tier}\n"
    ident.write_text(new, encoding="utf-8", newline="\n")

    # Inherit install-home defaults into the freshly-filled identity (T476). The
    # per-project values just written are the highest-precedence overrides; the
    # shared engine module layers install-home defaults underneath and fills gaps.
    # When the install home has no defaults file this is a no-op fallback.
    if _provision is not None:
        merged = _provision.inherit_identity(
            target / ".gald3r",
            project_overrides={"project_id": project_id,
                               "project_name": project_name, "tier": tier},
        )
        vault = _provision.provision_vault(merged)
        cprint(f"  Identity: project_id={project_id} (project: {project_name}, "
               f"tier: {tier}); inherited {len(merged)} field(s) from install home",
               "green")
        cprint(f"  Vault   : {vault}", "green")
    else:
        cprint(f"  Identity: project_id={project_id} "
               f"(project: {project_name}, tier: {tier})", "green")
    return True


def provision_engine(target: Path) -> None:
    """Run the bundled engine provisioning script (uv) in the target project.

    Errors are non-fatal -- skills fall back to SKILL.full.md when the engine
    is unavailable. T1601 (PS1-KILL epic T667): the provisioning script itself
    is now one cross-platform ``provision_engine.py`` (was ``.ps1``/``.sh``).

    Args:
        target: Project root that received ``.gald3r_sys/engine/``.
    """
    engine_dir = target / ".gald3r_sys" / "engine"
    prov_py = engine_dir / "provision_engine.py"
    if not prov_py.is_file():
        return
    cmd: List[str] = [sys.executable, str(prov_py)]
    print()
    cprint("  Provisioning the bundled gald3r engine (uv)...", "cyan")
    sys.stdout.flush()
    try:
        result = subprocess.run(cmd, cwd=str(target), check=False)
        if result.returncode != 0:
            raise OSError(f"provision script exited {result.returncode}")
    except (OSError, subprocess.SubprocessError) as exc:
        cprint(f"  Engine bootstrap skipped: {exc}", "yellow")
        cprint("  (Skills still work via their SKILL.full.md fallback.)", "darkgray")


def install_git_hooks(target: Path, template_dir: Path, dry_run: bool) -> None:
    """Run the ported install_git_hooks.py against the target project.

    Prefers the copy installed into the target (``.gald3r_sys/scripts/``),
    falling back to the template source next to this script. Non-fatal.

    Args:
        target: Project root (git repo root).
        template_dir: project_template/ directory next to this script.
        dry_run: When True only print the planned invocation.
    """
    candidates = [
        target / ".gald3r_sys" / "scripts" / "install_git_hooks.py",
        template_dir / ".gald3r_sys" / "scripts" / "install_git_hooks.py",
    ]
    script: Optional[Path] = next((c for c in candidates if c.is_file()), None)
    if script is None:
        cprint("  install_git_hooks.py not found -- git hooks step skipped.", "yellow")
        return
    if dry_run:
        print(f"[DRY] would run: {sys.executable} {script} --repo-root {target}")
        return
    print()
    cprint("  Installing gald3r git hooks...", "cyan")
    sys.stdout.flush()
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--repo-root", str(target)],
            cwd=str(target), check=False,
        )
        if result.returncode != 0:
            cprint(f"  Git hooks step exited {result.returncode} (non-fatal).", "yellow")
    except (OSError, subprocess.SubprocessError) as exc:
        cprint(f"  Git hooks step skipped: {exc}", "yellow")


def stamp_python_interpreter(target: Path, template_dir: Path,
                             dry_run: bool) -> None:
    """Stamp the host's Python interpreter into the installed hook configs.

    T1651 / BUG-207: hook trigger configs ship with the Windows-safe bare
    ``python`` token, which does not exist on stock python3-only Linux. The
    shipped stamper rewrites the leading interpreter token of every hook
    ``"command"`` string to the interpreter that actually resolves on this
    machine (``python3`` on POSIX). No-op on Windows. Prefers the copy
    installed into the target (``.gald3r_sys/scripts/``), falling back to the
    template source next to this script. Non-fatal.

    Args:
        target: Project root that received the hook configs.
        template_dir: project_template/ directory next to this script.
        dry_run: When True only print the planned invocation.
    """
    candidates = [
        target / ".gald3r_sys" / "scripts" / "stamp_python_interpreter.py",
        template_dir / ".gald3r_sys" / "scripts" / "stamp_python_interpreter.py",
    ]
    script: Optional[Path] = next((c for c in candidates if c.is_file()), None)
    if script is None:
        cprint("  stamp_python_interpreter.py not found -- interpreter "
               "stamping skipped.", "yellow")
        return
    if dry_run:
        print(f"[DRY] would run: {sys.executable} {script} "
              f"--project-root {target}")
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--project-root", str(target)],
            cwd=str(target), check=False,
        )
        if result.returncode != 0:
            cprint(f"  Interpreter stamping exited {result.returncode} "
                   "(non-fatal).", "yellow")
    except (OSError, subprocess.SubprocessError) as exc:
        cprint(f"  Interpreter stamping skipped: {exc}", "yellow")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser (kebab-case + PascalCase spellings for PS1 parity)."""
    parser = argparse.ArgumentParser(
        prog="setup_gald3r_project.py",
        description="gald3r Installer -- installs gald3r into a target project.",
        allow_abbrev=False,
    )
    parser.add_argument("--target-path", "-TargetPath", dest="target_path",
                        default="", help="Target project path (prompted if omitted).")
    parser.add_argument("--platform", "-Platform", dest="platform",
                        action="append", default=None,
                        help="Install a platform from platforms/ (default: Cursor + "
                             "Claude Code). Repeat the flag (--platform a --platform b) "
                             "or pass a comma list (--platform a,b,c) to install "
                             "several in one run.")
    parser.add_argument("--platforms", "-Platforms", dest="platforms",
                        nargs="+", default=None, metavar="PLATFORM",
                        help="Install several platforms in one run, space-separated "
                             "(--platforms a b c). Merged with any --platform values.")
    parser.add_argument("--all", "-All", dest="all_platforms",
                        action="store_true",
                        help="Install EVERY platform under platforms/ (the full "
                             "registry roster, including stub/weak overlays).")
    parser.add_argument("--all-ready", "-AllReady", dest="all_ready",
                        action="store_true",
                        help="Install every READY (>=80%%-working) platform — the "
                             "registry's derived readiness set (recommended bulk install).")
    parser.add_argument("--name", "--project-name", "-Name", "-ProjectName",
                        dest="name", default="",
                        help="Project name written to .gald3r/.identity "
                             "(default: target folder name).")
    parser.add_argument("--tier", "-Tier", dest="tier", default="",
                        help=f"Template tier label recorded in .gald3r/.identity "
                             f"(default: {TIER_DEFAULT}).")
    parser.add_argument("--force", "-Force", dest="force", action="store_true",
                        help="Skip confirmations.")
    parser.add_argument("--dry-run", "-DryRun", dest="dry_run", action="store_true",
                        help="Preview only -- print planned operations, write nothing.")
    parser.add_argument("--no-engine", "-NoEngine", dest="no_engine",
                        action="store_true",
                        help="Skip provisioning the bundled gald3r engine (uv); "
                             "skills then use SKILL.full.md.")
    parser.add_argument("--non-interactive", "-NonInteractive",
                        dest="non_interactive", action="store_true",
                        help="Never prompt; auto-answer every prompt with its "
                             "default and emit [AUTO] lines (CI mode).")
    return parser


def _split_platform_values(raw: Sequence[str]) -> List[str]:
    """Flatten repeated/comma-joined --platform values into lowercase tokens.

    Accepts the append-list from ``--platform`` (each item may itself be a comma
    list, e.g. ``--platform a,b``) plus the space-separated ``--platforms`` list,
    and yields cleaned, lowercased, non-empty tokens.
    """
    out: List[str] = []
    for item in raw:
        for token in str(item).split(","):
            token = token.strip().lower()
            if token:
                out.append(token)
    return out


def resolve_platforms(
    args: argparse.Namespace,
    available_platforms: Sequence[str],
) -> Tuple[List[str], Optional[str]]:
    """Resolve all platform-selection flags into one ordered, deduped roster (T533).

    Combines ``--platform`` (repeatable / comma list), ``--platforms`` (space list),
    ``--all`` (every overlay) and ``--all-ready`` (the registry's derived
    >=80%-working set). An EMPTY result means "no explicit platform" — the caller
    keeps the historical default (Cursor + Claude Code). Back-compat: a single
    ``--platform x`` resolves to ``["x"]`` exactly as before.

    Args:
        args: Parsed CLI namespace.
        available_platforms: The platforms/ overlay directory names (the ship roster).

    Returns:
        ``(platforms, error)``. On success ``error`` is None and ``platforms`` is the
        ordered selection ([] = default). On an unknown name, ``error`` is a message
        and ``platforms`` is empty.
    """
    available = set(available_platforms)
    selected: List[str] = []

    def _add(names: Sequence[str]) -> None:
        for n in names:
            if n not in selected:
                selected.append(n)

    # --all-ready: the derived readiness set (reuse the shared registry reader; fall
    # back to every available overlay if the reader/registry is unavailable).
    if getattr(args, "all_ready", False):
        if _registry is not None and hasattr(_registry, "ready_platforms"):
            ready = [p for p in _registry.ready_platforms() if p in available]
            _add(ready if ready else sorted(available))
        else:
            _add(sorted(available))

    # --all: every overlay directory under platforms/.
    if getattr(args, "all_platforms", False):
        _add(sorted(available))

    # Explicit names from --platform (append/comma) and --platforms (space list).
    explicit: List[str] = []
    if getattr(args, "platform", None):
        explicit += _split_platform_values(args.platform)
    if getattr(args, "platforms", None):
        explicit += _split_platform_values(args.platforms)
    _add(explicit)

    # Validate explicit names against the available roster (skip when we have no
    # roster to validate against, mirroring the prior single-platform behavior).
    if available_platforms:
        unknown = [p for p in selected if p not in available]
        if unknown:
            return [], (f"Unknown platform(s): {', '.join(unknown)}. "
                        f"Available: {', '.join(sorted(available))}")
    return selected, None


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Returns a process exit code (0 ok / 1 error)."""
    args = build_parser().parse_args(argv)
    non_interactive = args.non_interactive

    # -- Resolve paths -----------------------------------------------------------
    script_dir = Path(__file__).resolve().parent
    template_dir = script_dir / "project_template"
    platforms_dir = script_dir / "platforms"

    if not template_dir.is_dir():
        cprint("ERROR: Cannot find project_template/ next to this script.", "red")
        return 1

    available_platforms = (
        sorted(p.name for p in platforms_dir.iterdir() if p.is_dir())
        if platforms_dir.is_dir() else []
    )

    # -- Resolve / prompt for platform(s) ----------------------------------------
    # T533: multi-select — --platform (repeatable / comma list), --platforms (space
    # list), --all, --all-ready all fold into one ordered roster. An empty roster
    # keeps the historical Cursor + Claude Code default.
    platforms, plat_error = resolve_platforms(args, available_platforms)
    if plat_error:
        cprint(f"  {plat_error}", "yellow")
        return 1

    if REQUIRE_PLATFORM and not platforms:
        print()
        cprint("  gald3r Installer", "cyan")
        cprint("  -----------------------------------------", "darkgray")
        print("  Available platforms:")
        for name in available_platforms:
            cprint(f"    * {name}", "darkgray")
        print()
        answer = ask("  Platform(s) (e.g. cursor, claude, windsurf; comma-separated)",
                     "", non_interactive)
        platforms, plat_error = resolve_platforms(
            argparse.Namespace(platform=[answer], platforms=None,
                               all_platforms=False, all_ready=False),
            available_platforms,
        )
        if plat_error:
            cprint(f"  {plat_error}", "yellow")
            return 1

    # -- Prompt for target path ---------------------------------------------------
    target_path = args.target_path.strip()
    if not target_path:
        if not non_interactive:
            print()
            cprint("  gald3r Installer", "cyan")
            cprint("  -----------------------------------------", "darkgray")
            if not platforms:
                print("  Default: Cursor + Claude Code. "
                      "Use --platform <name> (repeatable), --all, or --all-ready "
                      "to install more.")
                if available_platforms:
                    cprint(f"  Platforms: {', '.join(available_platforms)}", "darkgray")
            else:
                print(f"  Platform(s): {', '.join(platforms)}")
            print()
        target_path = ask("  Target project path", str(Path.cwd()), non_interactive)

    target = Path(target_path.rstrip("\\/")).expanduser()

    # -- Project identity prompts (T1586 — written to .gald3r/.identity) ----------
    project_name = args.name.strip() or ask("  Project name", target.name,
                                            non_interactive)
    tier = (args.tier.strip().lower()
            or ask("  Tier (slim/full/adv)", TIER_DEFAULT, non_interactive).lower())
    project_id = str(uuid.uuid4())

    # -- Create target if missing --------------------------------------------------
    if not target.exists():
        if not args.force:
            if not confirm(f"  '{target}' does not exist. Create it?",
                           non_interactive):
                print("Aborted.")
                return 0
        if args.dry_run:
            print(f"[DRY] would create directory: {target}")
        else:
            ensure_dir(target)
            cprint(f"  Created: {target}", "green")

    # -- Warn on existing .gald3r/ -------------------------------------------------
    if (target / ".gald3r").exists() and not args.force and not args.dry_run:
        print()
        cprint("  WARNING: .gald3r/ already exists. "
               "Tasks/bugs/plans will NOT be overwritten.", "yellow")
        if not confirm("  Update gald3r config files?", non_interactive):
            print("Aborted.")
            return 0

    # -- Install layers --------------------------------------------------------------
    # T533: multi-platform. The shared project_template/ base is copied ONCE; the
    # tier1 IDE config (.cursor/.claude) lives in that base, so we only skip the
    # tier1 dirs that were NOT selected. Each selected non-tier1 platform then gets
    # its overlay copied on top. The empty-selection default keeps BOTH tier1 dirs.
    protected = [".gald3r"]
    tier1 = ["cursor", "claude"] if not REQUIRE_PLATFORM else []

    # Split the selection into tier1 (config lives in the base) vs overlay platforms.
    selected_tier1 = [p for p in platforms if p in tier1]
    overlay_platforms = [p for p in platforms if p not in tier1]

    # Which tier1 config dirs to keep in the base copy.
    tier1_dir = {"cursor": ".cursor", "claude": ".claude"}
    if not platforms:
        # Default: Cursor + Claude Code -> keep both tier1 dirs.
        keep_tier1 = set(tier1)
    elif selected_tier1:
        # Explicit tier1 selection -> keep exactly those that were requested.
        keep_tier1 = set(selected_tier1)
    else:
        # Only non-tier1 platforms selected -> base ships no tier1 IDE config.
        keep_tier1 = set()
    skip_dirs = [tier1_dir[t] for t in tier1 if t not in keep_tier1]

    # Human-facing label for the install banner.
    if not platforms:
        label = "Cursor + Claude Code (default)"
    else:
        pretty = {"cursor": "Cursor", "claude": "Claude Code"}
        label = ", ".join(pretty.get(p, p) for p in platforms)

    print()
    if args.dry_run:
        cprint("  DRY RUN -- no files will be written", "yellow")
    cprint(f"  Installing gald3r [{label}] into: {target}", "cyan")
    print()

    total = 0
    n1 = copy_layer(template_dir, target, skip_top_dirs=skip_dirs,
                    protected=protected, dry_run=args.dry_run)
    total += n1
    if args.dry_run:
        print(f"[DRY] would copy {n1} files from project_template/")
    print(f"  Base   : {n1} files  (project_template/)")

    if platforms_dir.is_dir():
        for plat in overlay_platforms:
            plat_dir = platforms_dir / plat
            if not plat_dir.is_dir():
                continue
            n2 = copy_layer(plat_dir, target, protected=protected,
                            dry_run=args.dry_run)
            total += n2
            if args.dry_run:
                print(f"[DRY] would copy {n2} files from platforms/{plat}/")
            print(f"  Config : {n2} files  (platforms/{plat}/)")

    # -- Identity / engine / hooks ----------------------------------------------------
    print()
    if args.dry_run:
        write_identity(target, project_id, project_name, tier, dry_run=True)
        if not args.no_engine:
            print(f"[DRY] would provision engine via "
                  f"{target / '.gald3r_sys' / 'engine'} (uv)")
        install_git_hooks(target, template_dir, dry_run=True)
        stamp_python_interpreter(target, template_dir, dry_run=True)
        cprint(f"  Dry run -- would copy {total} files.", "yellow")
        return 0

    cprint(f"  Done. {total} files installed.", "green")
    write_identity(target, project_id, project_name, tier, dry_run=False)

    if not args.no_engine:
        provision_engine(target)

    install_git_hooks(target, template_dir, dry_run=False)

    stamp_python_interpreter(target, template_dir, dry_run=False)

    print()
    cprint("  Next steps:", "cyan")
    if not platforms or "cursor" in platforms:
        print("   Cursor      : open project, run @g-setup")
    if not platforms or "claude" in platforms:
        print("   Claude Code : open project, run /g-setup")
    for plat in overlay_platforms:
        print(f"   {plat} : open project in {plat} -- "
              ".gald3r/ brain and AGENTS.md are ready")
    print()
    cprint("  Docs: https://github.com/wrm3/gald3r", "darkgray")
    return 0


if __name__ == "__main__":
    sys.exit(main())
