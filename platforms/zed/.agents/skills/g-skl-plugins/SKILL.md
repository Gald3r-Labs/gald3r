---
name: g-skl-plugins
maturity: beta
description: Authoritative reference for the gald3r plugin system — install, remove (uninstall), update, list, and per-project enable/disable git-cloned, SKILL.md-based third-party plugins via `gald3r plugin <verb>`. Documents the live `PluginManager` mechanism (git clone/pull/rmtree, GLOBAL install, no manifest, no ledger) plus the per-project ON/OFF association overlay (T287), and honestly flags the two operations (scaffold/NEW and CHECK_COMPAT) that are not implemented. Single source of truth for everything plugin-related.
token_budget: medium
subsystem_memberships: [PLUGIN_SYSTEM]
---

# g-skl-plugins — gald3r plugin system reference

> Plays the role for the **plugin lifecycle** that `g-skl-tasks` plays for tasks: the one
> place an agent reads to understand how plugins are installed, removed, updated, listed,
> and authored.

**Activate for**: install a plugin, remove/uninstall a plugin, update plugins, list
installed plugins, author a third-party plugin, or any `gald3r plugin <verb>` operation.

---

## ⚠️ Implementation-state honesty (read this first)

The live plugin system is **much simpler** than the historical ADR-015 design (a
`gald3r-plugin.yaml` component manifest copied into canonical `.gald3r_sys/` dirs, an
`installed.yaml` ledger, `plugin_source:` provenance stamping) that earlier drafts of this
skill described. That manifest/ledger design was **never built** in `gald3r_core` — it is
not a "designed but not-yet-ported" gap, it is a superseded design that this file
previously described as if it were current (BUG-129).

What actually shipped and is tested end-to-end
(`gald3r_core.server_bridge.plugins.manager.PluginManager`, T606 C-3, wired through the
T72 `cli.capabilities.PluginCapability` composition seam — `cli/commands/plugins.py`,
`composition/adapters.py::PluginAdapter`, `composition/build.py`) treats **a plugin as a
git repository with a `SKILL.md` file at its root** — nothing more.

| Operation | CLI | State |
|-----------|-----|-------|
| INSTALL | `gald3r plugin install <name-or-git-url>` | ✅ implemented |
| REMOVE (verb: `uninstall`) | `gald3r plugin uninstall <name>` | ✅ implemented |
| UPDATE | `gald3r plugin update <name>` | ✅ implemented |
| LIST | `gald3r plugin list [--project-root PATH] [--json]` | ✅ implemented |
| ENABLE (per-project) | `gald3r plugin enable <name> [--project-root PATH] [--json]` | ✅ implemented (T287) |
| DISABLE (per-project) | `gald3r plugin disable <name> [--project-root PATH] [--json]` | ✅ implemented (T287) |
| NEW (scaffold a plugin) | — | ❌ **not implemented** — no such verb exists |
| CHECK_COMPAT | — | ❌ **not implemented** — no such verb exists |

Confirmed live: `uv run gald3r plugin --help` reports exactly
`{install, uninstall, update, list, enable, disable}` — no `new`, no `check-compat`, no
`remove` alias (the alias is `uninstall`, not `remove`). `install`/`uninstall`/`update`
take no `--dry-run`, `--force`, `--source`, or `--keep-config` flag — each is a bare
`gald3r plugin <verb> <name-or-url>` (or `<name>`). `list`/`enable`/`disable` additionally
accept `--project-root PATH` (default: cwd) since they resolve the per-project
enable/disable overlay (see "Per-project enable/disable" below); confirm with
`gald3r plugin <verb> --help` if in doubt.

Do not resurrect the retired ADR-015 `.ps1` contract language
(`install_plugin.ps1` / `remove_plugin.ps1` / `validate_plugin_manifest.ps1`) — it does
not describe anything runnable on this tree.

---

## Concepts

