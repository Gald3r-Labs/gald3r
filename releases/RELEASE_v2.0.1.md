# gald3r v2.0.1 — Self-Update, Throne In-App Update & Developer Experience

**Date:** 2026-06-19

gald3r 2.0.1 adds the full self-update stack: the CLI can check for updates and safely upgrade
any project's `.gald3r/`, and gald3r_throne can now detect and apply updates from inside the app
— in compiled Rust, no Python required. A suite of Throne developer-experience improvements ships
alongside.

---

## Headline

**Your AI framework now keeps itself up to date — safely, with rollback, from the CLI or from inside Throne.**

---

## What's new

### Self-update (CLI — `gald3r_agent` + all template installs)

- **`gald3r version-check`** — queries the gald3r server for the latest published version, shows current vs. latest, and degrades gracefully when offline or unauthenticated (never crashes, never fabricates a version).
- **`gald3r upgrade`** — backs up your `.gald3r/` folder to a timestamped `.gald3r/_backups/*.zip` (gitignored), migrates it to the latest format using the ADD/MERGE/DEPRECATE engine, and **rolls back byte-for-byte on any failure**. Your tasks, bugs, plans, and constraints are on the denylist — they are never touched. `--dry-run` (default) previews; `--apply` executes.
- **`gald3r init`** — scaffolds a fresh gald3r project into any folder (`--name`, `--description`, `--vision`, `--tech-stack`). Existing projects route to the update path instead of re-initializing.
- **`gald3r upgrade --dry-run`** — safe preview of every file change before you commit.

### gald3r_throne in-app update

- **Version check badge** — Throne shows an "update available" indicator when a newer gald3r version is detected on connect. Queries world_tree's version endpoint; offline-first (unreachable → graceful badge, no crash).
- **In-app apply** — click to update your project's `.gald3r/` directly from Throne. The full safety envelope runs inside compiled Rust: backup ZIP → integrity verify → real file-merge (frontmatter/key ADD/MERGE/DEPRECATE) → audit report → **byte-for-byte rollback on failure**. No Python dependency, no network write — your local project files only.
- **Pre-apply preview** — a modal shows the exact version delta before you confirm.

### Shared install infrastructure

- **Centralized install home** (`settings/`, `logs/`, `gald3r_vault/`) resolved by precedence: override → portable → `GALD3R_HOME` → per-OS default (Windows `%LOCALAPPDATA%\gald3r`, macOS `~/Library/Application Support/gald3r`, Linux `$XDG_DATA_HOME/gald3r`). USB-portable mode: `--portable` / `GALD3R_PORTABLE=1`.
- **Global `gald3r` command** — `gald3r home --ensure` installs the global shim; `gald3r --version` works from any directory.
- **Vault + identity auto-provision** — on first run, the install home auto-creates `gald3r_vault/` at the configured location and seeds `.gald3r/.identity` from layered defaults (install-home → user → project). Secrets are never written to identity files.

### Throne developer experience (T438 epic)

- **Diff Review Center** — multi-file red/green review with book-folded unchanged sections.
- **Source Control Center** — per-hunk stage/revert, commit composer, branch switcher.
- **CodeMirror 6 editor** — replaces the legacy editor; syntax highlighting, multi-cursor, LSP diagnostics.
- **Context-aware chat dock** — right-panel chat wired to world_tree, project-context-aware.
- **Local agent wiring** — free BYO local models (Ollama, LM Studio) selectable alongside cloud providers.
- **Workspace project spawning** — scaffold new projects of any registered type from within Throne.
- **IDE shell** — integrated terminal (PTY), file editor with save, LSP transport + diagnostics, find-in-files.

---

## Why upgrade now

- **Your `.gald3r/` will never be left behind** — `gald3r upgrade` migrates forward safely with full rollback.
- **Throne users get in-app updates** with one click and no terminal required.
- gald3r 2.0.1 is the foundation for the precompiled installer release (T528/T529) coming next.

---

## Coming next

- `gald3r install agent|throne` — precompiled, signed, cross-platform installers so users never need to build from source. In progress as T528 (Throne) and T529 (Agent).

---

_See [CHANGELOG.md](../CHANGELOG.md) for the full technical list._
