---
description: 'Check or apply gald3r framework version updates via --check/--apply/--changelog/--dry-run flags'
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
execution_tier: orchestration
---
# @g-update — gald3r Framework Update Command

Check the installed gald3r version and apply framework updates.

## Flags

| Flag | Description |
|------|-------------|
| `--check` | Display current vs latest version (no changes made) |
| `--apply` | Show step-by-step update instructions for your install type |
| `--changelog` | Display CHANGELOG.md entries newer than current installed version |
| `--dry-run` | With `--apply`: print all planned project-side changes (VERSION, release backfill, inherited constraints) without writing |

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
4. **Schema backfill (T1280)** — after the version update, ensure newer `.identity`
   fields exist for backward compatibility. If `.gald3r/.identity` (or the
   `.gald3r/.project_type` dotfile, depending on install idiom) has no
   `project_type`, add it with the safe default `project_type=software_development`
   (existing installs keep current behavior — GitHub/code workflows stay active).
   An unknown value read later logs a warning and is treated as `freeform`.
5. **Version reconciliation (T1437 / BUG-102)** — after the framework files are synced,
   write the new framework version back into `.gald3r/.identity` so the install no longer
   reports a stale `gald3r_version`. Read the authoritative version from the source the
   update came from (the template repo's `project_template/.gald3r/.identity` `gald3r_version=`,
   or the latest `## [x.y.z]` CHANGELOG header when no template source is available), then
   key=value-replace `gald3r_version=` in the consumer's `.gald3r/.identity` (append it if the
   key is absent). This mirrors `platform_parity_sync.ps1 -SyncGaldSys -Sync`, which performs
   the same reconciliation for the maintained template/controller repos. Show the delta
   (`v{old} → v{new}`) before writing; make no change when the versions already match.

6. **VERSION file (T1438 / BUG-103)** — `g-skl-ship` reads a `VERSION` file at the project root.
   Check for `VERSION`; **when absent**, create it from the latest `## [X.Y.Z]` header in
   `CHANGELOG.md` (fallback: `0.1.0` when CHANGELOG has no versioned header). **Never overwrite**
   an existing `VERSION` — it is the user's product version, not the framework version.
   ```powershell
   $verFile = Join-Path $projectRoot "VERSION"
   if (-not (Test-Path $verFile)) {
       $cl = Join-Path $projectRoot "CHANGELOG.md"
       $v = "0.1.0"
       if (Test-Path $cl) {
           $m = (Get-Content $cl | Select-String -Pattern '^\#\#\s*\[(\d+\.\d+\.\d+)\]' | Select-Object -First 1)
           if ($m) { $v = $m.Matches[0].Groups[1].Value }
       }
       Set-Content $verFile $v -NoNewline -Encoding utf8
   }
   ```

7. **Release file backfill (T1438 / BUG-104, C-023)** — run the release backfill so every
   `## [X.Y.Z]` CHANGELOG entry has a matching `.gald3r/releases/` file. This silences the
   recurring session-start `N CHANGELOG version(s) missing release file` warning.
   ```powershell
   $backfill = Join-Path $projectRoot "gald3r ship"
   if (Test-Path $backfill) {
       & uv run python $backfill -ProjectRoot $projectRoot -Apply
   }
   ```
   (Equivalent to the `g-skl-release` SYNC/BACKFILL operation. With `--dry-run`, omit `-Apply`.)

8. **Inherited constraints (T1438 / BUG-105, Gap C)** — merge framework `inheritable` constraints
   into the consumer's `.gald3r/CONSTRAINTS.md` so `@g-constraint-check` and session start can find
   them. Read `.gald3r_sys/constraints/framework_inheritable_constraints.md`; for each
   `### C-{ID}` block whose `**Scope**:` is `inheritable`, **when the consumer's CONSTRAINTS.md
   has no `C-{ID}` heading**, append the full block to `## Constraint Definitions`, add a row to
   the `## Constraint Index` table, and append `**Inherited from**: gald3r-framework (propagated
   {today})`. **When the constraint already exists locally, skip it** (never overwrite a
   project-local customization). Delegate the actual `.gald3r/CONSTRAINTS.md` write to
   `g-skl-constraints` (the `.gald3r/` folder gate, g-rl-33).

