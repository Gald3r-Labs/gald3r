"""
raw_inbox_classifier.py — Phase 3 vault raw inbox classifier

Handles drops that Phase 2 watcher deferred:
  - *.pdf  : extract text via pdfplumber (preferred) or pypdf (fallback)
  - *.png / *.jpg / *.jpeg : vision summary via OpenAI/Anthropic vision API
  - *.txt / *.md (ambiguous) : LLM classify → article | note | project_context

Usage:
    python raw_inbox_classifier.py --file <path> --vault-path <vault_root>
    python raw_inbox_classifier.py --file <path> --vault-path <vault_root> --dry-run
    python raw_inbox_classifier.py --file <path> --vault-path <vault_root> --confidence-threshold 0.7

Environment variables (any):
    ANTHROPIC_API_KEY   — used for Anthropic claude-3-haiku (default preferred)
    OPENAI_API_KEY      — used for GPT-4o-mini (fallback)

    CLASSIFIER_MODEL    — override model slug (anthropic: claude-3-haiku-20240307, openai: gpt-4o-mini)
    VISION_MODEL        — override vision model slug
    CONFIDENCE_THRESHOLD — float 0.0-1.0 (default: 0.7)

Returns exit codes:
    0 — success, file written to vault
    1 — fatal error (can't read file, no provider available)
    2 — low confidence, human approval required (file NOT moved)
    3 — classified as non-vault content (moved to failed/)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from typing import Any


MIN_PDF_CHARS = 200
DEFAULT_CONFIDENCE = 0.7
TODAY = date.today().isoformat()


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

def load_dotenv(start: Path) -> None:
    for parent in [start, start.parent, start.parent.parent, Path.home()]:
        dotenv = parent / ".env"
        if dotenv.exists():
            for line in dotenv.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
            return


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

def detect_provider() -> str | None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return None


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def _anthropic_chat(messages: list[dict], max_tokens: int = 512) -> str:
    model = os.environ.get("CLASSIFIER_MODEL", "claude-3-haiku-20240307")
    key = os.environ["ANTHROPIC_API_KEY"]
    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"]


def _openai_chat(messages: list[dict], max_tokens: int = 512) -> str:
    model = os.environ.get("CLASSIFIER_MODEL", "gpt-4o-mini")
    key = os.environ["OPENAI_API_KEY"]
    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def llm_complete(messages: list[dict], provider: str, max_tokens: int = 512) -> str:
    if provider == "anthropic":
        return _anthropic_chat(messages, max_tokens)
    if provider == "openai":
        return _openai_chat(messages, max_tokens)
    raise ValueError(f"Unknown provider: {provider}")


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def extract_pdf_text(path: Path) -> str:
    """Extract text from PDF. Tries pdfplumber first, then pypdf."""
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(str(path)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n".join(pages).strip()
    except ImportError:
        pass

    try:
        import pypdf  # type: ignore
        reader = pypdf.PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except ImportError:
        pass

    raise RuntimeError(
        "No PDF extractor found. Install one: uv pip install pdfplumber  OR  uv pip install pypdf"
    )


def is_academic_shape(text: str) -> bool:
    """Heuristic: does the text look like an academic paper?"""
    academic_signals = [
        r"\babstract\b",
        r"\bintroduction\b",
        r"\bconclusion\b",
        r"\breferences\b",
        r"\bcitations\b",
        r"\barxiv\b",
        r"\bdoi:\s*10\.",
    ]
    text_lower = text.lower()[:3000]
    hits = sum(1 for p in academic_signals if re.search(p, text_lower))
    return hits >= 3


# ---------------------------------------------------------------------------
# Image vision
# ---------------------------------------------------------------------------

def _encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def vision_summarize(image_path: Path, provider: str) -> str:
    """Get a short description of an image using vision API."""
    ext = image_path.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    b64 = _encode_image(image_path)
    prompt = (
        "You are a knowledge archivist. Describe this image concisely (3-5 sentences) "
        "for a personal knowledge vault. Focus on: what it shows, why it might be valuable, "
        "and any text visible. Do NOT invent facts."
    )

    if provider == "anthropic":
        vision_model = os.environ.get("VISION_MODEL", "claude-3-haiku-20240307")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": f"image/{ext}",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        key = os.environ["ANTHROPIC_API_KEY"]
        payload = json.dumps({
            "model": vision_model,
            "max_tokens": 512,
            "messages": messages,
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read())
        return data["content"][0]["text"]

    elif provider == "openai":
        vision_model = os.environ.get("VISION_MODEL", "gpt-4o-mini")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/{ext};base64,{b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        key = os.environ["OPENAI_API_KEY"]
        payload = json.dumps({
            "model": vision_model,
            "max_tokens": 512,
            "messages": messages,
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

    raise ValueError(f"Vision not supported for provider: {provider}")


# ---------------------------------------------------------------------------
# LLM text classifier
# ---------------------------------------------------------------------------

CLASSIFY_PROMPT = """\
You are a knowledge archivist. Classify the following text into exactly ONE of these categories:
  - article    : external content worth keeping (blog post, tutorial, essay, news)
  - paper      : academic / research paper
  - note       : personal note, brain dump, or todo written by the user
  - project_context : project planning, architecture decisions, specs, or code

