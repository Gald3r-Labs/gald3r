#!/usr/bin/env python3
"""Python port of g-hk-encoding-normalize.ps1 (T1584).

gald3r Encoding Normalizer (T1428). Strips spurious BOMs, fixes UTF-16, and
normalizes CRLF to LF in text files written by the agent. Prevents PS5.1
mojibake, emoji corruption, and em-dash mangling (BUG-073 / BUG-094 class).

Three invocation modes:
  1. stop / turn-end: no args -- normalizes all git-dirty text files
  2. explicit files:  -Files <path1> <path2> -- normalizes those files
  3. pre-commit:      -PreCommit -- normalizes all staged text files (re-stages)

Encoding policy by file type (the critical T1428 distinction):
  - PowerShell source (.ps1/.psm1/.psd1): UTF-8 WITH BOM (required for PS5.1
    correctness, BUG-073).
  - Everything else (.md, .yaml, .json, .ts, .py, task/bug files, ...):
    UTF-8 WITHOUT BOM. All processed files are normalized to LF.
  - UTF-16 LE/BE inputs are converted to the correct UTF-8 variant.

-Scan is report-only (exit 0 = clean, 1 = drift found, for CI gates).
-Quiet suppresses per-file output; errors are always shown.
"""
# @subsystems: PLATFORM_INTEGRATION
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; this hook is pure stdlib)

# Text file extensions to normalize (binary files are always skipped).
TEXT_EXTENSIONS = {
    ".md", ".mdc", ".yaml", ".yml", ".json", ".ps1", ".psm1", ".psd1",
    ".ts", ".tsx", ".js", ".jsx", ".py", ".txt", ".sh", ".bash",
    ".html", ".htm", ".css", ".scss", ".sql", ".toml", ".ini", ".cfg",
    ".gitattributes", ".gitignore", ".env",
}

# PowerShell source -- requires UTF-8 WITH BOM for PS5.1 (BUG-073).
POWERSHELL_EXTENSIONS = {".ps1", ".psm1", ".psd1"}

UTF8_BOM = b"\xef\xbb\xbf"


def dotnet_get_extension(path: str) -> str:
    """Replicate System.IO.Path.GetExtension: substring from the LAST '.' in
    the file name (so '.gitattributes' -> '.gitattributes', unlike Python's
    os.path.splitext which treats leading-dot names as extensionless)."""
    name = os.path.basename(path)
    i = name.rfind(".")
    if i == -1 or i == len(name) - 1:
        return ""
    return name[i:]


def is_text_file(path: str) -> bool:
    ext = dotnet_get_extension(path).lower()
    if ext in TEXT_EXTENSIONS:
        return True
    # Extensionless files inside .gald3r/ are task/bug/plan files -- treat as text.
    if ext == "" and re.search(r"/\.gald3r/", path.replace("\\", "/"), re.IGNORECASE):
        return True
    return False


def is_powershell_file(path: str) -> bool:
    return dotnet_get_extension(path).lower() in POWERSHELL_EXTENSIONS


def get_bom_encoding(data: bytes) -> str:
    if len(data) >= 3 and data[0] == 0xEF and data[1] == 0xBB and data[2] == 0xBF:
        return "UTF8-BOM"
    if len(data) >= 2 and data[0] == 0xFF and data[1] == 0xFE:
        return "UTF16-LE"
    if len(data) >= 2 and data[0] == 0xFE and data[1] == 0xFF:
        return "UTF16-BE"
    return "UTF8"


