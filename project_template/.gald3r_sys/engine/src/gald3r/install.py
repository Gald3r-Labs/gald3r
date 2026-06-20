"""Per-OS install + setup planning for gald3r products (T472, epic T470).

This module is the SINGLE place that decides, for the detected host OS, *which*
artifact installs gald3r_agent and gald3r_throne and *where* it lives. It mirrors
the "one resolver, override -> env -> default" discipline that
:mod:`gald3r.home` (T471) and :mod:`gald3r_forge.paths` (T412) already establish,
and it composes with :mod:`gald3r.home`: ``setup`` targets the centralized install
home, never a per-repo ``.gald3r/``.

Two products are handled:

* **agent** (gald3r_agent) -- a Python/CLI runtime installed via ``uv`` (no bare
  pip/venv; g-rl-09). Installable from source on any OS uv supports.
* **throne** (gald3r_throne) -- a Tauri desktop app whose per-OS bundle (Windows
  NSIS/MSI, macOS .dmg/.app, Linux .deb/.AppImage/.rpm) is produced by the
  existing ``npm run tauri:build`` pipeline (cf. ``gald3r_throne/scripts/
  verify_packaged.ps1`` stage 7). This module does NOT re-implement packaging --
  it *locates* the bundle the throne build produced and **fails loud**
  (:class:`MissingArtifactError`) with the exact build command when the per-OS
  bundle is absent. There is no silent stub / fake-success path (spec / g-rl-34).

Everything here is pure planning over ``os`` / ``pathlib`` / ``platform`` plus the
filesystem (bundle discovery): no subprocess is launched, so the planning surface
is fully unit-testable by monkeypatching ``platform.system()`` and pointing the
products root at a temp tree. The CLI (:mod:`gald3r.adapters.cli`) is the thin
executor that turns a plan into actions and honours ``--dry-run``.
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from gald3r import home as _home

#: Product identifiers (the install/setup verbs operate on these).
PRODUCT_AGENT = "agent"
PRODUCT_THRONE = "throne"
PRODUCT_ALL = "all"
PRODUCTS = (PRODUCT_AGENT, PRODUCT_THRONE)

#: Normalized host-OS tokens (the only OS vocabulary the rest of the module uses).
OS_WINDOWS = "windows"
OS_MACOS = "macos"
OS_LINUX = "linux"

#: Env var that overrides where the product source trees (gald3r_throne/ and
#: gald3r_agent/) are found. Mirrors gald3r_forge.paths' override-then-env rule.
PRODUCTS_ROOT_ENV_VAR = "GALD3R_PRODUCTS_ROOT"

#: Source-tree directory names of the two products, relative to the products root.
AGENT_DIR_NAME = "gald3r_agent"
THRONE_DIR_NAME = "gald3r_throne"

#: Where `npm run tauri:build` drops bundles, relative to gald3r_throne/.
THRONE_BUNDLE_REL = Path("src-tauri") / "target" / "release" / "bundle"

#: Per-OS bundle subdir + filename glob the throne build emits. A list because a
#: single `tauri build` with `targets: "all"` can emit several formats per OS; the
#: first existing match wins, but all are reported in the plan / error message.
_THRONE_BUNDLE_PATTERNS: Dict[str, List[tuple]] = {
    OS_WINDOWS: [("nsis", "*-setup.exe"), ("msi", "*.msi")],
    OS_MACOS: [("dmg", "*.dmg"), ("macos", "*.app")],
    OS_LINUX: [("deb", "*.deb"), ("appimage", "*.AppImage"), ("rpm", "*.rpm")],
}

#: The throne build command (run from gald3r_throne/). `:build` colon matters --
#: `tauri:build` builds the real client; `build` is the frontend-only step. The
#: `--features reqwest` flag is carried by the npm script itself.
THRONE_BUILD_COMMAND = "npm install && npm run tauri:build"


class InstallError(Exception):
    """Base class for install/setup planning failures."""


class MissingArtifactError(InstallError):
    """Raised when a required per-OS artifact is absent.

    This is the fail-loud path the spec mandates: throne per-OS bundles require a
    full CI/host build, and the install command must never silently stub or fake
    success. The message names the missing artifact, where it was looked for, and
    the exact command that produces it.
    """


@dataclass
class InstallPlan:
    """A resolved, serializable plan for installing one product on this host."""

    product: str
    host_os: str
    method: str                       # "tauri-bundle" | "uv-runtime"
    artifact: Optional[str] = None    # resolved bundle path (throne) when present
    source_dir: Optional[str] = None  # product source tree (agent) / throne dir
    actions: List[str] = field(default_factory=list)
    path_changes: List[str] = field(default_factory=list)
    bundle_search: List[str] = field(default_factory=list)  # globs consulted
    artifact_present: bool = True     # False -> fail-loud on a non-dry-run execute
    build_command: Optional[str] = None  # how to produce a missing artifact

    def to_dict(self) -> dict:
        return {
            "product": self.product,
            "host_os": self.host_os,
            "method": self.method,
            "artifact": self.artifact,
            "source_dir": self.source_dir,
            "actions": list(self.actions),
            "path_changes": list(self.path_changes),
            "bundle_search": list(self.bundle_search),
            "artifact_present": self.artifact_present,
            "build_command": self.build_command,
        }


@dataclass
class SetupPlan:
    """A resolved, serializable plan for initializing one product's home state."""

    product: str
    home: str
    actions: List[str] = field(default_factory=list)
    paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "product": self.product,
            "home": self.home,
            "actions": list(self.actions),
            "paths": dict(self.paths),
        }


