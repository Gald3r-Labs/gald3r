# Changelog

All notable changes to gald3r are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
gald3r uses [Semantic Versioning](https://semver.org/).

---
## [Unreleased]

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

### Added
- **Plugin lifecycle ops in the engine (T663, epic T541).** `gald3r plugin install|remove|list|new|check-compat|update` CLI + `gald3r_plugin_*` MCP tools, backed by `gald3r.systems.plugins.PluginSystem` (owns the gald3r-plugin.yaml manifest schema, installed.yaml ledger, registry config, compat floor, D6 conflict-abort, `plugin_source:` provenance). Reimplements the designed-but-never-ported ops in Python (retires the PowerShell scripts per BUG-128/129/130). 21 tests; full engine suite 466 green. The single integration point for the T541 children (T664 editor / T665 marketplace backend / T666 UI).
- **Vault knowledge API tools (T609)** — `gald3r_vault_note_get` (note as structured JSON: frontmatter + body), `gald3r_vault_backlinks` (notes that `[[wikilink]]`-reference a note), and `gald3r_vault_context` (token-budgeted, newest-first vault context block — the `memory_context` pattern, vault-scoped). Engine `VaultSystem.note_get` / `backlinks` / `context` + the matching MCP tools. Offline/keyword (semantic search = T618). Completes the T609 vault API (search + ingest already shipped). 4 tests; canonical engine copy.
- **`gald3r vault location` CLI selector + layered resolution (T532).** Resolve/select the vault location (default user vault / workspace / project / create-new) with precedence session/project -> workspace -> default user home (T530); persists the choice to `.gald3r/.identity` (`vault_location`) via secret-stripping write_identity_file. New engine resolvers `resolve_vault_location_layered` / `resolve_vault_choice` / `persist_vault_location` (back-compat 2-layer resolver preserved). CLI `gald3r vault location [--select {default|workspace|project|create_new} [--path]]`. 23 tests; canonical + B-mirror parity. Throne selector UI is follow-up T650.
- **`@g-pt` workflow-profile CLI propagated to all IDE platform targets** (T417) — the
  `g-pt` command (`list`/`use`/`copy`/`edit`/`validate` for `.gald3r/config/workflow_profiles/*.yaml`)
  and its `g_pt.py` skill script are now fanned out across the `gald3r_core/platforms/` source trees:
  `g_pt.py` lands in every platform's `g-skl-project-types/scripts/` dir (31 targets, alongside the
  existing `load_profile.py`), and the `g-pt.md` command doc lands in every platform command/workflow
  dir that ships `g-workflow.md` (14 targets). Previously the CLI shipped only in the canonical
  `project_template/.claude` + `.cursor` copies, so non-`.claude`-owning platforms (cursor, codex,
  gemini, and the rest) built without it; this closes the last open T417 acceptance criterion.

### Changed
- **`g-hk-setup-user` reconciled onto the ONE unified identity home** (T627) — the interactive
  user-setup hook (`g-hk-setup-user.py` + its `g-hk-setup-user.ps1` twin) no longer writes a
  separate `~/.gald3r/user_config.json`. It now delegates identity provisioning to the engine's
  T530/T531 primitives (`gald3r.user_config.ensure_user_config` / `gald3r.home.resolve_home`) and
  writes the single canonical record at the unified per-user home
  (`%LOCALAPPDATA%/gald3r/user_config.json` on Windows, `~/.config/gald3r/user_config.json` on
  POSIX). A pre-existing `~/.gald3r/user_config.json` is migrated forward **once**, preserving its
  `user_id`/`machine_id` (never regenerated), with the source left intact and a breadcrumb dropped.
  The non-identity setup fields (`mcp_url`, `platform`, `setup_completed`, `setup_date`,
  `created_by`) are relocated to a `setup_meta.json` sidecar in the same home rather than co-mingled
  with the strict `user-config-v1` identity schema — so a machine running both surfaces no longer
  ends up with two competing identity files. The `.ps1` twin is now a thin delegator to the Python
  hook (single implementation). Engine test parity (`gald3r-engine`) extended with the mirrored T531
  unified-identity tests.

### Fixed
- **Claude Code hook wiring consolidated onto `settings.json`** (T420) — the canonical, doc-verified
  Claude Code hook config surface is `.claude/settings.json` under the top-level `"hooks"` key
  (PascalCase events `SessionStart`/`Stop`/`PreToolUse`/`PostToolUse`/`UserPromptSubmit`, three-level
  `event → matcher → hooks[]` shape — see `g-skl-platform-claude` PLATFORM_SPEC §6/§9). The wiring was
  moved out of the legacy top-level `.claude/hooks.json` (a Cursor-era surface that may silently not
  fire) into `settings.json`; `hooks.json` is now a retired pointer stub preserving provenance and the
  gald3r-internal lifecycle-event note. The Cursor-era `beforeShellExecution` event (no Claude Code
  equivalent) is remapped to a `PreToolUse` `Bash|Shell|…` matcher. This removes the
  two-competing-surfaces ambiguity flagged in `PLATFORM_SPEC_Claude.md` §9. The `g-skl-test`
  hook-wiring system check (`gald3r_system_checks.py check_hook_wiring`) now reads BOTH surfaces and
  flags any non-PascalCase event in `settings.json`.
- **`g-skl-test` PowerShell twin made dual-surface (T420 follow-up, T629)** — the PowerShell
  hook-wiring check (`g-skl-test/scripts/gald3r_system_test.ps1` `Test-HookWiring`) now reads BOTH
  the canonical `.claude/settings.json` `"hooks"` block AND the legacy `.claude/hooks.json`, matching
  its Python sibling `check_hook_wiring` (PascalCase-event validation, matcher-grouped shape,
  script-resolution-on-disk). It previously read only `hooks.json` and under-reported "no hook .ps1
  commands found in hooks.json" after the T420 consolidation moved the wiring into `settings.json`.
  The PS and Python checks now report the identical hook count/result on the same tree.

---
## [2.1.0] - 2026-06-20

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

### Fixed
- **Build hygiene: generated repos no longer ship Python build artifacts** (T507) â€” the build's copy primitive (`fs.copy_tree`) now always prunes `.venv`, `__pycache__`, and `.pytest_cache`, and the engine's dev-only pytest suite (`.gald3r_sys/engine/tests`) is excluded from every shipped `project_template` (runtime test fixtures under `g-skl-test` are preserved). A stray `.venv` had been adding ~52 MB of junk to each generated repo. Removed the duplicate `platforms/vibe` (it duplicated Mistral's `.vibe` config surface; Mistral retains it).

### Added
- **Platform template test harness + per-platform HTML report card** (T613) — a new harness scaffolds a
  throwaway gald3r project from any platform's template overlay (base `project_template/` minus
  other-platform IDE items, then the `platforms/<name>` overlay on top — same assembly the Forge uses for
  `gald3r_platform_<name>`), runs a **14-test plan** (engine launch, `--version`/VERSION, `doctor`,
  task round-trip, hook/MCP config validity, skills/commands/agents/rules counts, overlay dir, `.gitignore`,
  VERSION `2.x.x`, root `AGENTS.md`), and emits a **self-contained HTML report card** (inline CSS, no
  external deps; green ≥12 / yellow 8–11 / red <8) with a CRASH-primitives matrix, per-test table
  (✅/❌/⚠️/⏭️ + evidence), and environment block. Tests are data-driven and SKIP-able per platform
  (Hermes correctly SKIPs hooks/commands/agents/rules and PASSes on SKILL.md). New scripts:
  `.gald3r_sys/scripts/test_platform.py` (+ thin `test_platform.ps1` twin), the editable
  `.gald3r_sys/scripts/platform_report_card.html` skeleton, and `custom_scripts/test_all_platforms.py`
  (parallel batch runner → `ALL_PLATFORMS_REPORT_CARD.html` ranking, non-zero exit on any below-gate
  platform). Isolation order SmolVM → Docker → bare-local (bare-local prints a WARNING; the test image
  build is T615, CI wiring is T616). See `custom_scripts/TEST_RUNNER.md`. A red card is the correct
  output for a stub platform — the harness never fakes a pass.
