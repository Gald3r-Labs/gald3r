"""Read-only scanner that REPORTS scattered legacy gald3r locations (T559).

T530's one-time migration must first discover what scattered per-user storage
already exists before anything is moved. This module is the **discovery half
only**: it probes a documented set of legacy locations and returns a structured
report (existence + a shallow content summary) alongside the canonical target home
(T557 :func:`gald3r.home.resolve_home`). It is STRICTLY read-only — it never
creates, moves, writes, or deletes any path — so it is safe for an autonomous
agent to run. The destructive MOVE stays in the T530 epic.

Documented legacy candidate locations (per surface / OS), label → path:

    Windows: ``%APPDATA%\\gald3r``, ``~/.gald3r``, ``~/gald3r``
    macOS:   ``~/.gald3r``, ``~/Library/Application Support/gald3r``, ``~/.config/gald3r``
    Linux:   ``~/.gald3r``, ``~/.local/share/gald3r``, ``~/.config/gald3r``

(The canonical target itself is excluded from the candidate set when it collides.)
"""
# @subsystems: PROJECT_IDENTITY_SETUP
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from gald3r import home

HOME_DIR_NAME = home.HOME_DIR_NAME  # "gald3r"


def legacy_candidate_paths(env: dict, platform_name: str) -> Dict[str, Path]:
    """Return the documented label→path legacy-location map for this OS (pure)."""
    raw_home = (env.get("HOME") or env.get("USERPROFILE") or "").strip()
    base = Path(raw_home) if raw_home else Path.home()
    candidates: Dict[str, Path] = {
        "dot_gald3r": base / f".{HOME_DIR_NAME}",
    }
    if platform_name == "Windows":
        appdata = (env.get("APPDATA") or "").strip()
        appdata_base = Path(appdata) if appdata else base / "AppData" / "Roaming"
        candidates["appdata_roaming"] = appdata_base / HOME_DIR_NAME
        candidates["home_gald3r"] = base / HOME_DIR_NAME
    elif platform_name == "Darwin":
        candidates["app_support"] = base / "Library" / "Application Support" / HOME_DIR_NAME
        candidates["xdg_config"] = base / ".config" / HOME_DIR_NAME
    else:
        candidates["xdg_data"] = base / ".local" / "share" / HOME_DIR_NAME
        candidates["xdg_config"] = base / ".config" / HOME_DIR_NAME
    return candidates


@dataclass(frozen=True)
class LegacyCandidate:
    """One probed legacy location + a shallow, read-only content summary."""

    label: str
    path: Path
    exists: bool
    is_dir: bool
    entry_count: int  # immediate children when a dir, else 0
    total_bytes: int  # sum of file sizes (recursive), best-effort


@dataclass
class ScanReport:
    """The structured result of a legacy-location scan."""

    canonical_target: Path
    candidates: List[LegacyCandidate] = field(default_factory=list)

    def existing(self) -> List[LegacyCandidate]:
        """Only the candidates that actually exist on disk."""
        return [c for c in self.candidates if c.exists]


def _summarize(path: Path) -> LegacyCandidate:
    """Probe a single path read-only. No writes/moves/deletes ever occur here."""
    exists = path.exists()
    if not exists:
        return LegacyCandidate(path.name, path, False, False, 0, 0)
    is_dir = path.is_dir()
    entry_count = 0
    total_bytes = 0
    if is_dir:
        try:
            children = list(path.iterdir())
        except OSError:
            children = []
        entry_count = len(children)
        for sub in path.rglob("*"):
            try:
                if sub.is_file():
                    total_bytes += sub.stat().st_size
            except OSError:
                continue
    else:
        try:
            total_bytes = path.stat().st_size
        except OSError:
            total_bytes = 0
    return LegacyCandidate(path.name, path, True, is_dir, entry_count, total_bytes)


def scan(
    env: dict,
    platform_name: str,
    *,
    candidates: Optional[Mapping[str, Path]] = None,
) -> ScanReport:
    """Scan the legacy candidate locations and return a read-only report.

    Args:
        env: Environment mapping (injected for purity / testability).
        platform_name: ``platform.system()`` vocabulary string.
        candidates: Optional explicit label→path map (tests pass a tmp tree);
            defaults to :func:`legacy_candidate_paths`.

    Returns:
        A :class:`ScanReport` with the canonical target home and one
        :class:`LegacyCandidate` per probed location. Nothing is ever modified.
    """
    target = home.resolve_home(env, platform_name)
    cand_map = dict(candidates) if candidates is not None else legacy_candidate_paths(
        env, platform_name
    )
    results = [_summarize(Path(p)) for _label, p in sorted(cand_map.items())]
    # Preserve the caller-provided labels rather than the path stem.
    labelled = [
        LegacyCandidate(label, c.path, c.exists, c.is_dir, c.entry_count, c.total_bytes)
        for (label, _p), c in zip(sorted(cand_map.items()), results)
    ]
    return ScanReport(canonical_target=target, candidates=labelled)
