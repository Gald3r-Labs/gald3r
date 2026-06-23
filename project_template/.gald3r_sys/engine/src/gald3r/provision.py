"""Vault auto-provision + layered identity inheritance (T476, epic T470).

This is the SINGLE shared resolution both products call — gald3r_agent (its CLI
``setup`` verb) and gald3r_throne (the app's onboarding flow). There is no
agent/throne fork: the logic lives here in the engine and both surfaces import it.
It builds on :mod:`gald3r.home` (T471): the centralized install home is the
default source of both the vault location and the identity defaults.

Two things, one module:

1. **Vault auto-provision** — :func:`provision_vault` idempotently creates a
   ``gald3r_vault`` at the resolved location. The location honors a
   ``vault_location`` override (carried in the install-home defaults or an
   existing identity) and otherwise falls back to the install home's
   ``gald3r_vault/`` (``home.subdir(VAULT_DIR)``). It never re-creates an existing
   vault.

2. **Layered identity inheritance** — :func:`inherit_identity` writes
   ``.gald3r/.identity`` by layering, lowest precedence first:

       install-home defaults  ->  user identity  ->  per-project overrides

   Values already present in a higher layer win; the user only fills what is
   missing. This is the same cascade discipline documented for the settings
   layering (T447/T448): install-home defaults pre-populate the new identity,
   the user identity overrides them, and explicit per-project overrides win last.

**No secrets are written into the source-controlled identity file.** The ADR-016
contract ("no secrets in the install home") is enforced here too: keys that look
like credentials/tokens (see :data:`SECRET_KEY_HINTS`) are stripped from every
layer before the merged identity is written. Host-only secret state stays in the
gitignored ``.user_prefs.yaml`` / ``.user_id`` / ``.env`` files, never in
``.identity``.

Pure stdlib (``os`` / ``pathlib``) over the same flat ``key=value`` line format
:mod:`gald3r.config` already reads, so it runs anywhere uv puts a Python and is
runnable independently — with no install home configured it simply falls back to
the current defaults (empty install-home layer; vault under the resolved home).
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Mapping, Optional, Union

from gald3r import home as _home

#: The install-home settings file that carries identity defaults to inherit.
#: Lives under ``<install-home>/settings/`` (see :func:`gald3r.home.subdir`) and
#: uses the SAME flat ``key=value`` line format as ``.gald3r/.identity`` so the
#: two are read/written by one parser (DRY with :mod:`gald3r.config`).
IDENTITY_DEFAULTS_FILE = "identity_defaults"

#: Substrings that mark a key as carrying a secret. Any identity key whose name
#: contains one of these (case-insensitive) is NEVER written into ``.identity`` —
#: secrets stay host-only (``.user_prefs.yaml`` / ``.env``), per ADR-016 / the
#: ``.gald3r/.gitignore`` rules.
SECRET_KEY_HINTS = (
    "secret", "token", "password", "passwd", "api_key", "apikey",
    "key", "credential", "private", "passphrase", "phrase",
)


def _is_secret_key(key: str) -> bool:
    """Return True when ``key`` looks like it carries a secret (never persisted)."""
    low = key.strip().casefold()
    return any(hint in low for hint in SECRET_KEY_HINTS)


def _is_unset(value: str) -> bool:
    """Return True for "not really configured" values: empty or a ``{TEMPLATE}``
    placeholder (e.g. ``{LOCAL}`` / ``{project_id}``). Such values must not block a
    lower install-home default from filling the gap — consistent with the way
    :func:`resolve_vault_location` ignores a placeholder ``vault_location``."""
    text = str(value).strip()
    return text == "" or (text.startswith("{") and text.endswith("}"))


def parse_kv_lines(path: Path) -> Dict[str, str]:
    """Parse a flat ``key=value`` file (``.identity`` / install-home defaults).

    ``#`` lines and blank lines are ignored. Returns ``{}`` for a missing file so
    callers get a clean "no install home configured" fallback. Mirrors
    :func:`gald3r.config._parse_identity` exactly (same contract, reused format)
    rather than introducing a second key=value dialect.
    """
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def install_home_defaults_path(
    *,
    home: Optional[Path] = None,
    **home_kwargs,
) -> Path:
    """Return the path to the install-home identity-defaults file.

    ``home`` is a pre-resolved install home; when omitted it is resolved via
    :func:`gald3r.home.resolve_install_home` (passing through ``home_kwargs`` such
    as ``override`` / ``portable``). The file itself need not exist.
    """
    settings = _home.subdir(_home.SETTINGS_DIR, home=home, **home_kwargs)
    return settings / IDENTITY_DEFAULTS_FILE


def load_install_home_defaults(
    *,
    home: Optional[Path] = None,
    **home_kwargs,
) -> Dict[str, str]:
    """Load identity defaults from the install home (the lowest cascade layer).

    Returns ``{}`` when no defaults file exists — that is the real, documented
    fallback for "no install home configured", NOT a stub. Secret-looking keys are
    dropped here too, so a defaults file can never seed a secret into ``.identity``.
    """
    raw = parse_kv_lines(install_home_defaults_path(home=home, **home_kwargs))
    return {k: v for k, v in raw.items() if not _is_secret_key(k)}


def merge_identity(
    *layers: Mapping[str, str],
) -> Dict[str, str]:
    """Layer identity dicts, lowest precedence first; strip secret keys.

    The documented cascade is ``install-home defaults -> user identity ->
    per-project overrides`` (T447/T448): pass them in exactly that order. A value
    "really set" (non-empty and not a ``{TEMPLATE}`` placeholder) in a higher layer
    overrides lower layers; lower layers fill only the gaps. An unset value (empty
    or placeholder) never clobbers an already-set value, so install-home defaults
    can fill a template placeholder like ``vault_location={LOCAL}``. Secret-looking
    keys are removed from the final result (defense in depth).
    """
    merged: Dict[str, str] = {}
    for layer in layers:
        for key, value in layer.items():
            if value is None:
                continue
            text = str(value)
            # A higher (later) layer's "really set" value wins; an unset value
            # (empty or {TEMPLATE} placeholder) does not clobber a set value.
            if _is_unset(text) and not _is_unset(merged.get(key, "")):
                continue
            merged[key] = text
    return {k: v for k, v in merged.items() if not _is_secret_key(k)}


#: The identity key that carries an explicit vault override (T476/T532).
VAULT_LOCATION_KEY = "vault_location"


def _vault_location_value(source: Optional[Mapping[str, str]]) -> str:
    """Return a ``source``'s "really set" ``vault_location``, or ``""``.

    A blank value or a still-templated ``{PLACEHOLDER}`` means "not configured" (the
    same rule :func:`_is_unset` applies to every identity value), so the next, lower
    layer is consulted instead of pinning the vault to a placeholder.
    """
    if not source:
        return ""
    loc = str(source.get(VAULT_LOCATION_KEY, "")).strip()
    return "" if _is_unset(loc) else loc


def resolve_vault_location(
    identity: Optional[Mapping[str, str]] = None,
    *,
    home: Optional[Path] = None,
    **home_kwargs,
) -> Path:
    """Resolve where the ``gald3r_vault`` lives (honoring a ``vault_location``).

    Precedence:
        1. an explicit, non-placeholder ``vault_location`` in ``identity`` (or the
           merged install-home defaults), expanded/absolutized;
        2. otherwise the install home's ``gald3r_vault/``
           (:func:`gald3r.home.subdir`), honoring ``GALD3R_HOME`` / portable mode
           via ``home`` / ``home_kwargs``.

    A ``vault_location`` that is still a template placeholder (e.g. ``{LOCAL}``) is
    ignored — that means "not configured", so we fall back to the install home.

    This is the two-layer back-compat resolver (the one
    :func:`install.execute_setup` calls). :func:`resolve_vault_location_layered`
    implements the full T532 precedence (session/project -> workspace -> default
    user home) over an ordered list of layers.
    """
    if identity:
        loc = _vault_location_value(identity)
        if loc:
            return Path(loc).expanduser().resolve()
    return _home.subdir(_home.VAULT_DIR, home=home, **home_kwargs)


def resolve_vault_location_layered(
    *layers: Optional[Mapping[str, str]],
    home: Optional[Path] = None,
    **home_kwargs,
) -> Path:
    """Resolve the vault location across the T532 precedence chain (highest first).

    The documented precedence is **session/project override -> workspace -> default
    user home** (the install home's ``gald3r_vault/``). Pass the layers in that
    order — highest precedence first — and the first layer carrying a "really set"
    (non-empty, non-placeholder) ``vault_location`` wins. ``None`` layers and unset
    values are skipped, so a caller can pass e.g.::

        resolve_vault_location_layered(
            session_override,   # 1. session/project (highest)
            workspace_identity, # 2. workspace
            home=...,           # 3. default user home (fallback)
        )

    When no layer sets a non-placeholder ``vault_location`` it falls back to the
    install home's ``gald3r_vault/`` (honoring ``GALD3R_HOME`` / portable mode via
    ``home`` / ``home_kwargs``). This is the SINGLE resolver the engine, the CLI
    selector, and the Agent path all call so the three surfaces agree on one path.
    """
    for layer in layers:
        loc = _vault_location_value(layer)
        if loc:
            return Path(loc).expanduser().resolve()
    return _home.subdir(_home.VAULT_DIR, home=home, **home_kwargs)


# ---- CLI selector: choices -> resolved vault location (T532) ---------------

#: Selector choices the CLI prompt offers. ``create_new`` carries a caller-supplied
#: target path; the others resolve from the layers already in scope.
VAULT_CHOICE_DEFAULT = "default"      # use the default user vault (install home)
VAULT_CHOICE_WORKSPACE = "workspace"  # use the workspace-level vault override
VAULT_CHOICE_PROJECT = "project"      # use the per-project vault override
VAULT_CHOICE_NEW = "create_new"       # create a new vault at an explicit location
VAULT_CHOICES = (
    VAULT_CHOICE_DEFAULT, VAULT_CHOICE_WORKSPACE,
    VAULT_CHOICE_PROJECT, VAULT_CHOICE_NEW,
)


def resolve_vault_choice(
    choice: str,
    *,
    project_identity: Optional[Mapping[str, str]] = None,
    workspace_identity: Optional[Mapping[str, str]] = None,
    new_location: Optional[Union[str, Path]] = None,
    home: Optional[Path] = None,
    **home_kwargs,
) -> Path:
    """Map a selector ``choice`` to the resolved vault location (T532).

    * ``default``    -> the install home's ``gald3r_vault/`` (default user vault).
    * ``workspace``  -> the workspace identity's ``vault_location`` (falls back to
      the default user vault when the workspace has none configured).
    * ``project``    -> the project identity's ``vault_location`` (same fallback).
    * ``create_new`` -> the explicit ``new_location`` (required for this choice).

    Returns the resolved path (absolute, not necessarily existing). Raises
    ``ValueError`` for an unknown choice or a ``create_new`` without ``new_location``.
    """
    if choice == VAULT_CHOICE_DEFAULT:
        return _home.subdir(_home.VAULT_DIR, home=home, **home_kwargs)
    if choice == VAULT_CHOICE_WORKSPACE:
        return resolve_vault_location_layered(
            workspace_identity, home=home, **home_kwargs
        )
    if choice == VAULT_CHOICE_PROJECT:
        return resolve_vault_location_layered(
            project_identity, home=home, **home_kwargs
        )
    if choice == VAULT_CHOICE_NEW:
        if not new_location or not str(new_location).strip():
            raise ValueError("create_new requires a target location (new_location)")
        return Path(new_location).expanduser().resolve()
    raise ValueError(
        f"unknown vault choice '{choice}' (expected one of {VAULT_CHOICES})"
    )


def persist_vault_location(
    gald3r_dir: Union[str, Path],
    location: Union[str, Path],
) -> Dict[str, str]:
    """Persist the chosen ``vault_location`` into ``.gald3r/.identity`` (T532).

    Reads the existing identity, sets/overwrites ``vault_location`` with the resolved
    (absolute) path, and writes it back via :func:`write_identity_file` (which keeps
    the header comments and strips any secret keys). Returns the written identity
    dict. The directory is created if missing. This is the one place the selector's
    choice is recorded so every surface that re-reads ``.identity`` honors it.
    """
    gd = Path(gald3r_dir)
    identity = parse_kv_lines(gd / ".identity")
    identity[VAULT_LOCATION_KEY] = str(Path(location).expanduser().resolve())
    write_identity_file(gd / ".identity", identity)
    return identity


def provision_vault(
    identity: Optional[Mapping[str, str]] = None,
    *,
    home: Optional[Path] = None,
    **home_kwargs,
) -> Path:
    """Idempotently provision the local ``gald3r_vault`` at the resolved location.

    Resolves the location with :func:`resolve_vault_location` (honoring a
    configured ``vault_location`` / ``GALD3R_HOME`` / portable mode), creates the
    directory tree if it is missing, and returns its path. Idempotent: an existing
    vault directory is left exactly as-is (no contents touched). This is what an
    install of agent/throne calls so the vault is auto-provisioned.
    """
    vault = resolve_vault_location(identity, home=home, **home_kwargs)
    vault.mkdir(parents=True, exist_ok=True)
    return vault


def write_identity_file(path: Path, identity: Mapping[str, str]) -> None:
    """Write a merged identity to a flat ``key=value`` file (``.identity`` format).

    Preserves the gald3r header comments and emits one ``key=value`` line per
    field, secret keys already removed by :func:`merge_identity`. Stable key order:
    a few well-known identity keys first (for readability), then the rest sorted.
    """
    head_keys = [
        "project_id", "project_name", "project_type",
        "user_id", "user_name",
        "gald3r_version", "tier",
        "vault_location", "repos_location",
    ]
    ordered = [k for k in head_keys if k in identity]
    ordered += sorted(k for k in identity if k not in head_keys)
    lines = [
        "# gald3r_rel_version: "
        f"{identity.get('gald3r_version') or identity.get('gald3r_rel_version') or '2.0.0'}",
        "# schema_version: identity-v1",
    ]
    lines += [f"{k}={identity[k]}" for k in ordered if not _is_secret_key(k)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def inherit_identity(
    gald3r_dir: Union[str, Path],
    project_overrides: Optional[Mapping[str, str]] = None,
    *,
    home: Optional[Path] = None,
    write: bool = True,
    **home_kwargs,
) -> Dict[str, str]:
    """Build (and optionally write) a ``.gald3r/.identity`` inheriting install-home defaults.

    The layered merge is ``install-home defaults -> existing user identity ->
    per-project overrides`` (T447/T448 cascade): install-home values pre-populate
    the identity, an existing ``.identity`` overrides them, and explicit
    ``project_overrides`` win last. The user only fills what is missing.

    Args:
        gald3r_dir: The project's ``.gald3r/`` directory (its ``.identity`` is read
            as the middle layer and, when ``write`` is True, written back).
        project_overrides: Highest-precedence per-project values (e.g. the
            project_name/tier chosen at install time). Secret keys are dropped.
        home: Pre-resolved install home (else resolved via ``home_kwargs``). When
            no install home is configured the defaults layer is simply empty — a
            real fallback to current defaults, not a stub.
        write: When True, write the merged identity back to ``.gald3r/.identity``.
        **home_kwargs: Forwarded to the install-home resolver (``override`` /
            ``portable`` / ...).

    Returns:
        The merged identity dict (secret keys removed).
    """
    gd = Path(gald3r_dir)
    defaults = load_install_home_defaults(home=home, **home_kwargs)
    existing = parse_kv_lines(gd / ".identity")
    overrides = dict(project_overrides or {})
    merged = merge_identity(defaults, existing, overrides)
    if write:
        write_identity_file(gd / ".identity", merged)
    return merged