- **Unified `user_config.json` identity provisioning** (T531) — the engine now first-run-creates the one
  shared per-user identity record (`user_id`, `display_name`, optional `email`, stable `machine_id`) in the
  unified per-user home (T530). A single high-level entry point, `gald3r.user_config.ensure_user_config(env,
  platform_name)`, composes the one home resolver (`home.resolve_home`) with the idempotent, never-clobbering
  `ensure()`; it is wired into the shared `gald3r.install.execute_setup` flow (the `gald3r setup` verb and the
  Throne onboarding path) so the record exists on first run with no second identity path. The same record's
  `user_id` feeds the entitlement gate via `gald3r.user_config.principal_account_id`, supplying the logged-in
  identity the permissions epic (T527) keys decisions on. Throne and Agent consume this same record as thin
  clients (no per-client identity logic) — their wiring is a follow-up.
- **Canonical hook event set + shared-core handlers** (T424, reference increment) — gald3r is
  consolidating Cursor's ~18 native hook events down to a **canonical reduced set of 6**
  (`session-start`, `session-end`, `user-prompt-submit`, `tool-start`, `tool-end`, `stop`) served by
  **one shared Python core** (`g_hk_core.py`, built on the T1584 `_hook_common.py`). Six thin
  event-first entrypoints `g-hk-on-<event>.py` delegate to `g_hk_core.dispatch(<event>)` â€” behavior
  is authored once and every platform's trigger layer calls the same core. Wired the first canonical
  events additively into **Cursor** (`postToolUse`, `beforeSubmitPrompt`) and **Claude**
  (`PostToolUse`, `UserPromptSubmit`); added the **Kiro IDE** `.kiro.hook` file-event trigger and the
  **kiro-cli** agent-JSON `hooks` field + STDIN `.ps1` shims as the third/fourth trigger models. New
  `.cursor/hooks/README.md` + `.claude/hooks/README.md` document the model. Existing per-concern hook
  wiring is retained intact; fan-out to the remaining hook-capable platforms is tracked as T510.
