"""One-time, idempotent, non-destructive migration of scattered legacy gald3r
per-user locations into the unified canonical home (T530, epic T470).

T559's :mod:`gald3r.migration_scan` is the read-only *discovery* half — it reports
which legacy per-user locations exist (``~/.gald3r``, ``%APPDATA%\\gald3r``, …)
without touching anything. This module is the *move* half that T559 deferred to the
T530 epic: it consumes that scan report and consolidates the existing legacy trees
into the canonical home resolved by :func:`gald3r.home.resolve_home` (T557).

Design contract (matching the T530 spec — "safe, idempotent, logged, never
destructive on failure"):

    * **Idempotent.** A sentinel file (:data:`MIGRATION_SENTINEL`) is written inside
      the canonical home the first time migration completes. A second run sees the
      sentinel and is a no-op (``already_migrated``). Even without the sentinel, a
      file already present at the destination is never overwritten.
    * **Non-destructive.** Legacy source trees are **copied** (merge semantics), not
      moved, and are never deleted. A ``.migrated_to`` breadcrumb is dropped in each
      migrated legacy dir pointing at the canonical home, so a human can reclaim the
      space deliberately. Nothing is removed automatically.
    * **Safe on failure.** Each legacy location is migrated independently; a failure
      on one (permission, I/O) records an ``error`` for that entry and continues —
      it never leaves a half-written destination file (copy is per-file, skip-if-
      exists) and never deletes a source.
    * **Logged.** Both :func:`plan_migration` and :func:`migrate` return a structured,
      JSON-serializable report (and the CLI ``gald3r migrate-home`` prints it).

Pure stdlib (``os`` / ``pathlib`` / ``shutil``) so it runs anywhere uv puts a
Python, with no hardcoded drive letters or separators (DRY with
:mod:`gald3r.migration_scan` / :mod:`gald3r.home`).
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from gald3r import home, migration_scan

#: Sentinel written inside the canonical home once migration completes. Its
#: presence makes a re-run a no-op (idempotency marker, not user data).
MIGRATION_SENTINEL = ".home_migrated"

#: Breadcrumb dropped in a migrated legacy dir, pointing at the canonical home.
#: It documents (for a human) that the contents were consolidated and the legacy
#: copy is now safe to remove by hand. The legacy tree itself is left intact.
LEGACY_BREADCRUMB = ".migrated_to"


@dataclass
class MigrationAction:
    """One planned (or executed) per-legacy-location migration step."""

    label: str
    source: Path
    #: One of: ``migrate`` (will copy), ``skip_absent`` (source does not exist),
    #: ``skip_empty`` (source has no entries), ``skip_is_target`` (source IS the
    #: canonical home), ``done`` (copied OK), ``error`` (copy failed).
    action: str
    files_copied: int = 0
    files_skipped: int = 0  # already present at destination (never overwritten)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "source": str(self.source),
            "action": self.action,
            "files_copied": self.files_copied,
            "files_skipped": self.files_skipped,
            "error": self.error,
        }


@dataclass
class MigrationReport:
    """Structured, JSON-serializable result of a plan or a migration run."""

    canonical_target: Path
    already_migrated: bool
    actions: List[MigrationAction] = field(default_factory=list)

    def migrated(self) -> List[MigrationAction]:
        """Only the actions that actually copied (or would copy) something."""
        return [a for a in self.actions if a.action in ("migrate", "done")]

    def to_dict(self) -> Dict[str, object]:
        return {
            "canonical_target": str(self.canonical_target),
            "already_migrated": self.already_migrated,
            "actions": [a.to_dict() for a in self.actions],
        }


def _is_sentinel_present(target: Path) -> bool:
    """Return True when the canonical home already carries the migration sentinel."""
    return (target / MIGRATION_SENTINEL).exists()


def plan_migration(
    env: dict,
    platform_name: str,
    *,
    candidates: Optional[Mapping[str, Path]] = None,
) -> MigrationReport:
    """Plan the legacy→canonical migration without writing anything (pure).

    Runs the read-only T559 scan and classifies each candidate:

        * the canonical home itself        -> ``skip_is_target``
        * a non-existent legacy location    -> ``skip_absent``
        * an existing-but-empty legacy dir  -> ``skip_empty``
        * an existing non-empty legacy dir  -> ``migrate``

    Args:
        env: Environment mapping (injected for purity / testability).
        platform_name: ``platform.system()`` vocabulary string.
        candidates: Optional explicit label→path map (tests pass a tmp tree);
            defaults to :func:`gald3r.migration_scan.legacy_candidate_paths`.

    Returns:
        A :class:`MigrationReport` describing what a migration *would* do. Nothing
        is created, moved, or deleted.
    """
    scan_report = migration_scan.scan(env, platform_name, candidates=candidates)
    target = scan_report.canonical_target
    already = _is_sentinel_present(target)

    # T573 hardening: compare on a CONSISTENT resolution basis. ``target`` is
    # already fully resolved (``home.resolve_home`` calls ``.resolve()``); resolve
    # it again defensively so the self-skip below cannot diverge from a candidate
    # that is a symlink pointing at the canonical target. The candidate's
    # existence/is_dir classification comes from the scan (unresolved path), but
    # the ``== target`` self-skip is authoritative on the resolved path, so a
    # symlinked legacy dir cannot be both "skip_is_target" and "migrate".
    target = target.expanduser().resolve()

    actions: List[MigrationAction] = []
    for cand in scan_report.candidates:
        src = Path(cand.path).expanduser().resolve()
        if src == target:
            actions.append(MigrationAction(cand.label, src, "skip_is_target"))
        elif not cand.exists:
            actions.append(MigrationAction(cand.label, src, "skip_absent"))
        elif cand.is_dir and cand.entry_count == 0:
            actions.append(MigrationAction(cand.label, src, "skip_empty"))
        else:
            actions.append(MigrationAction(cand.label, src, "migrate"))
    return MigrationReport(canonical_target=target, already_migrated=already, actions=actions)


def _copy_tree_merge(source: Path, dest: Path) -> MigrationAction:
    """Copy ``source`` into ``dest`` with merge semantics; never overwrite.

    Existing destination files are LEFT as-is (counted as skipped) so a re-run or a
    partial prior run can never clobber already-migrated data. Returns a populated
    :class:`MigrationAction` (``done`` or ``error``); on any I/O failure the partial
    work done so far is reported but no source file is ever removed.

    T573 hardening: when ``source`` is a regular **file** (not a directory),
    ``source.rglob("*")`` yields nothing — pre-T573 that silently reported ``done``
    with 0 files copied, leaving the file's content un-migrated. Such a candidate is
    now copied as the single file it is (into ``dest/<source.name>``, skip-if-exists),
    so a file-shaped legacy location is migrated rather than dropped. All currently
    documented candidates are directories, so this guards a latent case.
    """
    label = source.name
    copied = 0
    skipped = 0
    # File-candidate case (latent today): copy the file itself rather than walking
    # an empty rglob. Skip-if-exists preserves the never-overwrite invariant.
    if source.is_file():
        out = dest / source.name
        try:
            if out.exists():
                skipped = 1
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, out)
                copied = 1
        except OSError as exc:
            return MigrationAction(
                label, source, "error", files_copied=copied, files_skipped=skipped,
                error=str(exc),
            )
        return MigrationAction(
            label, source, "done", files_copied=copied, files_skipped=skipped,
        )
    try:
        for item in source.rglob("*"):
            if item.name in (LEGACY_BREADCRUMB,):
                continue
            rel = item.relative_to(source)
            out = dest / rel
            if item.is_dir():
                out.mkdir(parents=True, exist_ok=True)
                continue
            if out.exists():
                skipped += 1
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, out)
            copied += 1
    except OSError as exc:
        return MigrationAction(
            label, source, "error", files_copied=copied, files_skipped=skipped,
            error=str(exc),
        )
    return MigrationAction(
        label, source, "done", files_copied=copied, files_skipped=skipped,
    )


def _write_breadcrumb(source: Path, target: Path) -> None:
    """Drop a ``.migrated_to`` breadcrumb in ``source`` pointing at ``target``.

    Best-effort and non-fatal: the legacy tree stays intact regardless, so a
    breadcrumb-write failure (e.g. read-only legacy dir) must not fail the
    migration of the data that was already copied.
    """
    try:
        (source / LEGACY_BREADCRUMB).write_text(
            f"Contents consolidated into the unified gald3r home (T530):\n"
            f"{target}\n"
            f"This legacy copy is safe to delete by hand once verified.\n",
            encoding="utf-8",
            newline="\n",
        )
    except OSError:
        # Breadcrumb is advisory only; a read-only legacy dir must not fail the
        # migration of data already copied. Intentionally swallowed.
        pass


def migrate(
    env: dict,
    platform_name: str,
    *,
    candidates: Optional[Mapping[str, Path]] = None,
    dry_run: bool = False,
) -> MigrationReport:
    """Run the one-time, idempotent, non-destructive legacy→canonical migration.

    Idempotent: if the canonical home already carries :data:`MIGRATION_SENTINEL`,
    this returns immediately with ``already_migrated=True`` and the planned actions
    (no copies). Otherwise each ``migrate`` candidate is copied into the canonical
    home (merge, skip-if-exists), a breadcrumb is left in the legacy dir, and the
    sentinel is written so subsequent runs are no-ops.

    Args:
        env: Environment mapping (injected for purity / testability).
        platform_name: ``platform.system()`` vocabulary string.
        candidates: Optional explicit label→path map (tests pass a tmp tree).
        dry_run: When True, behaves like :func:`plan_migration` — nothing on disk is
            created, copied, or marked.

    Returns:
        A :class:`MigrationReport` with the per-location outcome (``done`` /
        ``error`` / the various ``skip_*``). Source trees are never deleted.
    """
    report = plan_migration(env, platform_name, candidates=candidates)
    if dry_run or report.already_migrated:
        return report

    target = report.canonical_target
    target.mkdir(parents=True, exist_ok=True)

    executed: List[MigrationAction] = []
    for planned in report.actions:
        if planned.action != "migrate":
            executed.append(planned)
            continue
        result = _copy_tree_merge(planned.source, target)
        result.label = planned.label  # preserve caller-provided label
        if result.action == "done":
            _write_breadcrumb(planned.source, target)
        executed.append(result)

    report.actions = executed
    # Mark complete only when no candidate errored, so a failed run can be retried.
    if not any(a.action == "error" for a in executed):
        try:
            (target / MIGRATION_SENTINEL).write_text(
                "migrated\n", encoding="utf-8", newline="\n"
            )
        except OSError:
            # Sentinel is an idempotency optimization; if it cannot be written the
            # copy already succeeded (skip-if-exists keeps a re-run safe). Swallowed.
            pass
    return report
