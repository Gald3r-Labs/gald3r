"""Project location, identity, and tier resolution.

The tier flag (`slim` < `full` < `controller`; `maintainer` = dev-only) is read
from `.gald3r/.identity`. Modules consult it to decide whether they activate
(e.g. workspace.* is controller-tier). This is the single place that knows where
`.gald3r/` lives and what tier the install is.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

TIERS = ["slim", "full", "controller", "maintainer"]


def find_root(start: Optional[Path] = None) -> Path:
    """Walk up from `start` (or cwd) until a directory containing `.gald3r/` is found."""
    cur = Path(start or Path.cwd()).resolve()
    for d in [cur, *cur.parents]:
        if (d / ".gald3r").is_dir():
            return d
    raise FileNotFoundError(
        f"No .gald3r/ directory found at or above {cur}. "
        "Run from inside a gald3r project (or pass root=)."
    )


def _parse_identity(path: Path) -> Dict[str, str]:
    """Parse `.gald3r/.identity` (key=value lines; '#' lines are comments)."""
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


class Config:
    """Resolved view of a gald3r project: paths, identity, tier."""

    def __init__(self, root: Optional[Path] = None):
        self.root = find_root(root)
        self.gald3r_dir = self.root / ".gald3r"
        self.identity = _parse_identity(self.gald3r_dir / ".identity")

    # ---- tier ----
    @property
    def tier(self) -> str:
        t = (self.identity.get("tier") or "slim").lower()
        return t if t in TIERS else "slim"

    def tier_at_least(self, level: str) -> bool:
        return TIERS.index(self.tier) >= TIERS.index(level)

    # ---- identity ----
    @property
    def project_name(self) -> str:
        return self.identity.get("project_name") or self.root.name

    @property
    def gald3r_rel_version(self) -> str:
        return self.identity.get("gald3r_version") or self.identity.get("gald3r_rel_version") or "2.0.0"

    # ---- paths ----
    @property
    def tasks_dir(self) -> Path:
        return self.gald3r_dir / "tasks"

    @property
    def tasks_md(self) -> Path:
        return self.gald3r_dir / "TASKS.md"
