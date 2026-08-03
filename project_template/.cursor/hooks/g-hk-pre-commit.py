#!/usr/bin/env python3
"""Python port of g-hk-pre-commit.ps1 (T1584).

gald3r pre-commit sanity hook (opt-in). Checks staged changes for:
secrets (BLOCK), staged .env files (BLOCK), large files >5 MB (WARN),
C-026 worktree TASKS.md writes (BLOCK), gald3r task sync drift (WARN),
protected files per g-rl-02 (BLOCK), and bare stubs/TODOs without the
TODO[TASK-X->TASK-Y] annotation per g-rl-34 (BLOCK).

BUG-401: the "protected files" gate is reconciled with g-rl-02's
per-repo tracking policy. `.env`/`.mcp.json` (genuine secrets/machine-local
credentials) remain UNCONDITIONALLY blocked. Coordination-directory paths
(`.gald3r/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, etc.) only block when
THIS repo's own `.gitignore` says the path is ignored yet it was staged
anyway (drift, e.g. `git add -f`) -- a controller/WPAC repo that
intentionally tracks `.gald3r/`/`CLAUDE.md` is never blocked for doing so.
See `git_check_ignore()` and the "PROTECTED FILES ALLOWLIST" section below.

BUG-608: the secrets check scans only genuinely ADDED diff CONTENT lines
(`diff_added_content_lines()`), never unchanged unified-diff CONTEXT
lines that merely sit inside a hunk's surrounding context because an
unrelated nearby line changed, and never removed ('-') lines either
(deleting a secret-shaped line is not a new leak). Previously any
pre-existing, unmodified secret-shaped string within 3 lines of a real
change falsely BLOCKed the commit.

Exit 1 = BLOCK (commit halted). Exit 0 = ALLOW or WARN (commit proceeds).
GALD3R_HOOK_BYPASS=1 downgrades BLOCK to WARN (T600 §3.3 override path).
-BlockOnFailure is accepted but is a no-op because the exit-code semantics
already match the T600 B-4 contract (same as the .ps1 original).
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations
# --- gald3r calltrace bootstrap (T268) -- injected; inert unless gald3r call tracing is
# enabled. Strip everywhere: python scripts/inject_calltrace_bootstrap.py --strip
import os as _g3ct_os
_g3ct_home = _g3ct_os.environ.get("GALD3R_HOME") or _g3ct_os.path.join(
    _g3ct_os.path.expanduser("~"), ".gald3r")
_g3ct_env = (_g3ct_os.environ.get("GALD3R_TRACE_CALLS") or "").strip().lower()
if _g3ct_env not in ("", "0", "off", "false", "no") or _g3ct_os.path.isfile(
        _g3ct_os.path.join(_g3ct_home, "calltrace.json")):
    try:
        _g3ct_bs = _g3ct_os.path.join(_g3ct_home, "calltrace_bootstrap.py")
        if _g3ct_os.path.isfile(_g3ct_bs):
            with open(_g3ct_bs, "r", encoding="utf-8") as _g3ct_fh:
                exec(compile(_g3ct_fh.read(), _g3ct_bs, "exec"),
                     {"__g3ct_script__": __file__,
                      "__name__": "_gald3r_calltrace_exec"})
    except Exception:
        pass
# --- end gald3r calltrace bootstrap ---

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: F401  (shared bootstrap; this hook is pure stdlib)

# Built-in fallback — identical to the .ps1 in-hook fallback AND to
# Get-Gald3rSecretPatterns in gald3r_git_sanity_common.ps1.
DEFAULT_SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"Bearer\s+[a-zA-Z0-9._\-]{20,}",
    r"AKIA[A-Z0-9]{16}",
    r"password\s*=\s*\S+",
    r"api_key\s*=\s*\S+",
    r"secret_key\s*=\s*\S+",
    r"private_key\s*=\s*\S+",
    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
]

# BUG-597: narrow, explicit opt-out for individual diff lines that intentionally
# construct fake secret-shaped fixtures to test detection/redaction logic itself.
# Per-line and marker-based (not path-based) so a real secret pasted anywhere,
# including under tests/, still blocks -- only a line carrying this exact marker
# comment is excluded from the scan.
SECRET_SCAN_ALLOW_MARKER = "secret-scan: allow"

# Unconditional -- always forbidden regardless of per-repo tracking policy.
# These are genuine secrets / machine-local credentials per g-rl-02's
# "Protected Files" table ("the one category that is always forbidden,
# regardless of repo type").
UNCONDITIONAL_PROTECTED_PATTERNS = [
    r"^\.env(\..*)?$",
    r"^\.mcp\.json$",
]

# Coordination-directory patterns -- BUG-401: g-rl-02 now documents that
# tracked-vs-ignored for these is PER-REPO POLICY, not a fixed always-block
# list ("Before treating a path as protected, check what the repo actually
# does: `git check-ignore -v <path>` ... If git status shows an
# intentionally-tracked coordination path as staged, that's expected --
# do not block the commit."). A controller/WPAC repo (this repo included)
# intentionally TRACKS .gald3r/, AGENTS.md, CLAUDE.md, etc. These patterns
# only block when THIS repo's own .gitignore excludes the path yet it was
# staged anyway (drift -- e.g. `git add -f`); see git_check_ignore() and
# the "PROTECTED FILES ALLOWLIST" section below for the reconciliation.
COORDINATION_DIR_PATTERNS = [
    r"^\.agent/",
    r"^\.claude/",
    r"^\.codex/",
    r"^\.cursor/",
    r"^\.opencode/",
    r"^\.copilot/",
    r"^\.gald3r/",
    r"^\.project_template/",
    r"^temp_docs/",
    r"^temp_scripts/",
    r"^AGENTS\.md$",
    r"^CLAUDE\.md$",
    r"^GEMINI\.md$",
    r"^GUARDRAILS\.md$",
]

# Back-compat combined view (BUG-401 predecessor shape) -- not used for the
# BLOCK decision itself anymore (see section 4 below), kept only in case any
# external tooling imports this module's PROTECTED_PATTERNS name directly.
PROTECTED_PATTERNS = UNCONDITIONAL_PROTECTED_PATTERNS + COORDINATION_DIR_PATTERNS

STUB_BLOCK_PATTERNS = [
    r"^\+\s*(#|//|--)\s*(TODO|FIXME)\b",
    r"^\+\s*raise\s+NotImplementedError",
    r"^\+\s*throw\s+new\s+Error\(\s*[\"`']?not\s+implemented",
]
ANNOTATION_REGEX = re.compile(
    r"TODO\s*\[\s*TASK[-_]\d+\s*[-→>]+\s*TASK[-_]\d+\s*\]", re.IGNORECASE
)


def run_git(args: list) -> str:
    """Run git, return stdout ('' on any failure) — mirrors `git ... 2>$null`."""
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


def git_check_ignore(paths: list) -> set:
    """Return the subset of `paths` THIS repo's own .gitignore excludes.

    BUG-401: reconciles the "PROTECTED FILES ALLOWLIST" coordination-dir
    patterns with g-rl-02's per-repo tracking policy -- a path only counts
    as drift (force-staged despite being ignored) when git itself says the
    path is ignored; an intentionally-tracked path (this repo's own
    `.gald3r/`, `CLAUDE.md`, etc.) must never be reported here.

    Uses a single `git check-ignore --no-index --stdin` call (same
    subprocess style as run_git() above) so the whole staged set is
    classified in one shot instead of one subprocess per candidate path.
    `--no-index` is required: by default `git check-ignore` consults the
    index and reports an ALREADY-TRACKED-OR-STAGED path as "not ignored"
    even when a .gitignore rule matches it (verified against real git
    2.52 behavior -- staging a path with `git add -f` flips
    `check-ignore`'s answer from ignored to not-ignored unless `--no-index`
    is passed) -- exactly the force-staged-drift case this function exists
    to catch, so the default (index-aware) mode would silently defeat the
    BUG-401 fix. `git check-ignore` exits 0 when at least one supplied path
    is ignored, 1 when none are, and 128 on a fatal error (e.g. not inside a
    git work tree) -- only exit codes 0 and 1 are meaningful pass/fail
    signals; anything else (including a process launch failure) fails OPEN
    (returns no ignored paths) rather than mis-blocking every coordination-
    dir commit in a repo that deliberately tracks them.
    """
    if not paths:
        return set()
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "--no-index", "--stdin"],
            input="\n".join(paths),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if proc.returncode not in (0, 1):
        return set()
    # stdout lists exactly the paths (as supplied) that ARE ignored, one per line.
    return {ln for ln in proc.stdout.splitlines() if ln}


def diff_added_content_lines(diff_lines: list) -> list:
    """Return only genuinely ADDED CONTENT lines from unified diff output.

    BUG-608: the secrets check previously scanned every line of
    `git diff --cached` output verbatim, including unchanged unified-diff
    CONTEXT lines (the default 3-line hunk context git shows around each
    change). A pre-existing, unmodified secret-shaped string sitting a few
    lines away from a real change would get swept into a hunk's context and
    falsely BLOCK the commit even though nothing about that line was
    touched.

    Only ADDED ('+') lines are scanned -- not removed ('-') lines. Deleting
    a secret-shaped line is not a new leak entering the repository (it is
    still recoverable from history either way), so flagging it has no
    security benefit and only produces the same kind of false-positive
    friction this bug is about, on the departing side of an edit instead of
    the context side. Unchanged context lines and removed lines are both
    pre-existing/departing content, never new material.

    Per the unified diff grammar, every line between a hunk header
    (`@@ ... @@`) and the next hunk/file boundary begins with exactly one
    marker character: ' ' (context, unchanged), '+' (added), '-' (removed),
    or '\\' (a "No newline at end of file" marker, not content). The
    per-file `--- a/path` / `+++ b/path` headers that precede the FIRST
    hunk of each file are NOT content and must not be scanned even though
    `+++ b/path` begins with '+' characters.

    Naive prefix matching (e.g. `not line.startswith("+++")`) is not fully
    safe here: a genuinely ADDED line whose own content happens to start
    with "++ " would collide with the header spelling and be silently
    dropped -- exactly the kind of false-negative regression BUG-608 warned
    against. Tracking whether we are currently inside a hunk (seen `@@` for
    the current file, not yet a new `diff --git` file boundary) resolves
    the ambiguity precisely instead of guessing from the line's spelling.
    """
    added_lines = []
    in_hunk = False
    for ln in diff_lines:
        if ln.startswith("diff --git "):
            in_hunk = False
            continue
        if ln.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk:
            # Lines before the first hunk of a file (diff --git, index,
            # mode, --- a/path, +++ b/path) are headers, never content.
            continue
        if ln.startswith("+"):
            added_lines.append(ln[1:])
        # '-' (removed), ' ' (context), and '\' (no-newline marker) are
        # intentionally excluded -- none of them are new content.
    return added_lines


def load_secret_patterns(repo_root: str) -> list:
    """Source secret patterns from the shared sanity module.

    The .ps1 dot-sources gald3r_git_sanity_common.ps1 for
    Get-Gald3rSecretPatterns. Python cannot dot-source PowerShell, so:
    prefer a gald3r_git_sanity_common.py sibling when present (T1584
    transition), then extract the quoted regex list straight out of the
    .ps1 function body, then fall back to the built-in defaults (which are
    identical to the shared list today).
    """
    scripts_dir = Path(repo_root) / ".cursor" / "skills" / "g-skl-git-commit" / "scripts"
    py_common = scripts_dir / "gald3r_git_sanity_common.py"
    if py_common.is_file():
        try:
            spec = importlib.util.spec_from_file_location(
                "gald3r_git_sanity_common", py_common
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            fn = getattr(mod, "get_gald3r_secret_patterns", None)
            if callable(fn):
                pats = [str(p) for p in fn() if str(p).strip()]
                if pats:
                    return pats
        except Exception:
            pass
    ps1_common = scripts_dir / "gald3r_git_sanity_common.ps1"
    if ps1_common.is_file():
        try:
            text = ps1_common.read_text(encoding="utf-8", errors="replace")
            m = re.search(
                r"function\s+Get-Gald3rSecretPatterns\s*\{(.*?)\n\}",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if m:
                pats = re.findall(r'"([^"]+)"', m.group(1))
                if pats:
                    return pats
        except OSError:
            pass
    return list(DEFAULT_SECRET_PATTERNS)


def resolve_engine_cmd(repo_root: str):
    """Resolve the gald3r engine command prefix (P3 Tier-0, T179/T191 — A6/T1663).

    The org policy CHECK op was absorbed from g-skl-policy's `policy_engine.py`
    into the `gald3r policy check` verb. Delegates to the shared
    `_hook_common.resolve_engine_argv` (env var -> PATH -> legacy loose
    resolver -> loud degrade) so PATH resolution works even when the loose
    `.gald3r_sys/scripts/gald3r_bin.py` IP script is not shipped. Returns the
    command prefix (e.g. ``["gald3r"]``) or ``None`` (skip, never block)
    when no engine can be found."""
    return _hook_common.resolve_engine_argv(
        Path(repo_root), hook_name="g-hk-pre-commit"
    )


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(
        description="gald3r pre-commit sanity hook (Python port of g-hk-pre-commit.ps1)"
    )
    parser.add_argument(
        "-BlockOnFailure",
        "--block-on-failure",
        dest="block_on_failure",
        action="store_true",
        help="Accepted for T600 contract uniformity; no-op (hook is always-block).",
    )
    parser.parse_known_args(argv)

    bypass = os.environ.get("GALD3R_HOOK_BYPASS") == "1"
    if bypass:
        print(
            "gald3r pre-commit: BYPASS active (GALD3R_HOOK_BYPASS=1) — treating BLOCK as WARN."
        )

    repo_root = run_git(["rev-parse", "--show-toplevel"]).strip()
    if not repo_root:
        repo_root = str((Path(__file__).resolve().parent / ".." / "..").resolve())

    secret_patterns = load_secret_patterns(repo_root)
    # Resolved once, shared by section 6 (.gald3r VALIDATION GATE) and section 7 (org
    # policy) below -- both shell out to the gald3r engine via the same PATH-first
    # resolver (T292/T299: neither section imports the engine's Python package directly).
    engine_cmd = resolve_engine_cmd(repo_root)

    block = False
    warns = []

    print()
    print("gald3r pre-commit sanity check")
    print("=============================")

    # --- 1. SECRETS CHECK (BLOCK) ---
    diff = run_git(["diff", "--cached"])
    diff_lines = re.split(r"\r?\n", diff) if diff else []
    # BUG-608: scan only genuinely ADDED content lines, never bare
    # unified-diff CONTEXT lines that merely sit near an unrelated change,
    # and never removed ('-') lines either (deleting a secret-shaped line
    # is not a new leak -- see diff_added_content_lines()'s docstring).
    # diff_added_content_lines() tracks hunk boundaries explicitly rather
    # than guessing from a line's own spelling (BUG-608), which also fixes
    # a false-negative the original BUG-597 naive '+'/'+++' prefix check
    # had: a genuinely added line whose content itself starts with "++"
    # (e.g. "++counter;") would otherwise collide with the "+++ b/path"
    # file-header spelling and be silently skipped.
    added_content_lines = diff_added_content_lines(diff_lines)
    scannable_lines = [ln for ln in added_content_lines if SECRET_SCAN_ALLOW_MARKER not in ln]
    secret_hits = []
    for pat in secret_patterns:
        try:
            rx = re.compile(pat, re.IGNORECASE)  # Select-String is case-insensitive
        except re.error:
            continue
        hits = ["  " + ln.strip() for ln in scannable_lines if rx.search(ln)]
        if hits:
            secret_hits.extend(hits[:3])

    # Also check for staged .env files
    staged_files = [
        ln for ln in run_git(["diff", "--cached", "--name-only"]).splitlines() if ln
    ]
    env_files = [f for f in staged_files if re.match(r"^\.env(\..*)?$", f, re.IGNORECASE)]
    secret_hits.extend(f"  [.env file staged: {f}]" for f in env_files)

    if secret_hits:
        print("BLOCK: Secrets detected in staged changes:")
        for h in secret_hits:
            print(h)
        print("  -> Remove secrets before committing. Use environment variables or a vault.")
        block = True
    else:
        print("Secrets:     PASS")

    # --- 2. LARGE FILE CHECK (WARN) ---
    large_files = []
    for f in staged_files:
        try:
            p = Path(f)
            if p.is_file() and p.stat().st_size > 5 * 1024 * 1024:
                large_files.append(f)
        except OSError:
            continue

    if large_files:
        detail_lines = []
        for f in large_files:
            try:
                size_kb = round(Path(f).stat().st_size / 1024)
            except OSError:
                size_kb = 0
            detail_lines.append(f"  {f} ({size_kb} KB)")
        warns.append("WARN: Staged files > 5 MB detected:\n" + "\n".join(detail_lines) + "\n")
        print(f"Large files: WARN — {len(large_files)} file(s) > 5 MB")
    else:
        print("Large files: PASS")

    # --- 3. C-026 WORKTREE TASKS.MD GUARD (BLOCK) ---
    # Bucket agents in worktrees must never write TASKS.md directly (C-026).
    tasks_md_staged_check = [
        f
        for f in staged_files
        if re.search(r"\.gald3r[/\\]TASKS\.md$|^\.gald3r/TASKS\.md$", f, re.IGNORECASE)
    ]
    if tasks_md_staged_check:
        worktree_list = run_git(["worktree", "list"]).splitlines()
        # BUG-538: `git worktree list` always lists the primary/main working
        # tree FIRST, followed by any linked worktrees (see git-worktree(1))
        # -- anchor on that ordering guarantee instead of pattern-matching a
        # branch name. The prior `[HEAD]|[main]|[dev]` search silently
        # failed to identify the primary worktree whenever it was checked
        # out on any other branch name, which defaulted `primary_norm` to
        # `cwd_norm` and disabled the guard entirely for that case.
        primary_worktree = worktree_list[0] if worktree_list else None
        cwd_norm = str(Path.cwd().resolve()).rstrip("\\/")
        primary_norm = (
            re.split(r"\s+", primary_worktree)[0].rstrip("\\/")
            if primary_worktree
            else cwd_norm
        )

        # BUG-532: `git worktree list` output always uses forward slashes
        # while Path.cwd().resolve() is backslash-separated on Windows, so
        # a raw casefold() equality comparison could NEVER match even when
        # the commit genuinely runs from the primary checkout -- every
        # coordinator reconciliation commit from the real primary checkout
        # was falsely BLOCKED whenever any worktrees were registered.
        # Compare separator-normalized forms for the primary-checkout
        # equality check so it is OS-agnostic.
        cwd_slash = cwd_norm.replace("\\", "/")
        primary_slash = primary_norm.replace("\\", "/")

        # BUG-538: the old fallback searched for a cwd match against ANY
        # bracketed line in `worktree_list` -- but EVERY worktree entry
        # (including genuine bucket/non-primary worktrees) carries its own
        # `[branch]` bracket, so a bucket worktree's cwd matched its OWN
        # entry just as readily as the primary checkout matched its own
        # entry. That silently defeated the block for genuine
        # non-primary-worktree commits on any platform/path combination
        # where separators happened to align between `cwd_norm` and the
        # `git worktree list` text (e.g. non-Windows, where both are
        # already forward-slash). Restrict the fallback to the SINGLE
        # primary-worktree line (`worktree_list[0]`) so it can only ever
        # confirm "cwd IS the primary checkout", never "cwd is *a*
        # worktree" (which is trivially true for every worktree, primary
        # or not).
        cwd_is_primary_line = bool(
            primary_worktree
            and "[" in primary_worktree
            and re.search(re.escape(cwd_norm), primary_worktree, re.IGNORECASE)
        )

        in_non_primary_worktree = (
            len(worktree_list) > 1
            and cwd_slash.casefold() != primary_slash.casefold()
            and not cwd_is_primary_line
        )

        if in_non_primary_worktree:
            print()
            print("BLOCK: C-026 — TASKS.md is coordinator-owned.")
            print("  Bucket agents in worktrees must NOT write .gald3r/TASKS.md.")
            print("  Write your individual task file only (tasks/open/task{id}_*.md).")
            print("  The coordinator writes TASKS.md at reconciliation time.")
            print("  See .gald3r/CONSTRAINTS.md C-026 for details.")
            if bypass:
                warns.append(
                    "C-026 BYPASS: TASKS.md written from worktree — coordinator must reconcile."
                )
                print("  BYPASS active — proceeding with warning.")
            else:
                block = True

    # --- 3. gald3r SYNC DRIFT CHECK (WARN) ---
    if Path(".gald3r").exists():
        tasks_md_staged = [f for f in staged_files if re.search(r"TASKS\.md", f, re.IGNORECASE)]
        task_files_staged = [
            f for f in staged_files if re.search(r"\.gald3r[/\\]tasks[/\\]", f, re.IGNORECASE)
        ]

        if tasks_md_staged and not task_files_staged:
            warns.append(
                "WARN: .gald3r/TASKS.md is staged but no tasks/ files are staged. Run @g-task-sync-check."
            )
            print("gald3r sync: WARN — TASKS.md staged without tasks/ files")
        elif task_files_staged and not tasks_md_staged:
            warns.append(
                "WARN: tasks/ files staged but .gald3r/TASKS.md is not. Run @g-task-sync-check."
            )
            print("gald3r sync: WARN — tasks/ files staged without TASKS.md")
        else:
            print("gald3r sync: PASS")
    else:
        print("gald3r sync: SKIP (no .gald3r/ in this repo)")

    # --- 4. PROTECTED FILES ALLOWLIST (BLOCK) ---
    # Enforces g-rl-02 § "Protected Files". BUG-401: two classes now --
    # UNCONDITIONAL (.env/.mcp.json — genuine secrets, always blocked) and
    # COORDINATION_DIR_PATTERNS (.gald3r/, .claude/, CLAUDE.md, etc. — only
    # blocked when git_check_ignore() confirms THIS repo's own .gitignore
    # excludes the path, i.e. real drift, not intentional per-repo tracking).
    protected_hits = []
    coordination_candidates = []  # list of (staged_path, rel_path, pattern)
    for f in staged_files:
        rel = f.replace("\\", "/")
        matched_unconditional = False
        for pat in UNCONDITIONAL_PROTECTED_PATTERNS:
            if re.search(pat, rel, re.IGNORECASE):
                protected_hits.append(f"  {rel}  (matches /{pat}/)")
                matched_unconditional = True
                break
        if matched_unconditional:
            continue
        for pat in COORDINATION_DIR_PATTERNS:
            if re.search(pat, rel, re.IGNORECASE):
                coordination_candidates.append((f, rel, pat))
                break

    if coordination_candidates:
        ignored = git_check_ignore([f for f, _rel, _pat in coordination_candidates])
        for f, rel, pat in coordination_candidates:
            if f in ignored or rel in ignored:
                protected_hits.append(
                    f"  {rel}  (matches /{pat}/ AND this repo's .gitignore "
                    f"excludes it -- force-staged drift)"
                )

    if protected_hits:
        print(
            f"Protected files: BLOCK — {len(protected_hits)} staged path(s) match the Protected Files allowlist:"
        )
        for h in protected_hits:
            print(h)
        print(
            "  -> Unstage with: git reset HEAD <file>. See .claude/rules/g-rl-02-git_workflow.md § 'Protected Files'."
        )
        block = True
    else:
        print("Protected files: PASS")

    # --- 5. STUB / TODO ANNOTATION (BLOCK) ---
    # Enforces g-rl-34 — bare TODO/FIXME/NotImplementedError in staged added
    # lines must carry the TODO[TASK-X->TASK-Y] annotation (here or +/- 2 lines).
    stub_hits = []
    if diff:
        current_file = ""
        for i, line in enumerate(diff_lines):
            m = re.match(r"^\+\+\+\s+b/(.+)$", line)
            if m:
                current_file = m.group(1)
                continue
            if line.startswith("+") and not line.startswith("+++"):
                for pat in STUB_BLOCK_PATTERNS:
                    if re.search(pat, line, re.IGNORECASE):
                        # Check if THIS line already carries the annotation.
                        if ANNOTATION_REGEX.search(line):
                            continue
                        # Look at +/- 2 lines for the annotation on the same hunk.
                        has_annotation = False
                        for j in range(max(0, i - 2), min(len(diff_lines) - 1, i + 2) + 1):
                            if j == i:
                                continue
                            if ANNOTATION_REGEX.search(diff_lines[j]):
                                has_annotation = True
                                break
                        if not has_annotation:
                            trimmed = line[1:].rstrip()
                            if len(trimmed) > 100:
                                trimmed = trimmed[:100] + "…"
                            stub_hits.append(f"  {current_file}: {trimmed}")
                        break
    if stub_hits:
        print(
            f"Stub annotation: BLOCK — {len(stub_hits)} bare TODO/NotImplementedError without TODO[TASK-X->TASK-Y] form:"
        )
        for h in stub_hits[:10]:
            print(h)
        if len(stub_hits) > 10:
            print(f"  ... and {len(stub_hits) - 10} more")
        print("  -> Annotate each stub: TODO[TASK-<current>->TASK-<followup>]: <description>")
        print("     See .claude/rules/g-rl-34-todo_completion_gate.md.")
        block = True
    else:
        print("Stub annotation: PASS")

    # --- 6. .gald3r VALIDATION GATE (BLOCK) — T520/T299 ---
    # Run the native `gald3r validate` verb (T299 -- replaces the earlier direct
    # `gald3r.core.Gald3r` engine import, which made this hook import the vendored
    # .gald3r_sys/engine package the T292 retirement plan deletes) on staged task/bug
    # files: schema, status vocabulary, and folder placement. --strict additionally
    # enforces required-field presence, matching the old engine-backed gate's always-on
    # behavior (its `gald3r.schema.task`/`bugs._validate` checked required fields
    # unconditionally, with no opt-in flag). Shells out via the same PATH-first
    # `engine_cmd` resolver section 7 (below) uses -- ENFORCES what g-rl-34/35/38 advise.
    staged_gald3r = [
        f for f in staged_files
        if re.search(r"\.gald3r[/\\](tasks|bugs)[/\\].*\.md$", f.replace("\\", "/"), re.IGNORECASE)
    ]
    if staged_gald3r:
        if engine_cmd is None:
            warns.append("WARN: staged .gald3r task/bug files but the gald3r engine isn't resolvable — validation skipped.")
            print("validate gate: SKIP (engine not resolvable)")
        else:
            try:
                abs_paths = [str((Path(repo_root) / f)) for f in staged_gald3r]
                proc = subprocess.run(
                    [*engine_cmd, "validate", "--json", "--strict", "--root", repo_root, *abs_paths],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                rep = json.loads(proc.stdout.strip() or "{}")
                if "ok" not in rep:
                    raise ValueError(f"unexpected `gald3r validate` output (exit {proc.returncode})")
                if rep["ok"]:
                    print(f"validate gate: PASS ({rep.get('checked', 0)} staged file(s))")
                else:
                    print(f"validate gate: BLOCK — {rep.get('errors', 0)} error(s), "
                          f"{rep.get('fixable', 0)} fixable in staged .gald3r files:")
                    shown = [
                        v for v in rep.get("violations", []) if v.get("kind") in ("error", "fixable")
                    ]
                    for v in shown[:10]:
                        print(f"  [{v['kind']}] {v['file']}: {v['message']}")
                    if len(shown) > 10:
                        print(f"  ... and {len(shown) - 10} more")
                    print("  -> run `gald3r validate --fix` for fixable items, then repair errors.")
                    block = True
            except Exception as e:
                warns.append(f"WARN: validate gate errored ({e.__class__.__name__}); skipped.")
                print("validate gate: SKIP (validator error)")

    # --- 7. ORG POLICY-AS-CODE GUARDRAIL (BLOCK) — T1611 ---
    # Deterministic CHECK op against the active org policy bundle (g-skl-policy).
    # No-ops on free/retail installs (no org tier / no rules) — never fixed inline
    # unless the fix is 1-3 lines and zero-risk per g-rl-38; enforcement is by code.
    if engine_cmd is None:
        print("org policy: SKIP (gald3r engine not installed)")
    else:
        try:
            event = {
                "hook_event_name": "pre-commit",
                "staged_files": "\n".join(staged_files),
                "diff": diff,
            }
            # `gald3r policy check` reads the event JSON from STDIN and emits the
            # verdict object on stdout. --exit-zero keeps a `block` verdict from
            # raising exit 2 so we branch on the parsed JSON instead.
            proc = subprocess.run(
                [*engine_cmd, "policy", "check", "--json", "--exit-zero", "--root", repo_root],
                input=json.dumps(event),
                capture_output=True,
                text=True,
                timeout=15,
            )
            result = json.loads(proc.stdout.strip() or "{}")
            if result.get("verdict") == "block":
                print(f"org policy: BLOCK — {result.get('message')}")
                print("  -> Fix the violation, or confirm with an org admin, before committing.")
                block = True
            elif result.get("verdict") == "warn":
                warns.append(f"WARN: org policy — {result.get('message')}")
                print("org policy: WARN")
            else:
                print("org policy: PASS")
        except Exception as e:
            warns.append(f"WARN: org policy check errored ({e.__class__.__name__}); skipped.")
            print("org policy: SKIP (engine error)")

    print()

    # --- RESULT ---
    if block:
        if bypass:
            print(
                "Pre-commit check: BLOCK conditions found, but BYPASS is active — commit will proceed."
            )
            print()
            return 0
        print("Pre-commit check: BLOCKED — fix issues above before committing.")
        print()
        return 1

    if warns:
        print("Pre-commit check: WARNINGS (commit will proceed)")
        for w in warns:
            print(w)
        print()
        return 0

    print("Pre-commit check: ALL PASS")
    print()
    return 0


if __name__ == "__main__":
    try:
        # Never crash on console encodings that can't render em-dash etc.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:
        # Hooks must never crash the host session; an unexpected failure in
        # the checker itself must not block commits (matches the .ps1's
        # $ErrorActionPreference = "SilentlyContinue" posture).
        sys.exit(0)