def normalize_file(path: str, scan: bool, quiet: bool) -> bool:
    """Returns True when a change is needed; performs the write unless scan."""
    if not os.path.isfile(path):
        return False
    if not is_text_file(path):
        return False

    try:
        with open(path, "rb") as fh:
            data = fh.read()
        if len(data) == 0:
            return False

        encoding = get_bom_encoding(data)

        # Binary/invalid-content guard (T1447): a NUL byte (0x00) in a file the
        # BOM sniff treats as UTF-8/UTF-8-BOM (NOT UTF-16, which legitimately
        # contains NULs) means the file is really binary or invalid UTF-8
        # despite its text extension. Decoding would silently replace bytes
        # with U+FFFD (irreversible corruption). Leave it byte-identical.
        if encoding in ("UTF8", "UTF8-BOM") and 0x00 in data:
            if scan and not quiet:
                print(
                    "  skip-binary: {0} (NUL byte in non-UTF16 file)".format(
                        os.path.basename(path)
                    )
                )
            return False

        has_crlf = 0x0D in data
        is_ps = is_powershell_file(path)

        # Desired final state:
        #   PowerShell  -> UTF8-BOM + LF
        #   other text  -> UTF8 no-BOM + LF
        want_bom = is_ps

        bom_is_correct = (want_bom and encoding == "UTF8-BOM") or (
            not want_bom and encoding == "UTF8"
        )

        # Already clean? (correct BOM state AND LF-only)
        if bom_is_correct and not has_crlf:
            return False

        if scan:
            if not quiet:
                target = "UTF8-BOM" if want_bom else "UTF8-no-BOM"
                crlf = " +CRLF" if has_crlf else ""
                print(
                    "  encoding-drift: {0} [{1}{2} -> {3}+LF]".format(
                        os.path.basename(path), encoding, crlf, target
                    )
                )
            return True

        # Decode with the detected source encoding. errors='replace' mirrors
        # .NET Encoding.GetString, which substitutes U+FFFD for invalid bytes.
        if encoding == "UTF8-BOM":
            content = data[3:].decode("utf-8", errors="replace")
        elif encoding == "UTF16-LE":
            content = data[2:].decode("utf-16-le", errors="replace")
        elif encoding == "UTF16-BE":
            content = data[2:].decode("utf-16-be", errors="replace")
        else:
            content = data.decode("utf-8", errors="replace")

        # Normalize line endings: CRLF -> LF, then any bare CR -> LF.
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")

        # Write back with the encoding correct for this file type (binary mode
        # so Python performs no newline translation).
        out = normalized.encode("utf-8")
        if want_bom:
            out = UTF8_BOM + out
        with open(path, "wb") as fh:
            fh.write(out)

        if not quiet:
            target = "UTF8-BOM" if want_bom else "UTF8-no-BOM"
            parts = []
            if not bom_is_correct:
                parts.append(f"{encoding} -> {target}")
            if has_crlf:
                parts.append("CRLF -> LF")
            reason = "[" + ", ".join(parts) + "]"
            print("  encoding-fix: {0} {1}".format(os.path.basename(path), reason))
        return True
    except Exception as exc:  # mirror the .ps1 catch-all Write-Warning path
        print(
            "WARNING:   encoding-normalize: failed '{0}': {1}".format(path, exc),
            file=sys.stderr,
        )
        return False


def run_git(args: list) -> str:
    try:
        proc = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.stdout or ""
    except (OSError, subprocess.SubprocessError):
        return ""


def is_path_rooted(p: str) -> bool:
    """Replicate System.IO.Path.IsPathRooted (leading slash OR drive spec)."""
    return p.startswith(("\\", "/")) or (len(p) >= 2 and p[1] == ":")


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r encoding normalizer (Python port of g-hk-encoding-normalize.ps1)"
    )
    parser.add_argument(
        "-Files", "--files", dest="files", nargs="*", default=[],
        help="Specific file paths to normalize.",
    )
    parser.add_argument(
        "-PreCommit", "--pre-commit", dest="pre_commit", action="store_true",
        help="Normalize all staged text files; re-stages fixes.",
    )
    parser.add_argument(
        "-Scan", "--scan", dest="scan", action="store_true",
        help="Report-only. Exit 0 = clean, 1 = drift found.",
    )
    parser.add_argument(
        "-Quiet", "--quiet", dest="quiet", action="store_true",
        help="Suppress per-file output. Errors are always shown.",
    )
    args, _ = parser.parse_known_args(argv)

    files = list(args.files)

    # --- Resolve file list based on mode ---
    if args.pre_commit:
        git_files = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACM"])
        files = [f for f in git_files.splitlines() if f and f.strip() != ""]
    elif not files:
        # stop / scan mode: all git-dirty (modified + added) text files.
        git_status = run_git(["status", "--porcelain"])
        if git_status:
            files = []
            for line in git_status.splitlines():
                if re.match(r"^[ MARC?][ MARC?] ", line, re.IGNORECASE):
                    f = line[3:].strip()
                    if f != "":
                        files.append(f)

    if not files:
        if args.scan and not args.quiet:
            print("  encoding-scan: clean (no dirty files)")
        return 0

    touched = 0
    for f in files:
        path = f.strip('"').strip("'")
        if not is_path_rooted(path):
            path = os.path.join(os.getcwd(), path)
        if normalize_file(path, args.scan, args.quiet):
            touched += 1

    if args.scan:
        if touched > 0:
            if not args.quiet:
                print("  encoding-scan: {0} file(s) need normalization".format(touched))
            return 1
        if not args.quiet:
            print("  encoding-scan: clean")
        return 0

    if touched > 0 and not args.quiet:
        print("  encoding-normalize: {0} file(s) normalized".format(touched))

    # In pre-commit mode, re-stage normalized files so the fix lands in the commit.
    if args.pre_commit and touched > 0:
        for f in files:
            path = f.strip('"').strip("'")
            run_git(["add", "--", path])

    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session; the -Scan drift exit (1)
        # above is deliberate and raised via sys.exit, not caught here.
        sys.exit(0)