Respond with ONLY a JSON object: {"category": "<category>", "confidence": <0.0-1.0>, "title": "<short title>", "summary": "<1-2 sentences>"}

Text (first 3000 chars):
"""


def classify_text(text: str, provider: str) -> dict[str, Any]:
    """LLM-classify a block of text. Returns {category, confidence, title, summary}."""
    snippet = text[:3000]
    messages = [{"role": "user", "content": CLASSIFY_PROMPT + snippet}]
    raw = llm_complete(messages, provider, max_tokens=300)
    # Extract JSON from response
    m = re.search(r'\{[^{}]+\}', raw, re.DOTALL)
    if not m:
        raise ValueError(f"LLM returned unexpected format: {raw[:200]}")
    data = json.loads(m.group())
    return data


# ---------------------------------------------------------------------------
# Secret / PII pre-filter
# ---------------------------------------------------------------------------

def contains_sensitive_patterns(text: str) -> list[str]:
    """Detect API-key-shaped or credential strings. Returns list of findings."""
    findings = []
    patterns = [
        (r'\b[A-Za-z0-9_]{32,64}\b(?=.*api|.*key|.*token|.*secret)', "possible API key/token"),
        (r'\b4[0-9]{12}(?:[0-9]{3})?\b', "Visa card number"),
        (r'\b5[1-5][0-9]{14}\b', "Mastercard number"),
        (r'sk-[A-Za-z0-9]{20,}', "OpenAI-style secret key"),
        (r'xoxb-[0-9]+-[A-Za-z0-9]+', "Slack bot token"),
        (r'ghp_[A-Za-z0-9]{36}', "GitHub PAT"),
        (r'AIza[0-9A-Za-z_-]{35}', "Google API key"),
        (r'(?i)password\s*[:=]\s*\S{8,}', "plaintext password"),
    ]
    for pattern, label in patterns:
        if re.search(pattern, text):
            findings.append(label)
    return findings


# ---------------------------------------------------------------------------
# Frontmatter builder
# ---------------------------------------------------------------------------

def build_frontmatter(
    *,
    category: str,
    title: str,
    summary: str,
    source_file: str,
    source_type: str = "raw_inbox",
    extra_tags: list[str] | None = None,
) -> str:
    tags = ["raw_inbox", source_type, category]
    if extra_tags:
        tags.extend(extra_tags)
    tags_str = "[" + ", ".join(tags) + "]"
    return f"""---
date: {TODAY}
type: {category}
ingestion_type: {source_type}
source: raw_inbox/{source_file}
title: "{title}"
summary: "{summary}"
tags: {tags_str}
---

