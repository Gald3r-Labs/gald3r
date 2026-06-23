"""Self-update: version-check against world_tree + safe `.gald3r/` migration (T473/T475).

This is the SHARED self-update core for both the agent (T473) and template-installed
projects (T475). It wraps three concerns behind one system:

1. **version-check** (:func:`version_check`) — query world_tree's T112 version surface
   (``GET {base}/api/v1/gald3r/version`` -> ``{installed_version, latest_version,
   update_available, source}``) and compare it to the project's own
   ``.gald3r/.identity`` ``gald3r_version``. **Offline-first**: any network/contract
   failure degrades to a clear ``reachable=False`` envelope — never a crash, never a
   fabricated version.

2. **upgrade migration** (:meth:`UpgradeSystem.plan` / :meth:`UpgradeSystem.migrate`) —
   diff two ``.gald3r/`` release snapshots and apply idempotent ADD / MERGE / DEPRECATE
   actions, with an ABSOLUTE user-data denylist (``tasks/**``, ``bugs/**``, ``PLAN.md``,
   ``IDEA_BOARD.md``, ``BUGS.md``, ``TASKS.md``, ...) that is never touched. This honors
   the ``gald3r upgrade`` engine-op contract documented in the ``@g-update`` /
   ``@g-upgrade`` commands and the T430 structural-upgrade spec.

3. **safe self-update** (:meth:`UpgradeSystem.self_update`) — BEFORE applying anything,
   create a timestamped, **gitignored** backup of the whole ``.gald3r/`` tree (a
   ``.zip`` archive — already covered by the ``.gald3r/.gitignore`` ``*.zip`` rule), run
   the migration, and on ANY failure RESTORE from the backup (rollback) and report.

Pure stdlib (``urllib`` / ``zipfile`` / ``shutil`` / ``pathlib`` / ``json``) plus the
shared :mod:`gald3r.store` frontmatter helpers — no new dependency, so it runs anywhere
uv puts a Python and matches the engine's zero-dep CLI discipline. The CLI
(:mod:`gald3r.adapters.cli`) is the thin executor that turns these into ``version-check``
and ``upgrade`` subcommands and honors ``--dry-run``.

@subsystems: RELEASE_AND_VERSIONING
"""
from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gald3r.store import emit_frontmatter, split_doc

# ── version surface (T112) ────────────────────────────────────────────────────

#: The world_tree REST path that returns the version envelope (T112). Joined onto
#: whatever base URL the caller supplies. Documented contract (proven by
#: ``tests/test_gald3r_routes_t112.py``): the JSON body carries ``installed_version``,
#: ``latest_version``, ``update_available`` and ``source``.
VERSION_ENDPOINT_PATH = "/api/v1/gald3r/version"

#: Default base URL for a locally-running world_tree backend. Overridable per-call
#: (and, at the CLI, via ``--base-url`` / the ``GALD3R_WORLD_TREE_URL`` env var) so an
#: air-gapped or remote deployment can point elsewhere without code changes.
DEFAULT_WORLD_TREE_URL = "http://127.0.0.1:8000"

#: Network timeout (seconds) for the version probe. Short by design — the check is
#: advisory and must never block a session for long.
DEFAULT_TIMEOUT = 3.0


# ── upgrade migration: the ABSOLUTE user-data denylist ─────────────────────────

#: Path prefixes (relative to ``.gald3r/``) whose contents are USER DATA and are NEVER
#: added, merged, or deprecated by an upgrade. Enforced as an absolute gate before any
#: classification (matches the ``[SKIP user-data]`` row of the @g-update contract).
USER_DATA_PREFIXES: Tuple[str, ...] = (
    "tasks/",
    "bugs/",
    "features/",
    "prds/",
    "ideas/",
    "releases/",
    "vault/",
    "subsystems/",
    "logs/",
)

#: Top-level user-data files (relative to ``.gald3r/``) that are never touched.
USER_DATA_FILES: Tuple[str, ...] = (
    "TASKS.md",
    "BUGS.md",
    "FEATURES.md",
    "PRDS.md",
    "PLAN.md",
    "IDEA_BOARD.md",
    "RELEASES.md",
    "SUBSYSTEMS.md",
    "PROJECT.md",
    "CONSTRAINTS.md",
    "learned-facts.md",
    "vocab.md",
    ".identity",
    ".update_skips",
)

