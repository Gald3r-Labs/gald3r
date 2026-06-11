"""Swarm file-lock manifests (T1059 — earendil-works/pi file-lock pattern).

Python port of gald3r_worktree.ps1 (T1585) — lock layer.

Each parallel swarm bucket declares the files it intends to modify in a lock
manifest written under .gald3r-swarm-locks/lock_{bucket_id}.json BEFORE it
starts work. Create checks existing active manifests for overlap and refuses
(LOCK_CONFLICT). LockReport surfaces multi-bucket claims as WARN, never BLOCK.
Manifests are ephemeral (gald3rignored, never committed); expired manifests
are silently ignored everywhere.
"""
# @subsystems: AGENT_ORCHESTRATION
from __future__ import annotations

import json
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from worktree_lib.gitio import (
    WorktreeError,
    is_blank,
    iso_o,
    parse_datetime,
    read_json_file,
    safe_segment,
    utc_now,
)

LOCK_DIR_NAME = ".gald3r-swarm-locks"


def swarm_lock_dir(repo_root: str) -> Path:
    """<repo>/.gald3r-swarm-locks (PS1 Get-SwarmLockDir)."""
    return Path(repo_root) / LOCK_DIR_NAME


def normalize_lock_path(path: Optional[str]) -> Optional[str]:
    """Stable, case-insensitive comparison key (PS1 ConvertTo-NormalizedLockPath)."""
    if is_blank(path):
        return None
    p = str(path).strip().replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    p = p.rstrip("/")
    return p.lower()


def active_swarm_locks(repo_root: str) -> List[Dict[str, Any]]:
    """All active (non-expired) lock manifests (PS1 Get-ActiveSwarmLocks)."""
    lock_dir = swarm_lock_dir(repo_root)
    if not lock_dir.exists():
        return []

    now = utc_now()
    active: List[Dict[str, Any]] = []
    for file in sorted(lock_dir.glob("lock_*.json")):
        if not file.is_file():
            continue
        manifest = read_json_file(file)
        if manifest is None:
            continue

        # Silently ignore expired locks. Stored values are ISO-8601 UTC;
        # a missing timezone is interpreted as UTC (AssumeUniversal parity).
        expires_raw = manifest.get("expires_at")
        if expires_raw is not None and not is_blank(str(expires_raw)):
            expires_utc = parse_datetime(expires_raw, assume_utc=True)
            if expires_utc is not None and expires_utc < now:
                continue

        paths = manifest.get("paths") or []
        if not isinstance(paths, list):
            paths = [paths]
        normalized = [n for n in (normalize_lock_path(p) for p in paths) if n]

        active.append(
            {
                "bucket_id": manifest.get("bucket_id"),
                "owner": manifest.get("owner"),
                "paths": paths,
                "created_at": manifest.get("created_at"),
                "expires_at": manifest.get("expires_at"),
                "manifest_path": str(file),
                "normalized_paths": normalized,
            }
        )
    return active


def write_swarm_lock_manifest(
    repo_root: str,
    bucket_id: Optional[str],
    owner: str,
    lock_files: Sequence[str],
    bucket_ttl_minutes: int,
) -> Dict[str, Any]:
    """PS1 Write-SwarmLockManifest — overlap check, then atomic manifest write.

    Raises:
        WorktreeError: LOCK_CONFLICT when a claimed path overlaps another
            active bucket's claim; also on a missing bucket id or empty claim.
    """
    if is_blank(bucket_id):
        raise WorktreeError("-BucketId is required to write a swarm lock manifest.")
    assert bucket_id is not None

    claimed_normalized = [n for n in (normalize_lock_path(p) for p in lock_files) if n]
    if not claimed_normalized:
        raise WorktreeError(
            f"-LockFiles must list at least one path to claim for bucket '{bucket_id}'."
        )

    conflicts: List[Dict[str, Any]] = []
    for lock in active_swarm_locks(repo_root):
        if str(lock.get("bucket_id")) == str(bucket_id):
            continue  # our own prior manifest = refresh, not a conflict
        for claimed in claimed_normalized:
            if claimed in lock["normalized_paths"]:
                conflicts.append(
                    {
                        "path": claimed,
                        "owning_bucket": lock.get("bucket_id"),
                        "owning_owner": lock.get("owner"),
                    }
                )

    if conflicts:
        detail = "; ".join(
            f"{c['path']} (owned by bucket '{c['owning_bucket']}')" for c in conflicts
        )
        raise WorktreeError(
            f"LOCK_CONFLICT: bucket '{bucket_id}' claims path(s) already locked "
            f"by another bucket: {detail}"
        )

    lock_dir = swarm_lock_dir(repo_root)
    lock_dir.mkdir(parents=True, exist_ok=True)

    created_at = utc_now()
    expires_at = created_at + timedelta(minutes=2 * max(1, bucket_ttl_minutes))
    safe_bucket = safe_segment(bucket_id)
    manifest_path = lock_dir / f"lock_{safe_bucket}.json"

    manifest: Dict[str, Any] = {
        "schema_version": "1.0",
        "bucket_id": bucket_id,
        "owner": owner,
        "paths": list(lock_files),
        "created_at": iso_o(created_at),
        "expires_at": iso_o(expires_at),
        "ttl_minutes": bucket_ttl_minutes,
    }

    # Atomic write: temp file + rename so a concurrent reader never sees a half file.
    temp_path = lock_dir / f".lock_{safe_bucket}.{uuid.uuid4().hex}.tmp"
    try:
        temp_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temp_path.replace(manifest_path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return {
        "action": "lock-claimed",
        "bucket_id": bucket_id,
        "owner": owner,
        "manifest_path": str(manifest_path),
        "paths": list(lock_files),
        "created_at": manifest["created_at"],
        "expires_at": manifest["expires_at"],
    }


def swarm_lock_conflict_report(repo_root: str) -> Dict[str, Any]:
    """PS1 Get-SwarmLockConflictReport — coordinator-side WARN-level overlaps."""
    locks = active_swarm_locks(repo_root)

    # Map normalized path -> first original path + claiming bucket ids.
    by_path: Dict[str, Dict[str, Any]] = {}
    for lock in locks:
        normalized = lock["normalized_paths"]
        originals = lock["paths"]
        for i, norm in enumerate(normalized):
            orig = originals[i] if i < len(originals) else norm
            if norm not in by_path:
                by_path[norm] = {"path": orig, "buckets": []}
            by_path[norm]["buckets"].append(lock.get("bucket_id"))

    conflicts: List[Dict[str, Any]] = []
    for entry in by_path.values():
        unique_buckets = list(dict.fromkeys(entry["buckets"]))
        if len(unique_buckets) > 1:
            conflicts.append(
                {"path": entry["path"], "buckets": unique_buckets, "level": "WARN"}
            )

    return {
        "action": "lock-report",
        "active_locks": len(locks),
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "locks": [
            {
                "bucket_id": lock.get("bucket_id"),
                "owner": lock.get("owner"),
                "paths": lock.get("paths"),
                "expires_at": lock.get("expires_at"),
            }
            for lock in locks
        ],
    }
