## [1.9.0] - 2026-05-31 (Platforms/ Folder + Post-Push Verify + Plugin System Foundation)

### Added
- **Plugin system foundation** (T1557–T1559): `@g-plugin-install` lands — install a gald3r plugin from a local path (GitHub-URL path implemented, not yet network-tested). Backed by ADR-015 (`.gald3r_sys/docs/adr/ADR-015-plugin-system.md`), a `gald3r-plugin.yaml` manifest schema + validator (`.gald3r_sys/plugins/schema/`), and a security-first installer: it validates the manifest, enforces `gald3r_min_version`, **refuses to overwrite gald3r-core components** (conflict-abort, ADR-015 D6), stamps installed components with `plugin_source:`, records a `.gald3r_sys/plugins/installed.yaml` ledger, and **never auto-runs plugin lifecycle scripts** (opt-in `-RunInstallScript`, previews first, ADR-015 D7). Remaining plugin commands (list/new/remove/update/registry) are in progress (T1560–T1568).
- `scan_platform_docs.ps1 -WithHtml` / `-HappyPath` (T1545): after a platform's `PLATFORM_SPEC.md` is updated by a doc scan, automatically regenerates its `docs/platforms/<name>_guide.html` via `generate_platform_guide.ps1` (per-platform, in a child process so one guide's failure is non-fatal) and stamps `last_html_generated:` in the canonical spec for staleness visibility. Default (no `-WithHtml`) behavior is unchanged — no HTML regeneration. Closes the "happy path" gap where the spec and its HTML guide drifted out of sync.
- `check_platform_status.ps1 -GenerateMatrix` (T1543): auto-populates `.gald3r/PLATFORM_CAPABILITY_MATRIX.md` from the 23 canonical `PLATFORM_SPEC.md` `## Capability Summary` tables (Hooks / Rules / Skills / Commands / MCP, plus a Docs-Fresh cell computed from each spec's `crawl_max_age_days`). Replaces the all-❓ placeholder matrix with real values, cross-checks every cell against the hand-verified `PLATFORM_STATUS.md` and warns on disagreement (never overwrites STATUS). Wired into `platform_parity_sync.ps1 -ValidatePlatformSpecs` so the matrix refreshes after each parity sync. First run: `Updated 138 cells (45 ✅, 54 ⚠️, 33 ❌, 6 ❓)`.

### Changed
- **`gald3r` public repo restructured**: 34 platform directories moved from repo root into `platforms/` subfolder (`gald3r/platforms/<name>/`) for a cleaner root (T1556). `platform_parity_sync.ps1 -SyncToGald3r` updated to target `platforms/` automatically. `DISTRIBUTION_PLAYBOOK.md` Step 5 updated to reflect new target path.
- `platform_parity_sync.ps1 -ValidatePlatformSpecs` / `GeneratePlatformCats` now discover platforms by scanning `gald3r_template/.gald3r_sys/platforms/` dynamically rather than a hardcoded list (T1556 alignment).

### Added
- `action_scripts/post_push_verify.ps1` (T1572): 11-check post-push gate that verifies a release landed correctly — VERSION file, CHANGELOG entry + content depth, releases/ file, git remote tag, GitHub release existence + release-notes body populated, public gald3r repo VERSION, public gald3r README version mention, wiki file freshness, and a 10-pattern secrets scan of the release diff (AWS keys, GH tokens, private keys, password/API-key literals, bearer tokens, credential URLs, Slack tokens, DB connection strings). Code-file hits are FAIL; doc-file matches WARN with example suppression. Wired into `DISTRIBUTION_PLAYBOOK.md` Step 8b.

### Fixed
### Removed
- `@g-kamikaze` and `@g-juggernaut` commands (T1548): both were pure aliases for `@g-mission` with no added behavior — three names for one command added cognitive load without value. Deleted the command files (and their `.github/prompts` Copilot copies) across all platform targets, removed the alias references from `g-mission` and `docs/wiki/Commands.md`, and updated the parity-sync mission-command manifest. Use `@g-mission` directly.

---

