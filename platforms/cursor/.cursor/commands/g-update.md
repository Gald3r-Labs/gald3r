---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
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
   $backfill = Join-Path $projectRoot ".gald3r_sys\skills\g-skl-release\scripts\backfill_release_files.ps1"
   if (Test-Path $backfill) {
       & powershell -NoProfile -ExecutionPolicy Bypass -File $backfill -ProjectRoot $projectRoot -Apply
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
release files would be backfilled (run `backfill_release_files.ps1` without `-Apply`), and which
inheritable constraints would be merged into `CONSTRAINTS.md`.

### `@g-update --changelog`

1. Read `CHANGELOG.md` at project root
2. Read `gald3r_version` from `.gald3r/.identity`
3. Filter CHANGELOG.md sections: display only `## [x.y.z]` entries where version > installed version
4. If current is latest, show: `📋 No new changelog entries — you're on the latest version`

---

## Structural Upgrade (T430/T473/T475 — engine op, now implemented)

`@g-update --apply` migrates **data/config** (steps 4-8 above). The complementary
**structural** upgrade — diffing two `.gald3r/` release snapshots and applying safe,
idempotent ADD/MERGE/DEPRECATE migrations — is delegated to the canonical engine op
`gald3r upgrade` (now implemented in `gald3r.systems.upgrade` / `g.upgrade`, T473/T475). The
command **shells out** to the engine; it never re-implements the diff/merge logic (same
shell-out contract as `migrate_schemas.ps1` and g-medic).

```powershell
# version-check: query world_tree's T112 version surface (offline-safe — degrades gracefully)
gald3r --root <proj> version-check                 # current vs latest + update-available
gald3r --root <proj> version-check --base-url http://host:8000   # or GALD3R_WORLD_TREE_URL env
# dry-run (the DEFAULT for `upgrade`): print the version delta + planned actions, zero writes
gald3r --root <proj> upgrade
# apply: BACKUP .gald3r/ to a timestamped gitignored .zip, THEN ADD new files,
#        MERGE frontmatter (preserve user data, add new template keys, bump schema/rel version),
#        DEPRECATE removed files (archive with _deprecated_YYYYMMDD). ROLLBACK from the backup on failure.
gald3r --root <proj> upgrade --apply
gald3r --root <proj> upgrade --from-dir <from/.gald3r> --to-dir <to/.gald3r> --apply  # explicit snapshots
gald3r --root <proj> upgrade --json ...                                              # machine-readable result
```

**Safe self-update (T473 agent / T475 templates).** Before applying anything, `gald3r upgrade
--apply` writes a timestamped backup of the whole `.gald3r/` tree to
`.gald3r/_backups/.gald3r_backup_YYYYMMDD_HHMMSS.zip` — covered by the existing `.gald3r/.gitignore`
`*.zip` rule, so backups are **never committed**. On any migration failure it **restores from that
backup (rollback)** and reports. The agent (T473) and template-installed projects (T475) invoke the
**same** engine command; there is no fork. **T422:** this is the minimal version-check + backup/
rollback wrapper around the migration engine — it does **not** duplicate the deferred T422
consumer-upgrade subsystem (managed-manifest + conflict-resolver); T422 consumes/extends this
wrapper when it lands.

| Classification | Behavior |
|----------------|----------|
| `[ADD]` | file new in the target release → copied into the project |
| `[MERGE]` | file in both, frontmatter/schema changed → user data preserved, new template keys added with defaults, `schema_version` upgraded, `gald3r_rel_version` bumped |
| `[DEPRECATE]` | file removed in the target release → project copy archived with a `_deprecated_YYYYMMDD` suffix |
| `[SKIP user-data]` | path on the ABSOLUTE denylist (`tasks/**`, `bugs/**`, `PLAN.md`, `IDEA_BOARD.md`, `BUGS.md`, `TASKS.md`) → **never touched** |

- **`--dry-run`** (engine default — omit `--apply`): prints `[DRY]`-prefixed actions, **zero file writes**.
- **`--apply`**: writes a migration log to `.gald3r/logs/upgrade_YYYYMMDD_HHMMSS.log`.
- **Idempotent**: a second `--apply` reports 0 added / 0 updated / 0 deprecated.
- **User-data protection is ABSOLUTE** — enforced in the engine denylist and asserted by `tests/test_upgrade.py`.

> **Snapshot prerequisite (T430/T463)**: the engine diffs any two snapshot directories. When
> `--to-dir` is omitted, `g.upgrade.resolve_to_dir()` resolves the target automatically: a T463
> versioned snapshot (`.gald3r_sys/snapshots/<v>/.gald3r`) when one is present, **else** the single
> current canonical snapshot at `.gald3r_sys/template_verification/.gald3r/` (the only one the
> framework ships today — a real fallback, not a stub). `--from-dir` defaults to the live project
> `.gald3r/`. You may still pass both explicitly (e.g. a prior template tag vs. the current
> `template_verification/.gald3r`).

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
  "release_notes_url": "https://github.com/gald3r/gald3r/releases/tag/v2.2.0"
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
