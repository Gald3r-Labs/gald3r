"""Per-OS install + setup planning for gald3r products (T472/T1615, epic T470).

This module is the SINGLE place that decides, for the detected host OS, *which*
artifact installs gald3r_agent and gald3r_throne and *where* it lives. It mirrors
the "one resolver, override -> env -> default" discipline that
:mod:`gald3r.home` (T471) and :mod:`gald3r_forge.paths` (T412) already establish,
and it composes with :mod:`gald3r.home`: ``setup`` targets the centralized install
home, never a per-repo ``.gald3r/``.

Two products are handled, with two install methods:

* **github-release** (T1615 — the *consumer default*) downloads the precompiled,
  signed apps from the two PUBLIC GitHub Releases repos we publish:
  ``Gald3r-Labs/gald3r_agent`` (a Nuitka-compiled binary) and
  ``Gald3r-Labs/gald3r_throne`` (a Tauri desktop installer). A filesystem user who
  only has the gald3r framework can run one command and get the apps — no source
  build, no toolchain. Integrity is enforced fail-loud: throne installers carry a
  minisign ``.sig`` (Tauri updater key ``F110B9BD6FF00BA2``) and agent binaries a
  ``.sha256`` sidecar; a missing/tampered signature refuses the install.

* **from-source** (``--from-source``, the dev fallback) keeps the original T472
  behaviour: **agent** is synced via ``uv`` (no bare pip/venv; g-rl-09);
  **throne** locates the per-OS Tauri bundle the local ``npm run tauri:build``
  produced. A missing bundle fails loud with the exact build command.

Planning (:func:`plan_install`) is pure / side-effect-free and fully unit-testable
by overriding ``os_token`` / ``products_root`` and monkeypatching the network
seams (:func:`fetch_release` / :func:`download_asset`); *no* network call happens
at plan time, so ``--dry-run`` is offline. Only :func:`execute_install` touches the
network + filesystem. There is no silent stub / fake-success path (spec / g-rl-34).
"""
# @subsystems: RELEASE_AND_VERSIONING
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
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

# --- github-release (consumer) download method (T1615) ---------------------

#: Install methods recorded on a plan (and consumed by the executor).
METHOD_GITHUB_RELEASE = "github-release"
METHOD_UV_RUNTIME = "uv-runtime"
METHOD_TAURI_BUNDLE = "tauri-bundle"

#: GitHub REST API base (override for tests / GHE via the env var).
GITHUB_API_BASE = os.environ.get("GALD3R_GITHUB_API_BASE", "https://api.github.com")

#: The two PUBLIC repos whose Releases host the precompiled apps.
AGENT_RELEASE_REPO = "Gald3r-Labs/gald3r_agent"
THRONE_RELEASE_REPO = "Gald3r-Labs/gald3r_throne"

#: Per-OS agent release-asset names. The agent build (`agent-binary-build.yml`)
#: renames the Nuitka binary to a fixed, version-less OS-tagged name, so an exact
#: match is used (no glob). macOS has no published asset yet (deferred).
_AGENT_RELEASE_ASSET: Dict[str, str] = {
    OS_WINDOWS: "gald3r-windows-x86_64.exe",
    OS_LINUX: "gald3r-linux-x86_64",
}

#: Per-OS throne release-asset name globs. The Tauri build embeds the version in
#: the filename, so suffix/glob matching is used (first match in list order wins).
_THRONE_RELEASE_PATTERNS: Dict[str, List[str]] = {
    OS_WINDOWS: ["*_x64-setup.exe", "*_x64_en-US.msi"],
    OS_LINUX: ["*_amd64.AppImage", "*_amd64.deb"],
}

#: The Throne updater minisign public key (Tauri updater; key id F110B9BD6FF00BA2),
#: embedded in gald3r_throne/src-tauri/tauri.conf.json. Used to verify the `.sig`
#: that ships beside each throne installer asset.
THRONE_MINISIGN_KEY_ID = "F110B9BD6FF00BA2"
THRONE_MINISIGN_PUBKEY = (
    "untrusted comment: minisign public key: F110B9BD6FF00BA2\n"
    "RWSiC/BvvbkQ8b7JpjwjDG4YUbyjBECa/t9EX/CKRe15yBuIQpV81rwA\n"
)

