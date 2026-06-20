## [1.10] - 2026-06-02 (Cursor + Claude Unity Edition)

The platform-unification release: the install model and platform adapters are unified so
Cursor and Claude Code share one `project_template/` brain, and every other platform layers
a thin config overlay on top of it.

### Added
- **`platforms/` folder**: all 34 platform thin adapters now live directly in `gald3r` — no
  need to clone a separate advanced template for Windsurf, Cline, Copilot, etc.
- **`-Platform <name>` installer arg**: `setup_gald3r_project.ps1` accepts any of 34 platforms.
  Default (no arg) = Cursor + Claude Code. `-Platform windsurf` etc. copies the shared brain
  (without `.cursor/.claude`) plus the platform's thin config overlay.

### Changed
- **Restructured install model**: deliverable is now `project_template/` — copy its contents to
  your project root. Cursor + Claude Code are Tier 1; other platforms via `AGENTS.md` + `.gald3r/`.
- **Simplified installer**: `setup_gald3r_project.ps1` rewritten from 44KB → ~110 lines. Single
  purpose: copy `project_template/` to target, preserving existing `.gald3r/` user data.
- **Stripped maintainer-only rules** from the shipped template (`g-rl-25` session-start,
  `g-rl-33` enforcement-catchall, `g-rl-36` workspace-guard) — these are framework-build tools,
  not end-user config. Shipped set: 11 lightweight rules + `gald3r_personality`.

### Fixed
- **Personality rule extension**: renamed `gald3r_personality.md` → `gald3r_personality.mdc` in
  `project_template/.cursor/rules/`. Cursor only loads `.mdc` files from the rules folder; the
  Norse personality was silently not loading.
- **License reference in README**: corrected to `Fair Source License 1.1 (FSL-1.1-Apache)`.
- **README**: updated version badge, installer docs, and platform table.

> Reconciliation note (2026-06-18, BUG-157): this release record was reconstructed from the
> published GitHub tag `v1.10` (Gald3r-Labs/gald3r) plus the two CHANGELOG sections that had been
> mislabeled `## [1.11.0]` (dated 2026-06-03/06-04). GitHub never published a `1.11.0`; that work
> shipped under `v1.10`. See BUG-157.

---
