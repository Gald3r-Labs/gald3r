---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-plugin-update — Update installed plugins to their latest versions

Check the plugin registry for newer versions of installed plugins and apply updates
incrementally: back up the current copy, download and validate the new version, check
for conflicts, show a component diff, confirm, run the new version's `upgrade.ps1`
lifecycle (opt-in), apply, and rewrite `installed.yaml`. If any step after the backup
fails, the plugin is automatically rolled back. (ADR-015, plugin-system / SS-007.)

## Usage

```
g-plugin-update                       Update all installed plugins (interactive)
g-plugin-update <plugin-id>           Update one plugin
g-plugin-update --check               Print the update-availability table only
g-plugin-update --dry-run             Same as --check (no changes applied)
g-plugin-update <plugin-id> --force   Re-install even if already at latest version
g-plugin-update --no-backup           Skip the pre-update backup (disables rollback)
```

## What it does

For each installed plugin (or the one named):

1. Compare the installed version (`installed.yaml`) with the latest in the registry.
2. `--check` / `--dry-run`: print the availability table and stop.
3. Show the CHANGELOG excerpt between the old and new version (max 20 lines).
4. Check compatibility (`gald3r_min_version` host floor).
5. Back up the current plugin to `.gald3r_sys/plugins/.backup/<id>-<old-version>/`.
6. Download the new version and validate its `gald3r-plugin.yaml` manifest.
7. Check for component conflicts and show the added / removed / changed diff.
8. Confirm, then optionally run the new version's `upgrade.ps1` (user-confirmed).
9. Apply: remove components that disappeared, copy the new components into the
   canonical `.gald3r_sys/<type>/` dirs, and rewrite the `installed.yaml` entry.
10. Print a per-plugin summary.

## Steps

1. Run the backing script from the project root:
   ```powershell
   .gald3r_sys/plugins/scripts/update_plugin.ps1 [-PluginId <id>] [-DryRun] [-Force] [-NoBackup]
   ```
   Flag mapping: `--check` / `--dry-run` -> `-DryRun`; `--force` -> `-Force`;
   `--no-backup` -> `-NoBackup`; positional `<plugin-id>` -> `-PluginId <id>`.
2. Review the update-availability table.
3. Confirm the apply prompt (and the `upgrade.ps1` prompt, if the new version ships one).
4. Read the summary; on partial failure the script exits 1 and rolls back the
   failed plugin from its backup.

## Notes

- **Backups** live under `.gald3r_sys/plugins/.backup/` and are NOT cleaned by other
  commands. After a successful update the script keeps the 3 most recent backups per
  plugin (`-KeepBackups`) and prunes older ones.
- **Rollback**: any failure after the backup is created restores the plugin from
  backup, reverts the `installed.yaml` entry, and logs to
  `.gald3r/logs/plugin_update_failures.log`. Use `--no-backup` only knowingly — it
  disables rollback.
- **Lifecycle scripts** (`upgrade.ps1`) never run silently — they are opt-in and
  user-confirmed (ADR-015 security model).
- **Exit codes**: `0` all targeted plugins succeeded (or nothing to do); `1` partial
  failure (at least one plugin failed and was rolled back).
- Registry URL resolves from `.gald3r_sys/config/plugins.yaml` (`registry_url:`),
  falling back to the ADR-015 default raw GitHub registry; override with `-RegistryUrl`.
- ASCII-safe output markers (`[UPDATE]`, `[OK]`, `[SKIP]`, `[FAIL]`, `[INFO]`,
  `[WARN]`); PS 5.1 + PS 7 compatible.
- Sibling commands: `g-plugin-install`, `g-plugin-remove`, `g-plugin-list`,
  `g-plugin-new`.