#: Verification kinds recorded on a download plan.
VERIFY_SHA256 = "sha256"
VERIFY_MINISIGN = "minisign"
VERIFY_NONE = "unsigned"

#: Network timeouts (seconds) — small for the API call, larger for the download.
_API_TIMEOUT = 30.0
_DOWNLOAD_TIMEOUT = 300.0


class InstallError(Exception):
    """Base class for install/setup planning failures."""


class MissingArtifactError(InstallError):
    """Raised when a required per-OS artifact is absent.

    This is the fail-loud path the spec mandates: install artifacts must exist
    (a built throne bundle, or a published release asset), and the install command
    must never silently stub or fake success. The message names the missing
    artifact, where it was looked for, and how to produce / obtain it.
    """


class VerificationError(InstallError):
    """Raised when a downloaded artifact fails (or cannot complete) integrity
    verification: a missing/tampered throne ``.sig`` or a mismatched agent
    ``.sha256``. Refusing to install is the correct fail-loud behaviour — a
    download method must never install an unverified binary silently.
    """


@dataclass
class InstallPlan:
    """A resolved, serializable plan for installing one product on this host."""

    product: str
    host_os: str
    method: str                       # github-release | uv-runtime | tauri-bundle
    artifact: Optional[str] = None    # resolved bundle path (throne source) when present
    source_dir: Optional[str] = None  # product source tree (agent) / throne dir
    actions: List[str] = field(default_factory=list)
    path_changes: List[str] = field(default_factory=list)
    bundle_search: List[str] = field(default_factory=list)  # globs consulted
    artifact_present: bool = True     # False -> fail-loud on a non-dry-run execute
    build_command: Optional[str] = None  # how to produce a missing artifact
    # --- github-release download fields (T1615) ---
    repo: Optional[str] = None            # owner/repo on GitHub Releases
    release: Optional[str] = None         # "latest" or a pinned tag (vX.Y.Z)
    asset_name: Optional[str] = None      # exact asset (agent); None until resolved (throne)
    asset_patterns: List[str] = field(default_factory=list)  # globs (throne)
    verify: Optional[str] = None          # sha256 | minisign | unsigned
    target_path: Optional[str] = None     # where the artifact is installed
    install_home: Optional[str] = None    # resolved install home (executor needs it)
    require_verification: bool = False     # fail-closed: abort if integrity can't be verified

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
            "repo": self.repo,
            "release": self.release,
            "asset_name": self.asset_name,
            "asset_patterns": list(self.asset_patterns),
            "verify": self.verify,
            "target_path": self.target_path,
            "install_home": self.install_home,
            "require_verification": self.require_verification,
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


# --- network + integrity seams (T1615) -------------------------------------
# These are the ONLY functions that touch the network. They are module-level so
# tests monkeypatch them (e.g. install.fetch_release = fake) instead of hitting
# GitHub. Each fails loud with a clear, offline-first message — never a crash.

