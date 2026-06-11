#!/usr/bin/env python3
"""Python port of render.ps1 (T1585).

Render a gald3r human-facing report as themed HTML (T1316). Implements
CHOOSE_THEME + RENDER + VALIDATE + EXPORT for the g-skl-html-output skill.
Composes docs/templates/html-base.html with an already-rendered body fragment,
links the active theme (docs/themes/_active.css), and writes a timestamped
file under the output dir per g-rl-01 naming.

Coordination files (TASKS.md, BUGS.md, task specs) are NEVER rendered here.
"""
# @subsystems: UI_AND_OUTPUT
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence


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
    """Walk up from cwd until .gald3r is found (PS1 semantics: stop at FS root)."""
    d = Path.cwd()
    while not (d / ".gald3r").exists():
        if d.parent == d:
            break
        d = d.parent
    return str(d)


_MERMAID_KEYWORDS_RX = re.compile(
    r"^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|journey)"
)


def build_parser() -> argparse.ArgumentParser:
    """Argparse surface mirroring the PS1 param() block."""
    p = argparse.ArgumentParser(
        description="Render a gald3r human-facing report as themed HTML (T1316)."
    )
    p.add_argument("-Template", "--template", dest="template", required=True,
                   choices=("base", "report", "review", "backlog"))
    p.add_argument("-Title", "--title", dest="title", required=True)
    p.add_argument("-SessionLabel", "--session-label", dest="session_label", default="")
    p.add_argument("-BodyHtml", "--body-html", dest="body_html", required=True)
    p.add_argument("-Topic", "--topic", dest="topic", default=None)
    p.add_argument("-OutDir", "--out-dir", dest="out_dir", default="docs")
    p.add_argument("-ProjectRoot", "--project-root", dest="project_root", default=None)
    p.add_argument("-IDE", "--ide", dest="ide", default="Claude")
    p.add_argument("-ValidateOnly", "--validate-only", dest="validate_only",
                   action="store_true")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry: choose theme -> compose -> validate -> export."""
    args = build_parser().parse_args(argv)
    project_root = Path(args.project_root or find_project_root())
    themes_dir = project_root / "docs" / "themes"
    tpl_dir = project_root / "docs" / "templates"

    # --- CHOOSE_THEME ---
    theme = "gald3r-dark"
    cfg = project_root / ".gald3r" / "config" / "AGENT_CONFIG.md"
    if cfg.is_file():
        for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*html_theme:\s*([\w-]+)", line)
            if m:
                theme = m.group(1)
                break
    if not (themes_dir / f"{theme}.css").is_file():
        print(f"WARNING: Theme '{theme}' not found; falling back to gald3r-dark.",
              file=sys.stderr)
        theme = "gald3r-dark"
    # Rewrite _active.css redirect (T1328)
    active_path = themes_dir / "_active.css"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(
        "/*! _active.css - active-theme resolution redirect (T1328). "
        "Rewritten by g-skl-html-output. */\n"
        f"@import url('{theme}.css');\n",
        encoding="utf-8",
    )

    # --- Load templates ---
    base = (tpl_dir / "html-base.html").read_text(encoding="utf-8", errors="replace")
    # Strip the leading template-documentation comment so its literal {{ }} tokens
    # are not substituted into the output (keeps html-base.html self-documenting).
    base = re.sub(r"<!--.*?-->\s*", "", base, count=1, flags=re.DOTALL)
    # Body fragment templates document structure; the caller supplies fully
    # rendered BodyHtml, so we inject it directly into the base shell.

    # --- Compute substitutions ---
    out_abs = project_root / args.out_dir
    theme_href = "themes/_active.css"
    try:
        rel = os.path.relpath(themes_dir / "_active.css", out_abs)
        if rel:
            theme_href = rel.replace("\\", "/")
    except ValueError:
        pass  # different drives on Windows -- keep the default href
    mermaid_theme = "default" if theme == "gald3r-light" else "dark"
    gen_date = datetime.now().strftime("%Y-%m-%d")

    html = (base
            .replace("{{ title }}", args.title)
            .replace("{{ generated_date }}", gen_date)
            .replace("{{ session_label }}", args.session_label)
            .replace("{{ theme_href }}", theme_href)
            .replace("{{ mermaid_theme }}", mermaid_theme)
            .replace("{{ body }}", args.body_html))

    # --- VALIDATE ---
    errors: List[str] = []
    if re.search(r"\{\{\s*\w+\s*\}\}", html):
        errors.append("Unsubstituted placeholder(s) remain.")
    if re.search(r"<style[ >]", html):
        errors.append("Inline <style> present; styling must be external.")
    if not (themes_dir / f"{theme}.css").is_file():
        errors.append("Active theme CSS missing.")
    for m in re.finditer(r'<div class="mermaid">(.*?)</div>', html, flags=re.DOTALL):
        b = m.group(1).strip()
        if b and not _MERMAID_KEYWORDS_RX.match(b):
            errors.append("Mermaid block does not start with a known diagram keyword.")
    if errors:
        cprint("VALIDATE: FAIL", "red")
        for e in errors:
            cprint(f"  - {e}", "red")
        return 1
    cprint(f"VALIDATE: PASS (theme={theme}, mermaid={mermaid_theme})", "green")
    if args.validate_only:
        return 0

    # --- EXPORT (g-rl-01 naming) ---
    topic = args.topic or re.sub(r"[^A-Za-z0-9]+", "_", args.title).strip("_").upper()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{stamp}_{args.ide}_{topic.upper()}.html"
    out_abs.mkdir(parents=True, exist_ok=True)
    out_file = out_abs / fname
    out_file.write_text(html + "\n", encoding="utf-8")
    cprint(f"EXPORT: {out_file}", "cyan")
    print(out_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
