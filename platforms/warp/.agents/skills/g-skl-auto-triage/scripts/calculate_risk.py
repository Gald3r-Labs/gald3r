#!/usr/bin/env python3
"""Python port of calculate_risk.ps1 (T1585).

Auto-Triage L0 risk calculator for gald3r spec/policy defects.
Computes risk_score = (base_kind_score + file_sensitivity_bonus) * scope_multiplier.
Score <= threshold (default 2.0) = eligible for auto-fix; score > threshold =
needs_attention (human required). Infinity-class files = always blocked.

CLI prints the assessment as JSON (the PS1 emits a PSCustomObject); importable
via ``calculate_risk()`` for invoke_triage.py.
"""
# @subsystems: BUG_AND_QUALITY
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence


def _bootstrap_engine_utils() -> bool:
    """Make gald3r.utils importable: installed package, else walk up to .gald3r_sys/engine/src."""
    try:
        import gald3r.utils  # noqa: F401
        return True
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        cand = parent / ".gald3r_sys" / "engine" / "src"
        if (cand / "gald3r" / "utils" / "__init__.py").is_file():
            sys.path.insert(0, str(cand))
            try:
                import gald3r.utils  # noqa: F401
                return True
            except ImportError:
                return False
    return False


_HAS_UTILS = _bootstrap_engine_utils()

VALID_KINDS = ("spec_defect", "policy_incongruity", "design_gap", "code")
VALID_FIX_TYPES = (
    "schema_comment",
    "manifest_annotation",
    "command_annotation",
    "rule_annotation",
    "constraint_expire",
)

# --- Base kind scores ---
BASE_SCORES: Dict[str, float] = {
    "spec_defect": 1.0,
    "policy_incongruity": 2.0,
    "design_gap": 99.0,  # Always blocked -- design decisions require humans
    "code": 99.0,        # Always blocked -- code bugs never auto-triaged
}

# --- Hard-block path patterns (infinity-class) ---
# Any file matching these patterns is an absolute block regardless of score.
# NOTE: linking/workspace_manifest.yaml is intentionally NOT blocked (it is
# schema/config, not WPAC coordination state). Patterns accept both separators
# (the PS1 used backslash-only for TASKS.md/BUGS.md/CONSTRAINTS.md).
BLOCK_PATTERNS: List[re.Pattern] = [
    re.compile(r"[\\/]TASKS\.md$"),
    re.compile(r"[\\/]tasks[\\/]"),
    re.compile(r"[\\/]BUGS\.md$"),
    re.compile(r"[\\/]bugs[\\/]"),
    re.compile(r"[\\/]CONSTRAINTS\.md$"),
    re.compile(r"[\\/]features[\\/]"),
    re.compile(r"[\\/]releases[\\/]"),
    re.compile(r"[\\/]prds[\\/]"),
    re.compile(r"[\\/]experiments[\\/]"),
    # WPAC coordination state (not the manifest schema itself)
    re.compile(r"[\\/]linking[\\/]INBOX\.md$"),
    re.compile(r"[\\/]linking[\\/]link_topology\.md$"),
    re.compile(r"[\\/]linking[\\/]sent_orders[\\/]"),
    re.compile(r"[\\/]linking[\\/]pending_orders[\\/]"),
    re.compile(r"[\\/]linking[\\/]peers[\\/]"),
]

_MEMBER_REPO_RX = re.compile(r"[\\/]gald3r_(throne|agent|valhalla|web|discord|world_tree)[\\/]")
_DOC_EXT_RX = re.compile(r"\.md$|\.yaml$|\.yml$|\.json$", re.IGNORECASE)
_YAML_RX = re.compile(r"\.yaml$|\.yml$", re.IGNORECASE)


def get_file_sensitivity_bonus(file_path: str, fix_type: str) -> float:
    """Return the sensitivity bonus for one file (99.0 = infinity-class block)."""
    name = Path(file_path).name
    path_lower = file_path.lower()

    # Check hard-block patterns first
    for pat in BLOCK_PATTERNS:
        if pat.search(file_path):
            return 99.0

    # Source code files in member repos (.ts, .tsx, .py, .js, .cs, etc.)
    if _MEMBER_REPO_RX.search(file_path) and not _DOC_EXT_RX.search(file_path):
        return 99.0

    # Schema YAML comment (lowest risk)
    if fix_type == "schema_comment" and _YAML_RX.search(name):
        return 0.0

    # Manifest annotation or schema comment on workspace_manifest.yaml
    if name == "workspace_manifest.yaml":
        return 0.5

    # Rule files
    if re.search(r"[\\/]rules[\\/]", path_lower) and re.search(r"\.mdc$|\.md$", name):
        return 1.0

    # Command files
    if re.search(r"[\\/]commands[\\/]", path_lower) and name.endswith(".md"):
        return 1.0

    # AGENT_CONFIG
    if name == "AGENT_CONFIG.md":
        return 1.0

    # SKILL.md files
    if name == "SKILL.md":
        return 0.5

    # Generic YAML/schema files
    if _YAML_RX.search(name):
        return 0.5

    # Fallback -- unknown file type, treat as moderate
    return 1.5