#: Directory names skipped entirely when diffing snapshots (never part of the format).
_DIFF_SKIP_DIRS = {".git", "__pycache__", "logs", "_backups"}

#: Subdir of ``.gald3r_sys/`` that holds versioned ``.gald3r/`` template snapshots
#: captured at each release cut (T463). Layout: ``snapshots/v<X.Y.Z>/.gald3r/``. This is
#: the FROM/TO source a real vN->vN+1 ``gald3r upgrade`` resolves against; the single
#: ``template_verification/.gald3r`` remains the fallback when no versioned snapshot exists.
SNAPSHOTS_DIR_NAME = "snapshots"

#: Frontmatter keys bumped on a MERGE so the migrated file records the new format rev.
_REL_VERSION_KEYS = ("gald3r_rel_version", "schema_version")

#: Infix marking a file archived by a prior DEPRECATE pass (never re-processed).
_DEPRECATED_INFIX = "_deprecated_"


def is_user_data(rel: str) -> bool:
    """Return True when ``rel`` (a ``.gald3r/``-relative POSIX path) is protected user data."""
    rel = rel.replace("\\", "/").lstrip("/")
    if rel in USER_DATA_FILES:
        return True
    return any(rel == p.rstrip("/") or rel.startswith(p) for p in USER_DATA_PREFIXES)


def _snapshot_version_tag(version: str) -> str:
    """Normalize a semver into the ``v<X.Y.Z>`` snapshot dir name (idempotent on a leading 'v')."""
    return "v" + version.lstrip("vV")


def capture_snapshot(
    canonical_gald3r: Path,
    sys_dir: Path,
    version: str,
    *,
    overwrite: bool = True,
) -> Path:
    """Capture the canonical ``.gald3r/`` structure into a versioned snapshot (T463).

    Called at a RELEASE CUT so ``gald3r upgrade`` later has a real historical ``--from``
    source. The snapshot is the framework-owned format ONLY: every path classified as
    user data by :func:`is_user_data` (``tasks/**``, ``TASKS.md``, ``PLAN.md``, ...) is
    excluded, because a snapshot must carry the template skeleton, never a project's data.

    Args:
        canonical_gald3r: The canonical ``.gald3r/`` template source to capture
            (e.g. ``gald3r_core/project_template/.gald3r``).
        sys_dir: The ``.gald3r_sys`` dir that holds ``snapshots/``.
        version: The release version (``X.Y.Z`` or ``vX.Y.Z``).
        overwrite: Replace an existing snapshot dir for this version (default True —
            a re-cut of the same version restamps it).

    Returns:
        The created snapshot's ``.gald3r`` path
        (``<sys_dir>/snapshots/v<X.Y.Z>/.gald3r``).

    Raises:
        UpgradeError: When ``canonical_gald3r`` is not a directory.
    """
    canonical_gald3r = Path(canonical_gald3r)
    if not canonical_gald3r.is_dir():
        raise UpgradeError(f"canonical .gald3r/ not found for snapshot: {canonical_gald3r}")
    dest_root = Path(sys_dir) / SNAPSHOTS_DIR_NAME / _snapshot_version_tag(version)
    dest = dest_root / ".gald3r"
    if dest.exists():
        if not overwrite:
            return dest
        shutil.rmtree(dest_root)
    dest.mkdir(parents=True, exist_ok=True)
    for rel in sorted(_rel_files(canonical_gald3r)):
        if is_user_data(rel):
            continue
        src = canonical_gald3r / rel
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
    return dest


def _parse_semver(v: Optional[str]) -> Tuple[int, int, int]:
    """Parse a dot-separated semver into a comparable tuple (tolerant of suffixes).

    Mirrors the world_tree ``Gald3rVersionService._parse_semver`` so the engine and the
    backend agree on ordering.
    """
    if not v:
        return (0, 0, 0)
    main = v.split("+")[0].split("-")[0]
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


