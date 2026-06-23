#!/usr/bin/env python3
"""spec_refresh.py — GAP A consumer (T514): crawled docs -> PLATFORM_SPEC.md proposals.

Closes the first broken link of the T513 freshness loop: the crawl pipeline
refreshes raw platform docs into the backend ``platform_ext.memory_captures``
corpus, but nothing ever carries that knowledge back into the 23 curated
``PLATFORM_SPEC.md`` files, so the specs (and therefore the matrix + STATUS)
only change on manual edits.

This is the missing **host-side** consumer. Given the latest crawled-doc
snapshot for one platform, it:

  1. Loads that snapshot (a JSON export of the crawled chunks for the platform —
     the host-side artifact of ``scripts/platform_crawl.py`` / a
     ``platform_docs_search`` dump — passed via ``--crawl-snapshot``). C-001
     parity: the DB read happens host-side via the export, never inside a
     per-request backend tenant session.
  2. Derives, **deterministically**, the doc-evidenced capability signal for each
     of the 5 gald3r primitives (Hooks/Rules/Skills/Commands/MCP) from the crawled
     text, and diffs it against the spec's current ``## Capability Summary`` cells.
  3. Emits a **reviewable proposal** — a ``PLATFORM_SPEC.md.proposed`` draft with a
     ``[needs-review]`` block + a "what changed and why" summary — and stamps the
     proposed frontmatter ``last_doc_scan`` from the crawl ledger completion date
     (NOT "now" blindly). The default is dry-run; nothing is written to the live
     spec without ``--apply``.

MODEL-FOR-JUDGMENT-ONLY (g-rl-38): the diff/parse/registry-read plumbing here is
fully deterministic code. The doc-signal heuristic only ever *raises a question*
in a ``[needs-review]`` block ("docs evidence Hooks but the spec says ❌ — verify");
it never flips a curated ✅/⚠️/❌ cell by itself. A human (or the review LLM) makes
the final cell call by editing the proposed draft, then accepts it.

Idempotent: a second run on the same inputs (after acceptance) yields an empty
proposal (no signal delta, same last_doc_scan) and exit code 0.

OUT OF SCOPE (this is GAP A only): writing PLATFORM_STATUS.md (that is T515 /
generate_status.py); adding crawl targets / changing the crawl runner.

Usage::

    # dry-run (default): print the proposal + write *.proposed next to the spec
    python spec_refresh.py --platform cursor --crawl-snapshot cursor_docs.json

    # also read the real completion date from a crawl-ledger snapshot
    python spec_refresh.py --platform cursor \
        --crawl-snapshot cursor_docs.json --crawl-ledger registry.json

    # accept: stamp the spec's last_doc_scan from the ledger (still never flips
    # a capability cell — that is a human edit to the *.proposed draft)
    python spec_refresh.py --platform cursor --crawl-snapshot cursor_docs.json --apply
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Make this script's own folder importable (covers odd invocation cwds), then
# import the shared spec/ledger helpers and the registry-driven spec resolver.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import platform_spec_io as psio  # noqa: E402
from platform_spec_io import OK, WARN, NO, UNK  # noqa: E402

try:
    from check_platform_status import resolve_spec_path, _find_root
except ImportError:  # pragma: no cover - defensive
    resolve_spec_path = None  # type: ignore
    _find_root = None  # type: ignore


# --------------------------------------------------------------------------- #
# Doc-signal heuristic — deterministic capability evidence from crawled text   #
# --------------------------------------------------------------------------- #
# For each gald3r primitive: phrases that POSITIVELY evidence native support, and
# phrases that NEGATIVELY evidence absence. These never auto-flip a curated cell;
# they only raise a [needs-review] question when the doc evidence and the current
# spec cell disagree. Conservative on purpose (model-for-judgment-only).
_POSITIVE_SIGNALS: Dict[str, List[str]] = {
    "Hooks": [r"\bhooks?\b", r"lifecycle hook", r"preToolUse", r"PostToolUse",
              r"sessionStart", r"hooks\.json", r"hook events?"],
    "Rules": [r"\brules?\b", r"always[- ]?apply", r"custom instructions",
              r"AGENTS\.md", r"\.mdc\b", r"steering"],
    "Skills": [r"\bskills?\b", r"SKILL\.md", r"agent skills", r"agentskills"],
    "Commands": [r"slash command", r"custom command", r"\bworkflows?\b",
                 r"/[a-z][a-z-]+ command"],
    "MCP": [r"\bMCP\b", r"model context protocol", r"mcpServers",
            r"mcp\.json", r"mcp_config"],
}
_NEGATIVE_SIGNALS: Dict[str, List[str]] = {
    "Hooks": [r"no (?:native )?hooks?", r"hooks? (?:are )?not supported",
              r"no lifecycle hook"],
    "Rules": [r"no (?:native )?rules?", r"rules? not supported"],
    "Skills": [r"no (?:native )?skills?", r"skills? not supported",
               r"no SKILL\.md"],
    "Commands": [r"no (?:custom )?commands?", r"no slash command"],
    "MCP": [r"no (?:native )?MCP", r"MCP not supported"],
}


def snapshot_text(snapshot: dict) -> str:
    """Concatenate the crawled chunk text from a snapshot export into one corpus.

    Accepts the shapes the host crawl export / ``platform_docs_search`` produce:
      * ``{"results": [ {"content": "...", "title": "...", "url": "..."}, ... ]}``
      * ``{"chunks":  [ {"content": "..."}, ... ]}``
      * a bare ``[ {"content": "..."}, ... ]`` list.
    Robust to a missing key — empty corpus yields no signals (and thus no
    proposal), which is the correct degrade.
    """
    if isinstance(snapshot, list):
        rows = snapshot
    else:
        rows = snapshot.get("results") or snapshot.get("chunks") or []
    parts: List[str] = []
    for r in rows:
        if isinstance(r, str):
            parts.append(r)
            continue
        for key in ("title", "content", "text", "markdown"):
            v = r.get(key)
            if v:
                parts.append(str(v))
    return "\n".join(parts)


def doc_signal(corpus: str) -> Dict[str, str]:
    """Deterministic per-primitive doc evidence: ✅ (positive evidence, no
    negation), ❌ (explicit negation), or ❓ (no evidence either way).

    Negation wins over a bare positive mention (a page that says "no native
    hooks" also contains the word "hooks"). This is EVIDENCE, not a verdict — it
    feeds [needs-review] questions, never a silent cell flip.
    """
    out: Dict[str, str] = {}
    low = corpus.lower()
    for cap in psio.CAPABILITY_COLUMNS:
        neg = any(re.search(p, low) for p in _NEGATIVE_SIGNALS.get(cap, []))
        pos = any(re.search(p, low, re.IGNORECASE) for p in _POSITIVE_SIGNALS.get(cap, []))
        if neg:
            out[cap] = NO
        elif pos:
            out[cap] = OK
        else:
            out[cap] = UNK
    return out


def _evidence_disagrees(spec_cell: str, evidence: str) -> bool:
    """Does the doc evidence materially contradict the curated spec cell?

    ❓ evidence never contradicts (no evidence). A curated ⚠️ (partial) is NOT
    contradicted by ✅ evidence (partial is a human nuance the docs can't refute),
    but IS contradicted by ❌ evidence. ✅ vs ❌ and ❌ vs ✅ always disagree.
    """
    if evidence == UNK:
        return False
    if spec_cell == evidence:
        return False
    if spec_cell == WARN and evidence == OK:
        return False  # partial is a finer human judgement; docs showing support is consistent
    return True


# --------------------------------------------------------------------------- #
# Proposal construction                                                        #
# --------------------------------------------------------------------------- #
def _replace_frontmatter_field(content: str, field: str, value: str) -> str:
    """Return content with frontmatter ``field:`` set to ``value`` (added if absent)."""
    fm = re.match(r"(?s)^(\s*---\s*\r?\n)(.*?)(\r?\n---\s*\r?\n)(.*)$", content)
    if not fm:
        return content
    head, body, fence, rest = fm.group(1), fm.group(2), fm.group(3), fm.group(4)
    line_rx = re.compile(rf"(?m)^(\s*{re.escape(field)}\s*:\s*).*?(\s*#.*)?$")
    if line_rx.search(body):
        body = line_rx.sub(rf"\g<1>{value}", body, count=1)
    else:
        body = body.rstrip("\n") + f"\n{field}: {value}"
    return head + body + fence + rest


def build_proposal(
    platform: str,
    spec_content: str,
    corpus: str,
    last_doc_scan: Optional[str],
) -> dict:
    """Build the (deterministic) proposal: the proposed spec text, a unified diff,
    a change summary, and the per-capability evidence/needs-review rows.

    The ONLY mechanical edit applied to the proposed text is stamping
    ``last_doc_scan`` from the crawl ledger. Capability-cell decisions are left to
    the human via [needs-review] questions — the proposed draft preserves the
    curated cells verbatim so accepting it never silently rewrites a verdict.
    """
    current = psio.capability_cells(spec_content)
    evidence = doc_signal(corpus)
    cur_scan = psio.get_frontmatter_field(spec_content, "last_doc_scan")

    needs_review: List[Dict[str, str]] = []
    for cap in psio.CAPABILITY_COLUMNS:
        if _evidence_disagrees(current[cap], evidence[cap]):
            needs_review.append({
                "capability": cap,
                "spec_cell": current[cap],
                "doc_evidence": evidence[cap],
            })

    # Proposed spec text = curated content + (only) a refreshed last_doc_scan.
    proposed = spec_content
    scan_changed = False
    if last_doc_scan and last_doc_scan != cur_scan:
        proposed = _replace_frontmatter_field(proposed, "last_doc_scan", last_doc_scan)
        scan_changed = True

    diff = "".join(
        difflib.unified_diff(
            spec_content.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=f"{platform}/PLATFORM_SPEC.md (current)",
            tofile=f"{platform}/PLATFORM_SPEC.md (proposed)",
        )
    )

    empty = (not scan_changed) and (not needs_review)
    return {
        "platform": platform,
        "current_cells": current,
        "doc_evidence": evidence,
        "needs_review": needs_review,
        "current_last_doc_scan": cur_scan,
        "proposed_last_doc_scan": last_doc_scan,
        "last_doc_scan_changed": scan_changed,
        "proposed_text": proposed,
        "diff": diff,
        "empty": empty,
    }


def render_summary(proposal: dict) -> str:
    """Human-readable 'what changed and why' summary for the proposal."""
    p = proposal
    lines: List[str] = []
    lines.append(f"# Spec-refresh proposal — {p['platform']}")
    lines.append("")
    if p["empty"]:
        lines.append("No change proposed: the crawled docs raise no capability "
                     "questions and last_doc_scan is already current. "
                     "(idempotent no-op)")
        return "\n".join(lines) + "\n"
    if p["last_doc_scan_changed"]:
        lines.append(f"- Stamp `last_doc_scan`: "
                     f"`{p['current_last_doc_scan']}` -> `{p['proposed_last_doc_scan']}` "
                     "(from crawl-ledger completion date).")
    if p["needs_review"]:
        lines.append("- [needs-review] Doc evidence disagrees with curated "
                     "capability cells — a human must judge each (the proposed "
                     "draft does NOT flip these automatically):")
        for r in p["needs_review"]:
            lines.append(
                f"    - **{r['capability']}**: spec says `{r['spec_cell']}`, "
                f"crawled docs evidence `{r['doc_evidence']}` — verify against "
                "the platform's official docs and edit the *.proposed draft if "
                "the curated cell is wrong."
            )
    else:
        lines.append("- No capability-cell disagreements between the crawled "
                     "docs and the curated spec.")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #
def run(
    platform: str,
    snapshot_path: Path,
    ledger_path: Optional[Path],
    repo_root: Path,
    apply: bool,
    out_dir: Optional[Path] = None,
) -> dict:
    """Generate (and optionally apply) a spec-refresh proposal for one platform.

    Returns the proposal dict (also written as ``PLATFORM_SPEC.md.proposed`` +
    ``PLATFORM_SPEC.md.proposal.md`` next to the spec, or in ``out_dir``).
    """
    if resolve_spec_path is None:
        raise RuntimeError("check_platform_status.resolve_spec_path unavailable")
    specs_root = repo_root / ".gald3r_sys" / "platforms"
    spec_path = resolve_spec_path(repo_root, specs_root, platform)
    if spec_path is None:
        raise FileNotFoundError(
            f"No PLATFORM_SPEC.md resolved for '{platform}' "
            f"(legacy {specs_root} or registry skill trees)."
        )
    spec_content = spec_path.read_text(encoding="utf-8")

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    corpus = snapshot_text(snapshot)

    ledger = psio.load_crawl_ledger(ledger_path)
    # last_doc_scan source: crawl ledger first (real completion date), else keep
    # the spec's current value (do NOT stamp "now" blindly — AC requirement).
    last_doc_scan = psio.ledger_last_doc_scan(ledger, platform)

    proposal = build_proposal(platform, spec_content, corpus, last_doc_scan)
    proposal["spec_path"] = str(spec_path)

    target_dir = out_dir or spec_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    proposed_file = target_dir / "PLATFORM_SPEC.md.proposed"
    summary_file = target_dir / "PLATFORM_SPEC.md.proposal.md"
    proposed_file.write_text(proposal["proposed_text"], encoding="utf-8")
    summary_file.write_text(render_summary(proposal), encoding="utf-8")
    proposal["proposed_file"] = str(proposed_file)
    proposal["summary_file"] = str(summary_file)

    if apply and not proposal["empty"]:
        # The ONLY thing --apply lands is the mechanical last_doc_scan stamp.
        # Capability cells are NEVER auto-applied — they stay [needs-review].
        if proposal["last_doc_scan_changed"]:
            spec_path.write_text(proposal["proposed_text"], encoding="utf-8")
            proposal["applied"] = True
        else:
            proposal["applied"] = False
    else:
        proposal["applied"] = False
    return proposal


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="GAP A (T514): turn crawled platform docs into a reviewable "
                    "PLATFORM_SPEC.md change proposal (never a blind overwrite).",
        allow_abbrev=False)
    parser.add_argument("-Platform", "--platform", dest="platform", required=True,
                        help="Platform name (e.g. cursor, claude, windsurf).")
    parser.add_argument("--crawl-snapshot", dest="snapshot", required=True,
                        help="Path to the crawled-doc snapshot JSON for the platform "
                             "(host-side export of the platform_docs corpus).")
    parser.add_argument("--crawl-ledger", dest="ledger", default=None,
                        help="Optional crawl-ledger JSON snapshot "
                             "(platform_crawl_status registry) for the real "
                             "last_doc_scan completion date.")
    parser.add_argument("--apply", dest="apply", action="store_true",
                        help="Land the mechanical last_doc_scan stamp into the live "
                             "spec. Capability cells are NEVER auto-applied. "
                             "Default is dry-run.")
    parser.add_argument("--out-dir", dest="out_dir", default=None,
                        help="Write the *.proposed draft + summary here instead of "
                             "next to the spec (for review staging).")
    args = parser.parse_args(argv)

    if _find_root is None:
        print("ERROR: check_platform_status unavailable — cannot resolve repo root.")
        return 1
    repo_root = _find_root()
    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        print(f"ERROR: crawl snapshot not found: {snapshot_path}")
        return 1
    ledger_path = Path(args.ledger) if args.ledger else None

    try:
        proposal = run(
            args.platform, snapshot_path, ledger_path, repo_root,
            apply=args.apply,
            out_dir=Path(args.out_dir) if args.out_dir else None,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"\n=== spec_refresh (T514, GAP A) — {proposal['platform']} ===")
    print(f"  spec     : {proposal['spec_path']}")
    print(f"  proposed : {proposal['proposed_file']}")
    print(f"  summary  : {proposal['summary_file']}")
    print()
    print(render_summary(proposal))
    if proposal["empty"]:
        print("  (empty proposal — nothing to review; re-run is a no-op)")
    elif proposal["applied"]:
        print("  APPLIED: last_doc_scan stamped into the live spec.")
    else:
        print("  DRY-RUN: review the *.proposed draft + summary, then accept by "
              "editing the spec (capability cells) and/or re-running with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
