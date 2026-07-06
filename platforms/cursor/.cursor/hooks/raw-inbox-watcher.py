#!/usr/bin/env python3
"""Python port of raw-inbox-watcher.ps1 (T1584).

Vault Raw Inbox processor (Phase 2, manual trigger only). Scans {vault}/raw/
for dropped files, classifies each by extension/contents (rules-based, no
LLM — that lives in Phase 3), and routes to the appropriate vault
destination via the existing g-skl-ingest-* scripts. On success files move
to {vault}/raw/processed/YYYY-MM-DD/. On failure they move to
{vault}/raw/failed/ alongside an error.md sibling explaining the reason.

Phase 2 explicitly does NOT install a filesystem-watcher service. Since
T1627 (WS-A-4) it is registered on the canonical `stop` event with
`--hook-mode` (`g_hk_core.py` CONCERN_CHAIN["stop"], Claude `settings.json`
`hooks.Stop`, Cursor `hooks.json` `stop`), so the inbox is processed (or its
items flagged into raw/failed/) at the end of every agent turn. It remains
invocable manually via @g-vault-process-inbox or directly:

  python .claude/hooks/raw-inbox-watcher.py
  python .claude/hooks/raw-inbox-watcher.py -DryRun
  python .claude/hooks/raw-inbox-watcher.py -Verbose

Re-running on an empty raw/ is a no-op. Vault path resolution is a native
port of g-hk-vault-resolve.ps1 (which the PS1 dot-sources).

Exit codes: 0 = success or no work, 1 = unrecoverable error, 2 = some
failures or deferred files. In --hook-mode (lifecycle registration) the
exit code is ALWAYS 0 — failures are still moved/flagged and summarized,
but a lifecycle hook must never block or crash the host session.
"""
# @subsystems: WORKSPACE_COORDINATION
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hook_common  # noqa: E402,F401

SCRIPT_DIR = Path(__file__).resolve().parent

# Same (intentionally replicated) path filter as g-hk-vault-resolve.ps1's
# Get-MarkdownCount.
OBSIDIAN_FILTER = re.compile(r"\\.obsidian(\|\\)")

VERBOSE = False


def verbose(msg):
    if VERBOSE:
        print("VERBOSE: %s" % msg, file=sys.stderr)


def warn(msg):
    print("WARNING: %s" % msg, file=sys.stderr)


# ── Vault path resolution (native port of g-hk-vault-resolve.ps1) ───────────

def _parse_identity(path):
    identity = {
        "project_id": "", "project_name": "", "user_id": "", "user_name": "",
        "gald3r_version": "", "vault_location": "", "repos_location": "",
    }
    try:
        if path.is_file():
            for line in path.read_text(encoding="utf-8",
                                       errors="replace").splitlines():
                m = re.match(r"^(\w+)=(.*)$", line)
                if m:
                    identity[m.group(1)] = m.group(2).strip()
    except OSError:
        pass
    return identity


def _env_setting(env_path, keys):
    if not env_path.is_file():
        return None
    try:
        lines = env_path.read_text(encoding="utf-8",
                                   errors="replace").splitlines()
    except OSError:
        return None
    for key in keys:
        pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=\s*(.+)$")
        for line in lines:
            m = pattern.match(line)
            if m:
                value = m.group(1).strip().strip('"').strip("'")
                if value:
                    return value
                break  # first match per key only; empty value -> next key
    return None


def _path_writable(path_str):
    try:
        p = Path(path_str)
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".gald3r_write_probe.tmp"
        probe.write_text("", encoding="utf-8")
        try:
            probe.unlink()
        except OSError:
            pass
        return True
    except OSError:
        return False


def _markdown_count(path):
    if not path.is_dir():
        return 0
    count = 0
    try:
        for p in path.rglob("*.md"):
            if OBSIDIAN_FILTER.search(str(p)):
                continue
            if p.is_file():
                count += 1
    except OSError:
        pass
    return count


