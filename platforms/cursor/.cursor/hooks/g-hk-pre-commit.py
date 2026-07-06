#!/usr/bin/env python3
"""Python port of g-hk-pre-commit.ps1 (T1584).

gald3r pre-commit sanity hook (opt-in). Checks staged changes for:
secrets (BLOCK), staged .env files (BLOCK), large files >5 MB (WARN),
C-026 worktree TASKS.md writes (BLOCK), gald3r task sync drift (WARN),
protected files per g-rl-02 (BLOCK), and bare stubs/TODOs without the
TODO[TASK-X->TASK-Y] annotation per g-rl-34 (BLOCK).

Exit 1 = BLOCK (commit halted). Exit 0 = ALLOW or WARN (commit proceeds).
GALD3R_HOOK_BYPASS=1 downgrades BLOCK to WARN (T600 §3.3 override path).
-BlockOnFailure is accepted but is a no-op because the exit-code semantics
already match the T600 B-4 contract (same as the .ps1 original).
"""
# @subsystems: SECURITY_AND_COMPLIANCE
from __future__ import annotations

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

PROTECTED_PATTERNS = [
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
    r"^\.env(\..*)?$",
    r"^\.mcp\.json$",
]

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


def load_engine(repo_root: str):
    """Return the gald3r `Gald3r` class if the engine is importable, else None.

    Tries the ambient import first, then the installed engine source at
    `<repo>/.gald3r_sys/engine/src`. Returns None (so the validation gate degrades to a
    skip/WARN, never blocking) when the engine or its deps aren't available."""
    try:
        from gald3r.core import Gald3r  # type: ignore
        return Gald3r
    except Exception:
        pass
    src = Path(repo_root) / ".gald3r_sys" / "engine" / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))
        try:
            from gald3r.core import Gald3r  # type: ignore
            return Gald3r
        except Exception:
            return None
    return None


def resolve_engine_cmd(repo_root: str):
    """Resolve the gald3r engine command prefix via the zero-IP resolver (A6/T1663).

    The org policy CHECK op was absorbed from g-skl-policy's `policy_engine.py`
    into the `gald3r policy check` verb. Returns the command prefix
    (e.g. ``["gald3r"]``) or ``None`` (skip, never block) when the resolver is
    not shipped or no engine can be found."""
    resolver = Path(repo_root) / ".gald3r_sys" / "scripts" / "gald3r_bin.py"
    if not resolver.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("gald3r_bin_precommit", str(resolver))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return mod.resolve_engine_cmd(Path(repo_root))
    except Exception:
        return None
    return None


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

    block = False
    warns = []

    print()
    print("gald3r pre-commit sanity check")
    print("=============================")

    # --- 1. SECRETS CHECK (BLOCK) ---
    diff = run_git(["diff", "--cached"])
    diff_lines = re.split(r"\r?\n", diff) if diff else []
    secret_hits = []
    for pat in secret_patterns:
        try:
            rx = re.compile(pat, re.IGNORECASE)  # Select-String is case-insensitive
        except re.error:
            continue
        hits = ["  " + ln.strip() for ln in diff_lines if rx.search(ln)]
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
        primary_worktree = next(
            (
                ln
                for ln in worktree_list
                if re.search(r"\[HEAD\]|\[main\]|\[dev\]", ln, re.IGNORECASE)
            ),
            None,
        )
        cwd_norm = str(Path.cwd().resolve()).rstrip("\\/")
        primary_norm = (
            re.split(r"\s+", primary_worktree)[0].rstrip("\\/")
            if primary_worktree
            else cwd_norm
        )

        in_non_primary_worktree = (
            len(worktree_list) > 1
            and cwd_norm.casefold() != primary_norm.casefold()
            and not any(
                re.search(re.escape(cwd_norm), ln, re.IGNORECASE) and "[" in ln
                for ln in worktree_list
            )
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
    # Enforces g-rl-02 § "Protected Files" — never commit these even by mistake.
    protected_hits = []
    for f in staged_files:
        rel = f.replace("\\", "/")
        for pat in PROTECTED_PATTERNS:
            if re.search(pat, rel, re.IGNORECASE):
                protected_hits.append(f"  {rel}  (matches /{pat}/)")
                break
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

    # --- 6. .gald3r VALIDATION GATE (BLOCK) — T520 ---
    # Run the deterministic engine validator on staged task/bug files: schema, status
    # vocabulary, and folder placement. The engine ENFORCES what g-rl-34/35/38 advise.
    staged_gald3r = [
        f for f in staged_files
        if re.search(r"\.gald3r[/\\](tasks|bugs)[/\\].*\.md$", f.replace("\\", "/"), re.IGNORECASE)
    ]
    if staged_gald3r:
        Gald3r = load_engine(repo_root)
        if Gald3r is None:
            warns.append("WARN: staged .gald3r task/bug files but the engine isn't importable — validation skipped.")
            print("validate gate: SKIP (engine not importable)")
        else:
            try:
                g = Gald3r(root=repo_root)
                abs_paths = [str((Path(repo_root) / f)) for f in staged_gald3r]
                rep = g.validate.run(paths=abs_paths)
                if rep["ok"]:
                    print(f"validate gate: PASS ({rep['checked']} staged file(s))")
                else:
                    print(f"validate gate: BLOCK — {rep['errors']} error(s), "
                          f"{rep['fixable']} fixable in staged .gald3r files:")
                    shown = [v for v in rep["violations"] if v["kind"] in ("error", "fixable")]
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
    engine_cmd = resolve_engine_cmd(repo_root)
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
