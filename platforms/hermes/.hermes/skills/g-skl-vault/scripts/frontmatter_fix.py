#!/usr/bin/env python3
"""Python port of frontmatter_fix.ps1 (T1585).

Retrofit Obsidian/VAULT_OBSIDIAN_STANDARD YAML frontmatter onto vault notes
that are missing it (T1334). Backup-first, dry-run by default, idempotent.

Walks the vault for long-lived notes missing a leading ``---`` frontmatter
block and prepends a conformant block. Targets:
    projects/*/memory.md      -> type: session
    projects/*/sessions/*.md  -> type: session
    projects/*/decisions/*.md -> type: decision (+ decision_status, decided_on)
    knowledge/*.md            -> type: knowledge_card

Existing content is preserved byte-for-byte beneath the inserted block. Files
that already have valid frontmatter are skipped (idempotent). Symlinked or
read-only files are skipped with a warning.

DRY-RUN by default -- shows the planned per-file frontmatter. Pass -Apply to
write; each modified file is backed up to {vault}/.backups/{timestamp}/<relpath>
before the write.
"""
# @subsystems: VAULT_AND_RESEARCH
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


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


def _color_enabled() -> bool:
    if _HAS_UTILS:
        from gald3r.utils import console
        return console.color_enabled()
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


_ANSI = {"red": "31", "green": "32", "yellow": "33", "cyan": "36"}


def cprint(msg: str, color: Optional[str] = None) -> None:
    """Print with optional ANSI color (replaces Write-Host -ForegroundColor)."""
    if color and _color_enabled():
        print(f"\x1b[{_ANSI[color]}m{msg}\x1b[0m")
    else:
        print(msg)


def find_project_root() -> str:
    """Walk up (max 12 levels) from the script dir to the .gald3r marker; else cwd."""
    d = Path(__file__).resolve().parent
    for _ in range(12):
        if (d / ".gald3r").exists():
            return str(d)
        if d.parent == d:
            break
        d = d.parent
    return str(Path.cwd())


def get_identity_value(root: str, key: str) -> Optional[str]:
    """Read ``key = value`` from .gald3r/.identity (best effort)."""
    idf = Path(root) / ".gald3r" / ".identity"
    if idf.is_file():
        for line in idf.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(rf"^\s*{re.escape(key)}\s*=\s*(.+)\s*$", line)
            if m:
                return m.group(1).strip()
    return None


