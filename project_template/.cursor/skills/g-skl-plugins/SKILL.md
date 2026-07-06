---
name: g-skl-plugins
maturity: beta
description: Authoritative reference for the gald3r plugin system — install, remove, update, list, scaffold, and compatibility-check third-party plugins that bundle skills/commands/agents/rules/hooks. Documents the gald3r-plugin.yaml manifest, registry.json, the installed.yaml ledger, and the plugin_source: provenance convention (ADR-015 / SS-007). Single source of truth for everything plugin-related.
token_budget: medium
subsystem_memberships: [PLUGIN_SYSTEM]
---

# g-skl-plugins — gald3r plugin system reference

> Plays the role for the **plugin lifecycle** that `g-skl-tasks` plays for tasks: the one
> place an agent reads to understand how plugins are installed, removed, updated, listed,
> authored, and checked for compatibility.

**Design source of truth**: **ADR-015** (maintainer-tree ADR — not shipped in installs; T1652 D4)
and subsystem **SS-007** (`.gald3r/subsystems/plugin_system.md`). Read those for the
*why*; this skill is the operational *how*.

**Activate for**: install a plugin, remove/uninstall a plugin, update plugins, list
installed/available plugins, scaffold a new plugin, check plugin compatibility with the
host, author a third-party plugin, or any `@g-plugin-*` operation.

---

## ⚠️ Implementation-state honesty (read this first)

The plugin system was designed in full (ADR-015) and the lifecycle is now a **first-class
engine surface** (T663, epic T541): all six ops live in `gald3r.systems.plugins.PluginSystem`
and are reachable via the `gald3r plugin …` CLI and the `gald3r_plugin_*` MCP tools — one
implementation, no PowerShell. The retired PowerShell scripts (BUG-128/129/130) are **not**
the source of truth; prefer the engine ops.

| Operation | Engine op (CLI) | MCP tool | State |
|-----------|-----------------|----------|-------|
| INSTALL | `gald3r plugin install <local-source> [--dry-run]` | `gald3r_plugin_install` | ✅ Engine (T663) |
| REMOVE | `gald3r plugin remove <id>` (alias `uninstall`) `[--dry-run]` | `gald3r_plugin_remove` | ✅ Engine (T663) |
| LIST | `gald3r plugin list` | `gald3r_plugin_list` | ✅ Engine (T663) |
| NEW | `gald3r plugin new <id> [--name --author --subsystem]` | `gald3r_plugin_new` | ✅ Engine (T663) |
| CHECK_COMPAT | `gald3r plugin check-compat <local-source>` | `gald3r_plugin_check_compat` | ✅ Engine (T663) |
| UPDATE | `gald3r plugin update <id> [--source --force --dry-run]` | `gald3r_plugin_update` | ✅ Engine (T663) |

The engine owns the **manifest schema**, the **`installed.yaml` ledger**, the **registry
config**, the **compat floor** (`gald3r_min_version` ≤ `.gald3r_sys/VERSION`), the **D6
conflict-abort** (never overwrites a non-plugin core component), and the **`plugin_source:`
provenance stamping** that makes safe removal possible — a single source reused by every op.

