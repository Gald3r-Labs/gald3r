# Changelog

All notable changes to the gald3r framework are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) ·
gald3r uses [Semantic Versioning](https://semver.org/).

> This is the **product** changelog — what changed for you. Engineering-level detail
> (internal refactors, task IDs, file moves) lives in the git history, not here.
>
> The engine has its own changelog at
> [Gald3r-Labs/gald3r_core](https://github.com/Gald3r-Labs/gald3r_core/blob/main/CHANGELOG.md).

---

## [Unreleased]

_Pending notes accumulate here and are promoted at release time._

---

## [4.0.0] - 2026-08-01

**gald3r becomes a matched pair: framework + compiled engine.**

### Added
- **A signed, compiled engine.** The deterministic core that runs task and bug lifecycle,
  validation, the local database, and multi-agent orchestration now ships as a single signed
  binary from [gald3r_core](https://github.com/Gald3r-Labs/gald3r_core/releases) — with a
  Windows MSI installer. No Python toolchain required.
- **39 supported AI coding platforms**, up from 34.
- **15 specialized agents** for review, verification, QA, and infrastructure work.

### Changed
- **Version line unified.** "gald3r 4.0" now names the framework and the engine together.
  Version 3.x was template-only, installed per IDE; 4.0 is the first release where the two
  ship as one product.
- **Shipped component counts:** 116 skills, 182 commands, 38 hooks, 13 rules.
- **Install guidance split by product.** The framework installs from this repo; the engine
  installs from `gald3r_core`; the desktop app installs from `gald3r_throne`. Each product
  is fetched from its own release channel.
- **README rewritten** around what gald3r actually does for you rather than what it contains.

### Fixed
- Corrected repository links throughout the documentation (the project moved to the
  **Gald3r-Labs** organization).
- Repaired broken links to the platform support matrix and release notes.

---

## [3.0.0] - 2026-07-06

**The framework goes Python-first.**

### Changed
- Helper scripts that previously shipped as loose files are now built into the engine —
  fewer moving parts in your project, and the same behavior on every platform.
- Platform verification became a first-class capability: check an installed platform tree
  in place, with an HTML report card.

### Fixed
- Eliminated character-encoding corruption in shipped template files, with a guard to keep
  it from returning.
- Fresh installs no longer create stray placeholder directories.

---

## [2.4.0] - 2026-06-27

### Added
- One-command installs for the companion apps, downloading signed builds from public
  release channels with integrity verification before anything is written to disk.

### Fixed
- Install integrity can no longer fail open: a missing or tampered signature stops the
  install loudly instead of proceeding silently.

---

## [2.3.0] - 2026-06-25

### Changed
- Completed the migration from PowerShell to Python across the framework — one codebase,
  identical behavior on Windows, macOS, and Linux. Roughly a thousand redundant scripts
  were removed from the shipped payload.
- Task IDs in `TASKS.md` are now consistently formatted.

---

## [2.2.0] - 2026-06-24

### Added
- The autonomous work conductor streams live progress to your terminal instead of running
  silently.

### Fixed
- The conductor now halts on coordinator failure rather than burning through its remaining
  budget on repeated errors.

---

## [2.1.2] - 2026-06-23

### Added
- A comprehensive pre-flight backup before any upgrade is applied.

### Fixed
- Upgrades no longer deprecate removed components by default — that behavior is now opt-in.
- Version reporting no longer shows stale numbers after an upgrade.

---

## [2.1.1] - 2026-06-23

### Added
- **Plugin lifecycle management** — install, remove, list, and update gald3r plugins.
- **Vault knowledge tools** — structured note retrieval and backlink queries over your
  project's knowledge base.
- **Selectable vault location** — user-level, workspace, or per-project.

---

## [2.1.0] - 2026-06-20

### Added
- Per-platform test harness with an HTML report card.
- Unified identity provisioning on first run.
- A canonical hook event set shared across platforms.

### Fixed
- Generated projects no longer ship build artifacts or virtual environments.

---

## [2.0.1] - 2026-06-10

### Changed
- Copyright transferred to Gald3r Labs LLC across all repositories.
- Default organization updated to **Gald3r-Labs**.
- Platform repositories now publish GitHub Releases by default.

---

## [2.0.0] - 2026-06-04

**The engine arrives.**

### Added
- **A file-first engine** driving every system — tasks, bugs, vault, releases — deterministically,
  with zero LLM calls.
- **A command line** (`gald3r task new`, `gald3r bug new`, …) so you can drive the same state
  from a shell or a script.
- **An MCP server** exposing those operations as tools to any MCP-capable agent.
- **`gald3r doctor`** — a read-only health check for your installation.

---

## [1.10] - 2026-06-02 — *Cursor + Claude Unity Edition*

### Added
- All 34 platform adapters moved into this repository.
- `--platform <name>` installer flag to target a single platform.

### Changed
- Restructured the install model around a single `project_template/` directory you copy into
  your project.

---

## [1.0.0] – [1.9.0] · 2026-05

Early releases: the initial `.gald3r/` brain structure, the first skill and command sets,
Cursor and Claude Code support, and the installer scripts. Full detail is in the git history.