"""


# ---------------------------------------------------------------------------
# Destination routing
# ---------------------------------------------------------------------------

CATEGORY_TO_SUBDIR = {
    "article": "research/articles",
    "paper": "research/papers",
    "note": "knowledge",
    "project_context": "knowledge",
    "image_summary": "research/articles",
    "pdf_extract": "research/articles",
}


def route_to_vault(
    vault_path: Path,
    category: str,
    title: str,
    content: str,
    source_file: str,
    source_type: str,
    dry_run: bool = False,
) -> Path:
    subdir = CATEGORY_TO_SUBDIR.get(category, "research/articles")
    dest_dir = vault_path / subdir
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    # Build slug from title
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60] or "classified"
    filename = f"{TODAY}_{slug}.md"
    dest = dest_dir / filename

    if not dry_run:
        dest.write_text(content, encoding="utf-8")

    return dest


def append_vault_log(vault_path: Path, message: str, dry_run: bool = False) -> None:
    if dry_run:
        return
    log_path = vault_path / "log.md"
    if not log_path.exists():
        log_path.write_text("# Vault Activity Log\n", encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {TODAY} - raw_inbox_classifier\n{message}\n")


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def process_file(
    file_path: Path,
    vault_path: Path,
    provider: str | None,
    confidence_threshold: float,
    dry_run: bool,
) -> int:
    ext = file_path.suffix.lower()
    slug = file_path.stem

    # ------ PDF ---------------------------------------------------------------
    if ext == ".pdf":
        print(f"[T112] PDF detected: {file_path.name}")
        try:
            text = extract_pdf_text(file_path)
        except RuntimeError as e:
            print(f"[T112] FAIL: {e}", file=sys.stderr)
            return 1

        if len(text) < MIN_PDF_CHARS:
            print(f"[T112] FAIL: extracted only {len(text)} chars (min {MIN_PDF_CHARS}) — too short, moving to failed/")
            return 1

        # Secret pre-filter
        secrets = contains_sensitive_patterns(text)
        if secrets:
            print(f"[T112] WARN: possible sensitive content detected ({', '.join(secrets)}) — skipping vault write")
            return 3

        category = "paper" if is_academic_shape(text) else "pdf_extract"
        title = slug.replace("_", " ").replace("-", " ").title()
        summary = text[:200].replace("\n", " ").strip()

        fm = build_frontmatter(
            category=category,
            title=title,
            summary=summary,
            source_file=file_path.name,
            source_type="pdf_extract",
        )
        dest = route_to_vault(vault_path, category, title, fm + text, file_path.name, "pdf_extract", dry_run)
        append_vault_log(vault_path, f"- PDF classified as `{category}`: {file_path.name} → {dest.name}", dry_run)
        print(f"[T112] OK: {file_path.name} → {dest}")
        return 0

    # ------ Images ------------------------------------------------------------
    if ext in (".png", ".jpg", ".jpeg"):
        print(f"[T112] Image detected: {file_path.name}")
        if not provider:
            print("[T112] FAIL: no LLM provider available for vision — set ANTHROPIC_API_KEY or OPENAI_API_KEY")
            return 1
        try:
            description = vision_summarize(file_path, provider)
        except Exception as e:
            print(f"[T112] FAIL: vision API error: {e}", file=sys.stderr)
            return 1

        title = f"Image summary: {slug}"
        fm = build_frontmatter(
            category="article",
            title=title,
            summary=description[:200],
            source_file=file_path.name,
            source_type="image_summary",
        )
        body = fm + f"## Description\n\n{description}\n\n## Source\n\nOriginal file: `{file_path.name}`\n"
        dest = route_to_vault(vault_path, "image_summary", title, body, file_path.name, "image_summary", dry_run)
        append_vault_log(vault_path, f"- Image summarized: {file_path.name} → {dest.name}", dry_run)
        print(f"[T112] OK: {file_path.name} → {dest}")
        return 0

    # ------ Ambiguous text / markdown -----------------------------------------
    if ext in (".txt", ".md"):
        print(f"[T112] Text classification: {file_path.name}")
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"[T112] FAIL: cannot read file: {e}", file=sys.stderr)
            return 1

        secrets = contains_sensitive_patterns(text)
        if secrets:
            print(f"[T112] WARN: sensitive content ({', '.join(secrets)}) — skipping")
            return 3

        if not provider:
            # Heuristic fallback — no LLM available
            category = "article"
            title = slug.replace("_", " ").replace("-", " ").title()
            summary = text[:200].replace("\n", " ").strip()
            confidence = 0.5  # heuristic = lower confidence
        else:
            try:
                result = classify_text(text, provider)
                category = result.get("category", "article")
                confidence = float(result.get("confidence", 0.0))
                title = result.get("title", slug)
                summary = result.get("summary", "")
            except Exception as e:
                print(f"[T112] FAIL: LLM classification error: {e}", file=sys.stderr)
                return 1

        print(f"[T112] classified: category={category}, confidence={confidence:.2f}, title={title!r}")

        if confidence < confidence_threshold:
            print(
                f"[T112] LOW CONFIDENCE ({confidence:.2f} < {confidence_threshold}) — "
                "human approval required. File NOT moved."
            )
            return 2

        fm = build_frontmatter(
            category=category,
            title=title,
            summary=summary,
            source_file=file_path.name,
            source_type="llm_classified",
        )
        dest = route_to_vault(vault_path, category, title, fm + text, file_path.name, "llm_classified", dry_run)
        append_vault_log(vault_path, f"- Text classified as `{category}` (conf={confidence:.2f}): {file_path.name} → {dest.name}", dry_run)
        print(f"[T112] OK: {file_path.name} → {dest}")
        return 0

    print(f"[T112] FAIL: unsupported extension '{ext}' for Phase 3 classifier", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3 vault raw inbox classifier")
    parser.add_argument("--file", required=True, help="Path to file to classify")
    parser.add_argument("--vault-path", required=True, help="Vault root directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't write anything")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=float(os.environ.get("CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE)),
        help="Minimum LLM confidence to auto-route (default 0.7)",
    )

    args = parser.parse_args()
    file_path = Path(args.file)
    vault_path = Path(args.vault_path)

    if not file_path.exists():
        print(f"[T112] FAIL: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not vault_path.is_dir():
        print(f"[T112] FAIL: vault path is not a directory: {vault_path}", file=sys.stderr)
        sys.exit(1)

    load_dotenv(file_path.parent)
    load_dotenv(vault_path)
    provider = detect_provider()

    if args.dry_run:
        print(f"[T112] DRY RUN — provider: {provider or 'none (heuristic fallback)'}")

    rc = process_file(file_path, vault_path, provider, args.confidence_threshold, args.dry_run)
    sys.exit(rc)


if __name__ == "__main__":
    main()