**Source resolution**: the engine installs from a **local path / vendored
`.gald3r_sys/plugins/<id>/` dir** (a remote `https://` source is rejected, matching the
engine's no-daemon / single-GET discipline — vendor the plugin dir first). Lifecycle scripts
(`install.ps1` / `uninstall.ps1` / `upgrade.ps1`) are data-declared but **never auto-run** by
the engine (ADR-015 D7) — inspect and run them yourself if you opt in.

The legacy `@g-plugin-*` command names and the retired `.gald3r_sys/plugins/scripts/*.ps1`
remain documented below for historical context; the engine ops above are the live path.

---

## Concepts

A **plugin** is a self-contained, versioned directory that bundles any subset of gald3r's
five component types plus one declarative manifest. It is **additive**: it copies components
into the canonical component dirs and **never overwrites gald3r-core components** (conflict =
abort, ADR-015 D6).

```
.gald3r_sys/plugins/<plugin-id>/
├── gald3r-plugin.yaml      # manifest (data-only, REQUIRED)
├── CHANGELOG.md            # version history (used for update excerpts)
├── skills/<name>/SKILL.md  # folder-per-skill
├── commands/*.md
├── agents/*.md
├── rules/*.md
├── hooks/*.ps1
├── install.ps1             # optional, opt-in lifecycle script
├── uninstall.ps1           # optional, opt-in lifecycle script
└── upgrade.ps1             # optional, opt-in lifecycle script
```

**Component mapping** (plugin subdir → canonical target; `skills` is folder-per-skill, the
rest are flat files):

| Plugin subdir | Copied to | Type |
|---|---|---|
| `skills/<name>/SKILL.md` | `.gald3r_sys/skills/<name>/` | skill |
| `commands/*.md` | `.gald3r_sys/commands/` | command |
| `agents/*.md` | `.gald3r_sys/agents/` | agent |
| `rules/*.md` | `.gald3r_sys/rules/` | rule |
| `hooks/*.ps1` | `.gald3r_sys/hooks/` | hook |
| `gald3r-plugin.yaml` | stays at plugin root | manifest |
| `install.ps1` / `uninstall.ps1` / `upgrade.ps1` | stays; opt-in run | lifecycle script |

Key state files:

| File | Role |
|------|------|
| `.gald3r_sys/plugins/<id>/` | versioned, inspectable plugin source |
| `.gald3r_sys/plugins/installed.yaml` | install ledger (record of truth for removal/update) |
| `.gald3r_sys/plugins/.backup/<id>-<version>/` | pre-update backups (≤3 retained per plugin) |
| `.gald3r_sys/config/plugins.yaml` | host config; `registry_url:` override |
| `.gald3r/config/plugins/<id>.yaml` | per-plugin, project-local config (gitignorable) |
| `.gald3r/logs/plugin_update_failures.log` | append-only update-failure audit |
| registry `registry.json` | GitHub-hosted catalog of available plugins (raw HTTPS) |

Default registry: `https://raw.githubusercontent.com/gald3r/plugin-registry/main/registry.json`
(override via `plugins.yaml registry_url:` or `-RegistryUrl`).

---

## Agent decision tree

```
Need to work with a plugin?
│
├─ Add a new plugin to the project ──────────────► INSTALL  (@g-plugin-install)        (planned here)
├─ Get newer versions of installed plugins ──────► UPDATE   (@g-plugin-update)         ✅ available
├─ See what's installed / available ─────────────► LIST     (@g-plugin-list)           (planned here)
├─ Take a plugin out cleanly ────────────────────► REMOVE   (@g-plugin-remove)         (planned here)
├─ Author / start a brand-new plugin ────────────► NEW      (@g-plugin-new)            (planned here)
└─ Will plugin X run on this host? ──────────────► CHECK_COMPAT (validate_plugin_manifest.ps1)  (planned here)
```

Before invoking any non-UPDATE operation, confirm its script exists:
```powershell
Test-Path .gald3r_sys/plugins/scripts/install_plugin.ps1   # etc.
```
If absent, do **not** fabricate the behavior — tell the user the operation is designed
(ADR-015) but not yet implemented in this install, and stop.

---

## OPERATIONS

### UPDATE — `@g-plugin-update <id>`  ✅ implemented (engine, T663 / T1601)

**When**: an installed plugin's local source has a newer version, or you need to re-apply a
plugin (`--force`). Backed by `gald3r.systems.plugins.PluginSystem.update` — the Python
successor to the historical `update_plugin.ps1` (retired T1601, PS1-KILL epic T667).

**Invoke** (from project root):
```bash
uv run --project .gald3r_sys/engine gald3r plugin update <id> [--source <path>] [--dry-run] [--force]
```

| Flag | Effect |
|------|--------|
| `<id>` | Required. Update this one installed plugin. |
| `--source <path>` | Explicit local source dir (default: the already-vendored `.gald3r_sys/plugins/<id>/`) |
| `--dry-run` | Return the planned `from_version -> to_version` + component inventory; apply nothing |
| `--force` | Re-install even if already at the source version |

**Flow**: look up `installed.yaml` entry → resolve source + read its manifest → compat
check (`gald3r_min_version`) → compare versions (same + no `--force` -> `up_to_date`,
stop) → (`--dry-run` stops here) → apply via the same path as `plugin install` (remove
stale components, copy new, rewrite ledger). Returns
`{ok, status, id, from_version, to_version, components, reasons, dry_run}`.

**Scope narrowing from the historical `.ps1` (T1601)**: this is **single-plugin,
local-source only** — no bulk "check every installed plugin against a remote HTTPS
registry" loop, no CHANGELOG excerpt, no interactive confirm prompts, no `upgrade.ps1`
lifecycle execution, and no versioned on-disk backup/rollback directory. These were
designed-but-not-carried-forward when the engine module absorbed this op, matching
INSTALL/REMOVE/LIST/NEW/CHECK_COMPAT below (also "designed but never ported"). Remote
`https://` registry sources are intentionally not fetched by this engine surface —
use `--source <local-path>` for anything not already vendored under `.gald3r_sys/plugins/`.

---

### INSTALL — `@g-plugin-install <id>`  (planned here)

**When**: add a plugin to the project for the first time. **ADR-015 contract**:

```powershell
.gald3r_sys/plugins/scripts/install_plugin.ps1 -Source <local-path|github-url> [-Version <semver>] [-RunInstallScript] [-DryRun]
```

- Fetch from a local path or GitHub URL (GitHub-URL path designed; local-path path is what
  was network-tested in the source repo).
- Validate `gald3r-plugin.yaml`; enforce `gald3r_min_version` host floor.
- **Conflict-abort** (D6): refuses to overwrite any gald3r-core component.
- Copy components into canonical dirs; stamp each with `plugin_source: <id>` frontmatter.
- Record the `installed.yaml` ledger entry.
- **Never auto-runs lifecycle scripts** (D7): `install.ps1` runs only with opt-in
  `-RunInstallScript`, after printing a preview.

### REMOVE — `@g-plugin-remove <id>` (alias `@g-plugin-uninstall`)  (planned here)

**When**: cleanly uninstall a plugin. **ADR-015 contract** (`remove_plugin.ps1`):

```powershell
.gald3r_sys/plugins/scripts/remove_plugin.ps1 -PluginId <id> [-Force] [-DryRun] [-KeepConfig] [-RunUninstallScript]
```

- Uses `installed.yaml` as the record of truth (D4); removes exactly the listed component
  files — but **only** those still carrying this plugin's `plugin_source:` provenance, so
  gald3r-core and other plugins' files are never touched (D6).
- Preserves components modified after install unless `-Force`.
- Runs `uninstall.ps1` only with opt-in `-RunUninstallScript`, after a preview (D7).
- `-KeepConfig` retains `.gald3r/config/plugins/<id>.yaml`. Idempotent (removing an absent
  plugin is a no-op); warns on dangling cross-plugin references (cascade check).

### LIST — `@g-plugin-list`  (planned here)

**When**: see installed plugins (`installed.yaml`) and/or available plugins (`registry.json`).
Reads ledger + registry; reports id, installed version, latest version, and components.

### NEW — `@g-plugin-new <id>`  (planned here)

**When**: scaffold a skeleton to author a new plugin — creates `.gald3r_sys/plugins/<id>/`
with a starter `gald3r-plugin.yaml`, empty component subdirs, a CHANGELOG, and optional
lifecycle-script stubs. See the third-party development guide below for the manifest the
scaffolder produces.

### CHECK_COMPAT — `validate_plugin_manifest.ps1`  (planned here)

**When**: validate a plugin's manifest and check host compatibility before install/update.
**ADR-015 contract**:

```powershell
.gald3r_sys/plugins/scripts/validate_plugin_manifest.ps1 -PluginDir <path>   # exit 0 = valid
```

Checks the manifest is present and well-formed (at minimum `id` + `version`), and that
`gald3r_min_version` ≤ the host's `.gald3r_sys/VERSION` (SemVer compare). The engine's
`plugin update` op (see UPDATE above) calls the equivalent `PluginSystem.check_compat`
internally.

---

## Manifest format — `gald3r-plugin.yaml`

Data-only YAML (no inline code), at the plugin root. Example:

```yaml
# gald3r-plugin.yaml
id: gald3r-git-toolkit          # REQUIRED — unique, kebab-case, matches dir + ledger key
version: 1.2.0                  # REQUIRED — SemVer
name: Git Toolkit               # human-readable
description: Extra git automation commands and a pre-push hook.
author: jane-doe
homepage: https://github.com/jane-doe/gald3r-git-toolkit
license: MIT
gald3r_min_version: 1.8.0       # host floor — refuse install/update below this
default_subsystem: PLATFORM_INTEGRATION   # inherited by components omitting their own tag
components:                     # what this plugin ships (mirrors the subdirs)
  commands:
    - g-git-sync.md
  hooks:
    - g-git-sync-hook.ps1
  skills:
    - skl-git-helper
lifecycle:                      # all optional, all opt-in, never auto-run
  install: install.ps1
  uninstall: uninstall.ps1
  upgrade: upgrade.ps1
```

Rules:
- `id` + `version` are the only hard-required fields (matches the validator's minimal check).
- `id` must match the plugin directory name and the `installed.yaml` ledger key.
- Manifests are **data-only** — no executable logic. Behavior lives in the opt-in
  `install.ps1` / `uninstall.ps1` / `upgrade.ps1` lifecycle scripts.
- Every copied component MUST carry `subsystem_memberships:` (g-rl-38). If a component file
  omits it, it inherits `default_subsystem` from the manifest.

## Registry format — `registry.json`

GitHub-hosted catalog format (ADR-015 design). **Not fetched by the current engine
surface** (T1601): `gald3r plugin update`/`install`/`check-compat` operate on local
source paths only and intentionally do not download from a remote `https://` registry
— see the UPDATE section's scope-narrowing note above. `registry_url:` in
`.gald3r_sys/config/plugins.yaml` is still read (`gald3r plugin list` reports it) but
is not dereferenced over HTTP by this tree. Accepted shape (when a registry consumer
is added): both `{ "plugins": { ... } }` and a bare top-level map.

```json
{
  "plugins": {
    "gald3r-git-toolkit": {
      "version": "1.2.0",
      "source": "https://github.com/jane-doe/gald3r-git-toolkit",
      "gald3r_min_version": "1.8.0",
      "description": "Extra git automation commands and a pre-push hook."
    },
    "gald3r-3d-pack": {
      "version": "0.4.1",
      "source": "https://github.com/acme/gald3r-3d-pack",
      "gald3r_min_version": "1.9.0"
    }
  }
}
```

- `version` (string, SemVer) and `source` drive the update plan; `gald3r_min_version` is the
  compatibility floor; `description` is informational.
- `source` may be an `https://` URL (needs the installer's download helper) or a **local
  path** (a versioned subdir `<source>/<version>/` or the dir itself — used for fixtures and
  vendored sources; this is the path that works on the current tree).
- Override the URL via `plugins.yaml registry_url:` or the `-RegistryUrl` flag; a local
  file path is also accepted (test fixtures).

## Install ledger — `installed.yaml`

Written/read by the lifecycle scripts; the record of truth for removal and update. Shape:

```yaml
# gald3r plugin install ledger (installed.yaml) -- ADR-015
plugins:
  gald3r-git-toolkit:
    version: 1.2.0
    source: https://github.com/jane-doe/gald3r-git-toolkit
    installed_at: 2026-05-01T00:00:00Z
    components:
      commands: [g-git-sync.md]
      hooks: [g-git-sync-hook.ps1]
```

## `plugin_source:` tagging convention

Every component a plugin copies into a canonical dir is stamped with a `plugin_source:`
field in its frontmatter (markdown) or header comment (PowerShell), naming the owning
plugin id. This provenance tag is what makes safe removal possible:

```markdown
---
subsystem_memberships: [PLATFORM_INTEGRATION]
plugin_source: gald3r-git-toolkit
---
```

```powershell
# g-git-sync-hook.ps1
# @subsystems: PLATFORM_INTEGRATION
# plugin_source: gald3r-git-toolkit
```

- REMOVE deletes only files that still carry the matching `plugin_source:`, so gald3r-core
  files (no tag) and other plugins' files are never touched.
- It also enables deterministic re-materialization after parity sync (`-SyncGaldSys`)
  overwrites the canonical dirs (depends on SS-004 parity-pipeline).

---

## What NOT to do

| ❌ Don't | ✅ Do instead | Why |
|---------|--------------|-----|
| Manually edit a plugin-installed file in `.gald3r_sys/commands/` etc. | Edit the plugin source in `.gald3r_sys/plugins/<id>/` and re-run `@g-plugin-update` (or update upstream) | Hand-edits are silently lost on the next update/re-materialize, and post-install modifications get preserve-skipped on REMOVE |
| Manually `Remove-Item` plugin component files | Use `@g-plugin-remove <id>` | Leaves a stale `installed.yaml` ledger entry and dangling cross-plugin references |
| Install from an untrusted source without inspecting it | Read the plugin's `install.ps1` / `uninstall.ps1` / `upgrade.ps1` **before** opting in with `-RunInstallScript` etc. | Lifecycle scripts execute arbitrary code; ADR-015 makes them opt-in + preview-first precisely so you review them |
| Run `@g-plugin-update --no-backup` casually | Keep backups on; use `--no-backup` only when you understand rollback is disabled | A mid-update failure with no backup can leave the install in a broken half-applied state |
| Let a plugin overwrite a gald3r-core component | Resolve the conflict upstream; install aborts on conflict by design | Plugins are additive only (D6); silently shadowing core breaks the framework |
| Invoke a `@g-plugin-*` command whose script is absent on this tree | Check `Test-Path` first; report it as designed-but-not-implemented | Fabricating behavior for a missing script misleads the user |

---

## Third-party plugin development guide

To author a plugin others can install:

1. **Scaffold** the directory: `.gald3r_sys/plugins/<plugin-id>/` (use `@g-plugin-new` when
   present, or create it by hand).
2. **Write `gald3r-plugin.yaml`** with at least `id` + `version`; add `name`, `description`,
   `author`, `license`, `homepage`, `gald3r_min_version`, `default_subsystem`, `components`,
   and (optional) `lifecycle`.
3. **Add component files** under the matching subdirs, following gald3r naming conventions:

   | Component | Subdir | Naming convention |
   |-----------|--------|-------------------|
   | Skill | `skills/<name>/SKILL.md` | folder-per-skill; folder `skl-<topic>` or `g-skl-<topic>`; `SKILL.md` with frontmatter (`name`, `description`, `subsystem_memberships`, optional `skill_trust_level`) |
   | Command | `commands/*.md` | `g-<verb>-<noun>.md` (kebab-case), frontmatter with `subsystem_memberships:` |
   | Agent | `agents/*.md` | `g-agnt-<role>.md`, frontmatter with `subsystem_memberships:` |
   | Rule | `rules/*.md` | `g-rl-NN-<topic>.md`, frontmatter with `subsystem_memberships:` |
   | Hook | `hooks/*.ps1` | `g-hk-<name>.ps1`, `# @subsystems:` comment in first 15 lines |

4. **Tag every component** with `subsystem_memberships:` (g-rl-38) and — once installed —
   `plugin_source: <plugin-id>` (the installer stamps this; author files may pre-declare it).
5. **Keep manifests data-only.** Any real work goes in opt-in `install.ps1` / `uninstall.ps1`
   / `upgrade.ps1`. Make them ASCII-safe and PS 5.1 + PS 7 compatible; accept
   `-ProjectRoot`, and for `upgrade.ps1` also `-FromVersion` / `-ToVersion`.
6. **Maintain `CHANGELOG.md`** with `## [x.y.z]` headers — `@g-plugin-update` shows the
   excerpt between the installed and new version.
7. **Version with SemVer** and set `gald3r_min_version` to the lowest host you support.
8. **Publish** by adding an entry to a `registry.json` (your own or the gald3r registry) with
   `version`, `source`, and `gald3r_min_version`.

Trust note (mirrors `skl-skill-create` / C-032): contributed skills may declare a
`skill_trust_level:` of `core` / `local` / `community`. `community` or unset surfaces a
non-blocking provenance warning at install time — installers should inspect community plugin
bodies before first invocation.

---

## Related

- **`g-skill-pack-add` / `-del` / `-list` / `-save`** — the *skill-pack* system
  (`.gald3r_sys/skill_packs/<pack>/`) is a separate, curated bundle-of-skills mechanism, not
  the third-party plugin system documented here. Don't conflate them.
- **SS-007 `plugin_system.md`** — subsystem spec (decisions, scope boundary, constraints).
- **ADR-015** — foundational architecture decisions (D1–D7 referenced throughout; maintainer-tree ADR, not shipped).
- **g-rl-38 component-creation-standards** — mandatory `subsystem_memberships:` tagging that
  plugin components must satisfy.
