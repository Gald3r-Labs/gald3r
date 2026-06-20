# ADR 016 — Centralized Install Home, Global `gald3r` CLI, and USB-Portable Variant

- **Status:** Accepted
- **Date:** 2026-06-15
- **Task:** T471 (epic T470)
- **Binding for:** every gald3r product that needs a shared, cross-product home
  (gald3r_agent, gald3r_throne, the engine, and future products) and for any
  install scripting that registers the `gald3r` command.
- **Supersedes:** none
- **Deciders:** gald3r framework (templates pipeline)

---

## Status

**Accepted.** This decision is **BINDING**. There is exactly ONE resolution point
for the install-home path — `gald3r.home.resolve_install_home()` — and all
products MUST use it rather than re-deriving an OS path. Changing the layout, the
per-OS defaults, the `GALD3R_HOME` override, or the portable rule requires a new
ADR that supersedes this one.

---

## Context

gald3r products previously had no shared, OS-appropriate home for cross-product
state, and the `gald3r` command was not registered on the system PATH — it could
only be run as `uv run gald3r ...` from inside the engine checkout. Two distinct
"home" concepts must not be confused:

- **Project home** — a repo's `.gald3r/` directory, resolved per-repo by
  `gald3r.config.find_root()` (walk up to the nearest `.gald3r/`). Unchanged.
- **Install home** (this ADR) — a single machine-wide (or medium-wide, when
  portable) folder holding shared `settings/`, `logs/`, `gald3r_vault/`, and a
  `VERSION` manifest, used by every product regardless of which repo it runs in.

The project also has a standing plan for a **USB travel / portable** edition; per
the T470 directive that decision is folded in here rather than retrofitted later.

The repo already had a precedent for "one resolver, override → env → default":
`gald3r_forge.paths.resolve_workspace_root()` (T412) resolves the build-output
workspace with precedence `override > GALD3R_TEMPLATES_WORKSPACE env > fixed
default`. This ADR mirrors that pattern for the install home.

---

## Decision

### 1. Install-home layout

```
<install-home>/
  settings/        # shared, cross-product configuration
  logs/            # shared logs
  gald3r_vault/    # shared knowledge vault
  VERSION          # manifest: the engine version that created/owns this home
```

`settings/`, `logs/`, `gald3r_vault/` are created by `ensure_install_home()`;
`VERSION` is written (stamped with the engine `__version__`) only when absent.
**No secrets are written into the install home** — identity/secret handling stays
per existing conventions (per-project `.gald3r/.identity`, `.env`, etc.).

### 2. Per-OS defaults

| OS | Default install home |
|---|---|
| Windows | `%LOCALAPPDATA%\gald3r` (fallback `~\AppData\Local\gald3r`) |
| Linux / other POSIX | `$XDG_DATA_HOME/gald3r` (fallback `~/.local/share/gald3r`) |
| macOS | `~/Library/Application Support/gald3r` |

These are computed in `gald3r.home._os_default_home()` from `platform.system()`
plus `os`/`pathlib` only — **no hardcoded drive letters or path separators**.

### 3. `GALD3R_HOME` override — single resolution point

`GALD3R_HOME` overrides the per-OS default. The single function
`gald3r.home.resolve_install_home()` implements the full precedence and is the
ONLY place this is decided:

```
1. explicit override= argument          (tests / embedding callers)
2. portable mode                          (see §4)
3. GALD3R_HOME env var
4. per-OS default                         (§2)
```

### 4. USB-portable variant — detection + relocation

Portable mode is entered when **any** of the following is true:

- the `portable=True` argument is passed,
- the `GALD3R_PORTABLE` env var is truthy (`1`/`true`/`yes`/`on`), or
- a `portable_root` is supplied (arg or `GALD3R_PORTABLE_ROOT` env var).

When portable, the install home **relocates to `<medium-root>/gald3r/`**,
co-located on the medium, with **no writes outside the medium**. The medium root
is resolved as: explicit `portable_root` / `GALD3R_PORTABLE_ROOT` → otherwise the
filesystem anchor of the running engine package (`Path(__file__).anchor`), i.e.
the drive/mount the portable install was launched from. This means a gald3r
copied onto a removable drive and launched from there keeps all of its state on
that same drive without any drive-letter assumption. Portable mode takes
precedence over `GALD3R_HOME` so a portable launch is never silently redirected to
a machine-local default.

### 5. Global `gald3r` on PATH — registration strategy

A small launcher is placed on a PATH directory by an idempotent, dry-run-capable
installer (`.gald3r_sys/scripts/install_global_cli.py`, with a Windows-only
`.ps1` twin):

| OS | Launcher | PATH registration |
|---|---|---|
| Windows | `gald3r.cmd` in `<install-home>\bin` | add `<install-home>\bin` to the **user** PATH (`HKCU\Environment`), idempotently |
| macOS / Linux | `gald3r` shim (chmod +x) in `~/.local/bin` | `~/.local/bin` is a conventional user PATH dir; the installer warns if it is not on PATH |

The launcher prefers `uv run --project <engine> gald3r` (zero global Python
needed) and falls back to `python -m gald3r`. After install, `gald3r --version`
(backed by the existing `--version` action that reports `gald3r.__version__`)
works from any directory. The engine also gains a `gald3r home [--portable]
[--ensure] [--json]` subcommand to inspect/create the resolved home from anywhere.

### 6. Cross-OS path handling is centralized

All OS branching lives in `gald3r.home`; products and install scripts import it
rather than duplicating logic. The install scripts reuse the resolver for their
default launcher directory (engine importable) with a thin pure-stdlib fallback
only for the bootstrap case where the engine is not yet importable.

---

## Consequences

**Positive**
- One documented, testable resolver for the shared home; products stop
  re-deriving OS paths (DRY, g-rl-04).
- The USB-portable story is decided up front and is a first-class branch of the
  same resolver, not a later bolt-on.
- `gald3r` becomes a real global command; onboarding no longer requires `cd` into
  the engine checkout.

**Negative / costs**
- PATH registration cannot be exercised against a live machine inside an
  automated test, so the installer is verified via its `--dry-run` path plus unit
  tests on the pure resolver; live `gald3r --version`-from-anywhere is a
  per-machine manual verification step.
- Windows user-PATH edits require opening a new terminal to take effect; macOS/
  Linux may require adding `~/.local/bin` to the shell profile (the installer
  prints the exact line when needed).

**Neutral**
- The resolver does not create anything; `ensure_install_home()` is the explicit
  side-effecting entry point.
- `VERSION` records the creating engine version for future migration logic; this
  ADR does not define a migration policy (out of scope).
