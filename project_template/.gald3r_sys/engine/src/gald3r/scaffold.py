"""Project scaffolding orchestration: `gald3r init` / `gald3r update` (T477, epic T470).

This module is the thin ORCHESTRATION + PROJECT.md param-seeding layer for the
``gald3r init`` (scaffold a fresh gald3r PROJECT into a target folder) and
``gald3r update`` (route a target folder to the safe-update path) CLI verbs. It
deliberately re-implements nothing that already exists:

* **Scaffold** delegates to the canonical installer
  ``gald3r_core/setup_gald3r_project.py`` (the SAME ``g-skl-setup`` machinery
  that ``@g-setup`` runs) — it copies ``project_template/`` into the target,
  fills ``.gald3r/.identity`` and, via :mod:`gald3r.provision` (T476), inherits
  install-home / identity defaults. We invoke it as a subprocess with
  ``--target-path`` / ``--name`` / ``--tier`` / ``--non-interactive`` /
  ``--dry-run`` (its existing flag surface), exactly the way the installer itself
  shells out to ``provision_engine`` / ``install_git_hooks``.
* **PROJECT.md param-seeding** is the one genuinely new piece: the installer
  seeds ``.identity`` but leaves ``.gald3r/PROJECT.md`` as a template with
  ``{PROJECT_NAME}`` / ``*placeholder*`` sections. :func:`seed_project_md` fills
  the name, mission/description, and tech-stack from the passed params, falling
  back to install-home/identity defaults (T476) or the template placeholders for
  anything unspecified.
* **Update** routes to the shared T473 safe-update core
  (:class:`gald3r.systems.upgrade.UpgradeSystem`) — the CLI's existing
  ``upgrade`` executor is reused; this module only resolves the target folder.

Verb scheme (does NOT collide with T472's ``gald3r setup <agent|throne|all>``):
``setup`` keeps its T472 PRODUCT semantics (a positional ``agent|throne|all``,
install-home install). The PROJECT scaffold is a DISTINCT top-level verb
``gald3r init`` (no positional product), and the project-folder update is
``gald3r update`` (a thin alias onto the existing ``upgrade`` core). The two
``init``/``setup`` shapes never share a positional, so argparse never has to
disambiguate them.

Pure stdlib (``os`` / ``pathlib`` / ``subprocess`` / ``re``) plus the engine's
own :mod:`gald3r.provision` / :mod:`gald3r.store` helpers — zero new dependency,
so it runs anywhere uv puts a Python.

@subsystems: PROJECT_IDENTITY_SETUP
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from gald3r import provision as _provision
from gald3r.store import split_doc

#: Env var that overrides where the canonical installer
#: (``setup_gald3r_project.py`` + its ``project_template/``) is found. Mirrors
#: the override-then-env-then-walk-up discipline of
#: :func:`gald3r.install.resolve_products_root`.
INSTALLER_ENV_VAR = "GALD3R_INSTALLER"

#: Filename of the canonical installer the scaffold step delegates to.
INSTALLER_NAME = "setup_gald3r_project.py"

#: The directory that ships next to the installer and is copied into the target.
TEMPLATE_DIR_NAME = "project_template"

#: Sibling subdirs (relative to an ancestor of the engine package) that may hold
#: the installer + its ``project_template/``. These fixed names were calibrated to
#: the engine's *original* home (``gald3r_templates/gald3r-engine/``), where
#: ``gald3r_templates/`` is an ancestor and ``gald3r_core/`` a sibling. The engine
#: later relocated to ``.gald3r_sys/engine/`` but this table did not move with it
#: (BUG-167) — so :func:`resolve_installer` no longer relies on these names alone;
#: it ALSO marker-discovers a nested ``gald3r_core/`` at each ancestor, making
#: resolution independent of where the engine package itself sits.
_INSTALLER_SUBDIRS = ("", "gald3r_core")

#: Default project tier when none is passed (mirrors the installer's TIER_DEFAULT).
DEFAULT_TIER = "full"

#: PROJECT.md section headings (and their template placeholder bodies) the param
#: seed fills. Each maps a CLI param -> (markdown ``## heading``, placeholder body
#: pattern that marks "still a template"). The body is replaced only when it is
#: still the placeholder (don't clobber a user-edited section).
_PROJECT_MD_NAME = "PROJECT.md"


class ScaffoldError(Exception):
    """Raised when scaffolding cannot proceed (installer not found, etc.)."""


@dataclass
class ScaffoldPlan:
    """A resolved, serializable plan for ``gald3r init`` against a target folder."""

    target: str
    mode: str                          # "scaffold" | "update" (don't-clobber routes here)
    installer: Optional[str] = None    # resolved setup_gald3r_project.py
    name: str = ""
    tier: str = DEFAULT_TIER
    project_md_seed: Dict[str, str] = field(default_factory=dict)  # heading -> body
    actions: List[str] = field(default_factory=list)
    already_initialized: bool = False  # target already has .gald3r/

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "mode": self.mode,
            "installer": self.installer,
            "name": self.name,
            "tier": self.tier,
            "project_md_seed": dict(self.project_md_seed),
            "actions": list(self.actions),
            "already_initialized": self.already_initialized,
        }


def resolve_installer(override: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Resolve the canonical ``setup_gald3r_project.py`` installer (or None).

    Resolution order (mirrors :func:`gald3r.install.resolve_products_root`):

        1. explicit ``override`` argument (tests / embedding callers)
        2. ``GALD3R_INSTALLER`` env var (a path to the installer or its dir)
        3. walk up from this engine package until a directory is found that holds
           BOTH ``setup_gald3r_project.py`` AND ``project_template/``

    Returns the resolved installer script path, or ``None`` when no candidate is
    found (callers turn that into a fail-loud :class:`ScaffoldError`).
    """
    if override:
        p = Path(override).expanduser().resolve()
        if p.is_dir():
            cand = p / INSTALLER_NAME
            return cand if cand.is_file() else None
        return p if p.is_file() else None
    env_value = os.environ.get(INSTALLER_ENV_VAR, "").strip()
    if env_value:
        p = Path(env_value).expanduser().resolve()
        if p.is_dir():
            cand = p / INSTALLER_NAME
            return cand if cand.is_file() else None
        return p if p.is_file() else None
    here = Path(__file__).resolve()
    for parent in here.parents:
        bases = [parent / sub if sub else parent for sub in _INSTALLER_SUBDIRS]
        # Marker-anchored discovery (BUG-167): also look for a nested ``gald3r_core/``
        # one level below this ancestor (e.g. the post-relocation
        # ``gald3r_templates/gald3r_core/`` layout) so resolution does not depend on
        # where the engine package itself lives. We anchor on the installer marker,
        # not the engine's position.
        try:
            bases += [child / "gald3r_core" for child in parent.iterdir() if child.is_dir()]
        except OSError:
            pass
        for base in bases:
            cand = base / INSTALLER_NAME
            if cand.is_file() and (base / TEMPLATE_DIR_NAME).is_dir():
                return cand
    return None


