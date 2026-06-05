"""Canonical → platform-mirror parity — `gald3r sync --check|--apply`. Absorbs the live
transform contract of custom_scripts/platform_parity_sync.ps1 (its IDE adapter loop was dead
code; the working rules lived in the regen_cursor.py prototype, generalized here).

Scope: projects the canonical `.claude` component trees into the **full-tree** mirror
platforms present in the project (cursor-class: same layout, rules extension may differ). The
full 34-platform, atypical-layout build (copilot=commands-only, cline=.clinerules/workflows,
etc.) remains the maintainer's spec-driven `strategy/build_platforms.py` job, driven by
PLATFORM_DATA.json — that is out of scope for this in-project engine command.

Pure Mode-A: reads/writes files only, **no git** (the caller commits). Diffs are CRLF-normalized
so line endings never read as drift.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from gald3r.config import Config

SOURCE = ".claude"                              # canonical projection
SHARED_TREES = ("agents", "commands", "skills")  # copied verbatim
SOURCE_HOOK_DROP = ("claude-chat-logger",)       # source-platform-specific hooks not carried

# full-tree mirror targets: {platform: rules extension (None = platform takes no rules)}
ADAPTERS: Dict[str, Dict[str, Any]] = {
    "cursor":   {"dir": ".cursor",   "rules_ext": ".mdc"},
    "gemini":   {"dir": ".gemini",   "rules_ext": ".md"},
    "opencode": {"dir": ".opencode", "rules_ext": ".md"},
    "codex":    {"dir": ".codex",    "rules_ext": None},
}


_BOM = b"\xef\xbb\xbf"


def _norm(b: bytes) -> bytes:
    """CRLF→LF so line endings don't masquerade as content drift."""
    return b.replace(b"\r\n", b"\n")


def _ps1_safe(rel: str, data: bytes) -> bytes:
    """A generated .ps1 with non-ASCII bytes needs a UTF-8 BOM, or Windows PowerShell 5.1
    (powershell.exe) reads it as cp1252, misdecodes, and fails to parse. Idempotent."""
    if rel.endswith(".ps1") and not data.startswith(_BOM) and any(byte > 0x7F for byte in data):
        return _BOM + data
    return data


class SyncSystem:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    @property
    def _canonical(self) -> Path:
        return self.cfg.root / SOURCE

    def _targets(self, platform: Optional[str]) -> List[str]:
        if platform:
            if platform not in ADAPTERS:
                raise KeyError(f"'{platform}' is not a full-tree mirror target "
                               f"({', '.join(ADAPTERS)}); atypical platforms use the build pipeline")
            return [platform]
        # default: every adapter whose dir already exists in the project
        return [p for p, a in ADAPTERS.items() if (self.cfg.root / a["dir"]).is_dir()]

    def _projection(self, adapter: Dict[str, Any]) -> Dict[str, Path]:
        """{relative_target_path: canonical_source_file} that canonical projects into target."""
        src = self._canonical
        out: Dict[str, Path] = {}
        for tree in SHARED_TREES:
            base = src / tree
            for f in (base.rglob("*") if base.is_dir() else []):
                if f.is_file():
                    out[str(f.relative_to(src)).replace("\\", "/")] = f
        hbase = src / "hooks"
        for f in (hbase.rglob("*") if hbase.is_dir() else []):
            if f.is_file() and not any(s in f.name for s in SOURCE_HOOK_DROP):
                out[str(f.relative_to(src)).replace("\\", "/")] = f
        rext, rbase = adapter["rules_ext"], src / "rules"
        if rext and rbase.is_dir():
            for f in rbase.glob("*.md"):
                out[f"rules/{f.stem}{rext}"] = f
        return out

    # ---- public API ---------------------------------------------------------
    def check(self, platform: Optional[str] = None) -> Dict[str, Any]:
        if not self._canonical.is_dir():
            raise FileNotFoundError(f"canonical source {self._canonical} not found")
        results = []
        for plat in self._targets(platform):
            adapter = ADAPTERS[plat]
            tdir = self.cfg.root / adapter["dir"]
            proj = self._projection(adapter)
            missing, drift = [], []
            for rel, srcf in proj.items():
                tf = tdir / rel
                if not tf.exists():
                    missing.append(rel)
                elif _norm(tf.read_bytes()) != _norm(_ps1_safe(rel, srcf.read_bytes())):
                    drift.append(rel)
            # extras: files in the target's shared/rules trees not in the projection
            extra = []
            for sub in (*SHARED_TREES, "hooks", "rules"):
                base = tdir / sub
                for f in (base.rglob("*") if base.is_dir() else []):
                    rel = str(f.relative_to(tdir)).replace("\\", "/")
                    if f.is_file() and rel not in proj:
                        extra.append(rel)
            results.append({
                "platform": plat, "dir": adapter["dir"],
                "projected": len(proj), "missing": missing, "drift": drift, "extra": extra,
                "in_parity": not (missing or drift or extra),
            })
        total_gaps = sum(len(r["missing"]) + len(r["drift"]) + len(r["extra"]) for r in results)
        return {"mode": "check", "platforms": results, "total_gaps": total_gaps,
                "in_parity": total_gaps == 0}

    def apply(self, platform: Optional[str] = None) -> Dict[str, Any]:
        if not self._canonical.is_dir():
            raise FileNotFoundError(f"canonical source {self._canonical} not found")
        results = []
        for plat in self._targets(platform):
            adapter = ADAPTERS[plat]
            tdir = self.cfg.root / adapter["dir"]
            proj = self._projection(adapter)
            written, removed = 0, 0
            for rel, srcf in proj.items():
                tf = tdir / rel
                data = _ps1_safe(rel, srcf.read_bytes())
                if not tf.exists() or _norm(tf.read_bytes()) != _norm(data):
                    tf.parent.mkdir(parents=True, exist_ok=True)
                    tf.write_bytes(data)
                    written += 1
            # prune target-only files in the managed trees (heal drift authoritatively)
            for sub in (*SHARED_TREES, "hooks", "rules"):
                base = tdir / sub
                for f in (list(base.rglob("*")) if base.is_dir() else []):
                    rel = str(f.relative_to(tdir)).replace("\\", "/")
                    if f.is_file() and rel not in proj:
                        f.unlink()
                        removed += 1
            results.append({"platform": plat, "dir": adapter["dir"],
                            "written": written, "removed": removed, "projected": len(proj)})
        return {"mode": "apply", "platforms": results,
                "total_written": sum(r["written"] for r in results),
                "total_removed": sum(r["removed"] for r in results)}
