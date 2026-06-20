# gald3r v2.1.0 — A Real Home, Self-Update & Throne DX

**Released:** 2026-06-20

---

## Headline

gald3r now has a real home on your machine — one CLI, shared across every project, every OS.
Install once. Scaffold projects. Stay updated. Throne tells you when you're out of date and can
apply the update from inside the app.

---

## What's New

### Centralized gald3r Home + Global CLI (T471)
A shared install home (`settings/`, `logs/`, `gald3r_vault/`, `VERSION`) resolved by precedence:
`override > portable > GALD3R_HOME > per-OS default`
- Windows: `%LOCALAPPDATA%\gald3r`
- macOS: `~/Library/Application Support/gald3r`
- Linux: `$XDG_DATA_HOME/gald3r`

USB-portable mode (`--portable` / `GALD3R_PORTABLE=1`) runs with no outside writes.
New `gald3r home` subcommand + idempotent global `gald3r` CLI installer (Windows `.cmd` + user-PATH; POSIX `~/.local/bin` shim).

### Per-User Home Migration: `gald3r migrate-home` (T530)
Safely migrates `.gald3r/` data from an old layout to the new unified home. Backs up before touching anything, rolls back on failure.

### Self-Update: `gald3r version-check` + `gald3r upgrade` (T473, T475)
- `gald3r version-check` — queries the gald3r server for the latest version, shows current vs. latest. Offline-first: any network failure degrades gracefully, never crashes.
- `gald3r upgrade` — takes a timestamped backup of `.gald3r/`, migrates to the latest format (ADD/MERGE/DEPRECATE; user data — `tasks/**`, `bugs/**`, `TASKS.md`, `PLAN.md` — is **never touched**), and rolls back from the backup on any failure. `--dry-run` (default) previews; `--apply` performs.

### Throne: In-App Version Check + Update Badge (T474)
Throne now queries the version endpoint on connect and shows an **"update available"** badge in the UI when a newer version is detected. Offline-first — unreachable server means no badge, no crash.

### Throne: In-App Update APPLY in Rust (T481)
Throne can apply a `.gald3r/` update entirely from inside the app — no Python, no engine, no terminal. Full safety envelope: backup ZIP → integrity-verify → apply → rollback on any failure. User-data denylist mirrors the Python engine exactly. 34 Rust tests.

### Throne: Installed-Platforms Page (T534)
New page in Throne showing which platforms have gald3r installed in the current project (reads `.gald3r/`-safe platform data, no external calls).

### Throne: New-Project Platform Picker (T535)
When scaffolding a new project from Throne, a platform picker lets you choose your IDE/agent upfront so the right platform overlay is applied from the start.

### Throne: In-App Feedback + Issue Reporting (T537)
New "Report an Issue" flow inside Throne + `/feedback` endpoint. No IDOR — all submissions are tenant-scoped and validated server-side.

### Multi-Platform Install Selection + Readiness Catalog (T533)
The install system now detects which platforms are present on the machine and shows a readiness catalog — one place to see what's installed, what's missing, and what `gald3r install` will do.

### Crash Sink + Engine/Throne Reporters (T538)
Vendor crash sink with engine and Throne reporters. Crashes are anonymized (secrets, paths, emails scrubbed) before any report leaves the machine.

### Cross-Language `GALD3R_HOME` (T573)
Rust (Throne) and Python (engine) now agree on the same `GALD3R_HOME` resolution logic. One source of truth, no divergence.

### Registry-Driven Install Planner (T574)
The install planner is now registry-driven — platform op-gen reads a central registry rather than hard-coded conditionals. Easier to add platforms, easier to test.

### Project Scaffold: `gald3r init` + `gald3r update` (T477)
- `gald3r init` — scaffolds a fresh gald3r project into any folder, seeding `PROJECT.md` from CLI flags (`--name`, `--description`, `--vision`, `--tech-stack`). Idempotent: existing projects route to `update`.
- `gald3r update` — runs the safe-update core (backup → migrate → rollback) on an existing project.

### Vault + Identity Auto-Provisioned on Install (T476)
Local install folder now auto-creates `gald3r_vault` and writes `.gald3r/.identity` by layering `install-home defaults → user identity → per-project overrides`. Credentials/tokens are stripped before writing — secrets stay gitignored.

### CRASH Activation Tracking (T433)
`gald3r crash-stats` and `@g-crash-stats` report Most Active / Least Active / Never Activated / "Should Be Called But Isn't" across all five extension-point types. Appends one JSON line per activation to `.gald3r/logs/crash_activations.jsonl`.

---

## Coming Next

- **`gald3r install agent|throne`** — precompiled OS-native installers so users never need to build from source. Tracked in T528 (Throne) and T529 (Agent). Until those ship, `gald3r install` returns a clear "not yet available" message pointing to these tasks.
- **T575** — Server-side consent enforcement for `/feedback` diagnostics
- **T578** — Harden crash anonymizer (connection-string creds, POSIX paths)
- **T576** — Wire Throne crash CAPTURE sites (Rust panic hook + React boundary)
- **T579** — Migrate remaining Throne `app_data_dir()` sites onto `gald3r_home`

---

## Upgrade

```bash
gald3r upgrade --apply
```

Or from inside Throne: look for the **"update available"** badge and click Apply.

---

_See [CHANGELOG.md](../CHANGELOG.md) for the full technical list._