def version_check(
    *,
    current_version: Optional[str] = None,
    base_url: Optional[str] = None,
    token: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
    opener: Optional[Any] = None,
) -> Dict[str, Any]:
    """Query world_tree for the latest version and compare with ``current_version``.

    Offline-first: any failure to reach world_tree (DNS, connection refused, timeout,
    HTTP error, malformed body) returns ``reachable=False`` with a human-readable
    ``message`` and ``error`` — it NEVER raises and NEVER fabricates a latest version.

    Args:
        current_version: The project's installed version (from ``.gald3r/.identity``).
            When None, ``update_available`` is reported relative to the backend's own
            ``installed_version``.
        base_url: world_tree base URL (default :data:`DEFAULT_WORLD_TREE_URL`).
        token: Optional bearer token; the version route is JWT-gated (T112), so an
            unauthenticated probe yields ``reachable=False`` with an auth message.
        timeout: Socket timeout in seconds.
        opener: Test seam — a callable ``(url, headers, timeout) -> bytes`` that bypasses
            the network. Production leaves this None (uses :mod:`urllib`).

    Returns:
        A dict with ``reachable`` (bool), ``current`` (str|None), and — when reachable —
        ``latest`` (str), ``update_available`` (bool), ``source`` (str), plus a
        ``message``. When unreachable: ``reachable=False`` + ``error`` + ``message``.
    """
    base = (base_url or DEFAULT_WORLD_TREE_URL).rstrip("/")
    url = base + VERSION_ENDPOINT_PATH
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if opener is not None:
            raw = opener(url, headers, timeout)
        else:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - http(s) only
                raw = resp.read()
        body = json.loads(raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw)
    except urllib.error.HTTPError as e:
        reason = "authentication required" if e.code in (401, 403) else f"HTTP {e.code}"
        return {
            "reachable": False,
            "current": current_version,
            "error": reason,
            "message": (
                f"Could not reach world_tree version endpoint ({url}): {reason}. "
                "Working offline — version unknown."
            ),
        }
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        return {
            "reachable": False,
            "current": current_version,
            "error": str(e),
            "message": (
                f"Could not reach world_tree ({url}): {e}. Working offline — "
                "version unknown."
            ),
        }

    latest = body.get("latest_version") or body.get("installed_version")
    source = body.get("source", "backend")
    if current_version is not None and latest is not None:
        update_available = _parse_semver(latest) > _parse_semver(current_version)
    else:
        update_available = bool(body.get("update_available", False))

    if update_available:
        msg = f"Update available: {current_version or '?'} -> {latest} (source: {source})"
    else:
        msg = f"Up to date (current: {current_version or latest}, latest: {latest})"
    return {
        "reachable": True,
        "current": current_version,
        "latest": latest,
        "update_available": update_available,
        "source": source,
        "message": msg,
    }


# ── upgrade migration + safe self-update ───────────────────────────────────────


class UpgradeError(Exception):
    """Raised when a migration cannot proceed (missing snapshot, bad rollback, ...)."""


