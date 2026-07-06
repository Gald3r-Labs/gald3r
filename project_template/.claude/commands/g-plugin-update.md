---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-plugin-update — Update an installed plugin from a local source

Re-apply / move an installed plugin to a newer (or forced) version from a local source
directory: compare the installed version against the source's manifest, check host
compatibility (`gald3r_min_version`), and (unless `--dry-run`) re-materialize via the
same install path (removes this plugin's stale files, copies the new ones, rewrites
`installed.yaml`). (ADR-015, plugin-system / SS-007; engine-first per T663 — see
`gald3r.systems.plugins.PluginSystem.update`, the Python successor to the historical
`update_plugin.ps1`, retired T1601 / PS1-KILL epic T667.)

## Usage

```
gald3r plugin update <plugin-id>                    Update from the already-vendored source
gald3r plugin update <plugin-id> --source <path>     Update from an explicit local source dir
gald3r plugin update <plugin-id> --dry-run           Print the planned change; apply nothing
gald3r plugin update <plugin-id> --force             Re-install even if already at that version
```

## What it does

1. Look up the plugin's installed entry in `installed.yaml`; fail if not installed.
2. Resolve the source (`--source`, else the already-vendored `.gald3r_sys/plugins/<id>/`)
   and read its `gald3r-plugin.yaml` manifest.
3. Check compatibility (`gald3r_min_version` host floor); fail if incompatible.
4. Compare source version against the installed version. Same version + no `--force`
   -> `up_to_date`, nothing applied.
5. `--dry-run`: return the planned `from_version -> to_version` and component inventory;
   apply nothing.
6. Otherwise, apply via the same path as `plugin install`: remove this plugin's stale
   components, copy the new components into the canonical `.gald3r_sys/<type>/` dirs
   (provenance-stamped, gald3r-core components never overwritten), and rewrite the
   `installed.yaml` entry.

## Steps

1. Run from the project root:
   ```bash
   uv run --project .gald3r_sys/engine gald3r plugin update <plugin-id> [--source <path>] [--dry-run] [--force]
   ```
2. Read the JSON-shaped result: `{ok, status, id, from_version, to_version, components, reasons, dry_run}`.
   `status` is one of `not_installed`, `no_source`, `incompatible`, `up_to_date`,
   `planned` (dry-run), `updated`, `forced`.

## Notes

- **Scope narrowing from the historical `.ps1` (T1601)**: this is a **single-plugin,
  local-source** operation. The old `update_plugin.ps1`'s bulk "check every installed
  plugin against a remote HTTPS registry" loop, CHANGELOG excerpt printer, interactive
  confirmation prompts, `upgrade.ps1` lifecycle execution, and versioned on-disk backup
  directory were designed-but-not-carried-forward when the engine module absorbed this
  op (matching `INSTALL`/`REMOVE`/`LIST`/`NEW`/`CHECK_COMPAT`, which were similarly
  "designed but never ported" per the engine module's own docstring). Remote `https://`
  registry sources are intentionally not fetched by this engine surface.
- To enumerate installed plugins first: `gald3r plugin list`.
- To check a candidate source's compatibility before updating: `gald3r plugin check-compat <path>`.
- Lifecycle scripts (`upgrade.ps1` / `install.ps1` / `uninstall.ps1`) are data-declared
  on a plugin but are **never** auto-run by this engine surface (ADR-015 D7).
- Sibling ops on the same `gald3r plugin` CLI surface: `install`, `remove` (alias
  `uninstall`), `list`, `new`, `check-compat`.