A **plugin** is a git repository containing a `SKILL.md` file at its root.
`gald3r plugin install` clones it (`git clone --depth=1`) into the plugins directory and
requires `SKILL.md` to exist at the clone root — install aborts and removes the clone if
it doesn't. Nothing else about the plugin's contents is inspected, validated, or copied
elsewhere; the clone is used in place.

```
<plugins_dir>/<name>/          # a full --depth=1 git clone of the plugin's repo
├── SKILL.md                   # REQUIRED at the repo root — install aborts without it
└── ...                        # anything else the repo contains (not inspected)
```

Default `<plugins_dir>`: `<GALD3R_HOME>/plugins` (i.e. `~/.gald3r/plugins` unless
`GALD3R_HOME` is overridden) — resolved once at composition time
(`composition/build.py::_plugins_dir`); there is no per-invocation `--plugins-dir` flag.
**Install itself has no project concept at all** — it is one global directory shared by
every project on the machine, matching the real `PluginManager` (owner ruling, T287): a
plugin installed once is installed for every project, full stop. Per-project control is
layered on top, entirely separately — see "Per-project enable/disable" below.

Key state:

| Source | Role |
|--------|------|
| `<plugins_dir>/<name>/` | the git clone itself — this **is** the install record, there is no separate ledger file |
| `git remote get-url origin` (read live, per plugin, on `list`) | populates the `git_url` field shown by `list` |
| `SKILL.md` YAML frontmatter (`version`, `description`, `tags`) | populates the fields `list` shows; missing fields default to `"unknown"` (version) or empty |
| `.gald3r/config/plugins.yaml` (per project, T287) | the enable/disable overlay — see below; absent by default |

There is **no** `installed.yaml`, `.gald3r_sys/config/plugins.yaml`,
`.gald3r_sys/plugins/.backup/`, or `.gald3r/logs/plugin_update_failures.log` on this tree
— those belonged to the superseded ADR-015 design, not the live one. Likewise there is no
`plugin_source:` provenance stamping and no conflict-abort against core components: this
system clones a whole repo into its own directory, it does not merge files into
`.gald3r_sys/`. **`.gald3r/config/plugins/<id>.yaml` (one file per plugin) never existed
either** — do not confuse it with the real, T287 `.gald3r/config/plugins.yaml` (one file,
covering every plugin, see below), a different shape entirely.

A community registry manifest exists in code
(`https://raw.githubusercontent.com/gald3r-ecosystem/plugin-registry/main/manifest.yaml`,
read by `PluginManager.search()` / `_fetch_manifest()`) and is used internally to resolve
a bare registry slug passed to `install` into a git URL. It is **not exposed as its own
CLI verb** — there is no `gald3r plugin search` and no `gald3r plugin list --available`.
If the manifest is unreachable or the slug isn't listed, `install` falls back to assuming
`https://github.com/gald3r-ecosystem/<name>`.

**Do not confuse this with `gald3r_core.core.plugins`** (`Plugin` / `PluginRegistry` /
`discover_plugins` / `load_plugins`) — that is an unrelated, in-tree Python-package
extension-point mechanism (HA-016/feat-258) discovered at process start; it has nothing to
do with `gald3r plugin install` or third-party SKILL.md repos.

### Per-project enable/disable (T287)

Every project independently decides which of the globally-installed plugins it wants
active — install/uninstall/update never become per-project (owner ruling), but the
ON/OFF switch does. State lives in `<project_root>/.gald3r/config/plugins.yaml`
(`gald3r_core.core.plugins.association`), created on first `enable`/`disable`, absent by
default:

```yaml
schema_version: plugin-association-v1
plugins:
  my-skill:
    enabled: false
    entity_config: {}   # reserved slot — company/team/client component config (not yet
                         # written or read by any CLI verb; schema-only in this task)
```

- **No file, or a plugin missing from `plugins:`** → that plugin is enabled for this
  project. This is the load-bearing backward-compatibility rule: every project that has
  never touched `plugin enable`/`disable` behaves exactly as it did before T287 — every
  globally-installed plugin is active everywhere.
- Only an explicit `enabled: false` entry turns a plugin off, and only for the project
  whose `.gald3r/config/plugins.yaml` holds it — a sibling project's association file
  (or lack of one) is untouched.
