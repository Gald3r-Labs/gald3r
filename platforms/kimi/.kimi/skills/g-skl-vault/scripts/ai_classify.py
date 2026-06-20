"""
ai_classify.py

Summarize and classify a tracked repository or gist for the gald3r vault.
Prefers Anthropic or OpenAI when credentials are available, otherwise falls
back to a local heuristic summary so the workflow stays file-first.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


README_NAMES = [
    "README.md",
    "README.MD",
    "Readme.md",
    "README.rst",
    "README.txt",
    "README",
    "readme.md",
    "readme.txt",
]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def find_readme_text(local_path: str) -> str:
    base = Path(local_path)
    if not base.exists():
        return ""
    for name in README_NAMES:
        candidate = base / name
        if candidate.exists():
            try:
                return candidate.read_text(encoding="utf-8", errors="replace")[:8000]
            except OSError:
                return ""
    return ""


def _post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        return "\n".join(inner).strip()
    return text


def _ai_prompt(slug: str, entry: dict[str, Any], readme: str) -> str:
    return f"""Analyze this repository and return strict JSON with these keys only:
summary, category, tags, language, quality_score, quality_rationale, overview, why_track

Rules:
- summary: 1-2 sentence plain-English summary
- category: one of AI/ML, DevTools, Framework, Library, CLI, WebApp, MobileApp, Game, Data, Security, Infra/DevOps, Docs/Learning, Other
- tags: array of 3-6 lowercase tags
- language: primary language
- quality_score: integer 1-10
- quality_rationale: one short sentence
- overview: 1-3 short paragraphs
- why_track: one short paragraph focused on agentic coding, developer workflow, or research relevance

Repository: {slug}
Description: {entry.get("description", "")}
Language: {entry.get("gh_language", "Unknown")}
Stars: {entry.get("stars", 0)}
Forks: {entry.get("forks", 0)}
Open issues: {entry.get("open_issues", 0)}
Topics: {", ".join(entry.get("topics", []))}

README (truncated):
{readme or "(no README found)"}"""


def classify_with_anthropic(slug: str, entry: dict[str, Any], readme: str) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    body = {
        "model": "claude-3-5-haiku-latest",
        "max_tokens": 800,
        "system": "Return JSON only. No prose outside the JSON object.",
        "messages": [{"role": "user", "content": _ai_prompt(slug, entry, readme)}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    result = _post_json("https://api.anthropic.com/v1/messages", headers, body)
    text = result["content"][0]["text"]
    return json.loads(_strip_code_fences(text))


def classify_with_openai(slug: str, entry: dict[str, Any], readme: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    body = {
        "model": "gpt-4o-mini",
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": _ai_prompt(slug, entry, readme)},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    result = _post_json("https://api.openai.com/v1/chat/completions", headers, body)
    return json.loads(result["choices"][0]["message"]["content"])


def classify_heuristic(slug: str, entry: dict[str, Any], readme: str) -> dict[str, Any]:
    text = (readme or entry.get("description", "")).lower()
    category = "Other"
    if any(word in text for word in ("agent", "llm", "model", "inference", "transformer")):
        category = "AI/ML"
    elif any(word in text for word in ("editor", "ide", "developer", "plugin", "extension")):
        category = "DevTools"
    elif any(word in text for word in ("framework", "routing", "backend", "frontend")):
        category = "Framework"
    elif any(word in text for word in ("cli", "command line", "terminal")):
        category = "CLI"
    elif any(word in text for word in ("deploy", "docker", "kubernetes", "terraform")):
        category = "Infra/DevOps"

    language = entry.get("gh_language") or "Unknown"
    topic_tags = [tag.lower() for tag in entry.get("topics", [])[:4]]
    if not topic_tags:
        topic_tags = [part for part in re.findall(r"[a-z0-9][a-z0-9\-]+", text)[:4]]
    tags = list(dict.fromkeys([language.lower()] + topic_tags))[:5]

    summary = entry.get("description") or f"{slug} is a tracked repository in the {category} category."
    if readme:
        first_sentence = re.split(r"(?<=[.!?])\s+", readme.strip())[0][:220]
        if first_sentence and len(first_sentence) > 40:
            summary = first_sentence

    stars = int(entry.get("stars", 0) or 0)
    score = 4
    if stars > 1000:
        score = 7
    if stars > 10000:
        score = 8
    if stars > 50000:
        score = 9

    overview = summary
    why_track = (
        "Track this repo for reusable ideas, update monitoring, and curated "
        "vault summaries rather than raw mirror browsing."
    )

    return {
        "summary": summary,
        "category": category,
        "tags": tags or ["github", "tracked-repo"],
        "language": language,
        "quality_score": score,
        "quality_rationale": "Heuristic fallback based on README signals and GitHub metadata.",
        "overview": overview,
        "why_track": why_track,
    }


def classify_entry(
    slug: str,
    entry: dict[str, Any],
    provider: str = "auto",
    readme_text: str | None = None,
) -> dict[str, Any]:
    readme = readme_text if readme_text is not None else find_readme_text(entry.get("local_path", ""))

    providers: list[str]
    if provider == "auto":
        providers = ["anthropic", "openai", "heuristic"]
    else:
        providers = [provider]

    last_error = None
    for current in providers:
        try:
            if current == "anthropic":
                return classify_with_anthropic(slug, entry, readme)
            if current == "openai":
                return classify_with_openai(slug, entry, readme)
            return classify_heuristic(slug, entry, readme)
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    raise RuntimeError(f"classification failed for {slug}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify a repo or gist for gald3r vault sync")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--entry-json", required=True, help="JSON object for tracker entry metadata")
    parser.add_argument("--provider", default="auto", choices=["auto", "anthropic", "openai", "heuristic"])
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()

    load_dotenv(Path(args.env_file))
    entry = json.loads(args.entry_json)
    result = classify_entry(args.slug, entry, provider=args.provider)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
