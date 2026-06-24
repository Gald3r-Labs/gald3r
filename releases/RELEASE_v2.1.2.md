# gald3r v2.1.2 — Critical upgrade-safety fix

**If you ever run `gald3r update` / `gald3r upgrade`, update to 2.1.2 now.** This release stops
the upgrader from touching your data and adds an automatic full backup before every upgrade.

## Why upgrade now

A defect in earlier versions could rename your **entire `.gald3r/` workspace** —
tasks, bugs, specs, plans, idea board, coordination ledgers — as `*_deprecated_<date>` during a
routine `gald3r update`. 2.1.2 fixes the root cause and makes upgrades safe by default.

## Fixed

- **CRITICAL (BUG-176): `gald3r update` could archive all your content as obsolete.** The upgrade
  planner treated *everything in your project that isn't in the shipped template* as "removed",
  so a normal `gald3r update` (which has no old-template baseline) flagged every user-authored
  file as obsolete and renamed it `*_deprecated_<date>`. **Now deprecation is strictly opt-in
  (`--deprecate-removed`, default OFF)** — `gald3r update` only **adds** new framework files and
  **merges** format changes, and never archives your content.
- **BUG-175: correct version reporting.** `gald3r --version` and `.gald3r_sys/VERSION` now report
  the real release version (previously stuck at `0.1.0` / `2.0.0`). `--version` derives from
  installed package metadata, and the build stamps `.gald3r_sys/VERSION` in every generated repo.

## Added

- **Automatic pre-flight safety backup on `gald3r upgrade --apply`.** Before any change, every
  framework tree (`.gald3r`, `.gald3r_sys`, `.claude`, `.cursor`, `.agent`, `.codex`,
  `.opencode`) is zipped to a timestamped archive at your repo root (auto-gitignored) — so custom
  code anywhere in those trees is always recoverable.
- **`gald3r upgrade --deprecate-removed` opt-in flag** to re-enable the legacy removed-file
  cleanup, safe only with an explicit `--from-version` / `--from-dir` template baseline.

---

_Full technical detail in [CHANGELOG.md](../CHANGELOG.md)._