- `entity_config` round-trips whatever a caller writes there, untouched. Nothing in the
  shipped CLI reads or writes it yet — the owner ruling asked for the schema to leave
  room for company/team/client-scoped plugin component config, not for a CLI to manage
  it in this pass.

## Agent decision tree

```
Need to work with a plugin?
│
├─ Add a new plugin (global, every project) ─────► INSTALL  `gald3r plugin install <src>`      ✅ implemented
├─ Get a newer version of an installed plugin ───► UPDATE   `gald3r plugin update <name>`       ✅ implemented
├─ See what's installed (+ per-project state) ───► LIST     `gald3r plugin list`                ✅ implemented
├─ Turn a plugin ON for THIS project ─────────────► ENABLE   `gald3r plugin enable <name>`       ✅ implemented (T287)
├─ Turn a plugin OFF for THIS project ────────────► DISABLE  `gald3r plugin disable <name>`      ✅ implemented (T287)
├─ Take a plugin out cleanly (global, every project) ► REMOVE `gald3r plugin uninstall <name>`   ✅ implemented
├─ Author / start a brand-new plugin ────────────► NEW      ❌ not implemented — hand-author a git repo with a SKILL.md at its root (see the guide below)
└─ Will plugin X run on this host? ──────────────► CHECK_COMPAT ❌ not implemented — no compatibility floor exists; nothing checks a version/host-min before install
```

Before telling a user an operation is unsupported, confirm with `gald3r plugin --help`
(or the per-verb `<verb> --help`) rather than trusting stale docs — this file has been
wrong about this before (BUG-129).

---

## OPERATIONS

### INSTALL — `gald3r plugin install <name-or-git-url>` ✅ implemented

**When**: add a plugin to the project for the first time.

- `<name-or-git-url>` may be a full `https://` / `git@` URL (cloned directly, local
  folder name derived from the last path segment, `.git` suffix stripped), or a bare
  registry slug (resolved via the community manifest, falling back to
  `https://github.com/gald3r-ecosystem/<name>` if unresolved).
- Runs `git clone --depth=1 <url> <plugins_dir>/<name>/`.
- Fails if a plugin with that local name is already installed (message points at
  `gald3r plugin update` instead).
- Fails, and removes the partial clone, if the cloned repo has no `SKILL.md` at its root.
- No manifest validation, no compatibility check, no component copying, no lifecycle
  script of any kind runs — install is exactly "clone it, verify `SKILL.md` exists."

```bash
gald3r plugin install https://github.com/example/my-skill
gald3r plugin install gald3r-skl-aws   # resolved via the community registry manifest
```

### REMOVE — `gald3r plugin uninstall <name>` ✅ implemented

**When**: cleanly take out an installed plugin. (The command verb is `uninstall`, not
`remove` — there is no `remove` alias.)

- Deletes `<plugins_dir>/<name>/` outright (`shutil.rmtree`) — no confirmation prompt,
  no `--force` flag, no dry-run, no preserved backup.
- Fails with a clean error if the named plugin isn't installed.
- Does not distinguish "modified since install" from "untouched" — everything under the
  plugin's directory is removed regardless.

```bash
gald3r plugin uninstall my-skill
```

### UPDATE — `gald3r plugin update <name>` ✅ implemented

**When**: pull the latest commit for an already-installed plugin.

- Runs `git -C <plugins_dir>/<name> pull --ff-only`.
- Fails with a clean error if the named plugin isn't installed.
- Fails if the fast-forward pull itself fails (diverged history, local edits conflicting,
  no network, etc.) — surfaces git's stderr.
- Returns the git output (or `"Updated."` if git printed nothing useful) as the status
  line; there is no version comparison, no `--dry-run`, no `--force`, no `--source`
  override, and no CHANGELOG excerpt — it is a plain `git pull --ff-only`, nothing more.

```bash
gald3r plugin update my-skill
```

### LIST — `gald3r plugin list [--project-root PATH] [--json]` ✅ implemented