class UpgradeSystem:
    """Self-update operations for one project's ``.gald3r/`` (version-check + migrate).

    Attached to the :class:`gald3r.core.Gald3r` facade as ``g.upgrade``. Reuses the
    shared :class:`gald3r.config.Config` for the project root + identity version, and the
    shared :mod:`gald3r.store` frontmatter helpers for the MERGE step — it re-implements
    nothing that already exists in the engine.
    """

    #: Subdir of ``.gald3r/`` that holds the timestamped backups. Inside ``.gald3r/`` so
    #: the existing ``*.zip`` gitignore rule covers the archives.
    BACKUP_DIR_NAME = "_backups"

    #: Framework trees zipped to the repo ROOT before any apply (BUG-176 / safety). Each is
    #: snapshotted to ``<root>/<name>_<UTC ts>.zip`` so a user's custom edits ANYWHERE in
    #: a framework tree survive even a later wholesale-replace step (e.g. the deploy
    #: wrapper swapping ``.claude``/``.cursor``). Only those present on disk are zipped.
    FULL_BACKUP_DIRS: Tuple[str, ...] = (
        ".gald3r",
        ".gald3r_sys",
        ".claude",
        ".cursor",
        ".agent",
        ".codex",
        ".opencode",
    )

    #: Subtrees never recursed into when building a full backup (volatile / huge / VCS).
    _FULL_BACKUP_SKIP_PARTS = frozenset(
        {".git", "__pycache__", ".venv", "node_modules", BACKUP_DIR_NAME}
    )

    def __init__(self, config):
        self.config = config
        self.root = config.root
        self.gald3r_dir = config.gald3r_dir

    # ---- version-check (thin wrapper binding the project's current version) ----
    def check(
        self,
        *,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        opener: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """version_check() bound to this project's installed version (from .identity)."""
        return version_check(
            current_version=self.config.gald3r_rel_version,
            base_url=base_url,
            token=token,
            timeout=timeout,
            opener=opener,
        )

    # ---- snapshot resolution ----
    @property
    def snapshots_dir(self) -> Path:
        """The ``.gald3r_sys/snapshots`` dir holding versioned ``v<X.Y.Z>/.gald3r`` captures (T463)."""
        return self.root / ".gald3r_sys" / SNAPSHOTS_DIR_NAME

    def resolve_version_dir(self, version: str) -> Optional[Path]:
        """Map a stored snapshot version (``X.Y.Z`` or ``vX.Y.Z``) -> its ``.gald3r`` dir (T463).

        Looks under ``.gald3r_sys/snapshots/v<X.Y.Z>/.gald3r``. Returns None when no
        snapshot was captured for that version (the caller turns that into a clear,
        non-crashing error — no fabricated source).
        """
        if not version:
            return None
        cand = self.snapshots_dir / _snapshot_version_tag(version) / ".gald3r"
        return cand if cand.is_dir() else None

    def resolve_to_dir(
        self, to_dir: Optional[Path] = None, to_version: Optional[str] = None
    ) -> Optional[Path]:
        """Resolve the ``--to-dir`` (target format) snapshot.

        Precedence:
          1. explicit ``to_dir`` argument,
          2. an explicit ``to_version`` resolved against the T463 versioned snapshots,
          3. the newest T463 versioned snapshot (``.gald3r_sys/snapshots/<latest>/.gald3r``)
             when one is present,
          4. the single canonical snapshot at
             ``<root>/.gald3r_sys/template_verification/.gald3r`` (the framework fallback).

        Returns the resolved path, or None when no snapshot can be found (caller turns
        that into a clear, non-crashing message — no fabricated source).
        """
        if to_dir is not None:
            p = Path(to_dir)
            return p if p.is_dir() else None
        if to_version:
            return self.resolve_version_dir(to_version)
        sys_dir = self.root / ".gald3r_sys"
        # (3) T463 versioned snapshots — use the newest as the implicit target format.
        snapshots = sys_dir / SNAPSHOTS_DIR_NAME
        if snapshots.is_dir():
            versioned = sorted(
                (d for d in snapshots.iterdir() if (d / ".gald3r").is_dir()),
                key=lambda d: _parse_semver(d.name.lstrip("v")),
            )
            if versioned:
                return versioned[-1] / ".gald3r"
        # (4) Fallback: the single current canonical snapshot.
        canonical = sys_dir / "template_verification" / ".gald3r"
        return canonical if canonical.is_dir() else None

    # ---- classify (ADD / MERGE / DEPRECATE / SKIP) ----
    def plan(
        self,
        *,
        to_dir: Optional[Path] = None,
        from_dir: Optional[Path] = None,
        to_version: Optional[str] = None,
        from_version: Optional[str] = None,
        deprecate_removed: bool = False,
    ) -> Dict[str, Any]:
        """Diff the project's ``.gald3r/`` against the target snapshot. No writes.

        Source precedence: explicit ``from_dir`` > ``from_version`` (resolved against a
        stored T463 snapshot) > the live project ``.gald3r/``. Target precedence: explicit
        ``to_dir`` > ``to_version`` (stored snapshot) > newest stored snapshot > canonical
        fallback (see :meth:`resolve_to_dir`). Returns a plan dict with ``add`` / ``merge``
        / ``deprecate`` / ``skip`` lists (each a ``.gald3r/``-relative POSIX path) plus the
        resolved ``from_dir`` / ``to_dir`` and an ``error`` when a requested snapshot is
        missing.

        **DEPRECATE is opt-in (BUG-176).** By default (``deprecate_removed=False``) the
        plan NEVER deprecates: it only ADDs new framework files and MERGEs format changes,
        leaving every other live file untouched. The legacy "any live file absent from the
        target is obsolete" rule is unsafe whenever ``from`` is the *live project* (which
        is the default ``from`` source) rather than a real *old template* baseline — under
        that rule every user-authored file (specs, tracking notes, loose top-level docs,
        coordination ledgers, even an accidental nested framework tree) looks deletable and
        was being archived as ``*_deprecated_<date>`` (the T430 disaster). Pass
        ``deprecate_removed=True`` ONLY for a true template-vs-template diff (explicit
        ``from_version``/``from_dir`` baseline) where removed-framework cleanup is wanted.
        """
        if from_dir is not None:
            src: Optional[Path] = Path(from_dir)
        elif from_version:
            src = self.resolve_version_dir(from_version)
        else:
            src = self.gald3r_dir
        target = self.resolve_to_dir(to_dir, to_version)
        plan: Dict[str, Any] = {
            "from_dir": str(src) if src else None,
            "to_dir": str(target) if target else None,
            "add": [],
            "merge": [],
            "deprecate": [],
            "skip": [],
            "error": None,
        }
        if from_version and src is None:
            plan["error"] = (
                f"No stored snapshot for --from-version {from_version} (looked for "
                f".gald3r_sys/snapshots/{_snapshot_version_tag(from_version)}/.gald3r). "
                "Cannot plan migration."
            )
            return plan
        if to_version and target is None:
            plan["error"] = (
                f"No stored snapshot for --to-version {to_version} (looked for "
                f".gald3r_sys/snapshots/{_snapshot_version_tag(to_version)}/.gald3r). "
                "Cannot plan migration."
            )
            return plan
        if target is None:
            plan["error"] = (
                "No target snapshot found (looked for .gald3r_sys/snapshots/<v>/.gald3r "
                "and .gald3r_sys/template_verification/.gald3r). Cannot plan migration."
            )
            return plan

        target_files = _rel_files(target)
        src_files = _rel_files(src)

        for rel in sorted(target_files):
            if is_user_data(rel):
                plan["skip"].append(rel)
                continue
            if rel not in src_files:
                plan["add"].append(rel)
            elif _needs_merge(target / rel, src / rel):
                plan["merge"].append(rel)
        if deprecate_removed:
            for rel in sorted(src_files):
                if is_user_data(rel) or _is_deprecated_archive(rel):
                    continue
                if rel not in target_files:
                    plan["deprecate"].append(rel)
        return plan

    # ---- apply a plan to a target .gald3r/ ----
    def _apply_plan(self, plan: Dict[str, Any], gald3r_dir: Path) -> Dict[str, Any]:
        """Apply ADD / MERGE / DEPRECATE actions of ``plan`` to ``gald3r_dir``. Writes."""
        target = Path(plan["to_dir"])
        applied = {"added": 0, "merged": 0, "deprecated": 0}
        for rel in plan["add"]:
            dst = gald3r_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target / rel, dst)
            applied["added"] += 1
        for rel in plan["merge"]:
            _merge_file(target / rel, gald3r_dir / rel)
            applied["merged"] += 1
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        for rel in plan["deprecate"]:
            old = gald3r_dir / rel
            if old.exists():
                archived = old.with_name(f"{old.name}_deprecated_{stamp}")
                shutil.move(str(old), str(archived))
                applied["deprecated"] += 1
        return applied

    # ---- backup / rollback primitives ----
    def backup(self) -> Path:
        """Zip the whole ``.gald3r/`` tree to a timestamped, gitignored archive.

        The archive lives at ``.gald3r/_backups/.gald3r_backup_YYYYMMDD_HHMMSS.zip`` —
        a ``.zip`` under ``.gald3r/``, which the existing ``.gald3r/.gitignore`` ``*.zip``
        rule already excludes from version control. Returns the archive path.
        """
        backup_dir = self.gald3r_dir / self.BACKUP_DIR_NAME
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive = backup_dir / f".gald3r_backup_{ts}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(self.gald3r_dir.rglob("*")):
                if path.is_dir():
                    continue
                # Never recurse into the backup dir itself (no nesting backups).
                if self.BACKUP_DIR_NAME in path.relative_to(self.gald3r_dir).parts:
                    continue
                zf.write(path, path.relative_to(self.gald3r_dir).as_posix())
        return archive

    def restore(self, archive: Path) -> None:
        """Restore ``.gald3r/`` from a backup archive (rollback). Replaces non-backup state.

        Removes every child of ``.gald3r/`` except the ``_backups/`` dir, then extracts the
        archive back over the tree — leaving the project byte-for-byte as it was before the
        failed migration.
        """
        archive = Path(archive)
        if not archive.is_file():
            raise UpgradeError(f"backup archive not found for rollback: {archive}")
        for child in list(self.gald3r_dir.iterdir()):
            if child.name == self.BACKUP_DIR_NAME:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(self.gald3r_dir)

    # ---- comprehensive pre-flight safety backup (BUG-176) ----
    def backup_full(self) -> List[Path]:
        """Zip every present framework tree (:attr:`FULL_BACKUP_DIRS`) to the repo root.

        Each tree is written to ``<root>/<name>_<YYYYMMDD_HHMMSS>.zip`` (UTC) and the repo
        ``.gitignore`` is ensured to exclude those archives. This runs BEFORE any
        apply/install mutates the framework trees, so a user's custom code anywhere under
        ``.gald3r/``, ``.gald3r_sys/`` or any platform folder is always recoverable — even
        if a downstream step replaces a whole folder. Volatile/huge subtrees
        (``.git``/``.venv``/``__pycache__``/``node_modules``/``_backups``) are skipped.
        Returns the list of archive paths written (empty when no tree is present).
        """
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        written: List[Path] = []
        for name in self.FULL_BACKUP_DIRS:
            folder = self.root / name
            if not folder.is_dir():
                continue
            archive = self.root / f"{name}_{ts}.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in sorted(folder.rglob("*")):
                    if path.is_dir():
                        continue
                    rel = path.relative_to(folder)
                    if self._FULL_BACKUP_SKIP_PARTS.intersection(rel.parts):
                        continue
                    zf.write(path, (Path(name) / rel).as_posix())
            written.append(archive)
        if written:
            self._ensure_zip_gitignored()
        return written

    def _ensure_zip_gitignored(self) -> None:
        """Idempotently ensure the repo-root ``.gitignore`` excludes the full-backup zips.

        No-op when ``*.zip`` is already ignored. Otherwise appends an explicit, targeted
        block (one ``<name>_*.zip`` glob per framework tree) under a stable marker so the
        timestamped archives never dirty the working tree.
        """
        gi = self.root / ".gitignore"
        marker = "# gald3r upgrade/install safety backups (auto-added, BUG-176)"
        existing = gi.read_text(encoding="utf-8") if gi.is_file() else ""
        lines = {ln.strip() for ln in existing.splitlines()}
        if "*.zip" in lines or marker in existing:
            return
        block = [marker] + [f"{name}_*.zip" for name in self.FULL_BACKUP_DIRS]
        sep = "" if (not existing or existing.endswith("\n")) else "\n"
        with gi.open("a", encoding="utf-8") as fh:
            fh.write(sep + "\n".join(block) + "\n")

    # ---- the safe self-update orchestration ----
    def self_update(
        self,
        *,
        to_dir: Optional[Path] = None,
        from_dir: Optional[Path] = None,
        to_version: Optional[str] = None,
        from_version: Optional[str] = None,
        dry_run: bool = True,
        version_info: Optional[Dict[str, Any]] = None,
        deprecate_removed: bool = False,
    ) -> Dict[str, Any]:
        """Backup -> migrate -> rollback-on-failure. The shared T473/T475 safe-update.

        Sequence (apply mode):
          1. compute the migration plan (no writes),
          2. zip every present framework tree to the repo root (:meth:`backup_full`) — the
             comprehensive, gitignored safety snapshot (BUG-176),
          3. create a timestamped gitignored ``.gald3r/`` backup used for rollback,
          4. apply the plan; on ANY exception, RESTORE the ``.gald3r/`` backup and re-raise
             as a reported failure (``rolled_back=True``).

        DEPRECATE is opt-in (``deprecate_removed``, default False) — see :meth:`plan`.
        ``to_version`` / ``from_version`` resolve stored T463 snapshots (see :meth:`plan`).
        ``dry_run=True`` (default) returns the plan + ``version_delta`` and writes nothing
        (no backup taken). Returns a result dict the CLI/MCP render directly.
        """
        plan = self.plan(
            to_dir=to_dir, from_dir=from_dir,
            to_version=to_version, from_version=from_version,
            deprecate_removed=deprecate_removed,
        )
        result: Dict[str, Any] = {
            "dry_run": dry_run,
            "version_delta": _version_delta(version_info, self.config.gald3r_rel_version),
            "plan": plan,
            "full_backup": None,
            "backup": None,
            "applied": None,
            "rolled_back": False,
            "ok": plan["error"] is None,
            "error": plan["error"],
        }
        if plan["error"] is not None or dry_run:
            return result

        result["full_backup"] = [str(p) for p in self.backup_full()]
        archive = self.backup()
        result["backup"] = str(archive)
        try:
            result["applied"] = self._apply_plan(plan, self.gald3r_dir)
            result["ok"] = True
        except Exception as e:  # rollback on ANY failure, then report
            try:
                self.restore(archive)
                result["rolled_back"] = True
            except Exception as restore_err:  # pragma: no cover - defensive
                result["error"] = (
                    f"migration failed ({e}); ROLLBACK ALSO FAILED ({restore_err}) — "
                    f"restore manually from {archive}"
                )
                result["ok"] = False
                return result
            result["error"] = f"migration failed and was rolled back: {e}"
            result["ok"] = False
        return result


