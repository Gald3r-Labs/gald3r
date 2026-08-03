---
description: Check for gald3r updates and upgrade if available
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
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

### Native CLI equivalent (offline / no-MCP path — T303/T473/T475)

When the world_tree MCP is not reachable, the same version check runs **fully offline** via
gald3r_core's own native `gald3r` CLI (T303 absorbed `version-check` from the legacy vendored
engine into gald3r_core's compiled binary — one shared core, no separate engine process, no fork):

```
gald3r version-check            # query world_tree's version-surface route (JWT-gated -- run
                                 # `gald3r login` first for a real comparison); degrades HONESTLY
                                 # to "offline" (unreachable), "auth_required" (no/stale session
                                 # token), or "not yet available" (route absent on this deployment)
                                 # -- never fabricates a version, mirrors the `gald3r connect`
                                 # honesty-gate convention
gald3r schema-migrate            # dry-run (default): reports .gald3r/ files needing schema migration
gald3r schema-migrate --apply    # writes migrated .gald3r/ files to disk
gald3r schema-migrate --restore-missing --apply  # also restores accidentally-deleted single-file
                                                  # .gald3r/ artifacts from the embedded canonical snapshot
```

`gald3r version-check` is a real, native gald3r_core verb (T303, resolving the `version-check` gap
the T292 verb-sweep flagged) — see `server_bridge.version_check`'s module docstring for the honesty-
gate audit: a live probe against the deployed world_tree confirmed the version-surface route IS
registered and JWT-gated (401, distinct from sibling unmapped paths which 404). The legacy engine's
migration verb was `gald3r upgrade`; the current shipped equivalent is `gald3r schema-migrate`
(T304 repointed this doc's wording to match the built CLI). `gald3r schema-migrate` is dry-run by
default; pass `--apply` to write. It does **not** write a timestamped backup zip or auto-rollback
on failure — that BACKUP/ROLLBACK behavior described in an earlier revision of this doc does not
exist in the shipped verb; a backup-zip wrapper remains an unimplemented follow-up idea, not a
current guarantee.
**T422:** this is the minimal version-check + schema-migrate wrapper; it does not duplicate the
deferred T422 consumer-upgrade subsystem (managed-manifest + conflict-resolver), which
consumes/extends it when it lands.

### Notes

- Upgrade uses `gald3r_install mode=upgrade` (MCP) or `gald3r schema-migrate --apply` (CLI); both preserve all `.gald3r/` user data (tasks/bugs/PLAN/etc. are on an absolute denylist)
- After upgrade, any cached skill/rule content in the current session should be treated as potentially stale — re-read skills before relying on them
- The `--force` flag is useful in CI or non-interactive contexts
