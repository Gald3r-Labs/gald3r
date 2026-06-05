"""
github_sync.py

Standalone GitHub tracker adapted for gald3r.

- Mirrors raw repos and gists into repos_location
- Stores state in vault/projects/{project_name}/repo_tracker.json (falls back to .gald3r/ if no vault_location)
- Writes curated summary notes into the vault at research/github/
- Never puts raw upstream markdown inside the vault tree
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_classify import classify_entry, load_dotenv


GITHUB_API = "https://api.github.com"


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".gald3r").exists():
            return candidate
    raise RuntimeError("Could not locate project root with .gald3r/")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
GALD3R_DIR = PROJECT_ROOT / ".gald3r"
IDENTITY_PATH = GALD3R_DIR / ".identity"
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


def parse_key_value_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def resolve_storage_paths() -> tuple[Path, Path, str]:
    identity = parse_key_value_file(IDENTITY_PATH)
    project_name = identity.get("project_name", PROJECT_ROOT.name)

    vault_location = identity.get("vault_location") or os.environ.get("GALD3R_VAULT_LOCATION") or "{LOCAL}"
    repos_location = identity.get("repos_location") or os.environ.get("GALD3R_REPOS_LOCATION") or "{LOCAL}"

    vault_path = (GALD3R_DIR / "vault") if vault_location == "{LOCAL}" else Path(vault_location)
    repos_path = (GALD3R_DIR / "repos") if repos_location == "{LOCAL}" else Path(repos_location)

    vault_path.mkdir(parents=True, exist_ok=True)
    repos_path.mkdir(parents=True, exist_ok=True)
    return vault_path, repos_path, project_name


VAULT_PATH, REPOS_PATH, PROJECT_NAME = resolve_storage_paths()

# repos.txt and repo_tracker.json live in vault when vault_location is configured,
# otherwise fall back to .gald3r/ for local-only projects.
_tracking_dir = VAULT_PATH / "projects" / PROJECT_NAME
_tracking_dir.mkdir(parents=True, exist_ok=True)
_is_vault = not str(VAULT_PATH).startswith(str(GALD3R_DIR))
REPOS_LIST = (_tracking_dir / "repos.txt") if _is_vault else (GALD3R_DIR / "repos.txt")
TRACKER_PATH = (_tracking_dir / "repo_tracker.json") if _is_vault else (GALD3R_DIR / "repo_tracker.json")
VAULT_LOG_PATH = VAULT_PATH / "log.md"
GITHUB_NOTES_PATH = VAULT_PATH / "research" / "github"
GITHUB_NOTES_PATH.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "gald3r-github-sync/1.0",
}
if os.environ.get("GITHUB_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def api_get(url: str) -> dict[str, Any] | list[Any]:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def load_repo_list() -> list[str]:
    if not REPOS_LIST.exists():
        return []
    entries: list[str] = []
    seen: set[str] = set()
    for raw in REPOS_LIST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        normalized = normalize_slug(line)
        if normalized and normalized not in seen:
            seen.add(normalized)
            entries.append(normalized)
    return entries


def load_tracker() -> dict[str, Any]:
    if TRACKER_PATH.exists():
        data = json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
        data.setdefault("repos", {})
        return data
    return {"_comment": "Auto-managed by github_sync.py - do not edit manually", "repos": {}}


def save_tracker(data: dict[str, Any]) -> None:
    TRACKER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_slug(value: str) -> str:
    raw = value.strip().rstrip("/")
    if raw.startswith("https://github.com/"):
        parts = raw.removeprefix("https://github.com/").split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}".lower()
    if raw.startswith("https://gist.github.com/"):
        return f"gist:{raw.split('/')[-1]}"
    if raw.startswith("gist:"):
        return raw.lower()
    return raw.lower()


def tracker_slug_to_note(slug: str) -> str:
    if slug.startswith("gist:"):
        return f"gist__{slug.split(':', 1)[1]}"
    owner, repo = slug.split("/", 1)
    return f"{owner}__{repo}"


def append_log(operation: str, target: str, reason: str) -> None:
    VAULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not VAULT_LOG_PATH.exists():
        VAULT_LOG_PATH.write_text("# Vault Log\n", encoding="utf-8")
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    with VAULT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## {timestamp} | {operation} | {target}\n"
            f"- reason: {reason}\n"
        )


def extract_zip(zip_path: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        prefix = names[0].split("/")[0] + "/" if names else ""
        for member in names:
            stripped = member[len(prefix):] if member.startswith(prefix) else member
            if not stripped:
                continue
            target = destination / stripped
            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))


def get_repo_version(owner: str, repo: str) -> tuple[str, str, dict[str, Any], dict[str, Any] | None]:
    repo_info = api_get(f"{GITHUB_API}/repos/{owner}/{repo}")
    try:
        latest_release = api_get(f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            latest_release = None
        else:
            raise

    if latest_release:
        return latest_release["tag_name"], latest_release["tag_name"], repo_info, latest_release

    branch = repo_info["default_branch"]
    commit = api_get(f"{GITHUB_API}/repos/{owner}/{repo}/commits/{branch}")
    return commit["sha"][:12], commit["sha"], repo_info, None


def sync_repo(slug: str, tracker_entry: dict[str, Any], force: bool = False, dry_run: bool = False) -> str:
    owner, repo = slug.split("/", 1)
    version_label, ref, repo_info, release = get_repo_version(owner, repo)

    tracker_entry.update(
        {
            "last_checked": now_iso(),
            "latest_version": version_label,
            "repo_url": f"https://github.com/{slug}",
            "description": repo_info.get("description") or "",
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "watchers": repo_info.get("subscribers_count", 0),
            "open_issues": repo_info.get("open_issues_count", 0),
            "gh_language": repo_info.get("language") or "",
            "tags": repo_info.get("topics", []),
            "created_at": repo_info.get("created_at", ""),
            "published_at": release.get("published_at", "") if release else "",
        }
    )

    current_version = tracker_entry.get("downloaded_version")
    if not force and current_version == version_label:
        return f"up-to-date ({version_label})"
    if dry_run:
        return f"would update -> {version_label}"

    zip_path = REPOS_PATH / f"{owner}__{repo}.zip"
    repo_dir = REPOS_PATH / f"{owner}__{repo}"
    download_file(f"{GITHUB_API}/repos/{owner}/{repo}/zipball/{ref}", zip_path)
    extract_zip(zip_path, repo_dir)
    zip_path.unlink(missing_ok=True)

    tracker_entry["downloaded_version"] = version_label
    tracker_entry["downloaded_at"] = now_iso()
    tracker_entry["local_path"] = str(repo_dir)
    return f"updated -> {version_label}"


def sync_gist(slug: str, tracker_entry: dict[str, Any], force: bool = False, dry_run: bool = False) -> str:
    gist_id = slug.split(":", 1)[1]
    gist_info = api_get(f"{GITHUB_API}/gists/{gist_id}")
    history = gist_info.get("history", [])
    version_label = history[0]["version"][:12] if history else gist_info.get("updated_at", "unknown")

    tracker_entry.update(
        {
            "last_checked": now_iso(),
            "latest_version": version_label,
            "repo_url": gist_info.get("html_url", f"https://gist.github.com/{gist_id}"),
            "description": gist_info.get("description", ""),
            "gh_language": "Mixed",
            "tags": ["gist"],
            "published_at": gist_info.get("updated_at", ""),
        }
    )

    current_version = tracker_entry.get("downloaded_version")
    if not force and current_version == version_label:
        return f"up-to-date ({version_label})"
    if dry_run:
        return f"would update -> {version_label}"

    gist_dir = REPOS_PATH / f"gist__{gist_id}"
    if gist_dir.exists():
        shutil.rmtree(gist_dir)
    gist_dir.mkdir(parents=True, exist_ok=True)
    for filename, file_info in gist_info.get("files", {}).items():
        raw_url = file_info.get("raw_url")
        if raw_url:
            download_file(raw_url, gist_dir / filename)

    tracker_entry["downloaded_version"] = version_label
    tracker_entry["downloaded_at"] = now_iso()
    tracker_entry["local_path"] = str(gist_dir)
    return f"updated -> {version_label}"


def build_note(slug: str, entry: dict[str, Any], classification: dict[str, Any]) -> str:
    note_slug = tracker_slug_to_note(slug)
    title = slug
    related_tags = classification.get("tags", [])
    all_tags: list[str] = ["github"]
    for t in related_tags:
        if not isinstance(t, str):
            continue
        nt = t.strip().lower().replace(" ", "-").replace("_", "-")
        if nt and nt not in all_tags:
            all_tags.append(nt)
        if len(all_tags) >= 10:
            break
    tags_yaml = json.dumps(all_tags)

    update_section = ""
    if entry.get("latest_version"):
        update_section = (
            f"\n## Update History\n\n"
            f"### {entry['latest_version']} ({today()})\n"
            f"- Previous: {entry.get('previous_version', 'unknown')}\n"
            f"- Impact: refreshed curated repo summary for tracking\n"
        )

    return f"""---
