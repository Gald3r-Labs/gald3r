"""Platform capability reporting — `gald3r platform status`. Absorbs the read path of
custom_scripts/check_platform_status.ps1.

The script's original inputs (`.gald3r/PLATFORM_STATUS.md`, per-platform `PLATFORM_SPEC.md`)
no longer exist — the live, canonical source is the already-generated
`.gald3r/PLATFORM_CAPABILITY_MATRIX.md` (34-platform C.R.A.S.H. grid, produced by
`strategy/gen_platform_docs.py` from `strategy/PLATFORM_DATA.json`), optionally enriched with
`COMBINED_READINESS.md` verdicts. So this is a pure read+report over those files. The
`-GenerateMatrix` regeneration path is intentionally NOT absorbed: that belongs to whatever
owns `PLATFORM_DATA.json`, not the per-project engine.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.config import Config


def _parse_md_table(text: str) -> List[Dict[str, str]]:
    """Parse the first markdown table in `text` into a list of {column: cell} dicts."""
    rows = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
    if len(rows) < 2:
        return []

    def cells(line: str) -> List[str]:
        return [c.strip() for c in line.strip().strip("|").split("|")]

    header = cells(rows[0])
    out: List[Dict[str, str]] = []
    for line in rows[2:]:  # skip header + separator
        if re.match(r"^\s*\|[\s:|-]+\|?\s*$", line):
            continue
        vals = cells(line)
        if len(vals) != len(header):
            continue
        out.append(dict(zip(header, vals)))
    return out


class PlatformSystem:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    @property
    def _matrix_path(self) -> Path:
        return self.cfg.gald3r_dir / "PLATFORM_CAPABILITY_MATRIX.md"

    @property
    def _readiness_path(self) -> Path:
        return self.cfg.gald3r_dir / "COMBINED_READINESS.md"

    def status(self, platform: str = "all") -> Dict[str, Any]:
        if not self._matrix_path.exists():
            raise FileNotFoundError(
                f"no PLATFORM_CAPABILITY_MATRIX.md at {self._matrix_path} — "
                "platform data has not been generated for this install")
        rows = _parse_md_table(self._matrix_path.read_text(encoding="utf-8"))
        # normalize the platform-name key (first column)
        name_key = next(iter(rows[0]), "Platform") if rows else "Platform"
        for r in rows:
            r["platform"] = r.get(name_key, r.get("Platform", "")).strip()

        verdicts = self._readiness_verdicts()
        for r in rows:
            if r["platform"] in verdicts:
                r["readiness"] = verdicts[r["platform"]]

        if platform and platform.lower() != "all":
            sel = platform.lower()
            rows = [r for r in rows if r["platform"].lower() == sel]
            if not rows:
                raise KeyError(f"platform '{platform}' not found in the matrix")

        # summary by engine tier (the matrix's authoritative integration level)
        tier_key = next((k for k in (rows[0] if rows else {}) if "tier" in k.lower()), None)
        summary: Dict[str, int] = {"total": len(rows)}
        if tier_key:
            for r in rows:
                t = r.get(tier_key, "?") or "?"
                summary[t] = summary.get(t, 0) + 1
        return {"rows": rows, "summary": summary}

    def _readiness_verdicts(self) -> Dict[str, str]:
        """Best-effort {platform: verdict} from COMBINED_READINESS.md (table or headings)."""
        if not self._readiness_path.exists():
            return {}
        text = self._readiness_path.read_text(encoding="utf-8")
        verdicts: Dict[str, str] = {}
        for r in _parse_md_table(text):
            vals = list(r.values())
            if len(vals) >= 2:
                verdicts[vals[0].strip()] = vals[1].strip()
        return verdicts
