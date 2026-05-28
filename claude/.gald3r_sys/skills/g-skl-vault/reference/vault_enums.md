# Vault Enums & Reference Tables

Canonical reference for vault metadata values. Used by `g-skl-vault` and `g-skl-knowledge-refresh`.

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `date` | yes | Creation or last major rewrite date (`YYYY-MM-DD`) |
| `type` | yes | Content type that determines folder placement |
| `ingestion_type` | yes | How the note entered the vault |
| `source` | yes | Origin URL, repo URL, or system identifier |
| `title` | yes | Human-readable title |
| `topics` | yes | Searchable labels array |
| `project_id` | no | UUID for project-scoped notes, otherwise `null` |
| `refresh_policy` | no | `none` \| `daily` \| `weekly` \| `monthly` \| `on_demand` |
| `refresh_after` | no | ISO date for next refresh target |
| `expires_after` | no | ISO date after which note is stale |
| `source_volatility` | no | `low` \| `medium` \| `high` |
| `source_notes` | no | Relative note paths used to build a compiled note |
| `last_compiled` | no | ISO date for last compiled wiki rebuild |
| `last_synced` | no | ISO timestamp for repo mirror sync |
| `last_version` | no | Last seen repo tag or commit |

## `type` Enum

| Value | Folder | Description |
|-------|--------|-------------|
| `video_analysis` | `research/videos/` | Video transcript and analysis note |
| `platform_doc` | `research/platforms/` | Platform documentation note |
| `article` | `research/articles/` | Web article summary |
| `paper` | `research/papers/` | Paper or whitepaper summary |
| `harvest` | `research/harvests/` | Harvest output |
| `github_repo` | `research/github/` | Curated summary of a tracked repository |
| `session` | `projects/{name}/sessions/` | Session summary |
| `decision` | `projects/{name}/decisions/` | Decision record |
| `entity` | `knowledge/entities/` | Compiled entity page |
| `concept` | `knowledge/concepts/` | Compiled concept page |
| `comparison` | `knowledge/comparisons/` | Side-by-side analysis |
| `knowledge_card` | `knowledge/cards/` | Consolidated topic card |
| `correction` | `knowledge/cards/` | Durable correction note |
| `preference` | `knowledge/cards/` | Durable user or team preference |

## `ingestion_type` Enum

| Value | When to Use |
|-------|-------------|
| `video_analysis` | Video analyzed through a dedicated workflow |
| `crawl4ai` | Crawled documentation or web page |
| `url_fetch` | Direct fetch of a URL or article |
| `manual` | Human-written or manually curated note |
| `harvest` | External source harvested for ideas |
| `session` | Hook-generated session summary |
| `research` | Multi-source research synthesis |
| `paper` | Paper-specific workflow |
| `decision` | Decision record workflow |
| `knowledge_card` | Compiled card synthesized from multiple notes |
| `github_sync` | Repo tracker summary built from a raw mirror |
| `wiki_compile` | Entity, concept, or comparison page built from source notes |

## `refresh_policy` Defaults

| Source Type | Policy | Volatility | Expiration |
|-------------|--------|------------|------------|
| YouTube video | `none` | `low` | `null` |
| Platform docs | `weekly` | `high` | 14 days |
| GitHub repo summary | `weekly` | `high` | 30 days |
| Web article | `on_demand` | `medium` | 180 days |
| Paper | `none` | `low` | `null` |
| Knowledge card | `on_demand` | `medium` | 90 days by default |
| Preference | `none` | `low` | `null` |

## `topics` Guidance

Use 3-8 specific topics.

Prefer:

- platform or product name
- domain
- subsystem or pattern
- capability users will search for

Examples:

- `["AI", "obsidian", "knowledge-management", "wiki"]`
- `["github", "repo-tracker", "sync", "automation"]`
- `["cursor", "platform-docs", "IDE", "agents"]`

## Folder Routing Notes

- `projects/{name}/...` is for project-specific content
- `research/...` is for source material and curated repo summaries
- `knowledge/...` is for compiled, cross-source pages
- raw repo mirrors belong in `repos_location`, never the vault
