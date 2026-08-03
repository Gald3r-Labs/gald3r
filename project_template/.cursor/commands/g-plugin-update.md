---
subsystem_memberships: [PLATFORM_INTEGRATION]
---
# g-plugin-update — Update an installed plugin

Pull the latest commit for an already-installed plugin: `gald3r plugin update <name>`
runs `git -C <plugins_dir>/<name> pull --ff-only` against the plugin's own clone.
Nothing else — no manifest, no version comparison, no ledger.

## Usage

```
gald3r plugin update <name>
```

`<name>` is the plugin's local folder name under `<plugins_dir>/` (see `gald3r plugin
list`) — not a git URL and not a registry slug.

## What it does

1. Resolve `<plugins_dir>/<name>/` (default `<plugins_dir>` is `<GALD3R_HOME>/plugins`,
   i.e. `~/.gald3r/plugins` unless `GALD3R_HOME` is overridden). Fail with
   `FileNotFoundError` if that directory doesn't exist — the plugin isn't installed.
2. Run `git -C <plugins_dir>/<name> pull --ff-only` (60s timeout).
3. If the pull fails (diverged history, local edits conflicting, no network, etc.),
   fail and surface git's stderr.
4. On success, print git's stdout (or stderr, or the literal string `"Updated."` if
   git produced no output) as the status line.

There is no version check, no compatibility check, no `--dry-run`, no `--force`, no
`--source` override, and no component copy — it is a plain fast-forward `git pull`,
nothing more.

## Steps

1. Run from anywhere (no project-root argument needed — the plugin lives under
   `<GALD3R_HOME>/plugins`, not the project tree):
   ```bash
   uv run gald3r plugin update <name>
   ```
2. Read the printed line: `plugin '<name>': <git output>`.

## Notes

- To find the correct `<name>` first: `gald3r plugin list` (or `gald3r plugin list
  --json` for the full record).
- If the pull fails because the local clone has diverged (e.g. someone edited files
  inside `<plugins_dir>/<name>/` directly), resolve the clone manually (or
  `gald3r plugin uninstall <name>` and re-`install`) — this verb only attempts a
  fast-forward pull, it never force-resets or discards local changes.
- Sibling verbs on the same `gald3r plugin` CLI surface: `install`, `uninstall`
  (there is no `remove` alias), `list`, and (T287) `enable`/`disable` — the last two
  don't update anything, they flip a per-project ON/OFF flag; see
  `g-skl-plugins/SKILL.md`'s "Per-project enable/disable" section. There is no `new`
  (scaffold) or `check-compat` verb — see `g-skl-plugins/SKILL.md` for the full,
  ground-truth reference and for how to author a plugin by hand.
