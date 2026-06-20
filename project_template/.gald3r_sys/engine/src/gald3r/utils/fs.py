"""Filesystem operations — cross-platform replacements for the robocopy /
``Remove-Item`` / ``Set-VersionInTree`` patterns in the PS1 scripts.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import os
import re
import shutil
import stat
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Pattern, Tuple, Union

# Extensions treated as text by replace_in_file_tree when none are supplied.
# Mirrors the $TextExtensions list used by build_repos.ps1.
DEFAULT_TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".ps1", ".psm1",
    ".sh", ".bat", ".cmd", ".cfg", ".ini", ".xml", ".html", ".css", ".js",
    ".ts", ".mdc",
}

# Directory names that must never be copied into a generated tree — Python
# build artifacts that pollute output (and bloat it badly in the .venv case).
_ALWAYS_EXCLUDE_DIRS = {".venv", "__pycache__", ".pytest_cache"}


def _longpath(p: Path) -> str:
    """Return a string path safe for >260-char paths on Windows."""
    s = str(p)
    if os.name == "nt" and len(s) > 240 and not s.startswith("\\\\?\\"):
        return "\\\\?\\" + os.path.abspath(s)
    return s


def ensure_dir(path: Union[str, Path]) -> Path:
    """Create `path` (and parents) if missing; return it as a Path."""
    p = Path(path)
    os.makedirs(_longpath(p), exist_ok=True)
    return p


def copy_tree(
    src: Union[str, Path],
    dest: Union[str, Path],
    exclude_dirs: Optional[Iterable[str]] = None,
    exclude_files: Optional[Iterable[str]] = None,
) -> int:
    """Recursively copy `src` into `dest` — equivalent of ``robocopy /E /XD /XF``.

    Args:
        src: Source directory (must exist).
        dest: Destination directory (created if missing).
        exclude_dirs: Directory *names* to prune anywhere in the tree
            (case-insensitive, like robocopy /XD).
        exclude_files: File names or fnmatch patterns to skip
            (case-insensitive, like robocopy /XF).

    Returns:
        Number of files copied.

    Symlinks (file or directory) are skipped rather than followed, so a
    cyclic or dangling link can never corrupt the copy.
    """
    import fnmatch

    src, dest = Path(src), Path(dest)
    if not src.is_dir():
        raise FileNotFoundError(f"copy_tree source not found: {src}")
    # Build artifacts are never copyable output — a stray .venv/cache in the
    # source once added ~52 MB of junk to every generated repo. Pruned always,
    # regardless of caller-supplied excludes.
    xd = {d.casefold() for d in (exclude_dirs or [])} | _ALWAYS_EXCLUDE_DIRS
    xf = [f.casefold() for f in (exclude_files or [])]
    copied = 0
    for root, dirs, files in os.walk(src):
        root_p = Path(root)
        dirs[:] = [d for d in dirs
                   if d.casefold() not in xd and not (root_p / d).is_symlink()]
        target_root = dest / root_p.relative_to(src)
        ensure_dir(target_root)
        for name in files:
            if any(fnmatch.fnmatch(name.casefold(), pat) for pat in xf):
                continue
            src_file = root_p / name
            if src_file.is_symlink():
                continue
            shutil.copy2(_longpath(src_file), _longpath(target_root / name))
            copied += 1
    return copied


def _on_rm_error(func, path, exc_info) -> None:  # noqa: ANN001 — shutil callback
    """rmtree error handler: clear read-only bit and retry (Windows)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clear_dir_except_git(path: Union[str, Path], dry_run: bool = False) -> List[str]:
    """Remove every child of `path` except ``.git/`` — PS1 ``Clear-RepoExceptGit``.

    Args:
        path: Directory to clear (must exist).
        dry_run: When True, nothing is deleted; planned removals are printed
            with a ``[DRY]`` prefix.

    Returns:
        Names of the children removed (or that would be removed).
    """
    p = Path(path)
    if not p.is_dir():
        raise FileNotFoundError(f"clear_dir_except_git target not found: {p}")
    removed: List[str] = []
    for child in sorted(p.iterdir()):
        if child.name == ".git":
            continue
        removed.append(child.name)
        if dry_run:
            print(f"[DRY] would remove {child}")
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(_longpath(child), onerror=_on_rm_error)
        else:
            child.chmod(child.stat().st_mode | stat.S_IWRITE)
            child.unlink()
    return removed


PatternSpec = Union[Dict[str, str], Iterable[Tuple[str, str]]]


def replace_in_file_tree(
    root: Union[str, Path],
    patterns: PatternSpec,
    text_extensions: Optional[Iterable[str]] = None,
    exclude_dirs: Optional[Iterable[str]] = None,
) -> int:
    """Apply regex replacements across a file tree — PS1 ``Set-VersionInTree``.

    All patterns are compiled up front and applied in one pass per file; a file
    is rewritten only when at least one pattern matched.

    Args:
        root: Tree root to walk.
        patterns: Mapping (or pairs) of ``regex -> replacement``.
        text_extensions: File suffixes to consider (defaults to
            DEFAULT_TEXT_EXTENSIONS). Comparison is case-insensitive.
        exclude_dirs: Directory names to prune (e.g. ``.git``).

    Returns:
        Number of files modified.
    """
    root = Path(root)
    pairs = patterns.items() if isinstance(patterns, dict) else patterns
    compiled: List[Tuple[Pattern[str], str]] = [(re.compile(rx), rep) for rx, rep in pairs]
    exts = {e.lower() for e in (text_extensions or DEFAULT_TEXT_EXTENSIONS)}
    xd = {d.casefold() for d in (exclude_dirs or {".git"})}
    modified = 0
    for cur, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.casefold() not in xd]
        for name in files:
            fp = Path(cur) / name
            if fp.suffix.lower() not in exts:
                continue
            try:
                raw = fp.read_bytes()
            except OSError:
                continue
            if b"\x00" in raw[:8192]:  # binary despite the extension — skip
                continue
            text = raw.decode("utf-8", errors="surrogateescape")
            new = text
            for rx, rep in compiled:
                new = rx.sub(rep, new)
            if new != text:
                fp.write_bytes(new.encode("utf-8", errors="surrogateescape"))
                modified += 1
    return modified