# ── module-level helpers (no state) ────────────────────────────────────────────


def _rel_files(base: Path) -> set:
    """Return the set of ``base``-relative POSIX file paths (skipping non-format dirs)."""
    out = set()
    if not base.is_dir():
        return out
    for path in base.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(base)
        if any(part in _DIFF_SKIP_DIRS for part in rel.parts):
            continue
        out.add(rel.as_posix())
    return out


def _differs(a: Path, b: Path) -> bool:
    """True when files ``a`` and ``b`` have different bytes."""
    try:
        return a.read_bytes() != b.read_bytes()
    except OSError:
        return True


def _is_deprecated_archive(rel: str) -> bool:
    """True when ``rel`` names a file archived by a prior DEPRECATE pass."""
    return _DEPRECATED_INFIX in Path(rel).name


def _needs_merge(target: Path, dst: Path) -> bool:
    """Decide MERGE *idempotently* — what :func:`_merge_file` would actually change.

    The byte comparison alone is wrong because a MERGE intentionally keeps the project's
    body (user content), so a frontmatter file would otherwise classify as MERGE forever.
    This mirrors exactly what _merge_file does, so a second pass over an already-migrated
    file reports no change (the @g-update contract's idempotence guarantee).

    For frontmatter docs: MERGE only if a template key is missing from the project copy
    or a format-rev key (``gald3r_rel_version`` / ``schema_version``) differs.
    For framework-owned non-frontmatter files (template wins): MERGE iff bytes differ.
    """
    try:
        target_text = target.read_text(encoding="utf-8-sig")
        dst_text = dst.read_text(encoding="utf-8-sig")
    except OSError:
        return True
    t_fm, _ = split_doc(target_text)
    d_fm, _ = split_doc(dst_text)
    if not t_fm and not d_fm:
        return target.read_bytes() != dst.read_bytes()  # framework text file -> template wins
    for k, v in t_fm.items():
        if k in _REL_VERSION_KEYS:
            if d_fm.get(k) != v:
                return True
        elif k not in d_fm:
            return True
    return False


