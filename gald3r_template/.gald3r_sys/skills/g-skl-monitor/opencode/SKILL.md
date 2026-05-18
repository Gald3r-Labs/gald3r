---
name: g-skl-monitor
description: >
  Manage scheduled content monitors for YouTube playlists, docs sites, GitHub repos,
  and URLs via gald3r_valhalla MCP tools. Requires Docker backend (adv tier).
  Monitors trigger automatic re-ingestion when new content is detected.
version: 1.0.0
min_tier: adv
triggers:
  - "add monitor"
  - "content monitor"
  - "watch playlist"
  - "monitor docs"
  - "monitor repo"
  - "monitor url"
  - "check monitors"
  - "list monitors"
  - "remove monitor"
  - g-monitor
requires:
  - gald3r_valhalla MCP server (Docker backend)
  - monitor_add MCP tool
  - monitor_list MCP tool
  - monitor_check MCP tool
  - monitor_remove MCP tool
---

# g-skl-monitor

**Requires**: gald3r_valhalla Docker backend + `monitor_add` / `monitor_list` / `monitor_check` / `monitor_remove` MCP tools.

**Activate for**: Setting up scheduled content watching, checking for new videos/commits/docs changes, listing active monitors, removing monitors.

---

## Monitor Types

| Type | Use Case | Default Schedule |
|---|---|---|
| `playlist` | YouTube playlist — detect new videos | daily |
| `docs` | Documentation site — detect content changes | weekly |
| `github_repo` | GitHub repo — detect new commits | weekly |
| `url` | Any URL — detect ETag/Last-Modified changes | monthly |

---

## Operations

### ADD — Create a monitor

```
monitor_add(
  name="cursor-docs",
  monitor_type="docs",
  url="https://docs.cursor.com",
  schedule="weekly"
)
```

```
monitor_add(
  name="ai-research-playlist",
  monitor_type="playlist",
  url="https://youtube.com/playlist?list=PLxxx",
  schedule="daily"
)
```

**Parameters**:
| Param | Required | Description |
|---|---|---|
| `name` | ✅ | Unique slug (auto-lowercased, spaces→dashes) |
| `monitor_type` | ✅ | `playlist` \| `docs` \| `github_repo` \| `url` |
| `url` | ✅ | Full URL to monitor |
| `schedule` | optional | `hourly` \| `daily` \| `weekly` \| `monthly` (defaults by type) |
| `config` | optional | Type-specific JSON config (e.g. `{max_pages: 100}` for docs) |
| `user_id` | optional | User creating the monitor |

**Note**: Adding a monitor with a name that already exists **updates** it (upsert behavior).

---

### LIST — Show all monitors

```
monitor_list()
monitor_list(monitor_type="playlist")
monitor_list(enabled_only=false)
```

Returns: `id`, `name`, `monitor_type`, `url`, `schedule`, `enabled`, `last_checked_at`, `last_change_at`

---

### CHECK — Trigger a check now

```
monitor_check(name="cursor-docs")   # check one specific monitor
monitor_check()                      # check ALL due monitors
```

What happens per type:
- **playlist** → fetches current video list, compares against known IDs, triggers `video_analyze` for new ones
- **github_repo** → checks latest commit SHA via GitHub API, notes changes
- **docs** → re-crawls via `platform_crawl_trigger`
- **url** → checks ETag/Last-Modified headers for changes

---

### REMOVE — Delete a monitor

```
monitor_remove(name="cursor-docs")
```

Permanently removes the monitor and stops all scheduled checks.

---

## Workflow: Adding a new content source to watch

1. Identify the URL and type
2. `monitor_add(...)` — creates the monitor
3. `monitor_check(name="...")` — run first check immediately to seed state
4. `monitor_list()` — confirm it's registered and enabled
5. The heartbeat scheduler (`HEARTBEAT.md`) will run `monitor_check()` on schedule

---

## Availability Check

Before using this skill:
```
gald3r_server_status()
```
If unavailable: **this skill does not work in slim or full tier installs** — content monitors require the gald3r_valhalla PostgreSQL backend to store monitor state.