def host_os(system: Optional[str] = None) -> str:
    """Return the normalized host-OS token for the current (or given) platform.

    This is the ONE OS-detection point for install/setup. It consumes the same
    ``platform.system()`` value :mod:`gald3r.home` keys its per-OS defaults on, so
    the two modules never disagree about what "this OS" is.

    Args:
        system: Override for ``platform.system()`` (tests). When None, the live
            value is read.

    Returns:
        ``"windows"`` / ``"macos"`` / ``"linux"`` (Linux is the fallback for any
        other POSIX, matching ``home._os_default_home``).
    """
    sysname = system if system is not None else platform.system()
    if sysname == "Windows":
        return OS_WINDOWS
    if sysname == "Darwin":
        return OS_MACOS
    return OS_LINUX


def resolve_products_root(override: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Resolve the directory that contains gald3r_agent/ and gald3r_throne/.

    Resolution order (mirrors gald3r_forge.paths.resolve_workspace_root):

        1. explicit ``override`` argument (tests / embedding callers)
        2. ``GALD3R_PRODUCTS_ROOT`` environment variable
        3. walk up from this engine package until a directory is found that holds
           BOTH product source trees (the monorepo / ecosystem root)

    Returns the resolved root, or ``None`` when no candidate contains the product
    trees (callers turn that into a fail-loud :class:`MissingArtifactError`). No
    hardcoded drive letter or separator -- pure ``pathlib`` walk-up.
    """
    if override:
        return Path(override).expanduser().resolve()
    env_value = os.environ.get(PRODUCTS_ROOT_ENV_VAR, "").strip()
    if env_value:
        return Path(env_value).expanduser().resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / THRONE_DIR_NAME).is_dir() and (parent / AGENT_DIR_NAME).is_dir():
            return parent
    return None


def throne_dir(products_root: Optional[Path]) -> Optional[Path]:
    """Return the gald3r_throne/ source dir under ``products_root`` (or None)."""
    if products_root is None:
        return None
    cand = products_root / THRONE_DIR_NAME
    return cand if cand.is_dir() else None


def agent_dir(products_root: Optional[Path]) -> Optional[Path]:
    """Return the gald3r_agent/ source dir under ``products_root`` (or None)."""
    if products_root is None:
        return None
    cand = products_root / AGENT_DIR_NAME
    return cand if cand.is_dir() else None


def _throne_bundle_search(throne: Path, os_token: str) -> List[Path]:
    """Return the per-OS bundle glob roots consulted for ``os_token``."""
    bundle_root = throne / THRONE_BUNDLE_REL
    return [bundle_root / sub / pattern
            for sub, pattern in _THRONE_BUNDLE_PATTERNS.get(os_token, [])]


def find_throne_bundle(throne: Path, os_token: str) -> Optional[Path]:
    """Locate the per-OS throne bundle the build produced, or None when absent.

    Does NOT build anything -- it only inspects ``src-tauri/target/release/bundle``
    for the formats the host OS expects. The first existing match wins.
    """
    bundle_root = throne / THRONE_BUNDLE_REL
    for sub, pattern in _THRONE_BUNDLE_PATTERNS.get(os_token, []):
        sub_dir = bundle_root / sub
        if sub_dir.is_dir():
            matches = sorted(sub_dir.glob(pattern))
            if matches:
                return matches[0]
    return None


def _missing_throne_message(throne: Path, os_token: str,
                            search: List[Path]) -> str:
    """Build the fail-loud message for a missing per-OS throne bundle."""
    fmts = ", ".join(sub for sub, _ in _THRONE_BUNDLE_PATTERNS.get(os_token, [])) \
        or "(none for this OS)"
    looked = "\n    ".join(str(s) for s in search) or "(no bundle dir)"
    return (
        f"gald3r_throne bundle for host OS '{os_token}' not found.\n"
        f"  Expected one of these formats: {fmts}\n"
        f"  Looked under:\n    {looked}\n"
        f"  Throne per-OS bundles are produced by a full host/CI build -- there is\n"
        f"  no prebuilt artifact in the source tree. To produce it, on a {os_token}\n"
        f"  host run (from {throne}):\n"
        f"      {THRONE_BUILD_COMMAND}\n"
        f"  (cross-OS bundles must be built on each target OS or a per-OS CI runner.)"
    )


def plan_install(
    product: str,
    *,
    os_token: Optional[str] = None,
    products_root: Optional[Union[str, Path]] = None,
    home: Optional[Path] = None,
) -> InstallPlan:
    """Plan installing one product on the host OS (no side effects).

    Args:
        product: :data:`PRODUCT_AGENT` or :data:`PRODUCT_THRONE`.
        os_token: Override host-OS detection (tests). Defaults to :func:`host_os`.
        products_root: Override the products-source root (tests / embedding).
        home: Pre-resolved install home (defaults to :func:`gald3r.home`).

    Returns:
        An :class:`InstallPlan`. For throne, ``artifact_present`` is False (and
        ``artifact`` is None) when the per-OS bundle is missing -- the executor
        must then raise :class:`MissingArtifactError` rather than proceed.

    Raises:
        ValueError: on an unknown product.
        MissingArtifactError: when the product source tree cannot be located.
    """
    if product not in PRODUCTS:
        raise ValueError(f"unknown product '{product}' (expected one of {PRODUCTS})")
    otoken = os_token if os_token is not None else host_os()
    root = resolve_products_root(products_root)
    install_home = home if home is not None else _home.resolve_install_home()
    bin_dir = install_home / "bin"

    if product == PRODUCT_AGENT:
        adir = agent_dir(root)
        if adir is None:
            raise MissingArtifactError(
                f"gald3r_agent source tree not found under products root "
                f"({root or 'unresolved'}). Set {PRODUCTS_ROOT_ENV_VAR} to the "
                f"directory that contains {AGENT_DIR_NAME}/ and {THRONE_DIR_NAME}/."
            )
        return InstallPlan(
            product=PRODUCT_AGENT,
            host_os=otoken,
            method="uv-runtime",
            source_dir=str(adir),
            artifact_present=True,
            actions=[
                f"uv sync --project \"{adir}\"  (create/refresh the agent venv)",
                f"register global `gald3r` launcher in {bin_dir} "
                f"(reuses install_global_cli; idempotent)",
            ],
            path_changes=[f"ensure {bin_dir} on user PATH (idempotent)"],
        )

    # product == PRODUCT_THRONE
    tdir = throne_dir(root)
    if tdir is None:
        raise MissingArtifactError(
            f"gald3r_throne source tree not found under products root "
            f"({root or 'unresolved'}). Set {PRODUCTS_ROOT_ENV_VAR} to the "
            f"directory that contains {THRONE_DIR_NAME}/ and {AGENT_DIR_NAME}/."
        )
    search = _throne_bundle_search(tdir, otoken)
    bundle = find_throne_bundle(tdir, otoken)
    if bundle is None:
        # Fail-loud plan: artifact_present=False, with the exact build command.
        return InstallPlan(
            product=PRODUCT_THRONE,
            host_os=otoken,
            method="tauri-bundle",
            artifact=None,
            source_dir=str(tdir),
            artifact_present=False,
            bundle_search=[str(s) for s in search],
            build_command=THRONE_BUILD_COMMAND,
            actions=[_missing_throne_message(tdir, otoken, search)],
        )
    return InstallPlan(
        product=PRODUCT_THRONE,
        host_os=otoken,
        method="tauri-bundle",
        artifact=str(bundle),
        source_dir=str(tdir),
        artifact_present=True,
        bundle_search=[str(s) for s in search],
        actions=[
            f"launch the per-OS installer bundle: {bundle.name}",
            "(Windows: run the NSIS/MSI installer; macOS: open the .dmg / copy "
            "the .app to /Applications; Linux: install the .deb/.rpm or run the "
            ".AppImage)",
        ],
    )


def plan_setup(
    product: str,
    *,
    home: Optional[Path] = None,
    portable: Optional[bool] = None,
) -> SetupPlan:
    """Plan initializing one product against the centralized install home (T471).

    Setup is product-agnostic at the storage layer -- both products share the one
    install home (``settings/``, ``logs/``, ``gald3r_vault/``). This plan records
    the ensure + per-product settings/log linkage; the executor performs it by
    calling :func:`gald3r.home.ensure_install_home` and writing the marker files.

    Args:
        product: :data:`PRODUCT_AGENT` or :data:`PRODUCT_THRONE`.
        home: Pre-resolved install home (defaults to the resolver, honoring
            ``portable``).
        portable: Forwarded to :func:`gald3r.home.resolve_install_home`.

    Raises:
        ValueError: on an unknown product.
    """
    if product not in PRODUCTS:
        raise ValueError(f"unknown product '{product}' (expected one of {PRODUCTS})")
    base = home if home is not None else _home.resolve_install_home(portable=portable)
    settings = _home.subdir(_home.SETTINGS_DIR, home=base)
    logs = _home.subdir(_home.LOGS_DIR, home=base)
    vault = _home.subdir(_home.VAULT_DIR, home=base)
    # Per-product settings file inside the shared settings/ dir.
    product_settings = settings / f"{product}.json"
    product_log = logs / f"{product}.log"
    return SetupPlan(
        product=product,
        home=str(base),
        paths={
            "settings": str(settings),
            "logs": str(logs),
            "vault": str(vault),
            "product_settings": str(product_settings),
            "product_log": str(product_log),
        },
        actions=[
            f"ensure install home + settings/logs/gald3r_vault + VERSION ({base})",
            f"create {product_settings} if missing (per-product settings marker)",
            f"touch {product_log} (per-product log)",
            f"link the shared vault at {vault}",
        ],
    )


def execute_install(plan: InstallPlan) -> List[str]:
    """Execute a resolved :class:`InstallPlan` (non-dry-run). Returns log lines.

    Raises:
        MissingArtifactError: when the plan's artifact is absent (fail-loud -- the
            throne bundle must exist; this NEVER stubs or fakes success).
        InstallError: when a required tool (``uv``) is unavailable.
    """
    if not plan.artifact_present:
        # The plan already carries the exact build command in its single action.
        raise MissingArtifactError(plan.actions[0] if plan.actions
                                   else f"required artifact for {plan.product} is missing")
    log: List[str] = []
    if plan.method == "uv-runtime":
        if shutil.which("uv") is None:
            raise InstallError(
                "uv not found on PATH -- the agent runtime is installed with uv "
                "(g-rl-09). Install uv (https://docs.astral.sh/uv/) and retry."
            )
        cmd = ["uv", "sync", "--project", plan.source_dir]
        log.append("$ " + " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        log.append(result.stdout.strip())
        if result.returncode != 0:
            log.append(result.stderr.strip())
            raise InstallError(
                f"uv sync failed (exit {result.returncode}) for {plan.source_dir}"
            )
        log.append("agent runtime synced; register the global launcher with "
                   "install_global_cli for `gald3r` on PATH.")
        return log
    if plan.method == "tauri-bundle":
        # We do not silently auto-run platform installers (each OS differs and
        # some require elevation). We point the user at the resolved bundle.
        log.append(f"throne bundle ready: {plan.artifact}")
        log.append("run the per-OS installer for that bundle to install the desktop app.")
        return log
    raise InstallError(f"unknown install method '{plan.method}'")


def execute_setup(plan: SetupPlan, *, portable: Optional[bool] = None) -> List[str]:
    """Execute a resolved :class:`SetupPlan` against the install home. Returns log.

    Creates the install home layout (via :func:`gald3r.home.ensure_install_home`),
    auto-provisions the shared ``gald3r_vault`` at the resolved location (honoring a
    configured ``vault_location`` in the install-home defaults; idempotent via the
    SINGLE shared resolver :func:`gald3r.provision.provision_vault`, T476), writes a
    per-product settings marker if absent, and touches the per-product log.
    Idempotent -- existing files are left untouched.
    """
    from gald3r import provision as _provision

    base = _home.ensure_install_home(plan.home, portable=portable)
    log: List[str] = [f"ensured install home: {base}"]
    settings_path = Path(plan.paths["product_settings"])
    if not settings_path.exists():
        settings_path.write_text(
            json.dumps({"product": plan.product, "initialized": True}, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        log.append(f"wrote {settings_path}")
    else:
        log.append(f"settings already present: {settings_path}")
    log_path = Path(plan.paths["product_log"])
    if not log_path.exists():
        log_path.touch()
        log.append(f"created log: {log_path}")
    # Auto-provision the vault at the resolved location (vault_location override in
    # the install-home defaults wins; else the install home's gald3r_vault/). The
    # shared resolver is the one agent + throne both use — no fork. Idempotent.
    defaults = _provision.load_install_home_defaults(home=base)
    vault = _provision.provision_vault(defaults, home=base)
    log.append(f"vault: {vault}")
    return log
