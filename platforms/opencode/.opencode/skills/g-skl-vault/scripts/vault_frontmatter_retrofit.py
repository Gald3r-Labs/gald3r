#!/usr/bin/env python3
"""Retrofit Obsidian/VAULT_OBSIDIAN_STANDARD frontmatter onto vault notes (T1334).

Discovery (default): walk the vault and report every long-lived note missing the
required YAML frontmatter or required keys. Retrofit (--apply): prepend/complete
frontmatter non-destructively.

Required keys (all long-lived notes): date, type, ingestion_type, source, title, topics
Research content (research/**) additionally: refresh_policy, source_volatility
knowledge/** notes also get refresh_policy/source_volatility (long-lived reference).

Usage:
  python vault_frontmatter_retrofit.py --vault G:/gald3r_ecosystem/gald3r_vault
  python vault_frontmatter_retrofit.py --vault <path> --apply
"""
from __future__ import annotations
import argparse, datetime as dt, pathlib, re, sys

REQUIRED = ["date", "type", "ingestion_type", "source", "title", "topics"]
RESEARCH_EXTRA = ["refresh_policy", "source_volatility"]

# (glob, type, needs_research_extra)
# Default scope is the T1334 target set: per-project memory/sessions/decisions and
# knowledge cards. research/** is crawler-managed (its frontmatter + _index.yaml are
# owned by g-skl-recon-docs); only touch it when explicitly asked via --include-research.
TARGETS = [
    ("projects/*/memory.md",      "session",        False),
    ("projects/*/sessions/*.md",  "session",        False),
    ("projects/*/decisions/*.md", "decision",       False),
    ("knowledge/*.md",            "knowledge_card", True),
]
RESEARCH_TARGET = ("research/**/*.md", "research", True)


def parse_frontmatter(text: str):
    """Return (dict_or_None, body). dict is the raw key->rawvalue of a leading --- block."""
    if not text.startswith("---"):
        return None, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return None, text
    fm, body = {}, m.group(2)
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm, body


def derive(path: pathlib.Path, vault: pathlib.Path, ntype: str, body: str):
    rel = path.relative_to(vault)
    # project = segment after 'projects/' if present, else 'vault'
    parts = rel.parts
    project = parts[1] if parts and parts[0] == "projects" and len(parts) > 1 else "vault"
    date = dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
    hm = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = hm.group(1).strip() if hm else path.stem.replace("_", " ")
    topic_kind = {"knowledge_card": "knowledge", "research": "research"}.get(ntype, ntype)
    topics = sorted({topic_kind, "memory" if ntype == "session" else topic_kind, project})
    fm = {
        "date": date,
        "type": ntype,
        "ingestion_type": "agent",
        "source": f"gald3r-{project}",
        "title": f'"{title}"',
        "topics": "[" + ", ".join(topics) + "]",
    }
    return fm


def render_fm(fm: dict, order):
    lines = ["---"]
    for k in order:
        if k in fm:
            lines.append(f"{k}: {fm[k]}")
    for k, v in fm.items():
        if k not in order:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--include-research", action="store_true",
                    help="also scan crawler-managed research/** (out of T1334 default scope)")
    args = ap.parse_args()
    vault = pathlib.Path(args.vault)
    if not vault.is_dir():
        print(f"ERROR: vault not found: {vault}", file=sys.stderr); sys.exit(2)

    targets = list(TARGETS) + ([RESEARCH_TARGET] if args.include_research else [])
    seen, report = set(), []
    for glob, ntype, research in targets:
        for path in sorted(vault.glob(glob)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            fm, body = parse_frontmatter(text)
            need = REQUIRED + (RESEARCH_EXTRA if research else [])
            if fm is None:
                missing = need
            else:
                missing = [k for k in need if k not in fm]
            if not missing:
                continue
            report.append((path, fm is None, missing))
            if args.apply:
                derived = derive(path, vault, ntype, body)
                if research:
                    derived.setdefault("refresh_policy", "static")
                    derived.setdefault("source_volatility", "low")
                if fm is None:
                    new = render_fm(derived, need) + text
                else:
                    # merge: keep existing keys, add only the missing ones
                    merged = {**derived, **fm}
                    new = render_fm(merged, need) + body
                path.write_text(new, encoding="utf-8")

    rel = lambda p: p.relative_to(vault)
    if not report:
        print(f"VAULT FRONTMATTER: all conformant ({len(seen)} notes scanned).")
        return
    print(f"VAULT FRONTMATTER: {len(report)} non-conformant of {len(seen)} scanned"
          + (" — APPLIED" if args.apply else " — report only (use --apply to fix)"))
    for path, no_fm, missing in report:
        reason = "no frontmatter" if no_fm else f"missing: {', '.join(missing)}"
        print(f"  - {rel(path)} ({reason})")


if __name__ == "__main__":
    main()