**When**: see what's currently installed, and (T287) whether THIS project has it enabled.

- Scans `<plugins_dir>/` for subdirectories containing a `SKILL.md`; there is no separate
  registry of "available but not installed" plugins reachable from this verb.
- For each installed plugin, reports `name` (folder name), `version` (from `SKILL.md`
  frontmatter, else `"unknown"`), `path`, `git_url` (live `git remote get-url origin`,
  empty string if not resolvable), `description`, `tags` (from frontmatter), and (T287)
  `enabled` — resolved against `--project-root`'s `.gald3r/config/plugins.yaml`
  (default `--project-root`: cwd; see "Per-project enable/disable" above).
- `--json` emits the same fields (including `enabled`) as a JSON array; the default
  human view prints `name  version  path` per line (appending `  (disabled)` when that
  project has it off), or `No plugins installed.` when empty.

```bash
gald3r plugin list
gald3r plugin list --json
gald3r plugin list --project-root /path/to/other/project
```

### ENABLE — `gald3r plugin enable <name> [--project-root PATH] [--json]` ✅ implemented (T287)

**When**: turn a globally-installed plugin back ON for one project (or turn it on there
for the first time — every plugin starts enabled everywhere by default, so this is
mainly for reversing a prior `disable`).

- Fails with a clean error if `<name>` isn't installed globally (checked live against
  `<plugins_dir>/`, not against the association file).
- Writes/updates `<project_root>/.gald3r/config/plugins.yaml`, creating
  `.gald3r/config/` if needed; every OTHER plugin's entry (and this plugin's
  `entity_config`, if any) round-trips unchanged.
- Prints `plugin '<name>' enabled for <project_root>` (or the full record as JSON).

```bash
gald3r plugin enable my-skill
gald3r plugin enable my-skill --project-root /path/to/other/project
```

### DISABLE — `gald3r plugin disable <name> [--project-root PATH] [--json]` ✅ implemented (T287)

**When**: turn a globally-installed plugin OFF for one project without uninstalling it
(it stays installed globally, and stays active for every OTHER project).

- Same install check, same file-write behavior, same `entity_config` preservation as
  `enable` — only the `enabled` value differs.
- Prints `plugin '<name>' disabled for <project_root>` (or the full record as JSON).
- This does **not** remove the plugin's files, does **not** touch other projects, and
  does **not** stop `gald3r plugin update`/`uninstall` from still operating on it (those
  stay global-only and ignorant of enable/disable state entirely).

```bash
gald3r plugin disable my-skill
```

### NEW — ❌ not implemented

**No `gald3r plugin new` (or any scaffold) verb exists.** There is no generator that
creates a starter plugin directory, manifest, or CHANGELOG. To author a new plugin today,
follow the "Authoring a `SKILL.md` for a plugin" section below by hand — create a git
repo, add a `SKILL.md` at its root, and publish it. If this capability is wanted, file it
as a real follow-up task rather than assuming it already exists.

### CHECK_COMPAT — ❌ not implemented

**No `gald3r plugin check-compat` (or equivalent) verb exists.** There is no
`gald3r_min_version` field, no host-version floor, and nothing in `install`/`update`
checks compatibility before acting — the only gate `install` applies is "does the clone
have a `SKILL.md` at its root." Do not tell a user a plugin was "compatibility-checked";
it wasn't.

---

## Authoring a `SKILL.md` for a plugin

`gald3r plugin list` reads `version`, `description`, and `tags` from a plugin's frontmatter
(via `gald3r_core.crash._frontmatter.extract_frontmatter`, a permissive YAML-frontmatter
parser that returns `{}` rather than raising on a malformed block); `install` itself does
not parse the frontmatter — it only checks that `SKILL.md` exists. A minimal example:

```markdown
---
name: my-plugin-skill
version: 1.2.0
description: What this plugin does.
tags: [example, third-party]
---

# my-plugin-skill

...
```