date: {today()}
type: github
ingestion_type: github_sync
source: {entry.get('repo_url', '')}
title: "{title}"
tags: {tags_yaml}
refresh_policy: weekly
source_volatility: high
last_version: {entry.get('latest_version', '')}
last_synced: {entry.get('downloaded_at', now_iso())}
project_id: null
---
# {title}

## Overview
{classification.get('summary', '')}

## Key Details
- Language: {classification.get('language', entry.get('gh_language', 'Unknown'))}
- Category: {classification.get('category', 'Other')}
- Stars: {entry.get('stars', 0)}
- Forks: {entry.get('forks', 0)}
- Open issues: {entry.get('open_issues', 0)}

## What This Repo Does
{classification.get('overview', classification.get('summary', ''))}

## Why We Track It
{classification.get('why_track', 'Track for curated updates and reusable ideas.')}

## Related
- [[knowledge/entities/{note_slug}]]
- [[knowledge/concepts/repo-tracking]]
{update_section}
"""


def write_note(slug: str, entry: dict[str, Any], provider: str) -> Path:
    note_slug = tracker_slug_to_note(slug)
    note_path = GITHUB_NOTES_PATH / f"{note_slug}.md"
    classification = classify_entry(slug, entry, provider=provider)
    note_path.write_text(build_note(slug, entry, classification), encoding="utf-8")
    append_log("repo-sync", f"research/github/{note_slug}.md", f"synced {slug}")
    return note_path


def run_reindex() -> None:
    script = PROJECT_ROOT / ".cursor" / "hooks" / "g-hk-vault-reindex.ps1"
    command = f'powershell -ExecutionPolicy Bypass -File "{script}" -VaultOverride "{VAULT_PATH}"'
    os.system(command)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync GitHub repos and render curated vault notes")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", help="Only process this repo or gist slug")
    parser.add_argument("--provider", default="auto", choices=["auto", "anthropic", "openai", "heuristic"])
    args = parser.parse_args()

    tracker = load_tracker()
    slugs = [normalize_slug(args.repo)] if args.repo else load_repo_list()
    if not slugs:
        print("No tracked repos found.")
        return

    for slug in slugs:
        entry = tracker["repos"].setdefault(slug, {})
        previous_version = entry.get("downloaded_version", "unknown")
        entry["previous_version"] = previous_version
        try:
            if slug.startswith("gist:"):
                status = sync_gist(slug, entry, force=args.force, dry_run=args.dry_run)
            else:
                status = sync_repo(slug, entry, force=args.force, dry_run=args.dry_run)
            print(f"{slug}: {status}")
            if not args.dry_run and "update" in status:
                note_path = write_note(slug, entry, provider=args.provider)
                print(f"  note -> {note_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"{slug}: ERROR: {exc}")
        finally:
            save_tracker(tracker)

    if not args.dry_run:
        run_reindex()


if __name__ == "__main__":
    main()