def resolve_vault_path(project_root):
    """Resolve the active vault path (port of g-hk-vault-resolve.ps1).

    Side effects mirror the dot-sourced PS1: local vault/repos dirs and the
    per-project vault subtree are created.
    """
    identity = _parse_identity(project_root / ".gald3r" / ".identity")
    env_path = project_root / ".env"
    vault_local = project_root / ".gald3r" / "vault"
    repos_local = project_root / ".gald3r" / "repos"

    vault_location = identity.get("vault_location") or _env_setting(
        env_path, ["GALD3R_VAULT_LOCATION", "GALD3R_KNOWLEDGE_WELL_PATH"])
    repos_location = identity.get("repos_location") or _env_setting(
        env_path, ["GALD3R_REPOS_LOCATION"])

    if not vault_location or vault_location == "{LOCAL}":
        vault_path = vault_local
    elif _path_writable(vault_location):
        vault_path = Path(vault_location)
    else:
        vault_path = vault_local

    if not repos_location or repos_location == "{LOCAL}":
        repos_path = repos_local
    elif _path_writable(repos_location):
        repos_path = Path(repos_location)
    else:
        repos_path = repos_local

    for p in (vault_local, repos_local, vault_path, repos_path):
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    project_name = identity.get("project_name")
    if not project_name or project_name == "{project_name}":
        project_name = project_root.name
    project_dir = vault_path / "projects" / project_name
    for p in (project_dir, project_dir / "sessions", project_dir / "decisions"):
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    return vault_path


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_ingest_script(relative_path):
    """Walk up from cwd (max 8 levels) looking for relative_path."""
    current = Path.cwd()
    for _ in range(8):
        candidate = current / relative_path
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def classify_file(file_path):
    """Rules-based classification by extension/contents."""
    ext = file_path.suffix.lower()

    if ext == ".md":
        return {"kind": "markdown", "reason": "markdown article"}
    if ext == ".txt":
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if content == "":
                # Parity: Get-Content -Raw returns $null for an empty file,
                # so the PS1 classifies it unreadable.
                raise OSError("empty file")
            content = content.strip()
        except OSError as exc:
            return {"kind": "unreadable",
                    "reason": "could not read text body: %s" % exc}
        lines = [l for l in re.split(r"\r?\n", content) if l.strip() != ""]
        if len(lines) == 1 and re.match(r"^https?://", lines[0]):
            url = lines[0].strip()
            if re.search(r"youtube\.com|youtu\.be", url):
                return {"kind": "youtube_url", "reason": "single YouTube URL",
                        "url": url}
            return {"kind": "single_url", "reason": "single URL", "url": url}
        return {"kind": "text_article", "reason": "multi-line text article"}
    if ext == ".pdf":
        return {"kind": "deferred_phase3",
                "reason": "PDF requires Phase 3 (LLM + extractor)"}
    if ext in (".png", ".jpg", ".jpeg"):
        return {"kind": "deferred_phase3",
                "reason": "Image requires Phase 3 (vision classifier)"}
    return {"kind": "unknown", "reason": "no rule for extension '%s'" % ext}