### Dry-run

`@g-update --apply --dry-run` performs steps 1-5 read-only, and for steps 6-8 **prints the
planned changes without writing**: which VERSION would be created (and with what value), which
release files would be backfilled (run `gald3r ship` without `-Apply`), and which
inheritable constraints would be merged into `CONSTRAINTS.md`.

### `@g-update --changelog`

1. Read `CHANGELOG.md` at project root
2. Read `gald3r_version` from `.gald3r/.identity`
3. Filter CHANGELOG.md sections: display only `## [x.y.z]` entries where version > installed version
4. If current is latest, show: `📋 No new changelog entries — you're on the latest version`

---

## Structural Upgrade — Native CLI Equivalent (T303/T304/T430/T473/T475)

`@g-update --apply` migrates **data/config** (steps 4-8 above). T430 originally planned a
complementary **structural** upgrade — diffing two `.gald3r/` release snapshots and applying
ADD/MERGE/DEPRECATE migrations with a backup/rollback wrapper — delegated to a canonical engine
op `gald3r upgrade`. That op was never carried into gald3r_core's compiled CLI: `gald3r upgrade`
is not a valid subcommand (see `gald3r --help`). The shipped equivalent is **`gald3r
schema-migrate`** (per-file frontmatter/schema migration; same shell-out contract as g-medic).
T304 repointed this section's wording to match the built CLI.

```powershell
# version-check: real, native gald3r_core verb (T303) -- queries world_tree's version-surface
# route (JWT-gated; run `gald3r login` first for a real comparison). Offline-safe: degrades
# honestly to "offline" / "auth_required" / "not yet available" rather than fabricating a
# version. No global `--root` flag exists on this CLI -- `--root` is a per-verb flag.
gald3r version-check                                          # current vs latest + update-available
gald3r version-check --root <proj>                            # resolve installed version from <proj>/.gald3r/.identity
gald3r version-check --base-url http://host:8000               # or GALD3R_WORLD_TREE_URL env
# dry-run (the DEFAULT): reports .gald3r/ files needing schema migration, zero writes
gald3r schema-migrate --root <proj>
# apply: writes migrated .gald3r/ files to disk
gald3r schema-migrate --root <proj> --apply
# also restores accidentally-deleted single-file .gald3r/ artifacts from the embedded canonical
# snapshot before migrating
gald3r schema-migrate --root <proj> --restore-missing --apply
gald3r schema-migrate --root <proj> --json ...                # machine-readable result
```

**No backup/rollback wrapper (T304 correction).** `gald3r schema-migrate --apply` does **not**
write a timestamped backup zip and does **not** auto-rollback on failure — that BACKUP/ROLLBACK
behavior, and the `--from-dir`/`--to-dir` snapshot-diff ADD/MERGE/DEPRECATE mechanism described in
an earlier revision of this doc, do not exist in the shipped verb. The agent (T473) and
template-installed projects (T475) invoke the **same** `gald3r schema-migrate` command; there is
no fork. **T422:** this is the minimal version-check + schema-migrate wrapper — it does **not**
duplicate the deferred T422 consumer-upgrade subsystem (managed-manifest + conflict-resolver);
T422 consumes/extends this wrapper when it lands.

Per-file migration statuses: `to-migrate` / `migrated` (frontmatter/`schema_version`/
`gald3r_rel_version` behind the registry target → fields added/renamed per the schema registry) /
`skipped-current` (already at target version) / `skipped-newer` (file version ahead of target →
left untouched) / `skipped-no-frontmatter` (no YAML frontmatter to migrate). With
`--restore-missing`, restore statuses are `restored` / `to-restore` (file absent on disk, present
in the embedded canonical snapshot → copied back) / `restore-unavailable` (absent from both).

- **Dry-run is the default** (omit `--apply`): reports planned per-file migration/restore actions,
  **zero file writes**.
- **`--apply`**: writes the migrated/restored files to disk.
- A structural snapshot-to-snapshot (ADD/MERGE/DEPRECATE) diff engine remains an unimplemented
  follow-up idea, not a current guarantee.

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
  "release_notes_url": "https://github.com/gald3r/gald3r/releases/tag/v2.1.2"
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