def _merge_file(target: Path, dst: Path) -> None:
    """MERGE ``target`` into ``dst``, preserving user data and bumping the format rev.

    For markdown docs with frontmatter: keep the project's existing values, ADD any new
    template keys (with their template defaults), and bump ``gald3r_rel_version`` /
    ``schema_version`` from the target. The body is left as the project's (user content).
    For non-frontmatter files (e.g. ``.gitignore``): the template version wins, since these
    are framework-owned and the gitignore explicitly says "safe to overwrite on upgrades".
    """
    target_text = target.read_text(encoding="utf-8-sig")
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dst)
        return
    t_fm, _t_body = split_doc(target_text)
    d_fm, d_body = split_doc(dst.read_text(encoding="utf-8-sig"))
    if not t_fm and not d_fm:
        # No frontmatter on either side -> framework-owned text file; template wins.
        shutil.copy2(target, dst)
        return
    merged = dict(d_fm)  # start from project values (preserve user data)
    for k, v in t_fm.items():
        if k in _REL_VERSION_KEYS:
            merged[k] = v  # always adopt the new format revision
        elif k not in merged:
            merged[k] = v  # add new template keys with template defaults
    out = emit_frontmatter(merged) + "\n\n" + (d_body or "").strip() + "\n"
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)


def _version_delta(version_info: Optional[Dict[str, Any]], current: str) -> Dict[str, Any]:
    """Build a small {current, latest, update_available} delta from a version_check result."""
    if not version_info or not version_info.get("reachable"):
        return {
            "current": current,
            "latest": None,
            "update_available": None,
            "note": (version_info or {}).get(
                "message", "version unknown (world_tree not reached)"
            ),
        }
    return {
        "current": version_info.get("current", current),
        "latest": version_info.get("latest"),
        "update_available": version_info.get("update_available"),
    }