def is_initialized(target: Path) -> bool:
    """Return True when ``target`` already contains a gald3r project (``.gald3r/``)."""
    return (Path(target) / ".gald3r").is_dir()


# ── PROJECT.md param-seeding (the new layer) ───────────────────────────────────

#: Map of CLI seed param -> (PROJECT.md ``## heading``). The body under each
#: heading is replaced from the param ONLY while it is still the template
#: placeholder (an italic ``*...*`` line), so a user-edited section is never
#: clobbered. ``--name`` is special: it fills the ``# PROJECT.md — {PROJECT_NAME}``
#: title line, not a ``## section``.
PROJECT_MD_SECTIONS: Dict[str, str] = {
    "description": "Mission",
    "vision": "Vision",
    "tech_stack": "Tech Stack",
}


def _build_seed(
    *,
    name: str = "",
    description: str = "",
    vision: str = "",
    tech_stack: str = "",
    fallback: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Build the ``{heading: body}`` PROJECT.md seed from params + identity fallback.

    Unspecified fields fall back to install-home/identity defaults (T476) when a
    matching key exists (``description`` / ``vision`` / ``tech_stack``), otherwise
    they are simply omitted from the seed (the template placeholder is kept). The
    project name is carried under the synthetic ``"__name__"`` key.
    """
    fb = fallback or {}
    seed: Dict[str, str] = {}
    resolved_name = name.strip() or str(fb.get("project_name", "")).strip()
    if resolved_name and not _provision._is_unset(resolved_name):
        seed["__name__"] = resolved_name
    for param, value in (("description", description), ("vision", vision),
                         ("tech_stack", tech_stack)):
        text = value.strip() or str(fb.get(param, "")).strip()
        if text and not _provision._is_unset(text):
            seed[PROJECT_MD_SECTIONS[param]] = text
    return seed


def _replace_placeholder_section(text: str, heading: str, body: str) -> str:
    """Replace the body under ``## {heading}`` only when it is still a placeholder.

    The template marks an unfilled section with a single italic line
    (``*...*``). When that placeholder is present directly under the heading it is
    replaced with ``body``; an already-filled (user-edited) section is left as-is.
    """
    pattern = re.compile(
        r"(^##[ \t]+" + re.escape(heading) + r"[ \t]*\n\n)"  # heading + its blank line
        r"(\*[^\n]*\*[ \t]*\n)",                              # the italic placeholder line only
        re.MULTILINE,
    )
    # Keep the heading + its following blank line (group 1); the trailing blank
    # line after the placeholder (in the template) is left intact, so the seeded
    # body stays cleanly separated from the next ## section.
    return pattern.sub(lambda m: f"{m.group(1)}{body}\n", text, count=1)


def seed_project_md(target: Path, seed: Dict[str, str], *, dry_run: bool = False) -> bool:
    """Seed ``.gald3r/PROJECT.md`` basics (title + sections) from ``seed``. Writes.

    ``seed`` is ``{"__name__": project_name, "Mission": body, "Vision": body,
    "Tech Stack": body, ...}`` as built by :func:`_build_seed`. The title line
    ``# PROJECT.md — {PROJECT_NAME}`` is filled with the name; each ``## heading``
    placeholder body is replaced (without clobbering a user-edited section). The
    PROJECT.md frontmatter and unrelated sections are preserved verbatim.

    Returns True when PROJECT.md exists and (would be) updated; False when the file
    is absent or the seed is empty. Idempotent — re-seeding a filled PROJECT.md
    only touches sections that are still placeholders.
    """
    project_md = Path(target) / ".gald3r" / _PROJECT_MD_NAME
    if not project_md.is_file() or not seed:
        return False
    original = project_md.read_text(encoding="utf-8-sig")
    text = original

    name = seed.get("__name__")
    if name:
        # Title line: "# PROJECT.md — {PROJECT_NAME}" (template) or a prior name.
        text = re.sub(
            r"^(#\s+PROJECT\.md\s+—\s+).*$",
            lambda m: f"{m.group(1)}{name}",
            text,
            count=1,
            flags=re.MULTILINE,
        )

    for heading, body in seed.items():
        if heading == "__name__":
            continue
        text = _replace_placeholder_section(text, heading, body)

    if text == original:
        return True  # nothing to change (already filled / no placeholder) — still "present"
    if dry_run:
        return True
    project_md.write_text(text, encoding="utf-8", newline="\n")
    return True


# ── scaffold planning + execution ──────────────────────────────────────────────


def plan_scaffold(
    *,
    target: Optional[Union[str, Path]] = None,
    name: str = "",
    description: str = "",
    vision: str = "",
    tech_stack: str = "",
    tier: str = "",
    installer: Optional[Union[str, Path]] = None,
    home: Optional[Path] = None,
) -> ScaffoldPlan:
    """Plan ``gald3r init`` against a target folder (no side effects).

    Resolves the target (CWD when omitted), the canonical installer, the project
    name (param -> identity default -> target folder name), the tier, and the
    PROJECT.md param seed (with install-home/identity fallback per T476). When the
    target already contains a gald3r project the plan's ``mode`` is ``"update"``
    (don't-clobber: the caller routes to the safe-update path instead of re-init).

    Raises:
        ScaffoldError: when no installer can be located (fail-loud, no fake init).
    """
    tgt = Path(target).expanduser().resolve() if target else Path.cwd().resolve()
    inst = resolve_installer(installer)
    if inst is None:
        raise ScaffoldError(
            f"canonical installer '{INSTALLER_NAME}' not found. Set "
            f"{INSTALLER_ENV_VAR} to the installer (or the dir holding it + "
            f"{TEMPLATE_DIR_NAME}/)."
        )

    # Identity/install-home defaults are the seed fallback (T476). Read the merged
    # defaults so name/description/tech_stack can inherit when unspecified.
    fallback = _provision.load_install_home_defaults(home=home)

    resolved_name = name.strip() or str(fallback.get("project_name", "")).strip() or tgt.name
    resolved_tier = (tier.strip().lower()
                     or str(fallback.get("tier", "")).strip().lower()
                     or DEFAULT_TIER)
    seed = _build_seed(name=resolved_name, description=description, vision=vision,
                       tech_stack=tech_stack, fallback=fallback)

    already = is_initialized(tgt)
    plan = ScaffoldPlan(
        target=str(tgt),
        mode="update" if already else "scaffold",
        installer=str(inst),
        name=resolved_name,
        tier=resolved_tier,
        project_md_seed=seed,
        already_initialized=already,
    )
    if already:
        plan.actions = [
            f"target {tgt} already contains a gald3r project (.gald3r/) — "
            f"NOT re-initializing (don't-clobber).",
            "route to the safe-update path: gald3r update --target "
            f"\"{tgt}\"  (T473 backup -> migrate -> rollback).",
        ]
        return plan

    if not tgt.exists():
        plan.actions.append(f"create target folder: {tgt}")
    plan.actions.append(
        f"scaffold via {inst} --target-path \"{tgt}\" --name \"{resolved_name}\" "
        f"--tier {resolved_tier} --non-interactive  (copies project_template/, "
        f"fills .identity, inherits install-home defaults)"
    )
    seed_desc = ", ".join(
        ("name" if k == "__name__" else k) for k in seed
    ) or "(none — template placeholders kept)"
    plan.actions.append(f"seed .gald3r/PROJECT.md basics: {seed_desc}")
    return plan


def execute_scaffold(plan: ScaffoldPlan, *, dry_run: bool = False) -> List[str]:
    """Execute a resolved :class:`ScaffoldPlan` (delegating to the installer). Returns log.

    Scaffold path: create the target if missing, run the canonical installer with
    ``--non-interactive`` (and ``--dry-run`` when ``dry_run``), then seed PROJECT.md
    from the plan's param seed. Update path (``mode == "update"``) is a no-op here —
    the CLI routes those to the shared upgrade executor; this returns a routing note.

    Raises:
        ScaffoldError: when the installer subprocess fails (fail-loud; no fake init).
    """
    log: List[str] = []
    if plan.mode == "update":
        log.append(plan.actions[0] if plan.actions else "target already initialized")
        log.append("routing to the safe-update path (gald3r update).")
        return log

    target = Path(plan.target)
    if not dry_run and not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        log.append(f"created target: {target}")

    if plan.installer is None:  # pragma: no cover - plan_scaffold guarantees it
        raise ScaffoldError("no installer resolved in plan")

    cmd = [
        sys.executable, plan.installer,
        "--target-path", plan.target,
        "--name", plan.name,
        "--tier", plan.tier,
        "--non-interactive",
    ]
    if dry_run:
        cmd.append("--dry-run")
    log.append("$ " + " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ScaffoldError(f"installer invocation failed: {exc}") from exc
    if result.stdout:
        log.extend(line for line in result.stdout.splitlines() if line.strip())
    if result.returncode != 0:
        if result.stderr:
            log.append(result.stderr.strip())
        raise ScaffoldError(
            f"installer exited {result.returncode} for target {plan.target} "
            f"(no stub, no fake success)."
        )

    seeded = seed_project_md(target, plan.project_md_seed, dry_run=dry_run)
    if seeded:
        verb = "[dry-run] would seed" if dry_run else "seeded"
        log.append(f"{verb} .gald3r/PROJECT.md from params")
    return log
