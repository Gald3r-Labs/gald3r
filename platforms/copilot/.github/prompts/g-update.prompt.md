# @g-update — gald3r Framework Update Command

Check the installed gald3r version and apply framework updates.

## Flags

| Flag | Description |
|------|-------------|
| `--check` | Display current vs latest version (no changes made) |
| `--apply` | Show step-by-step update instructions for your install type |
| `--changelog` | Display CHANGELOG.md entries newer than current installed version |

---

## Usage

### `@g-update --check`

1. Read `.gald3r/.identity` → find `gald3r_version` value (key=value format)
2. Attempt to fetch latest version from remote (3-second timeout, non-blocking):
   - Default feed: `https://api.github.com/repos/gald3r/gald3r/releases/latest` (or configured `version_feed_url` in `.gald3r/config/AGENT_CONFIG.md`)
   - Local override: `.gald3r/config/version_feed.json` if present → use `latest_version` field
3. Compare installed vs latest:
   - If current == latest: `✅ gald3r is up to date (v{current})`
   - If current < latest: `💡 gald3r update available: v{current} → v{latest} — run @g-update --apply`
   - If fetch failed (network unavailable): silently skip with `ℹ️ Version check skipped (offline)`
4. Respect `disable_version_check: true` in `.gald3r/config/AGENT_CONFIG.md` — skip silently (air-gapped environments)

### `@g-update --apply`

1. Run `--check` first to confirm update is available
2. Detect install type from `.gald3r/.identity`:
   - `install_type: template_repo` → update path: `git -C {template_repo_path} pull origin main`, then re-run parity sync
   - `install_type: gald3r_install` → update path: re-run `gald3r_install` MCP tool (preserves `.gald3r/` task data)
   - `install_type: manual` → show manual update steps: copy updated files from template repo
3. Display the appropriate update instructions with confirmation prompt before any changes

### `@g-update --changelog`

1. Read `CHANGELOG.md` at project root
2. Read `gald3r_version` from `.gald3r/.identity`
3. Filter CHANGELOG.md sections: display only `## [x.y.z]` entries where version > installed version
4. If current is latest, show: `📋 No new changelog entries — you're on the latest version`

---

## Version Feed Format

**Remote** (GitHub Releases API):
```json
{ "tag_name": "v1.3.0", "published_at": "2026-05-01T..." }
```

**Local override** (`.gald3r/config/version_feed.json`):
```json
{
  "latest_version": "1.3.0",
  "release_date": "2026-05-01",
  "release_notes_url": "https://github.com/gald3r/gald3r/releases/tag/v1.3.0"
}
```

---

## Non-Blocking Behavior

The version check is intentionally lightweight:
- PowerShell: `Invoke-WebRequest -TimeoutSec 3 -ErrorAction SilentlyContinue`
- If the feed is unreachable, update check silently skips — **no error, no delay**
- Air-gapped: set `disable_version_check: true` in `.gald3r/config/AGENT_CONFIG.md`

---

## Session-Start Integration

This command is called automatically during the `g-rl-25` session-start protocol (Step 1.5 — Version Check). If the installed version is outdated, the session start surfaces:

```
💡 gald3r update available (v{current} → v{latest}) — run @g-update
```

The check is non-blocking and skips silently if the network is unavailable or `disable_version_check: true`.