def main():
    global VERBOSE

    parser = argparse.ArgumentParser(
        description="Vault Raw Inbox processor (Python port of "
                    "raw-inbox-watcher.ps1)")
    parser.add_argument("-DryRun", "--dry-run", dest="dry_run",
                        action="store_true",
                        help="Report what would happen without moving or "
                             "writing anything.")
    parser.add_argument("-VaultPathOverride", "--vault-path-override",
                        dest="vault_path_override", default="",
                        help="Override vault path resolution.")
    parser.add_argument("-Verbose", "--verbose", dest="verbose",
                        action="store_true",
                        help="Print per-file classification details.")
    parser.add_argument("-HookMode", "--hook-mode", dest="hook_mode",
                        action="store_true",
                        help="Lifecycle-hook mode (T1627, stop chain): always "
                             "exit 0 so the host session is never blocked; "
                             "failures are still moved to raw/failed/ and "
                             "flagged with an error.md sibling.")
    args, _unknown = parser.parse_known_args()
    dry_run = args.dry_run
    VERBOSE = args.verbose

    # ── Vault path resolution ────────────────────────────────────────────────
    if args.vault_path_override:
        vault_path = Path(args.vault_path_override)
    else:
        vault_path = resolve_vault_path(Path.cwd())

    if not vault_path.exists():
        print("raw-inbox-watcher: vault path '%s' does not exist — nothing "
              "to do." % vault_path)
        return 0

    raw_dir = vault_path / "raw"
    today = datetime.now().strftime("%Y-%m-%d")
    processed_dir = raw_dir / "processed" / today
    failed_dir = raw_dir / "failed"

    if not raw_dir.exists():
        print("raw-inbox-watcher: %s does not exist — nothing to do." % raw_dir)
        return 0

    # ── Idempotent no-op on empty inbox ──────────────────────────────────────
    candidates = [p for p in raw_dir.iterdir()
                  if p.is_file() and p.name != "README.md"]

    if not candidates:
        print("raw-inbox-watcher: inbox empty — no work.")
        return 0

    if not dry_run:
        processed_dir.mkdir(parents=True, exist_ok=True)
        failed_dir.mkdir(parents=True, exist_ok=True)

    def move_to_processed(file_path):
        if dry_run:
            return True
        try:
            dest = processed_dir / file_path.name
            if dest.exists():
                stamp = datetime.now().strftime("%H%M%S")
                dest = processed_dir / ("%s_%s%s" % (file_path.stem, stamp,
                                                     file_path.suffix))
            if dest.exists():
                dest.unlink()  # Move-Item -Force parity
            shutil.move(str(file_path), str(dest))
            return True
        except OSError as exc:
            warn("raw-inbox-watcher: could not move %s to processed/: %s"
                 % (file_path.name, exc))
            return False

    def move_to_failed(file_path, reason):
        if dry_run:
            return
        try:
            dest = failed_dir / file_path.name
            if dest.exists():
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = failed_dir / ("%s_%s%s" % (file_path.stem, stamp,
                                                  file_path.suffix))
            if dest.exists():
                dest.unlink()  # Move-Item -Force parity
            shutil.move(str(file_path), str(dest))
            error_md = Path(str(dest) + ".error.md")
            body = (
                "# raw-inbox-watcher failure\n"
                "\n"
                "- **File**: %s\n"
                "- **Date**: %s\n"
                "- **Reason**: %s\n"
                "\n"
                "This file was moved to `raw/failed/` because the Phase 2 "
                "watcher could not\n"
                "route it. To retry, move the file back into `vault/raw/` "
                "and re-run\n"
                "`@g-vault-process-inbox` (or pwsh "
                ".cursor/hooks/raw-inbox-watcher.ps1)."
                % (file_path.name,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reason)
            )
            error_md.write_text(body, encoding="utf-8")  # -NoNewline parity
        except OSError as exc:
            warn("raw-inbox-watcher: could not move %s to failed/: %s"
                 % (file_path.name, exc))

    def add_vault_log_entry(processed, failed, deferred, routed):
        log_path = vault_path / "log.md"
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        body = (
            "\n## %s — raw-inbox-watcher run\n"
            "- Inbox files seen: %d\n"
            "- Processed: %d\n"
            "- Failed: %d\n"
            "- Deferred to Phase 3: %d\n"
            "- Routes invoked: %s"
            % (stamp, len(candidates), processed, failed, deferred,
               ", ".join(routed))
        )
        if dry_run:
            return
        try:
            if not log_path.exists():
                log_path.write_text("# Vault Activity Log\n\n",
                                    encoding="utf-8")
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(body + "\n")
        except OSError as exc:
            warn("raw-inbox-watcher: could not append to vault log.md: %s"
                 % exc)

    def run_python(script, script_args):
        """Run an ingest/classifier python script; returns (rc, output)."""
        res = subprocess.run([sys.executable, str(script)] + script_args,
                             capture_output=True, text=True)
        output = (res.stdout or "") + (res.stderr or "")
        return res.returncode, output

    # ── Process each candidate ───────────────────────────────────────────────
    processed_count = 0
    failed_count = 0
    deferred_count = 0
    routes_used = []

    for file_path in candidates:
        cls = classify_file(file_path)
        verbose("raw-inbox-watcher: %s -> %s (%s)"
                % (file_path.name, cls["kind"], cls["reason"]))

        kind = cls["kind"]

        if kind == "markdown":
            articles_dir = vault_path / "research" / "articles"
            if not articles_dir.exists() and not dry_run:
                articles_dir.mkdir(parents=True, exist_ok=True)
            dest = articles_dir / file_path.name
            if dry_run:
                print("[dry-run] would route markdown %s -> %s"
                      % (file_path.name, dest))
            else:
                try:
                    shutil.copy2(str(file_path), str(dest))
                    if move_to_processed(file_path):
                        processed_count += 1
                        routes_used.append("markdown->articles")
                    else:
                        failed_count += 1
                except OSError as exc:
                    move_to_failed(file_path, "Markdown copy failed: %s" % exc)
                    failed_count += 1

        elif kind == "single_url":
            script = find_ingest_script(
                ".cursor/skills/g-skl-ingest-url/scripts/ingest_url.py")
            if not script:
                move_to_failed(file_path, "ingest_url.py not found")
                failed_count += 1
                continue
            if dry_run:
                print("[dry-run] would invoke g-skl-ingest-url for %s"
                      % cls["url"])
                continue
            try:
                rc, _out = run_python(script, ["--url", cls["url"],
                                               "--vault-path", str(vault_path)])
                if rc == 0:
                    if move_to_processed(file_path):
                        processed_count += 1
                        routes_used.append("url->ingest_url")
                    else:
                        failed_count += 1
                else:
                    move_to_failed(file_path,
                                   "ingest_url.py exited with code %d" % rc)
                    failed_count += 1
            except (OSError, subprocess.SubprocessError) as exc:
                move_to_failed(file_path,
                               "ingest_url invocation failed: %s" % exc)
                failed_count += 1

        elif kind == "youtube_url":
            script = find_ingest_script(
                ".cursor/skills/g-skl-ingest-youtube/scripts/"
                "fetch_transcript.py")
            if not script:
                script = find_ingest_script(
                    "<ECOSYSTEM_ROOT>/<template_full>/.cursor/skills/"
                    "g-skl-ingest-youtube/scripts/fetch_transcript.py")
            if not script:
                move_to_failed(file_path,
                               "fetch_transcript.py not found in any IDE "
                               "skill tree — invoke g-skl-ingest-youtube "
                               "manually")
                failed_count += 1
                continue
            if dry_run:
                print("[dry-run] would invoke g-skl-ingest-youtube for %s"
                      % cls["url"])
                continue
            try:
                rc, _out = run_python(script, ["--url", cls["url"],
                                               "--vault-path", str(vault_path)])
                if rc == 0:
                    if move_to_processed(file_path):
                        processed_count += 1
                        routes_used.append("url->ingest_youtube")
                    else:
                        failed_count += 1
                else:
                    move_to_failed(file_path,
                                   "ingest_youtube.py exited with code %d" % rc)
                    failed_count += 1
            except (OSError, subprocess.SubprocessError) as exc:
                move_to_failed(file_path,
                               "ingest_youtube invocation failed: %s" % exc)
                failed_count += 1

        elif kind == "text_article":
            articles_dir = vault_path / "research" / "articles"
            if not articles_dir.exists() and not dry_run:
                articles_dir.mkdir(parents=True, exist_ok=True)
            base = file_path.stem
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", base).lower().strip("-")
            if not slug:
                slug = "raw-text-%s" % datetime.now().strftime("%Y%m%d%H%M%S")
            dest = articles_dir / ("%s_%s.md" % (today, slug))
            if dry_run:
                print("[dry-run] would wrap text %s -> %s"
                      % (file_path.name, dest))
                continue
            try:
                body = file_path.read_text(encoding="utf-8", errors="replace")
                frontmatter = (
                    "---\n"
                    "date: %s\n"
                    "type: article\n"
                    "ingestion_type: raw_inbox_text\n"
                    "source: raw_inbox/%s\n"
                    "title: \"%s\"\n"
                    "tags: [raw_inbox, text_article]\n"
                    "---\n"
                    "\n"
                    "%s" % (today, file_path.name, base, body)
                )
                dest.write_text(frontmatter, encoding="utf-8")  # -NoNewline
                if move_to_processed(file_path):
                    processed_count += 1
                    routes_used.append("text->articles")
                else:
                    failed_count += 1
            except OSError as exc:
                move_to_failed(file_path, "Text wrap failed: %s" % exc)
                failed_count += 1

        elif kind == "deferred_phase3":
            # Phase 3: attempt LLM/vision classification via
            # raw_inbox_classifier.py
            classifier_script = find_ingest_script(
                ".cursor/skills/g-skl-vault/scripts/raw_inbox_classifier.py")
            if not classifier_script:
                if dry_run:
                    print("[dry-run] no classifier script found; would defer "
                          "%s" % file_path.name)
                else:
                    move_to_failed(file_path,
                                   "Phase 3 classifier script not found (%s)"
                                   % cls["reason"])
                    deferred_count += 1
                continue
            if dry_run:
                print("[dry-run] would invoke Phase 3 classifier for %s"
                      % file_path.name)
                continue
            try:
                rc, output = run_python(classifier_script,
                                        ["--file", str(file_path),
                                         "--vault-path", str(vault_path)])
                verbose(output)
                if rc == 0:
                    if move_to_processed(file_path):
                        processed_count += 1
                        routes_used.append("phase3->classified")
                    else:
                        failed_count += 1
                elif rc == 2:
                    print("raw-inbox-watcher: LOW CONFIDENCE - %s left in "
                          "raw/ for human review" % file_path.name)
                    print(output)
                    deferred_count += 1
                elif rc == 3:
                    move_to_failed(file_path,
                                   "Sensitive content detected by Phase 3 "
                                   "classifier")
                    failed_count += 1
                else:
                    move_to_failed(file_path,
                                   "Phase 3 classifier exited with code %d"
                                   % rc)
                    failed_count += 1
            except (OSError, subprocess.SubprocessError) as exc:
                move_to_failed(file_path,
                               "Phase 3 classifier invocation failed: %s" % exc)
                failed_count += 1

        elif kind == "unreadable":
            if dry_run:
                print("[dry-run] would mark unreadable: %s" % file_path.name)
                continue
            move_to_failed(file_path, cls["reason"])
            failed_count += 1

        elif kind == "unknown":
            if dry_run:
                print("[dry-run] unknown extension: %s (%s)"
                      % (file_path.name, cls["reason"]))
                continue
            move_to_failed(file_path, cls["reason"])
            failed_count += 1

    routes_used = list(dict.fromkeys(routes_used))
    add_vault_log_entry(processed_count, failed_count, deferred_count,
                        routes_used)

    summary = ("raw-inbox-watcher: seen=%d processed=%d failed=%d deferred=%d"
               % (len(candidates), processed_count, failed_count,
                  deferred_count))
    if dry_run:
        summary += " (dry-run)"
    print(summary)

    # Exit codes: 0 = success or no work, 1 = unrecoverable error,
    # 2 = some failures. Hook mode (T1627): a lifecycle hook must never
    # block the host session, so the exit code is always 0 there.
    if (failed_count > 0 or deferred_count > 0) and not args.hook_mode:
        return 2
    return 0


if __name__ == "__main__":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        # Parity with $ErrorActionPreference = "Stop": unrecoverable -> 1.
        # In hook mode a lifecycle hook must never crash the host session
        # (T1627), so even unrecoverable errors exit 0 there.
        print("raw-inbox-watcher: unrecoverable error: %s" % exc,
              file=sys.stderr)
        if "--hook-mode" in sys.argv or "-HookMode" in sys.argv:
            sys.exit(0)
        sys.exit(1)