def get_scope_multiplier(file_count: int) -> float:
    """Return the scope multiplier (99.0 = infinity-class for > 3 files)."""
    if file_count == 1:
        return 1.0
    if file_count <= 3:
        return 1.5
    return 99.0


def _read_config_threshold(project_root: str) -> Optional[float]:
    """Read auto_triage_risk_threshold from .gald3r/config/AGENT_CONFIG.md if present."""
    cfg = Path(project_root) / ".gald3r" / "config" / "AGENT_CONFIG.md"
    if not cfg.is_file():
        return None
    text = cfg.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"auto_triage_risk_threshold:\s*([\d.]+)", text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def calculate_risk(
    kind: str,
    files: Sequence[str],
    fix_type: str,
    threshold: float = 2.0,
    project_root: str = "",
) -> Dict[str, object]:
    """Compute the auto-triage risk assessment (mirrors calculate_risk.ps1 output)."""
    if kind not in VALID_KINDS:
        raise ValueError(f"invalid kind '{kind}' (expected one of {VALID_KINDS})")
    if fix_type not in VALID_FIX_TYPES:
        raise ValueError(f"invalid fix_type '{fix_type}' (expected one of {VALID_FIX_TYPES})")

    # Try to read threshold from AGENT_CONFIG.md (only when -Threshold left at default 2.0)
    if project_root:
        cfg_threshold = _read_config_threshold(project_root)
        if cfg_threshold is not None and threshold == 2.0:
            threshold = cfg_threshold

    base_score = BASE_SCORES[kind]
    blocked_paths: List[str] = []
    max_file_sensitivity = 0.0

    for f in files:
        bonus = get_file_sensitivity_bonus(f, fix_type)
        if bonus >= 99.0:
            blocked_paths.append(f)
        if bonus > max_file_sensitivity:
            max_file_sensitivity = bonus

    scope_multiplier = get_scope_multiplier(len(files))

    # If any hard-block, score is infinity
    if blocked_paths or max_file_sensitivity >= 99.0 or scope_multiplier >= 99.0:
        raw_score = 99.0
    else:
        raw_score = (base_score + max_file_sensitivity) * scope_multiplier

    risk_score = round(raw_score, 2)
    eligible = (risk_score <= threshold) and not blocked_paths

    if blocked_paths:
        reason = "BLOCKED: infinity-class files touched: " + ", ".join(blocked_paths)
    elif risk_score >= 99.0:
        reason = f"BLOCKED: kind='{kind}' or scope exceeds Phase 1 limits"
    elif eligible:
        reason = (
            f"ELIGIBLE: {kind} + {fix_type} on {len(files)} file(s) "
            f"-- score {risk_score} <= threshold {threshold}"
        )
    else:
        reason = f"NOT ELIGIBLE: score {risk_score} exceeds threshold {threshold} -- needs_attention"

    return {
        "risk_score": risk_score,
        "eligible": eligible,
        "threshold": threshold,
        "reason": reason,
        "blocked_paths": blocked_paths,
        "kind": kind,
        "fix_type": fix_type,
        "file_count": len(files),
    }


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Auto-Triage L0 risk calculator for gald3r spec/policy defects."
    )
    p.add_argument("-Kind", "--kind", dest="kind", required=True, choices=VALID_KINDS)
    p.add_argument("-Files", "--files", dest="files", required=True, nargs="+")
    p.add_argument("-FixType", "--fix-type", dest="fix_type", required=True,
                   choices=VALID_FIX_TYPES)
    p.add_argument("-Threshold", "--threshold", dest="threshold", type=float, default=2.0)
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", default="")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: print the assessment as JSON, exit 0."""
    args = build_parser().parse_args(argv)
    assessment = calculate_risk(
        kind=args.kind,
        files=args.files,
        fix_type=args.fix_type,
        threshold=args.threshold,
        project_root=args.project_root,
    )
    print(json.dumps(assessment, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