- **More platforms now route through the shared hook core** (T510, fan-out of T424) â€” seven more
  hook-capable platforms now run gald3r hook behavior through the one shared `g_hk_core.py` via their
  **real native trigger config** (each replaced a broken Claude-format clone, or was newly authored,
  and was pinned against the platform's authoritative hook docs): **codex** (`.codex/hooks.json`),
  **qwen** (`.qwen/settings.json`), **windsurf** (`.windsurf/hooks.json`), **openhands**
  (`.openhands/hooks.json`), **augment** (`.augment/settings.json` + `.ps1` shims), **copilot**
  (`.github/hooks/gald3r-hooks.json`), and **gemini** (`.gemini/settings.json`). Each wires only the
  native events it supports (graceful degradation) and ships its own byte-identical copy of the core +
  six `g-hk-on-<event>.py` entrypoints + the concern-chain hooks, with a per-platform hooks `README.md`.
  **kiro-cli** now carries the full concern chain (its canonical handlers run real behavior, not
  pass-through), and the **cursor** platform overlay's stale pre-canonical `hooks.json` was synced to
  the reference. **goose** (Open-Plugins model: `.agents/plugins/gald3r-hooks/` with `plugin.json` +
  `hooks/hooks.json`) and **antigravity** (`.agents/hooks.json` + a thin `g-hk-ag-dispatch.py`
  adapter that translates antigravity's `{decision}` I/O contract) are now wired too â€” **9/9
  hook-capable platforms**. Antigravity is authored to its launch-day docs and flagged PENDING
  live-install verification. Still pending (tracked in T510): antigravity live-verify, root live-repo
  tree propagation, and a forge rebuild.
- **Install gald3r_agent / gald3r_throne from the CLI** (T472, epic T470) â€” new `gald3r install agent|throne|all` detects the host OS (`windows`/`macos`/`linux`) and installs each product the right way: **agent** via `uv sync`; **throne** by locating the per-OS Tauri bundle (`npm run tauri:build` output â€” Windows NSIS/MSI, macOS .dmg/.app, Linux .deb/.AppImage/.rpm). `gald3r setup agent|throne|all` then initializes each product against the shared install home (vault, settings, log). `--dry-run` prints the full plan (artifact, target paths, PATH changes); `--json` emits it structured; `--products-root` / `GALD3R_PRODUCTS_ROOT` override the source root. Fail-loud (never a silent stub): a missing per-OS throne bundle raises a clear error with the exact build command and the paths searched. 27 unit tests.
- **Centralized install home + global `gald3r` CLI + USB-portable variant** (T471, epic T470) â€” new shared install home (`settings/`, `logs/`, `gald3r_vault/`, `VERSION`) resolved by precedence `override > portable > GALD3R_HOME > per-OS default` (Windows `%LOCALAPPDATA%\gald3r`, Linux `$XDG_DATA_HOME/gald3r`, macOS `~/Library/Application Support/gald3r`). USB-portable mode (`--portable` / `GALD3R_PORTABLE=1`) relocates the home to a removable medium with no outside writes. New `gald3r home [--portable] [--ensure] [--json]` subcommand + an idempotent, `--dry-run`-capable `install_global_cli` (Windows `gald3r.cmd` + user-PATH; POSIX `~/.local/bin` shim) so `gald3r --version` works from any directory. ADR-016. 26 unit tests.
- **Self-update: `gald3r version-check` + `gald3r upgrade`** (T473 agent + T475 templates, epic T470) â€” one shared engine serves both the agent and template-installed projects. `gald3r version-check` queries world_tree's version surface (`GET /api/v1/gald3r/version`) and reports current vs latest (offline-first: any unreachable/auth/timeout failure degrades to a clear message, never a crash or fabricated version). `gald3r upgrade` takes a timestamped gitignored backup of `.gald3r/`, migrates to the latest format (idempotent ADD/MERGE/DEPRECATE; user data â€” `tasks/**`, `bugs/**`, `TASKS.md`, `PLAN.md`, â€¦ â€” is never touched), and **rolls back from the backup on any failure**. `--dry-run` (default) previews; `--apply` performs; `--json` for both. 12 offline unit tests.
- **gald3r_throne: in-app version check + "update available" indicator** (T474, epic T470) â€” Throne now queries world_tree's version endpoint (`GET /api/v1/gald3r/version`) on connect and surfaces **current vs. latest** with an "update available" badge directly in the UI. Replaced the hardcoded `BUNDLED_LATEST_VERSION="1.2.0"` Rust constant with a live authenticated query via the existing `worldTreeFetch` client; project-relative version is read from `.gald3r/.identity`. Offline-first: unreachable / 401 / non-2xx world_tree â†’ `reachable: false`, no throw, file-first status preserved. Includes a pre-apply preview modal (shows version delta before confirming). 11 Vitest tests.
- **gald3r_throne: in-app update APPLY in compiled Rust** (T481, epic T470) â€” Throne can now apply a `.gald3r/` update entirely from within the app, with no Python or engine dependency. Completes the T474 version-check half: `apply_create` writes real new-file content from the bundled template snapshot; `FileChange::Merge` performs a real frontmatter/key merge consistent with the engine's ADD/MERGE/DEPRECATE semantics. The full safety envelope is preserved: backup ZIP â†’ integrity-verify â†’ apply â†’ registry-limited migrations â†’ audit report â†’ **byte-for-byte rollback on any failure**. User-data denylist (`tasks/**`, `bugs/**`, `TASKS.md`, `PLAN.md`, â€¦) mirrors the Python engine â€” both implementations agree on what is never overwritten. 34 Rust `cargo test --lib project_update` tests. No process-spawn of Python. Offline-first preserved.
- **Local install folder auto-provisions the vault + inherits identity defaults** (T476, epic T470) â€” one shared `gald3r.provision` resolution used by both agent and throne (no fork): idempotently creates `gald3r_vault` at the configured `vault_location` (else the install home), and writes `.gald3r/.identity` by layering `install-home defaults -> user identity -> per-project overrides`. Any credential/token/password/secret/api_key-looking key is stripped before the identity is written (host-only secret state stays in the gitignored `.user_prefs.yaml`/`.env`). 26 unit tests.
- **Project scaffold against a target folder: `gald3r init` + `gald3r update`** (T477, epic T470) â€” `gald3r init` scaffolds a fresh gald3r project into a target folder (current dir by default, or `--target <folder>`) via the same canonical installer `@g-setup` uses, with new PROJECT.md param-seeding (`--name`, `--description`, `--vision`, `--tech-stack`); a user-edited section is never clobbered (idempotent), and an existing project routes to the update path instead of re-init. `gald3r update` routes a target folder through the T473 safe-update core (backup â†’ migrate â†’ rollback). `--dry-run`/`--json` for both. 23 unit tests.
- **CRASH activation tracking** (T433) â€” datetime invocation statistics for the five gald3r
  extension-point types (Commands, Rules, Agents, Skills, Hooks). New engine module
  `gald3r/crash.py` appends one JSON line per activation to `.gald3r/logs/crash_activations.jsonl`
  (`{component_type, component_name, activated_at, session_id, trigger_source, elapsed_ms}`) and
  computes Most Active / Least Active / Never Activated / "Should Be Called But Isn't" stats (the
  last from rules' `fires_on:` / skills' `activate_for:` intent metadata). New `@g-crash-stats`
  command + `gald3r crash-stats` subcommand render the report on demand; `--crash-stats-reset`
  archives the log and starts fresh; `GALD3R_CRASH_STATS=show_in_response|show_in_log|show_in_terminal`
  surfaces a compact 3-5 line signature (zero overhead when unset/`off`). New `g-hk-crash-record`
  hook is the explicit recording path for Skill/Agent/Hook/Rule activations (which have no native
  IDE harness event). Integrates with T432 debug mode: a command dispatch writes the debug trace
  and the CRASH record in the same event.
- **Versioned `.gald3r/` snapshots for the upgrade engine** (T463) â€” each release cut now persists
  the canonical `.gald3r/` template as a stored, versioned snapshot
  (`gald3r_core/project_template/.gald3r_sys/snapshots/v<X.Y.Z>/.gald3r`, user data excluded) via
  `gald3r.systems.upgrade.capture_snapshot`, invoked by `@g-gald3r-publish`'s finalize step. The
  `gald3r upgrade` op gains `--from-version` / `--to-version` flags that resolve those stored
  snapshots automatically (`resolve_version_dir`), so a real vNâ†’vN+1 migration can run against
  genuine historical sources instead of only synthetic fixtures.
- **Human-prose wishlist â†’ task mining** (T453) â€” new `@g-wishlist-mine` command + `g-skl-wishlist-mine`
  skill productize the DELIVERABLES.md pattern: a non-technical user keeps a free-form, plain-language
  intent/wishlist document (no schema), and gald3r mines the READY, concrete wants into formal tasks.
  Mining is **READ-ONLY against the prose doc** (never rewritten/checklist-ified), dedups against
  existing `.gald3r/TASKS.md` entries, routes broad vision to a single epic, reports unsure items as
  backlog candidates (not over-created), and emits a created-tasks table + backlog-candidates list.
  Supports `--dry-run`, a configurable/default doc path (`.gald3r/DELIVERABLES.md`), and a WPAC
  controller cascade path via `@g-wpac-order`.
- **Turnkey hot-inbox staging zones** (T480) â€” fresh installs now ship pre-seeded
  `.gald3r/tasks/inbox/.gitkeep` and `.gald3r/bugs/inbox/.gitkeep` so the "drop a draft task/bug
  while g-go-go runs" zones are discoverable out of the box. The template `.gald3r/.gitignore` now
  declares them as gitignored staging zones (`tasks/inbox/*` + `!tasks/inbox/.gitkeep`, same for
  `bugs/inbox/`), matching the "gitignored staging zones" language in `g-go-go.md`: draft contents
  stay untracked (the `gald3r inbox` intake deletes them after absorbing), while the `.gitkeep`
  keeps the folder shipped.
- **All skill scripts ported to Python** (T1585) â€” every `.ps1` under `skills/*/scripts/`
  (48 scripts incl. the 1,765-line `gald3r_worktree.ps1`, decomposed into a `worktree_lib/`
  package) now has a `.py` sibling; SKILL.md/command invocations rewritten from
  `powershell/pwsh -File <script>.ps1` to `uv run python <script>.py` across all platform
  mirrors. PS1 files remain as transition fallbacks; ports prefer `.py` siblings for
  cross-script calls with `pwsh` fallback.
- **All platform hooks ported to Python** (T1584) â€” every `g-hk-*.ps1` hook (27 scripts)
  now has a `.py` sibling plus a shared `_hook_common.py` bootstrap; hook configs
  (`.claude/hooks.json`, `.cursor/hooks.json`, and all platform-overlay configs) now invoke
  `python <hook>.py` instead of `pwsh -File <hook>.ps1`. macOS/Linux installs get fully
  functional hooks without PowerShell. The `.ps1` files remain as transition fallbacks.
- **`setup_gald3r_project.py` cross-platform installer** (T1586) â€” Python port of the
  first-run setup with `--non-interactive` mode, `--dry-run`, UUID4 project_id generation,
  and new `setup_gald3r_project.sh` shim; `setup_gald3r_project.bat` now calls the Python
  version. `install_git_hooks.py` ports the git-hook installer (`core.hooksPath`,
  POSIX chmod +x).
- **`gald3r.utils` cross-platform utility module** (T1583) â€” new engine sub-package with
  `console` (colored output, NO_COLOR/FORCE_COLOR support), `fs` (`copy_tree` robocopy
  replacement, `clear_dir_except_git`, `replace_in_file_tree`, `ensure_dir`), `process`
  (`run_cmd`/`run_git` with dry-run and `RunResult`), and `paths` (`temp_file`,
  `gald3r_root`, `ecosystem_root`). Foundation for the PS1 â†’ Python migration (T1581):
  ported scripts import from here instead of re-implementing PowerShell patterns.

### Changed
- **User scaffolding commands no longer reference maintainer-only commands** (BUG-137) â€” the
  shipped `@g-command-new` / `@g-rule-new` / `@g-skill-new` commands (48 files across 16 platform
  trees) dropped their `## Related` "Maintainer-only equivalent: `@g-gald3r-*-new`" bullet. These
  are end-user commands scoped to the user's own project; the maintainer `@g-gald3r-*` commands
  edit gald3r itself and have no place in a shipped user template (C-009 policy).

### Fixed
- **CRASH hook component metadata** (BUG-160, partial) â€” `g-hk-crash-record.md` was missing its
  `subsystem_memberships:` frontmatter (g-rl-38); added `[LOGGING_SYSTEM]` to match the hook's
  `.ps1` tag. The larger CRASH shipping gaps (engine `crash.py` absent from the shipped
  `project_template` engine, `.cursor` hook parity, `.py` port) are tracked in T511.
- **Stale `gald3r_rel_version` stamp in template `.gald3r/.gitignore`** (T480) â€” corrected the
  `# gald3r_rel_version: 2.1.1` header to `2.0.1` in both the canonical `project_template/.gald3r/.gitignore`
  and the `.gald3r_sys/template_verification/.gald3r/.gitignore` reference copy. (The forge does not
  re-stamp extensionless `.gitignore` files on build, so the canonical source carried the only stamp.)
- **Workspace manifest validator typo re-fixed in the canonical engine** (BUG-128) â€” the
  documented `pcac_relationship` â†’ `wpac_relationship` fix had not landed in
  `project_template/.gald3r_sys/engine`; `validate_manifest()` and `status()` corrected.

---

## [2.0.1] - 2026-06-10

Patch release â€” copyright transfer, release pipeline org fix, and workspace engine bug fix.

### Changed
- **Copyright transferred to Gald3r Labs LLC** â€” all repository LICENSE files updated from
  `Warren R. Martel III` to `Gald3r Labs LLC` following company formation.
- **`push_repos.ps1` default org updated** â€” `GitHubOrg` default changed from `wrm3` to
  `Gald3r-Labs` to reflect the completed GitHub organization transfer.
- **Platform repos now get GitHub Releases by default** â€” previously required `-GitHubReleaseAll`
  flag; now all platform repos receive a tagged GitHub Release on every `push_repos.ps1` run.
  Use new `-SkipPlatformRelease` flag to opt out.

### Fixed
- **BUG-128**: `workspace.py status()` always returned `role: standalone` due to misspelled
  dict key `pcac_relationship` (should be `wpac_relationship`). WPAC topology was completely
  invisible â€” every project appeared standalone regardless of configured parent/child
  relationships. (`WORKSPACE_COORDINATION`)

---

## [2.0.0] - 2026-06-04

The **gald3r engine** release. gald3r gains a bundled, file-first Python core that backs every
system deterministically â€” while staying 100% markdown-on-disk. Existing installs keep working;
the engine is additive, and every slimmed component ships a no-engine fallback.

### Added
- **Bundled gald3r engine** (`.gald3r_sys/engine/`) â€” a pure, file-first state backend for every
  system: tasks, bugs, features, goals, prds, ideas, vocab, constraints, subsystems, vault,
  release, workspace, and inbox. **Mode-A**: deterministic, no LLM, no network, no Docker. One
  prerequisite â€” [`uv`](https://docs.astral.sh/uv/).
- **`gald3r` CLI** (and `python -m gald3r`) â€” drive every system from the shell: `gald3r task new`,
  `gald3r bug new`, `gald3r goal add`, `gald3r vault ingest`, `gald3r release new`,
  `gald3r workspace â€¦`, `gald3r prompt get â€¦`.
- **MCP server** (`gald3r mcp`) â€” ~20 Model Context Protocol tools exposing the same operations to
  any MCP-capable agent.
- **`gald3r doctor`** â€” read-only health check (structure, per-system index integrity, skill
  frontmatter, `.ps1` encoding) with an overall functionality score and a `--fail-below` CI gate.
- **Engine-absorbed operations** â€” five maintenance scripts reimplemented as pure engine verbs,
  each keeping its original `.ps1` as a no-engine (L0) fallback: `gald3r inbox` Â· `gald3r doctor` Â·
  `gald3r platform status` Â· `gald3r tier show|set` Â· `gald3r sync --check|--apply` (alias
  `gald3r parity`).
- **Judgment / prompt layer** â€” 15 reasoning assets (Norse persona, role briefs, review rubrics,
  marketing voice) served by the engine (`gald3r prompt get role.code_reviewer`), so a brief is
  authored once and shared across platforms.

### Changed
- **Thinned component shims** â€” judgment skills and agents are slimmed to load their brief from the
  engine's prompt assets. Skills keep a full `SKILL.full.md` fallback; agents reference the shipped
  asset directly (no `.full.md` sidecar â€” it would register as a duplicate component).
- **Task status vocabulary** â€” `task_file.v1.schema.yaml` realigned to mirror the engine's enforced
  vocabulary (`pending â†’ in-progress â†’ awaiting-verification â†’ completed â€¦`). The YAML previously
  listed a never-implemented pipeline as "current" and the real vocabulary as "legacy."

### Fixed
- **Windows PowerShell 5.1 parse crash** â€” 1,055 shipped `.ps1` files were UTF-8 without a BOM, so
  `powershell.exe` mis-read multi-byte characters and failed to parse (including the installer
  itself). All BOM-protected (installer ASCII-cleaned); the build generators now emit safe `.ps1`
  and `gald3r doctor` flags any regression.
- **Duplicate component names** â€” removed the per-agent `*.full.md` sidecars and the deprecated
  `g-skl-medkit` (named `g-skl-medic`, colliding with the real skill). 106 skills + 13 agents now
  audit clean (no duplicate `name:`, no dangling shim references).
- **`doctor` / `bug sync` index mis-parse** â€” the id-scan matched the `## Next Bug ID:` counter line
  (and any title mentioning it), producing false phantom/orphan rows and a non-converging
  `bug sync`. Anchored to the counter heading.
- **Malformed component frontmatter** â€” added missing `name`/`description` to 5 skills and agents.

### Engineering
- 97 engine unit tests (pytest). The engine is the new source of truth; `.gald3r_sys/schemas/`
  mirrors it.

---

## [1.10] - 2026-06-02 (Cursor + Claude Unity Edition)

<!-- BUG-157 reconciliation (2026-06-18): the two entries below were mislabeled `## [1.11.0]`
     (dated 2026-06-03 and 2026-06-04). GitHub (Gald3r-Labs/gald3r) never published a 1.11.0;
     this work shipped under tag `v1.10`. Merged and relabeled to match the real release set. -->

### Added
- **`platforms/` folder**: all 34 platform thin adapters now live directly in `gald3r`.
  No need to clone a separate advanced template for Windsurf, Cline, Copilot, etc.
- **`-Platform <name>` installer arg**: `setup_gald3r_project.ps1` now accepts any of 34
  platforms. Default (no arg) = Cursor + Claude Code (unchanged). `-Platform windsurf` etc.
  copies the shared brain (without .cursor/.claude) + the platform's thin config overlay.

### Changed
- **Restructured install model**: deliverable is now `project_template/` â€” copy its contents to
  your project root. Cursor + Claude Code are Tier 1; other platforms via `AGENTS.md` + `.gald3r/`.
- **Simplified installer**: `setup_gald3r_project.ps1` rewritten from 44KB â†’ ~110 lines. Single
  purpose: copy `project_template/` to target, preserving existing `.gald3r/` user data.
- **Stripped maintainer-only rules**: `g-rl-25` (session-start), `g-rl-33` (enforcement-catchall),
  and `g-rl-36` (workspace-guard) removed from the shipped template â€” these are framework-build
  tools, not end-user config. Shipped set: 11 lightweight rules + `gald3r_personality`.
- **Updated README**: reflects actual structure and accurate component counts (110 skills,
  177 commands, 37 hooks, 12 rules); version badge, installer docs, and platform table.

### Fixed
- **Personality rule extension**: renamed `gald3r_personality.md` â†’
  `gald3r_personality.mdc` in `project_template/.cursor/rules/`. Cursor only loads
  `.mdc` files from the rules folder; the Norse personality was silently not loading.
- **License reference in README**: corrected from `[MIT]` to `[Fair Source License 1.1
  (FSL-1.1-Apache)]`. The actual LICENSE file was always FSL â€” only the README link was wrong.
- **BUG-099 safety fix**: All platform scaffold `gald3r_worktree.ps1` scripts and `development.yaml`
  files defaulted `TargetBranch`/`default_branch` to `dev` instead of `main` â€” a data-loss trap for
  new projects created from any platform template. Flipped 78 files (44 worktree scripts + 34
  development.yaml) to `main`. Affects all 34+ platform scaffolds.

---

## [1.9.0] - 2026-05-31 (Platforms/ Folder + Post-Push Verify + Plugin System Foundation)

### Added
- **Plugin system foundation** (T1557â€“T1559): `@g-plugin-install` lands â€” install a gald3r plugin
  from a local path (GitHub-URL path implemented, not yet network-tested). Backed by ADR-015, a
  `gald3r-plugin.yaml` manifest schema + validator, and a security-first installer: validates the
  manifest, enforces `gald3r_min_version`, **refuses to overwrite gald3r-core components**, stamps
  installed components with `plugin_source:`, records a `installed.yaml` ledger, and **never
  auto-runs plugin lifecycle scripts** (opt-in `-RunInstallScript`, previews first).
- `scan_platform_docs.ps1 -WithHtml` / `-HappyPath` (T1545): after a platform's `PLATFORM_SPEC.md`
  is updated by a doc scan, auto-regenerates its `docs/platforms/<name>_guide.html` and stamps
  `last_html_generated:` for staleness visibility.
- `check_platform_status.ps1 -GenerateMatrix` (T1543): auto-populates
  `.gald3r/PLATFORM_CAPABILITY_MATRIX.md` from the canonical `PLATFORM_SPEC.md` capability tables,
  cross-checks each cell against the hand-verified `PLATFORM_STATUS.md`, and warns on disagreement.
- `post_push_verify.ps1` (T1572): 11-check post-push gate that verifies a release landed correctly
  (VERSION, CHANGELOG depth, releases/ file, git tag, GitHub release body, public repo VERSION/README,
  wiki freshness, plus a 10-pattern secrets scan of the release diff).

### Changed
- **`gald3r` public repo restructured**: 34 platform directories moved from repo root into a
  `platforms/` subfolder (T1556). `platform_parity_sync.ps1 -SyncToGald3r` updated to target it.
- `platform_parity_sync.ps1` now discovers platforms by scanning
  `project_template/.gald3r_sys/platforms/` dynamically rather than a hardcoded list.

### Removed
- `@g-kamikaze` and `@g-juggernaut` commands (T1548): both were pure aliases for `@g-mission` with
  no added behavior. Deleted across all platform targets; use `@g-mission` directly.

---

## [1.8.0] - 2026-05-30 (Wiki Launch + GitHub Discussions + Test Harness + 35-Platform Sweep)

### Added
- **GitHub wiki launched** (T1550): 7 pages auto-generated from `.gald3r_sys/` â€” Home, Quickstart,
  Commands, Skills, Agents, Rules, Hooks.
- GitHub Discussions enabled as the community Q&A and announcement channel.
- Batch-11 platform specs consolidated into the canonical
  `project_template/.gald3r_sys/platforms/.<platform>/PLATFORM_SPEC.md` single-source location
  (T1544); `platforms/` now holds 35 platform specs.
- gald3r systems functional test harness `gald3r_system_test.ps1` (T1540): per-system
  PASS/PARTIAL/FAIL + overall "N% functional" score across 13 gald3r systems; `-FailBelow <N>` CI
  gate. Added as the **FUNCTIONAL (L0)** operation in `g-skl-test`.
- Two-layer release system (T1528-T1530) + native tier graduation scripts in `g-skl-release/scripts/`.
- Framework constraints C-041..C-043 (destructive git gate, content scrub, public main-only).

### Changed
- `scan_platform_docs.ps1` now discovers platforms by scanning
  `project_template/.gald3r_sys/platforms/` (no hardcoded 23-platform list; T1544 AC6). Verified at
  35 platforms under powershell.exe 5.1.
- **Branch model: feature-branches-only â†’ `main` (USER-SAFETY, T1535)**. Retired the long-lived
  `dev`/`test` promotion branches (root cause of repeated history-loss incidents, BUG-099 class).
  `g-go`/`g-go-go` auto-merge default flipped `dev` â†’ `main`; `gald3r_worktree.ps1`,
  `development.yaml`, and `g-skl-setup` realigned to `main`.

### Fixed
- **Eliminated the stale-`dev` auto-merge data-loss hazard (BUG-099, USER-SAFETY)**: gald3r no longer
  defaults swarm/autopilot auto-merge to a long-lived `dev` integration branch. Existing user repos
  are offered a safe, confirmation-gated migration â€” never an automatic branch delete.

---

## [1.7.0] - 2026-05-28 (Workspace Distribution + Swarm Fix + 34-Platform Sweep)

### Changed

- **Public-face restructure (T1522)**: The 23 ready-to-deploy platform templates moved from `platforms/<name>/` to `<name>/` directly at repo root. The standalone `platforms/README.md` matrix was removed (the platform comparison matrix lives in the main `README.md` per T1515). Removed internal/build artifacts that polluted the public view: `.cursor/`, `.claude/`, `.agent/`, `.codex/`, `.opencode/`, `.copilot/`, `.gald3r/`, `project_template/`, `docs/`, `scripts/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `GUARDRAILS.md`, `.claudeignore`, `.cursorignore`, `opencode.json`. Added `instructions_new_project.md` + `instructions_existing_project.md` covering the two audiences. The hero `README.md` was rewritten as a discovery-first document (no internal-tool references).
- **Per-platform README templates fixed (T1522 iter 2)**: Original 23 platform READMEs (`cursor/`, `claude/`, etc.) updated for the new flat layout -- install instruction says `Copy the contents of <name>/` (not `platforms/<name>/`); cross-links use `../README.md` and `../CHANGELOG.md` (not `../../`); removed the stale `Platform comparison matrix` link (matrix now lives in main `README.md`). The 11 newer platform READMEs (T1523/T1524/T1525 -- `amp/`, `astrbot/`, `codebuddy/`, `continue/`, `deepcode/`, `hermes/`, `kilo-code/`, `kimi/`, `qoder/`, `trae/`, `void/`) were authored with the correct flat-layout patterns from the start and were not touched in this commit.

### Added

- **Platform Support section in README with tier matrix (T1515).** New top-level `## Platform Support (23 AI Coding Tools)` section listing all 23 platforms with shields.io tier badges (Tier 1 = green, Tier 2 = yellow, Tier 3 = orange), tier definitions, install steps, and per-platform folder links. Tier distribution: 8 Tier 1 (Claude Code, Cline, OpenAI Codex, GitHub Copilot, Cursor, opencode.ai, Roo Code, Windsurf), 10 Tier 2 (Aider, Augment, Gemini, Goose, Junie, Kiro, Kiro CLI, OpenHands, Replit AI, Warp), 5 Tier 3 (Antigravity, Mistral, OpenClaw, Qwen, SubQ). (T1521-era `platforms/<name>/` paths superseded by T1522 root-level layout; the `## Platform Support` section's table links are accurate for the flat layout.)
- "6-IDE parity" feature bullet updated to "23-platform parity" with full list.
- `What's Included` table updated: `IDE Platforms | 6 | ...` row replaced with `Platforms | 23 | See Platform Support` cross-link.
- `docs/PLUGINS.md`: plugin author guide covering skill pack structure, distribution, naming guidelines, and licensing options for third-party extensions.
- README "Plugins & Skill Packs" section with naming guideline and licensing clarification (plugins are separate works, any license allowed).
- NOTICE clarified with plain-language license summary and plugin naming guideline.

---

## [1.6.0] - 2026-05-25 (WPAC v1.6, Schema System, Ship Skill)

### Added

- **Schema enforcement system**: every `.gald3r/` file now carries version provenance, validated against 15 versioned schema definitions. A read-only session-start probe flags drift in under a second, and a data-preserving migration engine (`migrate_schemas.ps1`) upgrades older files in place. `g-medic` gained an L1 validation layer that auto-fixes common schema gaps.
- **Semantic versioning and release management** (`g-skl-ship`, `@g-ship`): promotes the CHANGELOG `[Unreleased]` section to a versioned release -- bumps `VERSION`, tags the release, and can publish. Task and bug completion feed CHANGELOG entries automatically.
- **Dedicated bug-fix pipeline** (`@g-go-bugs`, `@g-go-bugs-swarm`): an autopilot built only for bugs -- reproduce, fix, regression test, adversarial review -- working through the backlog in severity order (critical first).
- **Encoding normalization** (`g-hk-encoding-normalize`): pre-commit and stop-event hook that normalizes line endings and BOM policy, with a content-aware guard that leaves real binary files untouched. Ships with a `.gitattributes` scaffold and a one-command git-hooks installer so fresh installs are protected by default.
- **Cross-project promotion lifecycle** (`@g-wpac-promote`): workspace members can graduate from a lightweight controlled member to a fully independent autonomous child via a formal, dry-run-first lifecycle instead of hand-editing files.
- **Swarm file-lock manifests**: parallel `g-go --swarm` runs declare file locks so agents never edit the same files; overlapping buckets raise a lock conflict.
- **Profile-aware core skills**: `g-go`, `g-go-code`, `g-go-review`, and `@g-status` read a configurable `workflow_profile` instead of hardcoded status strings.
- **Context-aware autopilot**: `g-go-go` shrinks its parallel batch size under context pressure instead of stopping mid-run, with a stop-detection guard that resumes a stalled loop.

### Changed

- `@g-update` reconciles the gald3r version stamp in every consumer install on sync.
- PCAC terminology renamed to WPAC (Workspace Project-Aware Coordination) across the command suite.

### Fixed

- Cross-platform file corruption from an early coordination transition cleaned up across all framework trees; a reusable cleanup script was added.
- Several PowerShell hook parse and compatibility issues resolved.
- Root `VERSION` file and `.gald3r/releases/` history now created and backfilled by both setup and `@g-update`.
- Context Budget and Conflict Pattern hard rules restored to the core enforcement ruleset.

---

## [1.5.2] - 2026-05-21 (HTML/JSON/TOON Output, Memory Compression, Vocab)

### Added

- **HTML output + theme system** (`g-skl-html-output`, `--html` flag): human-facing reports (`@g-status`, `@g-review`, QA reports) render as self-contained themed HTML. Three built-in themes: `gald3r-dark` (default), `gald3r-light`, `gald3r-mocha`. Coordination files stay markdown.
- **JSON output mode** (`g-skl-json-output`, `--json` flag): a structured `{gald3r_version, generated_at, command, schema, data}` envelope for scripting, CI gates, and dashboards.
- **TOON output mode** (`g-skl-toon-output`, `--toon` flag): Token-Oriented Object Notation -- a compact, lossless, LLM-friendly tabular format (about 40% smaller than JSON).
- **Theme editor** (`g-skl-theme-editor`, `@g-theme-edit`): file-first editor for creating and editing gald3r HTML themes, with import/export of `:root` token blocks.
- **Memory compression** (`g-skl-compress-memory`, `@g-compress-memory`): compact session memory and learned-facts entries to reduce context bloat while preserving key insights.
- **Vocabulary management** (`@g-vocab-add`, `@g-vocab-list`, `@g-vocab-search`): define project-specific abbreviations that agents read at session start.
- **Skill review** (`@g-skill-review`): list, review, and selectively promote auto-proposed skill drafts; human approval required before promotion.
- **Auto-skill generation** (`--propose-skill` on `@g-go-review`): optionally drafts a `SKILL.md` after a PASS verdict when a novel, generalizable pattern is found. Off by default.
- **`@g-mission` improvements**: `resume --budget N`, drain-queue scan order, a 75% context checkpoint threshold, mandatory split for oversized tasks, cross-repo task fix in `--until-empty`, and an autonomous push gate.

---

## [1.5.1] - 2026-05-18

### Added

- `docs/PLUGINS.md`: plugin author guide covering skill pack structure, distribution, and naming guidelines for third-party extensions.
- README "Plugins & Skill Packs" section with a naming guideline (plugins are separate works).
- NOTICE clarified with the plugin naming guideline.

---

## [1.5.0] - 2026-05-10 (Maestro Harvest)

### Added

- **Security scanning** (`g-skl-security-scan`): a two-phase SAST scanner. A fast, free regex pass surfaces candidates across 12 vulnerability categories (hardcoded credentials, SQL injection, eval/exec, weak crypto, path traversal, CORS wildcards, and more), then a focused LLM pass analyzes only the flagged batches. Complements `g-skl-code-review`.
- **Dynamic context assembly** (`g-skl-context-builder`): builds a token-budgeted context block on the fly from live `.gald3r/` state -- active tasks, constraints, relevant subsystems, and recent memory.
- **Engineering-team delegation** (`g-skl-delegate`): task-brief templates, code-review request templates, quality-gate checklists, and clean handoff protocols.
- **More coding-agent runtimes**: `g-skl-cli-jcode` (jcode Rust agent -- millisecond startup, local embeddings via Ollama) and `g-skl-comfyui` (local GPU image/video generation via ComfyUI, zero cloud cost).
- **Code-graph context prep**: `g-go-code` can query a code graph (`g-skl-graphify`) for cheaper architecture lookups, with graceful fallback to grep-based prep.
- **External backlog intake** (`@g-triage`): turns unstructured input (emails, Slack, meeting notes) into routed gald3r items behind a hard human-approval gate.
- **Mid-flight control** (`@g-steer`, `@g-queue`): course-correct or queue work onto an in-progress worktree session; `@g-go-code --resume` adds crash recovery via checkpoint artifacts.
- **Harness tuning guide** (`AGENT_CONFIG.md`): documents context budgets, temperature presets, and retry configuration.
- **Recon provenance**: harvested patterns carry a similarity-risk field from capture through apply.

### Changed

- README component counts and platform parity updated for the 1.5 line.

### Fixed

- Session-start and lint hook compatibility issues on PowerShell resolved.

---

## [1.4.0] - 2026-04-14

### Added

- **GitHub Copilot support** (`.copilot/`): 6th IDE added to the parity set. Full command surface (89 commands) deployed to `.copilot/commands/`. gald3r now supports Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot.
- **Recon suite** (`g-skl-recon-repo`, `g-skl-recon-url`, `g-skl-recon-docs`, `g-skl-recon-yt`, `g-skl-recon-file`): unified research/reconnaissance skill family. Replaces the separate `g-skl-reverse-spec`, `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube`, and `g-skl-harvest` skills with a consistent `recon-*` namespace. Each produces a structured recon report for human review before any writes occur.
- **Research review/apply suite** (`g-skl-res-review`, `g-skl-res-deep`, `g-skl-res-apply`): three-step workflow -- review a recon report, deep-dive on specific findings, then apply approved findings into `.gald3r/features/` staging. Replaces `g-skl-harvest-intake`.
- **Release management skill** (`g-skl-release`, `@g-release-new`, `@g-release-assign`, `@g-release-status`, `@g-release-accelerate`, `@g-release-publish`): full release lifecycle from planning to publishing. Manages `.gald3r/releases/` and `.gald3r/RELEASES.md`.
- **Platform skills** (`g-skl-platform-cursor`, `g-skl-platform-claude`, `g-skl-platform-gemini`, `g-skl-platform-codex`, `g-skl-platform-opencode`, `g-skl-platform-copilot`): per-IDE platform reference skills for understanding each IDE's agent model, permission system, and tool surface.
- **Medic skill** (`g-skl-medic`, `@g-medic`): targeted surgical repair for a specific `.gald3r/` file or subsystem, complementing `g-skl-medkit` (which does full-project health checks).
- **Tier setup skill** (`g-skl-tier-setup`, `@g-tier-setup`): upgrade a project's gald3r installation tier (slim â†’ full â†’ adv) without losing existing state.
- **Codex CLI skill** (`g-skl-cli-codex`): dedicated reference skill for Codex terminal-first operation.
- **Copilot CLI skill** (`g-skl-cli-copilot`): dedicated reference skill for GitHub Copilot terminal-first operation.
- **Swarm commands** (`@g-go-swarm`, `@g-go-code-swarm`, `@g-go-review-swarm`): multi-agent coordinated execution across the backlog.
- **Vault process-inbox command** (`@g-vault-process-inbox`): process pending vault inbox items.
- **`.gald3r/releases/`** directory, **`.gald3r/release_profiles/`** directory, and **`.gald3r/RELEASES.md`** index: new release tracking structure.
- **`.gald3r/logs/`** directory: session log storage.
- **`ROADMAP.md`**: project roadmap file at repo root.
- **`raw-inbox-watcher.ps1`** hook: real-time PCAC inbox watcher.

### Changed

- `g-skl-reverse-spec` â†’ `g-skl-recon-repo`: renamed and expanded. The recon namespace (`recon-*`) supersedes the ad-hoc harvest/ingest/reverse-spec naming.
- `g-skl-harvest-intake` â†’ `g-skl-res-apply`: part of the three-step res-* workflow (res-review â†’ res-deep â†’ res-apply).
- `g-skl-ingest-docs` â†’ `g-skl-recon-docs`: unified into recon namespace.
- `g-skl-ingest-url` â†’ `g-skl-recon-url`: unified into recon namespace.
- `g-skl-ingest-youtube` â†’ `g-skl-recon-yt`: unified into recon namespace.
- `g-skl-harvest` â†’ subsumed by `g-skl-recon-repo` + `g-skl-res-review`.
- README: IDE parity updated from 5 â†’ 6 IDEs (12 parity targets). Skills 49 â†’ 58, Commands 78 â†’ 89.
- `g-skl-medkit` version migration updated to include 1.2 â†’ 1.4 path.

### Removed

- `g-skl-harvest`, `g-skl-harvest-intake` skill directories (superseded by recon-* / res-* suites)
- `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube` skill directories (superseded by recon-*)
- `g-skl-reverse-spec` skill directory (superseded by `g-skl-recon-repo`)
- Corresponding commands: `@g-harvest`, `@g-harvest-intake`, `@g-ingest-docs`, `@g-ingest-url`, `@g-ingest-youtube`, `@g-reverse-spec`

---

## [1.2.1] - 2026-04-14

### Added

- **PCAC Spawn skill** (`g-skl-pcac-spawn`, `@g-pcac-spawn`): spawn a new gald3r project from the current one -- creates the project folder in the ecosystem root, installs gald3r (matching current project's install style), seeds it with an optional description/features/code, runs subsystem discovery, and registers bidirectional PCAC topology links in both projects. Supports `--sibling`, `--child`, `--parent`, and `--dry-run`.
- **PCAC Send-To skill** (`g-skl-pcac-send-to`, `@g-pcac-send-to`): transfer files, features, specs, ideas, bugs, or code from the current project to any related project in the topology. Lighter-weight than `g-skl-pcac-move` -- works with freshly spawned projects, writes an INBOX notification in the destination, and logs provenance in the source vault. Supports `--type features|code|ideas|bugs|docs|spec`, `--delete-source`, and `--dry-run`.
- Both skills deployed across all 5 IDE trees (`.cursor`, `.claude`, `.agent`, `.codex`, `.opencode`) with full parity.

---

## [1.2.0] - 2026-04-14

### Added

- **Feature pipeline** (`g-skl-features`, `FEATURES.md`, `.gald3r/features/`): structured staging layer between idea capture and task creation. Features move through `staging â†’ specced â†’ committed â†’ shipped`. Only reach the TASKS.md backlog when explicitly promoted via `@g-feat-promote`. Prevents backlog pollution and keeps implementation intent explicit.
- **Reverse-spec skill** (`g-skl-reverse-spec`, `@g-reverse-spec`): deep 5-pass analysis of any external repository. Produces a structured harvest report in `research/harvests/{slug}/` with skeleton, module map, feature scan, deep dives, and synthesis passes. Human reviews and marks features `[âœ…] approved` before APPLY writes to `.gald3r/features/`.
- **Harvest intake skill** (`g-skl-harvest-intake`, `@g-harvest-intake`): processes approved harvest output into `.gald3r/features/` staging entries. Deduplicates against existing staging features -- appends a Collected Approach rather than creating a duplicate.
- **Subsystem graph skill** (`g-skl-subsystem-graph`, `@g-subsystem-graph`): generates a visual Mermaid dependency graph of all registered subsystems with dependency annotations.
- **IDE CLI skills** (`g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode`): dedicated reference skills for headless and terminal-first operation of each supported IDE. Cover agent mode, Cloud Agent handoff, API mode, session continuation, MCP config, checkpointing, and multi-agent patterns.
- **Granular task commands** (`@g-task-add`, `@g-task-upd`, `@g-task-del`): fine-grained task operations to supplement the existing `@g-task-new` and `@g-task-update` commands.
- **Granular bug commands** (`@g-bug-add`, `@g-bug-upd`, `@g-bug-del`): fine-grained bug management to complement `@g-bug-report` and `@g-bug-fix`.
- **Granular constraint commands** (`@g-constraint-upd`, `@g-constraint-del`): update and delete constraints in `CONSTRAINTS.md`.
- **Granular subsystem commands** (`@g-subsystem-add`, `@g-subsystem-upd`, `@g-subsystem-del`, `@g-subsystem-graph`): full CRUD surface for the subsystem registry.
- **Feature commands** (`@g-feat-new`, `@g-feat-add`, `@g-feat-upd`, `@g-feat-promote`, `@g-feat-rename`, `@g-feat-del`): full feature lifecycle management from the command surface.
- **IDE CLI commands** (`@g-cli-cursor`, `@g-cli-claude`, `@g-cli-gemini`): quick reference commands for each IDE's CLI usage patterns.

### Changed

- `g-go-verify` renamed to `@g-go-review` -- clearer intent (this is the review/verification phase, not a QA pass). Old command name removed from all IDE directories.
- `g-skl-cursor-cli`, `g-skl-claude-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` renamed to `g-skl-cli-cursor`, `g-skl-cli-claude`, `g-skl-cli-gemini`, `g-skl-cli-opencode` -- consistent `g-skl-cli-*` namespace pattern. Old skill directories removed.
- `g-skl-plan` updated: `features/` replaces `prds/` as the primary deliverable directory. PRD concepts live inside feature spec files.
- `g-skl-harvest` updated: `APPLY` operation now calls `g-skl-features COLLECT` to dedup against existing staging features instead of creating tasks directly.
- `g-skl-medkit` updated: detects projects with `prds/` folder and no `features/` folder -- offers migration path to 1.2.0 feature pipeline.
- README: updated component counts (Skills: 39 â†’ 47, Commands: 52 â†’ 76, Skill Packs: 6 â†’ 7), added Feature Pipeline section, updated directory tree to show `features/`, updated all skill and command references.

### Removed

- `g-claude-cli.md`, `g-cursor-cli.md`, `g-gemini-cli.md` commands (superseded by `g-cli-claude.md`, `g-cli-cursor.md`, `g-cli-gemini.md`)
- `g-go-verify.md` command (superseded by `g-go-review.md`)
- `g-skl-claude-cli`, `g-skl-cursor-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` skill directories (superseded by `g-skl-cli-*` namespace)

---

## [1.1.0] - 2026-04-08

### Added

- **Task circuit breaker** (`[ðŸš¨]` Requires-User-Attention): tasks that fail verification 3 or more times are automatically escalated for human review. Automated agents skip them and they remain visible in the backlog until a human resets or cancels.
- **Status History table** on all task and bug files: every state transition records a timestamp, from-state, to-state, and reason. Creates a full audit trail for every item in the backlog.
- **Re-work surface at session start**: if a task's last Status History entry is a FAIL, it is flagged at session start so the implementing agent knows what to watch for before starting.
- **Pre-push gate** (`@g-git-push`, `scripts/gald3r_push_gate.ps1`): validates that tasks are in the correct state, CHANGELOG is updated, and no staged secrets are present before allowing a push to reach the remote.
- **Pre-commit sanity check** (`@g-git-sanity`): detects staged secrets, files over size limits, and `.gald3r/` sync drift before a commit is created.
- **Architectural constraints skill** (`g-skl-constraints`): dedicated ADD, UPDATE, CHECK, and LIST operations for `CONSTRAINTS.md`. Constraints are validated at session start and before marking any task complete.
- **Knowledge vault Obsidian compliance**: standardized frontmatter schema (type, topics, date, source), type registry, tag taxonomy, and encoding rules. All vault notes now comply with Obsidian's native indexing format.
- **MOC hub generation** (`gen_vault_moc.py`): automatically generates `_INDEX.md` navigation files for vault directories with 10 or more notes. Creates wikilinks that show connections in Obsidian graph view.
- **Platform documentation crawling** (`g-skl-ingest-docs`): schedule-aware ingestion with per-platform freshness tracking. Stale docs are flagged at session start.
- **Native web crawler** (`g-skl-crawl`): crawl4ai integration for clean LLM-optimized markdown extraction without Docker. Shared primitive used by ingest-docs, ingest-url, and harvest.
- **URL ingestion** (`g-skl-ingest-url`): one-time article and page capture into the vault with frontmatter and deduplication by source URL.
- **YouTube transcript ingestion** (`g-skl-ingest-youtube`): offline transcript extraction via yt-dlp. Stores in `research/videos/` with full frontmatter compliance.
- **Vault management skill** (`g-skl-vault`): unified vault operations including Obsidian compatibility tools, MOC rebuild, frontmatter linting, and GitHub repo summaries.
- **Continual learning skill** (`g-skl-learn`): agents self-report insights to vault memory files after each session. No external services required -- file-only persistence.
- **Health and repair skill** (`g-skl-medkit`): single skill that detects what a `.gald3r/` directory needs (version migration, structural repair, or routine maintenance) and performs it. Replaces the separate g-cleanup, g-grooming, and g-upgrade skills.
- **Platform crawl skill** (`g-platform-crawl`): dedicated skill for crawling Cursor, Claude Code, Gemini, and other platform documentation with configurable targets.
- **Dependency graph** (`g-skl-dependency-graph`): auto-generates `.gald3r/DEPENDENCY_GRAPH.md` from task file dependencies. Shows blocked and blocking relationships.
- **SWOT review skill** (`g-skl-swot-review`): automated SWOT analysis for the current project phase. Reviewsprogress, architectural compliance, code quality, and technical debt.
- **Verify ladder skill** (`g-skl-verify-ladder`): configurable multi-level verification gates from minimal (lint only) to thorough (tests + acceptance + hallucination guard).
- **Knowledge refresh skill** (`g-skl-knowledge-refresh`): audit vault freshness, rebuild compiled pages, detect broken links and stale notes.

### Changed

- `g-go-code` now requires a Status History entry before marking any item `[ðŸ”]`. The b3 step is mandatory.
- `g-go-review` FAIL path now counts FAIL rows in Status History to determine whether to reset to `[ðŸ“‹]` or escalate to `[ðŸš¨]`.
- `g-go-code` skips `[ðŸš¨]` items entirely -- logs them in the Skipped section as Requires-User-Attention.
- Session start protocol (step 2) now surfaces re-work tasks when the last Status History entry is a FAIL.
- `g-skl-tasks` and `g-skl-bugs` templates include Status History section. Every status transition appends a row.

### Fixed

- Session hook (`g-hk-agent-complete.ps1`): `$input` pipeline variable does not capture external-process stdin in PowerShell. Fixed to use `[Console]::In.ReadToEnd()`. Status mapping corrected from `"success"` to `"completed"` per Cursor hook schema.
- `pending_reflection.json` was never written when the session hook ran in a non-interactive terminal. Fixed `[Console]::IsInputRedirected` guard to prevent blocking on `ReadToEnd()`.

---

## [1.0.0] - 2026-04-04

### Added

- **Task management system**: YAML frontmatter task specs with sequential IDs, priority, dependencies, and subsystem tracking. Master `TASKS.md` checklist with per-file status sync.
- **Two-phase adversarial code review** (`@g-go-code` / `@g-go-verify`): implementation and verification are separated into distinct agent sessions. The implementing agent marks `[ðŸ”]`; a separate agent marks `[âœ…]`. Neither can do both.
- **Five-IDE parity**: identical agents, skills, commands, and rules across Cursor (`.cursor/`), Claude Code (`.claude/`), Gemini (`.agent/`), Codex (`.codex/`), and OpenCode (`.opencode/`).
- **PCAC cross-project topology**: projects declare parent, child, and sibling relationships. Parents broadcast tasks (`@g-pcac-order`). Children request actions (`@g-pcac-ask`). Siblings sync shared contracts (`@g-pcac-sync`). Cross-project INBOX tracks all coordination items.
- **Knowledge vault**: file-based knowledge store for session summaries, research notes, architectural decisions, and platform documentation. Vault notes use standardized YAML frontmatter.
- **Session start protocol**: reads `.gald3r/` state at session start, validates task sync, surfaces open bugs, checks for specification files, and displays project context in a structured summary.
- **Bug tracking**: sequential BUG-NNN IDs, severity classification (Critical/High/Medium/Low), `BUGS.md` index, individual bug spec files, and code annotation format (`BUG[BUG-NNN]: description`).
- **Architectural constraints** (`CONSTRAINTS.md`): non-negotiable project rules loaded at every session start. Agents flag violations before proceeding.
- **Subsystem registry** (`SUBSYSTEMS.md`, `subsystems/`): each subsystem has a spec file with locations, dependencies, dependents, and an Activity Log. Agents update the Activity Log on task completion.
- **9 gald3r system agents**: task-manager, qa-engineer, code-reviewer, project, infrastructure, ideas-goals, verifier, project-initializer, pcac-coordinator.
- **Docker MCP server** (42 tools): RAG search, Oracle SQL, MediaWiki, vault indexing, session memory capture and retrieval, video analysis, platform crawling, and project health reports.
- **Continual learning**: agents extract durable facts from conversation transcripts and persist them in `AGENTS.md`. Agents remember preferences, project conventions, and past decisions across sessions.
- **TODO lifecycle enforcement**: stubs and TODOs must be annotated with `TODO[TASK-Xâ†’TASK-Y]` format and a follow-up task created before the implementing task can be marked complete.
- **Bug discovery gate**: pre-existing bugs encountered during implementation must have a BUG entry and code annotation before the task is marked `[ðŸ”]`.
- **Git commit skill** (`g-skl-git-commit`): conventional commit format with task references and agent footers.
- **Project planning** (`g-skl-plan`, `g-skl-project`): PLAN.md (milestones and deliverables), PROJECT.md (mission, vision, goals), PRD files, and CONSTRAINTS.md.
- **Code review** (`g-skl-code-review`): structured review covering security, performance, maintainability, and architectural alignment. Severity-classified output with file/line references.
- **Harvest skill** (`g-skl-harvest`): analyze external repositories for adoptable patterns and improvements. Zero-change-without-approval output.

---

*gald3r is built with gald3r. The development history of this framework lives in the <gald3r_source> source repository.*
