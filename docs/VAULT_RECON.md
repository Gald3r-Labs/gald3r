# Follow-up spec — Vault Recon Fetchers (and the wider research subsystem)

**Status:** follow-up / not built. The vault *store* is done (in the engine); the *recon fetchers*
that feed it are the network-touching follow-on, deliberately left out of the pure Mode-A core.
**Audience:** an implementing agent picking this up later.
**Prereq reading:** `reviews/REVIEW_vault_system.md` (the diagnosis), `gald3r-engine/SYSTEMS.md`
(what the vault store already does), and `gald3r-engine/src/gald3r/systems/vault.py`.

---

## 0. One-paragraph summary

gald3r's vault is a file-first, Obsidian-compatible Markdown knowledge store. The **store half** —
route a note by `type`, write it with correct frontmatter, append the log, regenerate `_index.yaml` +
`index.md` — is built and tested as `gald3r.systems.vault.VaultSystem` (pure, no LLM, no network). The
**recon half** — the fetchers that pull source material *in* from repos, URLs, docs sites, YouTube, and
local files, then hand it to `vault.ingest()` — is the follow-on. Recon touches the network and (for
the richer paths) optional LLM classification, so it lives outside the pure core, exactly like the
Mode-B pipeline does.

## 1. What's already built (don't redo)

`VaultSystem` (engine, `systems/vault.py`) already provides the deterministic spine the fetchers call:
- `ingest(title, type, source, tags, ingestion_type, body, …)` — routes by `type` to the right folder
  (`research/articles`, `research/github`, `research/papers`, `research/platforms`, `research/videos`,
  `knowledge/{cards,comparisons,concepts,entities}`, `projects/{project}/{sessions,decisions}`),
  writes the note, appends `log.md`, reindexes. **`tags:` is canonical (D021)** — it migrates any
  incoming `topics:` to `tags:` so the index can never lose the label field again (the original's
  signature bug, see the review).
- `reindex()` — regenerates `_index.yaml` + `index.md` from note frontmatter.
- `list(type=…)`, `get(rel_or_slug)`, `lint()` — read/validate.

So a fetcher's job is narrow: **acquire raw material → normalize to a note (title/type/source/tags/
body) → call `vault.ingest()`.** It never writes vault files directly.

## 2. The fetchers to build (mirror the existing `g-skl-recon-*` skills)

| Fetcher | Source | Maps to vault `type` | Notes |
|---|---|---|---|
| `recon_repo` | a GitHub repo | `github` → `research/github/` | curated summary only — never dump raw upstream md; raw mirrors live outside the vault in `repos_location` |
| `recon_url` | a single URL / article | `article` → `research/articles/` | the original's single-URL route was the broken one (pointed at the deleted `g-skl-ingest-url`); the engine path replaces it |
| `recon_docs` | a docs site (crawl) | `platform_doc` → `research/platforms/` | platform-docs crawl; feeds `last_doc_scan` freshness (ties into the platform matrix cron) |
| `recon_yt` | a YouTube video | `video` → `research/videos/` | transcript fetch + summary |
| `recon_file` | a local PDF/image/text | by content | PDF extraction is **optional-import** (`pdfplumber`→`pypdf`); degrade to heuristic when no extractor/API key |

Plus the **raw-inbox watcher** (`{vault}/raw/` drops auto-routed by type) and the
**knowledge-refresh / lint** pass (freshness + contradiction review) — both already have engine-side
hooks (`vault.lint()` is the deterministic half; the contradiction/enrichment judgment is a prompt).

## 3. Architecture (where recon sits)

```
   network / disk                         pure engine (built)            files
   ┌──────────────┐   raw material   ┌──────────────────────┐
   │ recon_repo   │ ───────────────► │                      │
   │ recon_url    │                  │  normalize → Note     │
   │ recon_docs   │ ───────────────► │  vault.ingest()       │ ──► .gald3r/vault/
   │ recon_yt     │                  │  (route + log +       │      research/… knowledge/…
   │ recon_file   │ ───────────────► │   reindex, tags:)     │      _index.yaml index.md log.md
   └──────────────┘                  └──────────────────────┘
        ▲ network/LLM here                ▲ no network, no LLM
```

- **Recon = the impure edge** (network, optional LLM classify/summarize). Keep it in a separate package
  (e.g. `gald3r/recon/`) with its network/LLM deps as an **optional extra**, so the pure core stays
  installable without them — same discipline as the `mcp` and (future) `agent` extras.
- **The store stays pure.** Recon hands a fully-formed note to `vault.ingest()`; the engine owns
  routing/frontmatter/index. This keeps the file-first guarantee (the vault works with no MCP/DB).

## 4. Build approach

1. **Stdlib-first acquisition.** `urllib`/`json`/`pathlib` for the core path (the original's
   `github_sync.py`/`ai_classify.py` already prove this); PDF/vision/LLM are optional-import with clear
   install hints, degrading to heuristic. Pin min-Python and use `datetime.timezone.utc` (not the
   3.11-only `datetime.UTC` — a real bug the review caught).
2. **One fetcher = one function** `fetch(source) -> Note-args` (title/type/source/tags/body), then
   `g.vault.ingest(**args)`. Thin and individually testable with a recorded fixture (no live network in
   the default test suite).
3. **Expose** via CLI (`gald3r vault recon <url|repo|file>`) + MCP tools, the same surfaces as the rest.
4. **Judgment stays prompts.** Entity/concept extraction, repo classification, the
   `VAULT_OBSIDIAN_STANDARD` curation, and contradiction review are prompt-layer assets, not fetcher
   code — the fetcher gets the bytes, a prompt decides what's worth compiling into `knowledge/`.
5. **Wire the docs-crawl** (`recon_docs`) into the platform-docs freshness loop: a crawl updates
   `research/platforms/_index.yaml` + the platform `last_doc_scan`, which feeds `extract_targets` →
   the platform matrix/build (`strategy/regen_platforms.py`). Recon and the platform pipeline share
   the same freshness signal.

## 5. Acceptance (when it's "done")

- Each fetcher: `fetch(source)` returns valid note-args and `g.vault.ingest()` writes a correctly-routed
  note with `tags:` (never `topics:`), an appended `log.md` entry, and a regenerated index.
- Optional deps absent → fetcher degrades gracefully (heuristic), never crashes the core.
- The default test suite runs offline (recorded fixtures); live fetches behind an env flag.
- `gald3r vault recon …` + MCP tools work against a real `.gald3r/vault/`.
- The pure `VaultSystem` is unchanged and still makes no network/LLM calls.

## 6. Why it was deferred

Recon is the **network/LLM edge** of the vault. The pure store (deterministic, testable, file-first) is
the valuable, trustworthy core and is finished. The fetchers add real external dependencies (network,
PDF/vision libs, optional API keys) and so belong outside the pure core — bundled as an optional extra,
on the same side of the line as Mode-B. Build them when the team wants live ingestion; until then the
vault works fully for hand-authored and `raw/`-dropped notes.