def has_frontmatter(path: Path) -> bool:
    """True when the file's first line is the YAML fence '---'."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
    except OSError:
        return False
    return first.strip() == "---"


def get_note_type(rel_path: str) -> str:
    """Classify the note by its vault location (decision/session/knowledge_card)."""
    if re.search(r"[\\/]decisions[\\/]", rel_path):
        return "decision"
    if re.search(r"[\\/]sessions[\\/]", rel_path):
        return "session"
    if re.search(r"[\\/]knowledge[\\/]", rel_path):
        return "knowledge_card"
    if re.search(r"memory\.md$", rel_path):
        return "session"
    return "session"


def get_title(path: Path) -> str:
    """First markdown H1 heading, else the file stem."""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\#\s+(.+)$", line)
            if m:
                return m.group(1).strip()
    except OSError:
        pass
    return path.stem


def new_frontmatter(path: Path, rel_path: str, project_name: str) -> str:
    """Build the conformant frontmatter block for one note."""
    note_type = get_note_type(rel_path)
    title = get_title(path)
    date = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    topics: List[str] = []
    for t in ("memory", note_type, project_name):
        if t not in topics:
            topics.append(t)
    topics_str = "[" + ", ".join(topics) + "]"
    lines = ["---"]
    lines.append(f"date: {date}")
    lines.append(f"type: {note_type}")
    lines.append("ingestion_type: agent")
    lines.append(f"source: gald3r-{project_name}")
    escaped_title = title.replace('"', '\\"')
    lines.append(f'title: "{escaped_title}"')
    lines.append(f"topics: {topics_str}")
    if note_type == "decision":
        lines.append("decision_status: active")
        lines.append(f"decided_on: {date}")
    lines.append("---")
    return "\n".join(lines)


def collect_candidates(vault: Path, single_file: Optional[str]) -> Tuple[List[Path], int]:
    """Return (candidate files, exit_code_or_0). Single-file mode validates existence."""
    if single_file:
        p = Path(single_file)
        if not p.exists():
            print(f"WARNING: File not found: {single_file}", file=sys.stderr)
            return [], 1
        return [p], 0
    candidates: List[Path] = []
    for sub in ("projects", "knowledge"):
        g = vault / sub
        if not g.is_dir():
            continue
        for f in sorted(g.rglob("*.md")):
            if not f.is_file():
                continue
            full = str(f)
            if (re.search(r"memory\.md$", full)
                    or re.search(r"[\\/]sessions[\\/]", full)
                    or re.search(r"[\\/]decisions[\\/]", full)
                    or re.search(r"[\\/]knowledge[\\/]", full)):
                candidates.append(f)
    return candidates, 0


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Retrofit Obsidian frontmatter onto vault notes missing it (T1334)."
    )
    p.add_argument("-VaultLocation", "--vault-location", dest="vault_location", default=None)
    p.add_argument("-File", "--file", dest="file", default=None,
                   help="Single-file mode: retrofit just this one .md file.")
    p.add_argument("-Apply", "--apply", dest="apply", action="store_true",
                   help="Perform writes (with backup). Omit for dry-run.")
    p.add_argument("-ProjectName", "--project-name", dest="project_name", default=None)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: scan -> report -> dry-run preview or backup+apply."""
    args = build_parser().parse_args(argv)

    root = find_project_root()
    vault_location = args.vault_location or get_identity_value(root, "vault_location")
    project_name = args.project_name or get_identity_value(root, "project_name") or "unknown"

    if not vault_location or vault_location == "{LOCAL}":
        print(f"WARNING: No shared vault_location configured "
              f"(value: '{vault_location}'). Nothing to walk.", file=sys.stderr)
        return 0
    vault = Path(vault_location)
    if not vault.exists():
        print(f"WARNING: Vault path '{vault_location}' does not exist.", file=sys.stderr)
        return 1

    candidates, err = collect_candidates(vault, args.file)
    if err:
        return err

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = vault / ".backups" / ts
    vault_prefix_len = len(str(vault).rstrip("\\/"))
    report: List[Tuple[str, str]] = []  # (status, relpath)
    to_fix: List[Path] = []

    def relpath(p: Path) -> str:
        return str(p)[vault_prefix_len:].lstrip("\\/")

    for c in candidates:
        rel = relpath(c)
        if has_frontmatter(c):
            report.append(("ok (has frontmatter)", rel))
            continue
        # skip read-only / symlinks
        if not os.access(c, os.W_OK):
            report.append(("SKIP read-only", rel))
            continue
        if c.is_symlink():
            report.append(("SKIP symlink", rel))
            continue
        to_fix.append(c)
        report.append(("NEEDS frontmatter", rel))

    cprint(f"=== Vault frontmatter scan: {vault_location} ===", "cyan")
    for status, rel in report:
        print(f"  [{status}] {rel}")
    print(f"Total: {len(report)} scanned, {len(to_fix)} need frontmatter.")

    if not to_fix:
        cprint("Nothing to retrofit. Idempotent no-op.", "green")
        return 0

    if not args.apply:
        cprint(f"\n--- DRY RUN (pass -Apply to write; backups go to {backup_root}) ---",
               "yellow")
        for f in to_fix:
            rel = relpath(f)
            cprint(f"\n# would prepend to: {rel}", "yellow")
            print(new_frontmatter(f, rel, project_name))
        return 0

    # Apply: backup then prepend.
    for f in to_fix:
        rel = relpath(f)
        backup_path = backup_root / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_bytes(f.read_bytes())
        fm = new_frontmatter(f, rel, project_name)
        body = f.read_text(encoding="utf-8", errors="surrogateescape")
        f.write_text(fm + "\n\n" + body, encoding="utf-8", errors="surrogateescape")
        cprint(f"  retrofitted: {rel} (backup: .backups/{ts}/{rel})", "green")
    cprint(f"\nDone. {len(to_fix)} file(s) retrofitted; backups in {backup_root}", "green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