Fields beyond `version`/`description`/`tags` are not read by the plugin system itself,
but should still follow the general skill-authoring convention used elsewhere in gald3r
(`name`, `subsystem_memberships:`, optional `skill_trust_level:` per `skl-skill-create` /
C-032) since the file is a normal `SKILL.md` once a `SkillLoader` picks it up — the
plugin installer itself does not validate or enforce any of that, it only checks that the
file exists.

---

## What NOT to do

| ❌ Don't | ✅ Do instead | Why |
|---------|--------------|-----|
| Assume `install` merges files into `.gald3r_sys/` | Expect a full repo clone under `<plugins_dir>/<name>/` and nothing else | There is no component-copy step in the live implementation |
| Look for `installed.yaml`, `plugin_source:` tags, or a compat-floor field | Treat the presence of `<plugins_dir>/<name>/SKILL.md` as the install record | Those artifacts belong to the superseded ADR-015 design, not the shipped one |
| Run `gald3r plugin uninstall` expecting a confirmation prompt or backup | Confirm the plugin name first (`gald3r plugin list`) — removal is an immediate, unconditional `rmtree` | No `--force`, no dry-run, no undo |
| Tell a user NEW or CHECK_COMPAT "just needs a flag" | Say plainly that no such verb exists | Fabricating behavior for a missing verb misleads the user (this file did exactly that until BUG-129) |
| Reference `install_plugin.ps1` / `remove_plugin.ps1` / `validate_plugin_manifest.ps1` as the current contract | Reference `gald3r plugin <verb> --help` and this file | Those scripts were retired/never built here; they don't run |
| Assume `gald3r plugin install` becomes per-project, or that `enable`/`disable` install/uninstall anything | Install/uninstall/update stay global-home-only; `enable`/`disable` only flip a per-project `enabled` flag in `.gald3r/config/plugins.yaml` | Owner ruling (T287): one global install, per-project ON/OFF overlay — never per-project vendored copies |
| Look for a CLI verb that reads/writes a plugin's `entity_config` | There isn't one yet — the schema slot exists (`.gald3r/config/plugins.yaml`), nothing in `cli/commands/plugins.py` populates it | T287 was schema-design-complete, implementation-minimal for `entity_config`; a real editing verb is a future follow-up, not shipped here |

---

## Related

- **`g-skill-pack-add` / `-del` / `-list` / `-save`** — the *skill-pack* system
  (`.gald3r_sys/skill_packs/<pack>/`, `crash/skill_packs.py`) is a separate, curated
  bundle-of-skills mechanism with its own install path (`gald3r skill-pack …`), not the
  git-clone plugin system documented here. Don't conflate them.
- **`gald3r_core.core.plugins`** — unrelated in-tree Python-package extension-point
  system (`Plugin`, `PluginRegistry`, `discover_plugins`, `load_plugins`); shares the word
  "plugin" but is not this skill's subject.
- **`.gald3r/subsystems/plugin-precedence.md`** — a separate, `status: planned` subsystem
  covering CRASH-catalog precedence across project-local/plugin/gald3r-extras/stock
  sources; not yet implemented, and not the install/remove/update/list mechanism above.
- **ADR-015** — the original component-manifest/ledger design (maintainer-tree ADR, not
  shipped in installs). Useful for historical *why* context only; it does not describe
  what `gald3r plugin install/uninstall/update/list` actually do on this tree — see the
  honesty section at the top of this file.
- **Ground truth source files**: `src/gald3r_core/server_bridge/plugins/manager.py`
  (`PluginManager`), `src/gald3r_core/core/plugins/association.py` (per-project
  enable/disable + `entity_config` schema, T287), `src/gald3r_core/cli/commands/plugins.py`
  (`gald3r plugin` argparse wiring), `src/gald3r_core/composition/adapters.py`
  (`PluginAdapter`), `src/gald3r_core/composition/build.py` (`_plugins_dir` default), and
  `tests/cli/test_plugins_cmds.py` / `tests/server_bridge/plugins/test_plugin_manager.py` /
  `tests/composition/test_adapters.py` / `tests/core/plugins/test_plugin_association.py`
  for behavior proof.
