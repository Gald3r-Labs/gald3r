---
description: Check for gald3r updates and upgrade if available
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---

## @g-upgrade — gald3r Update Check & Upgrade

Check for a newer version of gald3r and optionally upgrade.

### Usage

```
@g-upgrade              → check and offer to upgrade (interactive)
@g-upgrade --skip       → dismiss current available version; store in .gald3r/.update_skips
@g-upgrade --force      → upgrade immediately without confirmation prompt
```

### Steps

1. Call MCP tool `gald3r_check_update` with `project_path` = current project root (the directory containing `.gald3r/`)
2. **If `update_available: false`**: report `✅ gald3r is up to date (current: {currentVersion})` and stop.
3. **If `update_available: true`**:
   - Show: `🔔 gald3r {latestVersion} is available (you have {currentVersion})`
   - Show first 3 lines of `release_notes` from the response (if present)
   - Show `release_url` from the response (if present)
   - If `--force` flag provided: skip confirmation and proceed directly to upgrade
   - Otherwise ask user: `Upgrade now? (yes / no / skip-this-version)`
     - **yes**: call `gald3r_install` MCP tool with `mode=upgrade`, `project_path=<cwd>`, `dry_run=False`
       - On success: `✅ gald3r upgraded to {latestVersion} — .gald3r/ data preserved`
       - On failure: `❌ Upgrade failed: {error} — run @g-upgrade again or upgrade manually`
     - **no**: `Upgrade skipped. Run @g-upgrade any time to upgrade later.`
     - **skip-this-version** (or `--skip` flag): append `{latestVersion}` to `.gald3r/.update_skips` (newline-delimited). `🔕 Version {latestVersion} will not be shown again. Run @g-upgrade --force to override.`
4. **If `gald3r_check_update` fails** (network unavailable, MCP unreachable): report `⚠️ Update check unavailable — working offline. Run @g-upgrade again when connected.`

### Version Skip File

`.gald3r/.update_skips` — newline-delimited list of version tags the user has dismissed.

Example contents:
```
v1.2.0
v1.2.1
```

The session-start version check skips the notification if `latestVersion` appears in this file.
This file is gitignored (host-local user preference).

### Notes

- Upgrade uses `gald3r_install mode=upgrade` which preserves all `.gald3r/` project data
- After upgrade, any cached skill/rule content in the current session should be treated as potentially stale — re-read skills before relying on them
- The `--force` flag is useful in CI or non-interactive contexts