def fetch_release(repo: str, release: Optional[str] = None, *,
                  token: Optional[str] = None,
                  timeout: float = _API_TIMEOUT) -> dict:
    """Resolve a release on ``owner/repo`` via the GitHub REST API.

    Args:
        repo: ``owner/repo`` (e.g. ``Gald3r-Labs/gald3r_agent``).
        release: ``None``/``"latest"`` -> the latest release; otherwise a tag
            (``vX.Y.Z``) pinned via ``releases/tags/{tag}``.
        token: optional bearer token (raises the API rate limit; not required for
            public repos).

    Returns:
        ``{"tag_name": str, "assets": [{"name": str, "url": str}, ...]}``.

    Raises:
        InstallError: on any network / HTTP failure (offline-first, fail loud).
    """
    if not release or release == "latest":
        path = f"/repos/{repo}/releases/latest"
    else:
        path = f"/repos/{repo}/releases/tags/{release}"
    url = GITHUB_API_BASE + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "gald3r-install",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise InstallError(
                f"no '{release or 'latest'}' release found on {repo} (HTTP 404). "
                f"Check the repo/tag, or omit --release for the latest."
            ) from exc
        raise InstallError(
            f"GitHub API error fetching the release from {repo}: HTTP {exc.code}. "
            f"Retry later, or pass --token to raise the rate limit."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise InstallError(
            f"could not reach GitHub Releases for {repo} ({exc}). gald3r install "
            f"needs network for the download method — check your connection, or "
            f"use --from-source for an offline developer build."
        ) from exc
    assets = [
        {"name": a.get("name"), "url": a.get("browser_download_url")}
        for a in (data.get("assets") or [])
        if a.get("name") and a.get("browser_download_url")
    ]
    return {"tag_name": data.get("tag_name"), "assets": assets}


def select_asset(assets: List[dict], *, exact: Optional[str] = None,
                 patterns: Optional[List[str]] = None) -> Optional[dict]:
    """Pure asset selection: exact-name match first, else the first asset matching
    any glob in ``patterns`` (pattern order is preference order). Returns the asset
    dict (``{"name", "url"}``) or ``None`` when nothing matches.
    """
    if exact is not None:
        for a in assets:
            if a.get("name") == exact:
                return a
        return None
    for pat in (patterns or []):
        for a in assets:
            if fnmatch.fnmatch(a.get("name") or "", pat):
                return a
    return None


def download_asset(url: str, dest: Path, *, token: Optional[str] = None,
                   timeout: float = _DOWNLOAD_TIMEOUT) -> Path:
    """Stream-download ``url`` to ``dest`` (atomic temp + rename). Returns ``dest``.

    Raises:
        InstallError: on any network / HTTP / IO failure (fail loud).
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "gald3r-install"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(dest.parent), suffix=".part")
    tmp = Path(tmp_name)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, \
                os.fdopen(tmp_fd, "wb") as out:
            shutil.copyfileobj(resp, out)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        tmp.unlink(missing_ok=True)
        raise InstallError(
            f"failed to download {url} ({exc}). Network problem or the asset was "
            f"removed — nothing was installed."
        ) from exc
    os.replace(tmp, dest)
    return dest


def compute_sha256(path: Union[str, Path]) -> str:
    """Return the lowercase hex SHA-256 of a file (stdlib hashlib, streamed)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_sha256_text(text: str) -> Optional[str]:
    """Extract the 64-hex digest from a ``.sha256`` sidecar (``<hex>  <name>`` or
    bare ``<hex>``). Returns the lowercase digest or None when unparseable."""
    for token in (text or "").split():
        token = token.strip().lower()
        if len(token) == 64 and all(c in "0123456789abcdef" for c in token):
            return token
    return None


def verify_sha256(path: Union[str, Path], expected_hex: str) -> None:
    """Raise :class:`VerificationError` when ``path``'s SHA-256 != ``expected_hex``."""
    expected = (expected_hex or "").strip().lower()
    actual = compute_sha256(path)
    if actual != expected:
        raise VerificationError(
            f"SHA-256 mismatch for {Path(path).name}: expected {expected or '(empty)'}, "
            f"computed {actual}. The download is corrupt or tampered — refusing to install."
        )


def verify_minisign(artifact: Union[str, Path], sig_path: Optional[Union[str, Path]],
                    *, pubkey: str = THRONE_MINISIGN_PUBKEY,
                    allow_unsigned: bool = False) -> bool:
    """Verify a throne ``.sig`` (minisign / Tauri updater key) against ``artifact``.

    Fail-loud contract (AC4):
      * a **missing** sig refuses the install (unless ``allow_unsigned``);
      * a **tampered** sig (verifier reports failure) refuses the install;
      * a good sig passes.

    Real cryptographic verification shells out to a ``minisign`` / ``signify``
    binary when one is on PATH (the engine is zero-dep, so it carries no Ed25519
    implementation). When no verifier is available the signature cannot be checked:
    that, too, refuses the install unless ``allow_unsigned`` is set — never a silent
    pass.

    Returns:
        ``True`` when the signature was cryptographically verified;
        ``False`` when verification was skipped under ``allow_unsigned``.
    """
    sig = Path(sig_path) if sig_path else None
    if sig is None or not sig.exists():
        if allow_unsigned:
            return False
        raise VerificationError(
            f"throne signature (.sig) for {Path(artifact).name} is missing — "
            f"refusing a silent unsigned install. Re-run with --allow-unsigned to "
            f"override at your own risk, or --from-source for a local build."
        )
    verifier = shutil.which("minisign") or shutil.which("signify")
    if verifier is None:
        if allow_unsigned:
            return False
        raise VerificationError(
            f"no minisign/signify verifier on PATH to check {sig.name} "
            f"(key {THRONE_MINISIGN_KEY_ID}). Install minisign "
            f"(https://jedisct1.github.io/minisign/) and retry, or re-run with "
            f"--allow-unsigned to override."
        )
    pub_fd, pub_name = tempfile.mkstemp(suffix=".pub")
    os.close(pub_fd)  # close the mkstemp handle so Windows can unlink it later
    pub_file = Path(pub_name)
    try:
        pub_file.write_text(pubkey, encoding="utf-8")
        cmd = [verifier, "-V", "-p", str(pub_file),
               "-m", str(artifact), "-x", str(sig)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise VerificationError(
                f"minisign verification FAILED for {Path(artifact).name} "
                f"({(result.stderr or result.stdout or '').strip()}). The installer "
                f"is unsigned or tampered — refusing to install."
            )
    finally:
        pub_file.unlink(missing_ok=True)
    return True


def record_installed_version(home: Path, product: str, version: Optional[str], *,
                             method: str, repo: Optional[str]) -> Path:
    """Write/refresh ``settings/{product}.json`` with the installed version + source.

    Returns the settings-file path. Merges onto any existing marker so a prior
    ``setup`` ``initialized`` flag is preserved.
    """
    settings = _home.subdir(_home.SETTINGS_DIR, home=home)
    settings.mkdir(parents=True, exist_ok=True)
    path = settings / f"{product}.json"
    data: Dict[str, object] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8")) or {}
        except (ValueError, OSError):
            data = {}
    data.update({
        "product": product,
        "version": version,
        "install_method": method,
        "installed_from": repo,
    })
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def _agent_target(install_home: Path, os_token: str) -> Path:
    """Return the install-home path the agent binary is placed at."""
    name = "gald3r-agent.exe" if os_token == OS_WINDOWS else "gald3r-agent"
    return install_home / "bin" / name


def _plan_install_from_source(
    product: str, otoken: str, root: Optional[Path], install_home: Path,
) -> InstallPlan:
    """The original T472 source-build plan (agent via uv / throne via tauri bundle)."""
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
            method=METHOD_UV_RUNTIME,
            source_dir=str(adir),
            artifact_present=True,
            install_home=str(install_home),
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
            method=METHOD_TAURI_BUNDLE,
            artifact=None,
            source_dir=str(tdir),
            artifact_present=False,
            install_home=str(install_home),
            bundle_search=[str(s) for s in search],
            build_command=THRONE_BUILD_COMMAND,
            actions=[_missing_throne_message(tdir, otoken, search)],
        )
    return InstallPlan(
        product=PRODUCT_THRONE,
        host_os=otoken,
        method=METHOD_TAURI_BUNDLE,
        artifact=str(bundle),
        source_dir=str(tdir),
        artifact_present=True,
        install_home=str(install_home),
        bundle_search=[str(s) for s in search],
        actions=[
            f"launch the per-OS installer bundle: {bundle.name}",
            "(Windows: run the NSIS/MSI installer; macOS: open the .dmg / copy "
            "the .app to /Applications; Linux: install the .deb/.rpm or run the "
            ".AppImage)",
        ],
    )


def _plan_install_github(
    product: str, otoken: str, install_home: Path, release: Optional[str],
    require_verification: bool = False,
) -> InstallPlan:
    """The consumer download plan (network-free at plan time; T1615).

    ``require_verification`` is the fail-closed policy (BUG-198 gap 2): when set,
    a missing/unverifiable integrity artifact aborts the install instead of
    proceeding unsigned. It is recorded on the plan so ``--dry-run`` shows the
    fail-closed intent honestly, and the executor enforces it.
    """
    rel = release or "latest"
    # macOS has no published assets yet for either product (deferred).
    if otoken == OS_MACOS:
        return InstallPlan(
            product=product,
            host_os=otoken,
            method=METHOD_GITHUB_RELEASE,
            artifact_present=False,
            install_home=str(install_home),
            release=rel,
            repo=(AGENT_RELEASE_REPO if product == PRODUCT_AGENT else THRONE_RELEASE_REPO),
            require_verification=require_verification,
            actions=[
                f"macOS coming soon — no published macOS {product} assets yet. "
                f"Build locally with --from-source in the meantime."
            ],
        )

    if product == PRODUCT_AGENT:
        asset = _AGENT_RELEASE_ASSET.get(otoken)
        target = _agent_target(install_home, otoken)
        verify_action = (
            f"verify SHA-256 ({asset}.sha256 sidecar) — REQUIRED: a missing or "
            f"mismatched checksum ABORTS the install (--require-verification)"
            if require_verification else
            f"verify SHA-256 ({asset}.sha256 sidecar) — "
            f"or log unsigned-experimental if the sidecar is absent"
        )
        return InstallPlan(
            product=PRODUCT_AGENT,
            host_os=otoken,
            method=METHOD_GITHUB_RELEASE,
            artifact_present=True,
            repo=AGENT_RELEASE_REPO,
            release=rel,
            asset_name=asset,
            verify=VERIFY_SHA256,
            target_path=str(target),
            install_home=str(install_home),
            require_verification=require_verification,
            actions=[
                f"download {asset} from {AGENT_RELEASE_REPO} ({rel} release)",
                verify_action,
                f"install the binary to {target} (chmod +x on POSIX)",
            ],
            path_changes=[f"ensure {install_home / 'bin'} on user PATH (idempotent)"],
        )

    # product == PRODUCT_THRONE
    patterns = list(_THRONE_RELEASE_PATTERNS.get(otoken, []))
    return InstallPlan(
        product=PRODUCT_THRONE,
        host_os=otoken,
        method=METHOD_GITHUB_RELEASE,
        artifact_present=True,
        repo=THRONE_RELEASE_REPO,
        release=rel,
        asset_patterns=patterns,
        verify=VERIFY_MINISIGN,
        target_path=str(install_home / "cache" / "throne"),
        install_home=str(install_home),
        require_verification=require_verification,
        actions=[
            f"resolve the per-OS installer matching {patterns} "
            f"from {THRONE_RELEASE_REPO} ({rel} release)",
            "download the installer + its minisign .sig",
            f"verify the .sig against the Throne updater key {THRONE_MINISIGN_KEY_ID} "
            f"(fail loud on a missing/tampered signature)",
            "place the installer in the install-home cache and report the next step "
            "(no silent elevation)",
        ],
    )


def plan_install(
    product: str,
    *,
    os_token: Optional[str] = None,
    products_root: Optional[Union[str, Path]] = None,
    home: Optional[Path] = None,
    from_source: bool = False,
    release: Optional[str] = None,
    require_verification: bool = False,
) -> InstallPlan:
    """Plan installing one product on the host OS (no side effects, no network).

    Args:
        product: :data:`PRODUCT_AGENT` or :data:`PRODUCT_THRONE`.
        os_token: Override host-OS detection (tests). Defaults to :func:`host_os`.
        products_root: Override the products-source root (``--from-source`` only).
        home: Pre-resolved install home (defaults to :func:`gald3r.home`).
        from_source: When True, plan the developer source build (agent via uv,
            throne via the local Tauri bundle). When False (the consumer default),
            plan a download from the public GitHub Releases repo.
        release: ``None``/``"latest"`` -> latest release; a tag pins it.
        require_verification: fail-closed policy (BUG-198) — when True, a download
            whose integrity cannot be verified (no agent ``.sha256`` sidecar / no
            throne ``.sig`` / no verifier) aborts instead of installing unsigned.

    Returns:
        An :class:`InstallPlan`. ``artifact_present`` is False (fail-loud at
        execute) for a missing throne source bundle or an unsupported (macOS) host.

    Raises:
        ValueError: on an unknown product.
        MissingArtifactError: when a ``--from-source`` product tree is missing.
    """
    if product not in PRODUCTS:
        raise ValueError(f"unknown product '{product}' (expected one of {PRODUCTS})")
    otoken = os_token if os_token is not None else host_os()
    install_home = home if home is not None else _home.resolve_install_home()
    if from_source:
        root = resolve_products_root(products_root)
        return _plan_install_from_source(product, otoken, root, install_home)
    return _plan_install_github(product, otoken, install_home, release,
                                require_verification=require_verification)


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


def _execute_github_release(plan: InstallPlan, *, token: Optional[str],
                            allow_unsigned: bool) -> List[str]:
    """Execute a github-release download plan: resolve -> download -> verify ->
    install. Every failure path raises :class:`InstallError` (fail loud)."""
    log: List[str] = []
    install_home = Path(plan.install_home) if plan.install_home \
        else _home.resolve_install_home()
    rel = fetch_release(plan.repo, plan.release, token=token)
    tag = rel.get("tag_name") or plan.release or "latest"
    assets = rel.get("assets") or []
    asset = select_asset(assets, exact=plan.asset_name,
                         patterns=plan.asset_patterns or None)
    if asset is None:
        want = plan.asset_name or " | ".join(plan.asset_patterns) or "(no pattern)"
        raise MissingArtifactError(
            f"no asset matching '{want}' in {plan.repo} release {tag}. "
            f"Available: {', '.join(a['name'] for a in assets) or '(none)'}."
        )
    cache = install_home / "cache"
    dest = cache / asset["name"]
    download_asset(asset["url"], dest, token=token)
    log.append(f"downloaded {asset['name']} from {plan.repo} ({tag})")

    # Fail-closed policy (BUG-198 gap 2): when require_verification is set, a
    # missing/unverifiable integrity artifact ABORTS the install. It also overrides
    # --allow-unsigned (you cannot both require verification and waive it).
    require_verification = plan.require_verification
    if plan.verify == VERIFY_SHA256:
        sha_asset = select_asset(assets, exact=f"{asset['name']}.sha256")
        if sha_asset is not None:
            sha_dest = cache / sha_asset["name"]
            download_asset(sha_asset["url"], sha_dest, token=token)
            digest = _parse_sha256_text(sha_dest.read_text(encoding="utf-8"))
            if not digest:
                raise VerificationError(
                    f"{sha_asset['name']} did not contain a valid SHA-256 digest — "
                    f"refusing to install an unverifiable binary."
                )
            verify_sha256(dest, digest)
            log.append(f"SHA-256 verified against {sha_asset['name']}")
        elif require_verification:
            dest.unlink(missing_ok=True)
            raise VerificationError(
                f"no {asset['name']}.sha256 sidecar in {plan.repo} release {tag}, "
                f"and --require-verification was set — refusing to install an "
                f"unverified agent binary (fail-closed). Drop --require-verification "
                f"to accept the unsigned-experimental binary, or use a release that "
                f"ships a .sha256 sidecar."
            )
        else:
            log.append(
                f"WARNING: no {asset['name']}.sha256 sidecar in {tag} — installing "
                f"UNSIGNED (experimental). Integrity was NOT verified. "
                f"Use --require-verification to make this fail-closed."
            )
    elif plan.verify == VERIFY_MINISIGN:
        sig_asset = select_asset(assets, exact=f"{asset['name']}.sig")
        sig_dest = None
        if sig_asset is not None:
            sig_dest = cache / sig_asset["name"]
            download_asset(sig_asset["url"], sig_dest, token=token)
        # require_verification overrides allow_unsigned (fail-closed wins).
        effective_allow_unsigned = allow_unsigned and not require_verification
        try:
            verified = verify_minisign(dest, sig_dest,
                                       allow_unsigned=effective_allow_unsigned)
        except VerificationError:
            dest.unlink(missing_ok=True)
            raise
        log.append(
            f"minisign signature verified (key {THRONE_MINISIGN_KEY_ID})"
            if verified else
            "WARNING: throne installer NOT signature-verified (--allow-unsigned)"
        )

    # Install step (product-specific).
    if plan.product == PRODUCT_AGENT:
        target = Path(plan.target_path) if plan.target_path \
            else _agent_target(install_home, plan.host_os)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(dest, target)
        if plan.host_os != OS_WINDOWS:
            try:
                target.chmod(0o755)
            except OSError:
                pass
        log.append(f"installed agent binary -> {target}")
        log.append(f"add {target.parent} to your PATH to run `gald3r-agent` anywhere.")
    else:  # throne — place the installer; do not silently elevate.
        if plan.host_os == OS_LINUX and dest.suffix == ".AppImage":
            try:
                dest.chmod(0o755)
            except OSError:
                pass
        log.append(f"throne installer ready: {dest}")
        log.append(
            "run that installer to complete setup "
            "(Windows: launch the .exe/.msi; Linux: run the .AppImage or "
            "`sudo dpkg -i` the .deb). gald3r does not auto-elevate."
        )

    marker = record_installed_version(install_home, plan.product, tag,
                                      method=METHOD_GITHUB_RELEASE, repo=plan.repo)
    log.append(f"recorded version {tag} in {marker}")
    return log


def execute_install(plan: InstallPlan, *, token: Optional[str] = None,
                    allow_unsigned: bool = False) -> List[str]:
    """Execute a resolved :class:`InstallPlan` (non-dry-run). Returns log lines.

    Args:
        plan: the plan from :func:`plan_install`.
        token: optional GitHub token (download method; raises the API rate limit).
        allow_unsigned: download method only — proceed past a missing throne ``.sig``
            / absent verifier instead of failing loud (explicit opt-out).

    Raises:
        MissingArtifactError: when a required artifact/asset is absent (fail-loud).
        VerificationError: when integrity verification fails (download method).
        InstallError: on a network failure or a missing tool (``uv``).
    """
    if plan.method == METHOD_GITHUB_RELEASE:
        if not plan.artifact_present:
            # macOS-coming-soon (and any other unsupported host) — fail loud.
            raise MissingArtifactError(plan.actions[0] if plan.actions
                                       else f"{plan.product} is not available for {plan.host_os}")
        return _execute_github_release(plan, token=token, allow_unsigned=allow_unsigned)

    if not plan.artifact_present:
        # The plan already carries the exact build command in its single action.
        raise MissingArtifactError(plan.actions[0] if plan.actions
                                   else f"required artifact for {plan.product} is missing")
    log: List[str] = []
    if plan.method == METHOD_UV_RUNTIME:
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
    if plan.method == METHOD_TAURI_BUNDLE:
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
    SINGLE shared resolver :func:`gald3r.provision.provision_vault`, T476), ensures the
    unified per-user identity record (``user_config.json``, T531) exists in the T530
    per-user home, writes a per-product settings marker if absent, and touches the
    per-product log. Idempotent -- existing files are left untouched.
    """
    from gald3r import provision as _provision
    from gald3r import user_config as _user_config

    base = _home.ensure_install_home(plan.home, portable=portable)
    log: List[str] = [f"ensured install home: {base}"]
    # First-run create-or-read the ONE unified identity record (T531). This is the
    # same record Throne + Agent consume, and it feeds the permissions epic (T527).
    # Idempotent + non-destructive: an existing user_config.json is never clobbered.
    # It lives in the T530 per-user home (gald3r.home.resolve_home), the single home
    # resolver, so every surface agrees on one location.
    _env = dict(os.environ)
    identity = _user_config.ensure_user_config(_env, platform.system())
    log.append(
        f"identity: {_user_config.default_config_path(_env, platform.system())} "
        f"(user_id={identity.user_id[:8]}...)"
    )
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
