# Changelog

All notable changes to gald3r are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
gald3r uses [Semantic Versioning](https://semver.org/).

---
## [Unreleased]

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

### Added

### Changed

### Fixed

---
## [3.0.0] - 2026-07-06

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

### Fixed
- **Template mojibake (double-encoded UTF-8) eliminated and guarded (BUG-213).** Repaired
  README.md, CHANGELOG.md, and a `template_verification` RELEASE fixture whose punctuation
  and emoji had been double-encoded ("sloppy-windows-1252") by the retired `.ps1` tooling
  and then byte-faithfully copied into every generated repo. The forge already reads/writes
  UTF-8 explicitly, so the root cause was corrupt source, not the build. The fail-closed
  leak-lint build + publish gate now rejects any mojibake in shipped text (new
  `scan_text_for_mojibake` / `find_mojibake_in_file`; `maintainer/tests/test_mojibake_guard.py`),
  so a corrupted source file can never silently ship again.

### Changed
- **A1-A6 skill/orchestration scripts now run from the compiled `gald3r` engine, not shipped
  Python (T1664).** Every skill, command, rule, and hook that invoked a bundled helper is
  re-pointed to a stable engine verb: worktree state machine -> `gald3r worktree <action>`,
  push gate -> `gald3r push-gate`, housekeeping -> `gald3r housekeep`, WPAC connectivity ->
  `gald3r workspace probe|entitlement|token-status|preflight`, WPAC transport ->
  `gald3r workspace outbox …`, WPAC inbox -> `gald3r workspace inbox migrate|archive`, the
  g-go-go outer loop -> `gald3r autopilot loop`, auto-triage -> `gald3r bug triage`, the
  linking-topology mirror -> `gald3r workspace pull|status`, and org policy -> `gald3r policy
  check|status`. The five shipping hooks (`g-hk-agent-worktree-janitor`, `g-hk-policy-check`,
  `g-hk-pre-commit`, `g-hk-pre-push`, `g-hk-wpac-inbox-check`) resolve the engine through the
  zero-IP `.gald3r_sys/scripts/gald3r_bin.py` resolver and degrade gracefully (no-op) when no
  engine is installed. These skills have no `SKILL.full.md` fallback, so the engine verb is now
  the sole path.

### Removed
- **The absorbed A1-A6 helper scripts no longer ship (T1664).** Deleted from every shipped tree:
  `g-skl-git-commit` `worktree_lib/` + `gald3r_worktree.py` / `gald3r_worktree_janitor.py` /
  `gald3r_session_capture.py` / `gald3r_housekeeping_commit.py` / `gald3r_push_gate.py`;
  `g-skl-workspace` `wpac_client.py` / `wpac_transport.py` / `preflight_touch_set.py`;
  `.gald3r_sys/scripts/ggo_outer_loop.py` + `gald3r_wpac_inbox.py`; `g-skl-auto-triage`
  `calculate_risk.py` / `invoke_triage.py`; `g-skl-linking` `linking_mirror.py`; `g-skl-policy`
  `policy_engine.py` (plus their co-located tests). The `g-skl-workspace` marker scripts and the
  read-only `ggo_status.py` reporter are retained. The deny-by-default shipped-code lint now
  asserts these files' absence.

### Fixed
- **Fresh installs no longer grow a literal `{LOCAL_REPOS}` directory (BUG-209 + BUG-210).**
  The shipped `.gald3r/.identity` default `repos_location={LOCAL_REPOS}` was a dead token: no
  component expanded it and the session-start hook only recognized the `{LOCAL}` sentinel, so
  on first session `g-hk-session-start.py`'s writability probe `mkdir`-ed a literal
  `{LOCAL_REPOS}/` folder in the project root (observed on Windows and on the stock-Linux v3
  install test). Fixed both ends: (1) the identity template now ships `repos_location={LOCAL}`
  and `setup_gald3r_project.py::write_identity()` normalizes any legacy `{LOCAL_REPOS}` to
  `{LOCAL}`; (2) `resolve_vault()` now routes ANY unexpanded `{PLACEHOLDER}` token (and
  `{LOCAL}`) for both `vault_location` and `repos_location` to the local fallback, and
  `_path_writable()` refuses a placeholder path outright — it never `mkdir`s a `{TOKEN}` path
  again. Hook fanned out byte-identical to all 19 copies.
- **Shipped `.gald3r/.identity` now carries the correct version (BUG-211).** The build stamps
  version headers across text files, but `.identity` is a dotfile whose `Path.suffix` is `''`,
  so it never matched its own `TEXT_EXTENSIONS` entry and shipped stale (`gald3r_version=3.0.0`
  while `.gald3r_sys/VERSION` was correct). `gald3r.utils.fs.replace_in_file_tree` now matches
  `TEXT_EXTENSIONS` by full filename as well as suffix, so `.identity` is stamped like any
  other text file (same class BUG-175 fixed for `.gald3r_sys/VERSION`).
- **`install_global_cli.py` install-time message matches the binary-first launcher (BUG-212).**
  The absent-dev-engine status line said `(not found -- launcher uses python -m gald3r)`, which
  contradicted the binary-first launcher it writes (T1645) and triggered a wasted verification
  loop on the Linux v3 install test. It now reads `(no dev engine source -- launcher is
  binary-first: gald3r-agent, then PATH, then python -m gald3r)`.
- **Fresh Linux installs no longer require a `python` symlink (BUG-207 / T1651).** Shipped
  hook trigger configs (Claude `settings.json`, Cursor `hooks.json`, and the gemini / qwen /
  openhands / kiro-cli / goose / copilot / codex / antigravity per-platform equivalents — 155
  command strings across 14 configs) launch their Python hooks with the bare `python` token,
  which does not exist on stock python3-only Linux (Debian 12+, Ubuntu, Fedora, RHEL 9+) —
  every hook silently failed to launch on a fresh Linux install. Fix is **install-time
  interpreter stamping**: templates keep the Windows-safe `python` default (Windows installs
  stay byte-identical in behavior), and the new shipped
  `.gald3r_sys/scripts/stamp_python_interpreter.py` — invoked automatically by
  `setup_gald3r_project.py` after layer copy — rewrites the leading interpreter token of every
  hook `"command"` string to the interpreter that actually resolves on the installing machine
  (`python3`-first on POSIX; idempotent; re-runnable by hand after cloning a project across OS
  families). An inline `python3 X || python X` fallback was rejected by design: `||` conflates
  "interpreter missing" with a legitimate exit-2 BLOCK verdict and double-runs stateful hooks.
  Windsurf needed no stamping (dual `command`/`powershell` keys already ship `python3`/`python`).
  Also fixed under the same bug: `g-hk-graph-update.py` now launches the muninn indexer with
  `sys.executable` instead of a bare-`python` PATH lookup (was silently skipped forever on
  python3-only distros; canonical + all fan-out copies), the `g-skl-medic` doctor tool probe
  falls back to `python3` before warning "python not found", the shipped
  `settings.local.json` permission allowlists carry both `Bash(python ...)` and
  `Bash(python3 ...)` spellings, and the always-on `g-rl-00` shell-probe rule table gains a
  Python-interpreter routing row (`python` on Windows / `python3` on POSIX) so agent-facing
  doc examples resolve per OS without a mass rewrite. 18 new maintainer tests
  (`maintainer/tests/test_python_interpreter_stamp.py`) pin POSIX stamping, the Windows
  no-op, idempotency, Windsurf `powershell`-key immunity, and a coverage guard that fails if
  a future platform overlay ships a bare-python hook config the stamper does not know about.

### Added
- **One-time install nudge at session start (T1649 — prompt, not force).** On a binary-only
  v3 install (T1645: no engine source ships), the session-start hook
  (`g-hk-session-start.py`, canonical + all platform overlay copies) now detects a REAL
  `gald3r_bin.py` resolver miss (`GALD3R_BIN` → PATH → bundled → dev-source order — dev
  checkouts with engine source never trigger) and/or an undetected Gald3r Throne
  (best-effort install-home `cache/throne` probe) and emits ONE soft banner:
  run **`g-install-agent`** / **`g-install-throne`** to unlock the engine-backed
  experience. Strictly non-blocking (banner-only, `continue: true`, every probe failure
  degrades to silence), shown **once per project** — a marker file
  (`.gald3r/.install_nudge_shown`) written with the banner permanently suppresses it, and
  an unwritable marker silences the nudge rather than risk repeating. The banner says
  explicitly that the file-first SKILL.full.md fallback keeps working — this is an unlock
  offer, not an error. Pre-T1642 installs (no shipped resolver) are left alone. 10 new
  maintainer tests (`maintainer/tests/test_install_nudge.py`) incl. an end-to-end
  zero-engine hook run and a 19-copy byte-parity pin.
- **Territory leasing skill family (T1612, D15): `g-skl-territory` — LEASE / RENEW / RELEASE /
  STATUS.** New `g-skl-territory` skill (`.claude/skills/g-skl-territory/`, canonical +
  root-level dev tree) exposes atomic territory leasing over subsystem/path scopes with TTLs,
  building on the existing T631 atomic-claim primitive (SQLite `INSERT OR IGNORE` + expiry
  takeover) and the T632 subsystem-partitioning policy **rather than re-implementing either**.
  `gald3r/db.py` gains a new `territory_leases` table plus `lease_territory` / `renew_territory`
  / `release_territory` / `territory_status` / `sweep_stale_territory_leases` (canonical
  `gald3r_core/project_template/.gald3r_sys/engine` + the root dev-tree mirror, byte-identical
  as required by the engine/canonical parity model). `gald3r/adapters/mcp.py` exposes the same
  operations as `gald3r_territory_lease` / `_renew` / `_release` / `_status` MCP tools. Contention
  is resolved by CODE, never model discretion (g-rl-38): exactly one caller gets `GRANTED`; every
  other caller gets the deterministic loser result `{"status": "HELD", "owner": ..., "reason":
  "held by {owner} until {ts}"}`. Crash-safety mirrors the T642 Redis TTL + sweep model — an
  expired, unrenewed lease is reclaimable inline on the next `LEASE` call, or proactively cleared
  by `sweep_stale_territory_leases`. Lease rows carry the worktree metadata standard already
  used elsewhere (`worktree_path`/`worktree_branch`/`worktree_owner`, g-rl-02) so a lease is
  attributable to a concrete checkout. Tier boundary: the SQLite path above is the free/Pro
  single-coordinator local lease (all tiers, offline-capable); multi-machine leasing is gated
  behind the Redis add-on entitlement (`can_use_redis_coordination`, T642/T641), the same
  boundary the swarm-lock interface uses. The online world_tree pre-check + push half follows
  the T640 pattern but is **not implemented here** — world_tree T640 (`task_claims` PG mirror) is
  still open, so online durability is partial until it lands; the local SQLite half is fully
  functional today. 12 new tests
  (`gald3r_core/project_template/.gald3r_sys/engine/tests/test_db_territory_t1612.py`): exclusive
  lease/loser-result, idempotent re-lease, expired-lease takeover, renew (extend/reject-non-owner/
  unknown-territory), release (+ no-op double-release), status (list/filter/exclude-expired),
  stale-lease sweep, and on-disk persistence across a snapshot rebuild.
- **Policy-as-code guardrail skill + hook wiring (T1611, D12).** New `g-skl-policy` skill
  (`.claude/skills/g-skl-policy/`, mirrored to all 33 shipped platform overlays + `.cursor`)
  loads an org policy bundle — online via `world_tree` (`GET /api/v1/policy/{org_id}/bundle`,
  best-effort 2s-timeout fetch), file (`.gald3r/policy/org_policy.yaml`) offline, or an empty
  default bundle — and exposes a `CHECK` op (`scripts/policy_engine.py`, zero required external
  dependency: uses PyYAML when importable, else a small dependency-free parser). Enforcement is
  **deterministic, by code, never model discretion** (g-rl-38): a new `g-hk-policy-check.py`
  concern hook is registered in `g_hk_core.py`'s canonical `tool-start` chain (T424/T510), so it
  fans out for free to every one of the 14 hook-capable platforms (antigravity, augment, cline,
  codex, copilot, cursor, gemini, goose, kiro-cli, opencode, openhands, qwen, windsurf, plus the
  `.claude`/`.cursor` dev trees) via the existing shared-core dispatcher — a `block` verdict
  returns `permission: deny` + exit code 2, `warn` surfaces `additional_context`, and platforms
  with no hook surface simply never invoke it (graceful no-op, not a special case). The same
  `policy_engine.py` also backs a new pre-commit check (`g-hk-pre-commit.py` section 7) that
  evaluates the staged diff/file list at commit time. **Tier-gated**: org-wide enforcement
  requires both a non-empty `org_id` and a Team/Org/Enterprise `plan_tier` in `.gald3r/.identity`
  (`GALD3R_PLAN_TIER` env override for local testing) — mirrors the T633 paywall-gate pattern
  (deterministic local check + safe default, billing authority server-side). Free/retail
  installs always evaluate against an empty bundle and are never blocked by another org's rules
  (namespacing: `load_bundle` short-circuits before any file/network access when no org tier is
  active) — local-only constraints continue to be served by the existing `g-skl-constraints`.
  14 new tests (`gald3r_core/project_template/.gald3r_sys/engine/tests/test_policy_engine_t1611.py`)
  cover the tier gate, bundle resolution order, CHECK block/warn/allow verdicts, and the hook's
  fail-open behavior on engine/parse errors. BUG-205 filed separately for a pre-existing stale
  `SKILL_INDEX.md` discovered (not fixed inline) while registering the new skill.
- **Explicit per-project coordination on/off toggle (T1621).** `Config.coordination_enabled` (`gald3r-engine/src/gald3r/config.py`) reads a new `.identity` key, `coordination_enabled` (default **on** when absent, matching pre-T1621 behavior; recognizes `true/false`, `1/0`, `yes/no`, `on/off`, case-insensitively, falling back to the default on an unrecognized value rather than raising). `WorkspaceSystem.coordination_enabled()` / `WorkspaceSystem.transport_mode()` (`gald3r-engine/src/gald3r/systems/workspace.py`) expose the same gate to every coordination call-site — `add_item()` now raises the new `CoordinationDisabledError` (a clean, first-class "OFF" state, not a crash) instead of touching `.gald3r/linking/` when the switch is off; reads (`list_items`/`conflicts`/`has_conflicts`) are unaffected so existing coordination state stays visible while participation is off. This is a pre-flight participation gate checked BEFORE any hub/world_tree connectivity — the repo has no hub client yet (WPAC is file-transport-only today), so this lands the on/off switch and its default/documentation ahead of that future wiring. Documented in both `project_template/.gald3r/.identity` shipped templates. Default: **enabled** (opt-out), so a corporate/owner kill-switch sets `coordination_enabled=false`. New tests: `gald3r-engine/tests/test_config.py` (parsing/default) + coordination-toggle cases added to `gald3r-engine/tests/test_workspace.py`.
- **New platform support: Zed (agent panel + ACP host).** Adds the `zed` overlay (`gald3r_core/platforms/zed/`) to `PLATFORM_REGISTRY.yaml` and `PLATFORM_CAPABILITY_MATRIX.md`, plus the authoritative `g-skl-platform-zed` spec skill (`PLATFORM_SPEC.md`/`SKILL.md`/`README.md`, mirrored under `.claude/skills/`, `.cursor/skills/`, and `gald3r_core/project_template/{.claude,.cursor}/skills/`). Zed is a Rust-native, GPU-accelerated code editor whose Agent Panel hosts both its own built-in agent and **External Agents** (Claude Code, Kimi Code, Codex, Copilot, Cursor, OpenCode, Pi Coding Agent) via the open **Agent Client Protocol (ACP)** — making Zed both a platform and a distribution/hosting channel for other vendors' coding agents. Verified 2026-07-03 against https://zed.dev/docs/ai/external-agents, https://zed.dev/docs/ai/agent-settings, https://zed.dev/docs/ai/instructions, https://zed.dev/docs/ai/skills, https://zed.dev/docs/ai/mcp, https://zed.dev/docs/ai/agent-panel, and https://agents.md/: native Agent Skills (`SKILL.md`) in `.agents/skills/` (the same cross-client convention shared with Codex/Amp/Deep Code); native `AGENTS.md` support at both project root and a personal, machine-global scope (`~/.config/zed/AGENTS.md`, `%APPDATA%\Zed\AGENTS.md` on Windows) — with a legacy project-root `.rules` file taking precedence over `AGENTS.md` if both exist; native MCP via `context_servers` in `.zed/settings.json` (also forwarded to ACP-hosted External Agents); External Agents configured via `agent_servers` in the same settings file. No project-scoped agent roster (Zed's own agent is Profile/UI-configured), no dedicated user-authored commands file format (Skills fill that role — only the built-in `/compact` is documented), and no published hooks/lifecycle-event system for hand-authored hooks. Registered `tier3` in the registry; `_platform_capabilities.json` (both copies) and the `platform_registry.py` fallback roster (4 copies) updated to include `.zed`/`zed`.
- **New platform support: Pi (badlogic/pi-mono coding harness).** Adds the `pi` overlay (`gald3r_core/platforms/pi/`) to `PLATFORM_REGISTRY.yaml` and `PLATFORM_CAPABILITY_MATRIX.md`, plus the authoritative `g-skl-platform-pi` spec skill (`PLATFORM_SPEC.md`/`SKILL.md`/`README.md`) inside the overlay's mirrored `.pi/skills/` tree. Pi is a minimal, open-source terminal coding-agent harness (67.5k+ GitHub stars) — "AI agent toolkit: unified LLM API, agent loop, TUI, coding agent CLI". Verified 2026-07-03 against https://pi.dev/docs/latest/{usage,skills,prompt-templates,extensions,settings} and the `coding-agent` README: native Agent Skills (`SKILL.md`, agentskills.io standard) in `.pi/skills/` + `~/.agents/skills/`; native prompt-template slash commands (`.pi/prompts/<name>.md`, invoked `/name`); native lifecycle hooks via TypeScript extensions (`pi.on(event, handler)` in `.pi/extensions/*.ts` — no `hooks.json`); reads `AGENTS.md`/`CLAUDE.md` via genuine **hierarchical** directory-walk concatenation (global `~/.pi/agent/AGENTS.md` + walk-up + cwd — NOT a flat two-scope append like ZCode), plus a distinct `SYSTEM.md`/`APPEND_SYSTEM.md` system-prompt override; **no** project-level `agents/*.md` subagent roster; **no MCP support** at all ("No MCP" per the README, an explicit design choice). Ships a `.pi/extensions/gald3r-hooks.ts` lifecycle-hook bridge that shells out to the same shared canonical `g_hk_core.dispatch()` core already used for the Goose port. Registered `tier3` (weak-but-active) in the registry; `_platform_capabilities.json` and the `platform_registry.py` fallback roster (4 copies) updated to include `.pi`/`pi`.
- **New platform support: ZCode (Z.ai / Zhipu).** Adds the `zcode` overlay (`gald3r_core/platforms/zcode/`) to `PLATFORM_REGISTRY.yaml`, `.gald3r/PLATFORM_STATUS.md`, and `PLATFORM_CAPABILITY_MATRIX.md`, plus the authoritative `g-skl-platform-zcode` spec skill (`PLATFORM_SPEC.md`/`SKILL.md`/`README.md`, mirrored under `.claude/skills/`, `.cursor/skills/`, and `gald3r_core/project_template/{.claude,.cursor}/skills/`). ZCode is Z.ai's free cross-platform Agentic Development Environment built around GLM-5.2 (BYOK-capable). Verified 2026-07-03 against https://zcode.z.ai/en/docs/: native Agent Skills (`SKILL.md`), native slash commands, and native MCP (Settings UI, stdio/HTTP/SSE); reads a two-scope `AGENTS.md` (global `~/.zcode/AGENTS.md` appended by workspace `AGENTS.md` — no hierarchical merge, no `@import`); subagents are Beta and global/user-level only (no project-level roster yet); no published hooks/lifecycle-event system for hand-authored hooks. Registered `tier3` (weak-but-active) in the registry; `_platform_capabilities.json` (both copies) and the `platform_registry.py` fallback roster (4 copies) updated to include `.zcode`/`zcode`.
- **Agent-worktree janitor auto-prunes stale `.claude/worktrees/agent-*` / `.cursor/worktrees/agent-*` background-agent worktrees (T1592).** New `worktree_lib.janitor` module (+ `gald3r_worktree_janitor.py`/`.ps1` CLI in `g-skl-git-commit/scripts/`) scans native Cursor/Claude background-agent worktrees — a different concern from `gald3r_worktree.py -Action Cleanup`, which only ever touches `.gald3r-worktree.json`-owned worktrees. A worktree is prunable once its owning process (resolved from the `git worktree` lock reason's `pid`) is dead and the directory has been idle past a threshold (default 2h); a live owning process always protects it regardless of age. Uncommitted changes are **rescued** (committed to the worktree's own branch) before removal — never force-discarded — and the branch is deleted only when fully merged into `main` (unmerged branches are kept for triage). Process reaping is opt-in (`GALD3R_JANITOR_REAP_PROCESSES=1`) and never touches a process still protecting a live worktree. Wired into both `SessionStart` and `Stop` via the new `g-hk-agent-worktree-janitor` hook (`.claude/settings.json`, `.cursor/hooks.json`), idempotent and logged to `.gald3r/logs/worktree_janitor.log` (counts + rescued-commit shas). Addresses the 2026-06-24 incident (23 stale worktrees + 12 orphaned 8h-old `claude.exe` processes that git-locked worktrees so a plain `git worktree remove --force` hung); 12 new tests against synthetic git repos (`g-skl-git-commit/scripts/tests/test_worktree_janitor.py`).
- **`gald3r.ui.terminal` — reusable rich terminal-output framework for gald3r Python scripts (T1590).** New `gald3r.ui.terminal.Terminal` (+ `gald3r.ui.theme.load_palette`) provides leveled logging (`QUIET`/`INFO`/`DEBUG`/`TRACE` via `Level.resolve()`, CLI flag > `GALD3R_LOG_LEVEL` env > `INFO` default), anti-frozen `stall()` progress cues ("doing X / waiting on Y", elapsed time on exit either way), a TTY-aware `spinner()`/`heartbeat_if_due()` that animates on a real terminal and degrades to plain `flush=True` lines with zero ANSI when piped/redirected, and `header()`/`summary_table()` rendering optionally themed via the owner's PyPI `fstrent_colors`/`fstrent_charts` libraries (new `ui` extra on the engine, `gald3r[ui]`) using the project's active color scheme (`.gald3r/config/active_theme.json` → `.gald3r/themes/` / vault themes / `docs/themes/*.css`, falling back to the `gald3r-dark` reference palette). Both optional libraries are imported behind `try`/`except ImportError` and every call site is additionally wrapped, so a missing or misbehaving optional dependency never crashes a headless/CI run — verified against a real environment where `fstrent_charts` itself fails to import (undeclared transitive `pandas_ta` dependency). `.gald3r_sys/scripts/ggo_outer_loop.py`'s ad-hoc `log()` now delegates to this module (new `--verbosity` flag), with its coordinator-invoke stall point and heartbeat migrated to the new API; 34 new tests (`gald3r_core/project_template/.gald3r_sys/engine/tests/test_ui_terminal_t1590.py`) cover level filtering, isatty simulation, and import-fallback safety.
- **Orphan policy mechanized: hook-parity lint gates the forge build (T1628, WS-A-5, decision D-7).** New `maintainer/src/gald3r_forge/systems/hook_lint.py` runs inside `1_build_repos.py` (`BuildSystem.run` calls `lint_hooks()` on the SOURCE trees — flagship template + every platform overlay, with the same template+overlay union semantics the build produces — BEFORE any repo is wiped; a failing hook surface raises and never reaches the workspace, dry-run included). Policy: **every hook file that ships must be registered, chained, or deleted** — the lint classifies each shipped hook script as registered (named by a trigger config), chained (in the shipped `g_hk_core.py` `CONCERN_CHAIN` with a live dispatcher) / chained-indirect (`INDIRECT_CONCERNS` launch via a registered launcher), entrypoint (`g-hk-on-<event>`), convention-shim, support (`_`-prefixed / core), git-allowlist (`g-hk-pre-commit`/`g-hk-pre-push` + `g-hk-component-tag-check` per its T1624 keep-justification), or an explicit reasoned `MANUAL_DISPATCH` disposition (setup-user, wpac/pcac inbox gates, skill-timing) — anything else is an ORPHAN; hook-named scripts outside a `hooks/` dir are STRAYS; every config-referenced hook script AND every `_hook_md` companion (T1171 contract — the fleet-shared dangling set T1626 deferred here) must resolve, else MISSING. Per-platform report emitted on every build. The pre-fix tree failed on 10 of 17 surfaces; making it pass executed the remaining D-7 dispositions: deleted the 5 never-referenced pre-T510 dot-dir-root hook rosters (226 files at `antigravity/.agents`, `codex/.codex`, `goose/` root, `openhands/.openhands`, `windsurf/.windsurf` — live copies ship in each `<dotdir>/hooks/`); deleted `g-hk-wrkspc-manifest-check` everywhere (zero consumers; superseded by `g-skl-workspace` VALIDATE); restored the dropped `g-hk-agent-worktree-janitor` registrations to the claude overlay `settings.json` + cursor overlay `hooks.json` (the overlays replace the template configs on build and had silently dropped both); wired the gemini `.agent` overlay's stranded logging+vault chain (pre/post-session-trace, graph-update, vault-resolve/migrate/verify/reindex, raw-inbox-watcher) under native `SessionStart`/`AfterAgent` and fanned the canonical `g_hk_core.py` into `.agent/hooks/` so the T1625 chat-logger `INDIRECT_CONCERNS` launch resolves there; shipped the canonical 20-file hook set at `pi/.pi/hooks/` and re-pointed the `gald3r-hooks.ts` bridge to resolve it first (previously referenced a core no pi install path shipped — silent no-op); authored the 8 missing hook.md companions (`g-hk-session-start/-end`, `g-hk-agent-complete`, `g-hk-nightly-learn`, `g-hk-validate-shell`, 3× pre-tool-call guards) and fanned them to the referencing cursor + gemini surfaces. New maintainer regression suite `test_hook_lint.py` (17 tests) pins every policy class, the report format, the build gate (fail → `ValueError` before any write; clean → builds), and that the REAL tree passes — the orphan class of defect now cannot re-enter a build without failing it.
- **Shared O(1) per-project sequence allocator (T1607, closes T599).** New `gald3r.sequence.SequenceAllocator` backs every ID-minting system (tasks, bugs, features, prds, release, and future per-type counters) with a single `.gald3r/state/last_ids.json` counter file instead of a `max(id)` folder scan on every `create()`. Writes are crash-safe (temp file + `fsync` + `os.replace`), and a cross-process advisory file lock (`msvcrt`/`fcntl`) serializes concurrent allocation so two coordinators on one machine never mint the same id. First use of a given counter key transparently migrates by reconciling to the current on-disk max (`max_id_from_ids`) before minting the next id, so upgrading an existing project never collides with ids already in use. `FolderSystem._next_id`/`TaskSystem._next_id` now allocate through this primitive (`_peek_next_id` added for the non-consuming "Next ID" index-hint display); exposed directly as `Gald3r.sequence` for CLI/MCP callers and new counter types. Unit + concurrency tests (multiprocess + threaded) in `gald3r-engine/tests/test_sequence.py`.

### Changed
- **IP leak-stop LANDED: distributed repos ship the compiled engine, never readable source (T1645 — part 2 of T1642, the build-side switch-over).** `Forge.build` now strips the ENTIRE `.gald3r_sys/engine` subtree from every generated repo — `SHIP_EXCLUDED_TEMPLATE_DIRS` grew from `.gald3r_sys/engine/tests` to `.gald3r_sys/engine`, pruning `src/**/*.py` (incl. the `entitlements/` tier logic), `pyproject.toml` (load-bearing: it is the `gald3r_bin.py` resolver's dev-source sentinel — left behind it would falsely trigger the `uv run` source fallback), `uv.lock`, and `provision_engine.*` — and writes a version-stamped stub `engine/README.md` in its place (a positive "intentional binary-only ship" marker pointing at `g-install-agent`, the zero-IP `scripts/gald3r_bin.py` PATH-first resolver — which still ships — and the `SKILL.full.md` fallback). The build-side `_stamp_engine_pyproject` (T572) is retired; `ShipSystem`'s SOURCE-side stamp (T1605) stays, since dev trees keep engine source (only build OUTPUT is stripped). `Forge.publish` gained a fail-closed content gate — `scan_engine_leak()` runs before any commit/push in `_push_one_repo` and REFUSES the repo (loud `engine-leak-blocked` status, excluded from GitHub-release targets) when engine source is present, covering STALE pre-strip workspace clones (a real stale `gald3r_platform_kimi` clone scans at 69 offenders) independent of whether the builder re-ran. `Forge.deploy`'s `.gald3r/` upgrade step now follows the resolver order (compiled `gald3r` on PATH first; `uv run` gated on the pyproject sentinel). Bootstrap re-pointed off the stripped source: `gald3r_bin.py`'s not-found guidance now targets `g-install-agent` (was `install_global_cli.py`, whose launcher shelled `uv run` against source — a dead end post-strip); `install_global_cli.py` launchers exec the compiled `gald3r-agent[.exe]` in the gald3r home `bin/` first (the T1615 drop location), keeping the `uv run` source path only on dev checkouts; `g-install-agent`/`g-install-throne` command docs (`.claude` + `.cursor`) resolve via gald3r_bin.py order and document a zero-engine bootstrap (signed binary + SHA-256 sidecar direct from Gald3r-Labs/gald3r_agent releases); the 4 agents missed by the 7a12631 skill sweep (code-reviewer, marketing, qa-engineer, verifier; ×2 mirrors) now call bare `gald3r …`; `g-skl-setup`'s engine section documents the binary install instead of `provision_engine.py`. Regression net: new `maintainer/tests/test_leak_lint.py` (8 tests: zero engine `.py`/pyproject/uv.lock in flagship + platform output, stub content, resolver + SKILL.full.md ship, dev source untouched, stale-clone detection — reusing the SAME `scan_engine_leak` predicate the publish gate enforces) + 5 publish-gate tests + 2 reworked build tests; maintainer suite 233/233, resolver 7/7. Verified on a REAL `gald3r_platform_kimi` build into a temp workspace: engine dir = README.md only, 0 engine `.py` (was 67), resolver ships, stub stamped v2.4.0. Decision recorded: PATH-first delivery — NO per-repo bundled binary in `.gald3r_sys/bin/` (40 repos × an OS/arch matrix = bloat + version drift; `g-install-agent` delivers the verified binary once per machine). Follow-ups tracked in T1645: `platforms/*` overlay trees still carry stale `uv run --project .gald3r_sys/engine` doc examples (parity-sync scope, T1628/T1631); git-history scrub of the already-public engine source is an owner decision.
- **Kimi Code platform spec + registry rebrand-refreshed to the `kimi-cli` → `kimi-code` rename (2026-07-03).** Moonshot renamed `MoonshotAI/kimi-cli` to `MoonshotAI/kimi-code` (v0.22.2) in the same release that moved the CLI from Python/uv to Node.js — verified against `www.kimi.com/code/docs/en` and its `moonshotai.github.io/kimi-code/en/` mirror (four independent doc-page fetches: skills, hooks, agents, config-files). The project/user config directories renamed with it — `.kimi/` → `.kimi-code/`, `~/.kimi/` → `~/.kimi-code/` (overridable via `KIMI_CODE_HOME`) — and the documented cross-tool Agent-Skill discovery set changed from `.claude/skills/`/`.codex/skills/` to `.agents/skills/` only; `AGENTS.md` remains the instruction-file convention, unchanged. `gald3r_core/platforms/kimi/PLATFORM_SPEC.md` (the T1474 authoring source), its `README.md`, and the shipped `.kimi/kimi_instructions.md`/`.kimi/config.yaml` scaffold now document both conventions with the old `.claude/`/`.codex/` reuse claim marked superseded/unverified. Also fixed a pre-existing drift: `PLATFORM_REGISTRY.yaml`'s `kimi` entry was still `lifecycle: stub` / `support_level: tier3` (a T516 seed value) despite the spec having been fully verified `✅` by T1474 months earlier and `PLATFORM_CAPABILITY_MATRIX.md`/`PLATFORM_COMBINED_READINESS.md` already showing all-native rows — corrected to `lifecycle: active` / `support_level: tier1`. Synced the same refreshed spec content into the four previously-stale `g-skl-platform-kimi/PLATFORM_SPEC.md` mirror copies (`.claude/`, `.cursor/`, and both `gald3r_core/project_template/` equivalents), which were still the original all-❓ T516 stub despite the canonical source being current. No new "Kcode" platform was added — research (8 search variations + direct source fetches, task-required verification) found no distinct product by that name; every signal resolves to this same Kimi Code rebrand.
- **`@g-setup` first-run scaffolding now sets the gald3r-guard bypass scoped to its `.gald3r/` writes (T1591).** New `g-skl-setup` "Step 0.1 — Guard bypass for first-run scaffold writes" instructs setup to set `GALD3R_HOOK_BYPASS=1` (or run under `GALD3R_ACTIVE_AGENT`) only for the first-run scaffold writes, then clear it — so the pre-tool-call gald3r-guard (`g-hk-pre-tool-call-gald3r-guard`, `g-rl-33`) stops false-denying legitimate setup (BUG-179 secondary half) while still blocking unsupervised `.gald3r/` writes once setup completes. Applied to the canonical `project_template` setup skill and parity-synced to all 31 platform copies + the local mirrors.
- **`g-rl-26` now names `gald3r_core/CHANGELOG.md` the canonical changelog for this repo — ending the release-pipeline drift (BUG-185).** The "Where to Update" table used to send framework contributors to the **root** `CHANGELOG.md`, but the release pipeline (`Forge().publish` promotes, `Forge().ship` audits) only ever reads **`gald3r_core/CHANGELOG.md`** — so the promoted `[Unreleased]` kept coming up empty at ship time (observed on 2.2.0). The rule's this-repo row + a new "Canonical changelog for this repo (BUG-185)" note now direct framework-facing entries to `gald3r_core/CHANGELOG.md [Unreleased]`; synced across all 17 `g-rl-26` platform copies + the canonical `project_template` and local mirrors.
- **`@g-platform-scan-docs` wired end-to-end to the T514/T515 freshness consumers (T647).** The command previously only crawled + diffed docs; it now drives the full loop documented in `g-skl-platform-monitor`: `scripts/platform_crawl.py` (T646) crawl-export → `gald3r platform refresh` proposal (dry-run, human review) → **mandatory human-accept gate** → `gald3r platform refresh --apply` (mechanical `last_doc_scan` stamp only — capability cells are never auto-applied) → `gald3r platform status --apply` (STATUS regen) → `check_platform_status.py --generate-matrix` cross-check warning count (verified 0 in a live end-to-end smoke test against the real repo). Authored for both the `.claude/` and `.cursor/` command trees (parity). `g-skl-platform-monitor/SKILL.md`'s `Wiring` section updated to reference the wired command.

### Fixed
- **Vault reindex generator hardened against real-vault pollution, legacy per-subdir `_INDEX.md` indexes unified into the ONE regen, and the personal-vault rerun executed — BOM/mojibake cleared, 99-day staleness ended (T1632, WS-B-9).** Two generator gaps in `g-hk-vault-reindex.py` would have corrupted the WS-B-9 rerun: (1) the note scan excluded only `.obsidian/`, so a real vault's framework infrastructure (`.gald3r_sys/`, `.cursor/`, `.backups/`, `.git/`, ...) — 1,471 files in the owner vault — would have been indexed as notes and littered with generated `index.md` views; the scan (and the stale-view cleanup) now skip every hidden directory below the vault root, counted RELATIVE to the vault root so the default `.gald3r/vault` fallback location still indexes normally. (2) The 16 per-subdir `_INDEX.md` MOC views left behind by the retired `gen_vault_moc.py` script (divergent since 2026-04-08; the generator script no longer exists anywhere in the vault) would have been indexed as `type: moc` notes; `_INDEX.md` is now a reserved index name (reserved-file matching made case-insensitive), marker-carrying copies (`gen_vault_moc` / `auto_generated: true`) are removed on regen — unifying the per-subdir index function into the T1627 per-directory `index.md` views from the single generator — and their presence defeats the debounce so leftovers self-heal on the next Stop; hand-written `_INDEX.md`/`index.md` files are never touched, and hidden dirs are never cleaned (protects the shipped `.gald3r_sys/template_verification` fixture). Fanned out byte-identical (4× `g-hk-vault-reindex.py` + 4× companion `.md`). **Rerun executed on the owner-local vault** (`gald3r_vault`, the plan's flagged owner-run step): `_index.yaml` regenerated — UTF-8 **no BOM** (old file was BOM'd with em-dash mojibake from the retired `.ps1` generator), 1,803 notes (was 831, dated 2026-03-28 — 99 days stale), timestamp current, zero hidden-dir/`_INDEX.md` entries — plus 174 OKF `index.md` views with agreeing note counts (root `Notes in this section: 1803`); all 16 legacy `_INDEX.md` files removed; the four skill-owned operational `research/{articles,platforms,repos,videos}/_index.yaml` state files (recon dedup/refresh trackers with their own schemas, actively consumed by `g-skl-recon-*`) deliberately left untouched — they are URL/ingestion state, not note indexes, and the root regen now carries the note registry for those directories. Live debounce verified in a fresh process; vault working-tree changes left uncommitted for the owner. 6 new tests in `test_vault_chain_wiring.py` (28 total) pin hidden-dir exclusion, dot-rooted-vault indexing, legacy-MOC unification + hand-written survival, debounce defeat/skip, BOM/mojibake replacement, and hidden-dir cleanup immunity.
- **Vault chain + raw-inbox watcher registered — the orphaned hooks that let `_index.yaml` go 96 days stale now fire, and the reindex emits BOTH index artifacts (T1627, WS-A-4, OKF amendment).** The five vault concerns shipped in every install but were registered nowhere. `g_hk_core.py` `CONCERN_CHAIN` now runs `g-hk-vault-resolve` + `g-hk-vault-migrate --if-diverged` on `session-start`, and `g-hk-vault-verify` + `raw-inbox-watcher --hook-mode` + `g-hk-vault-reindex` on `stop` (watcher deliberately BEFORE reindex so routed inbox files land in the same regen); the same five are registered directly in the Claude `settings.json` (`SessionStart`/`Stop`) and Cursor `hooks.json` (`sessionStart`/`stop`) trigger configs (template + platform overlays). `g-hk-vault-migrate` gains the `--if-diverged` gate — it consults `g-hk-vault-resolve`'s `VaultMigrationCandidate` divergence signal and no-ops unless the local vault holds notes while a different shared vault is configured (WS-A-4 AC). `raw-inbox-watcher` gains `--hook-mode` — failures are still moved to `raw/failed/` and flagged with an `error.md` sibling, but the exit code is always 0 so a lifecycle hook can never block the host session. `g-hk-vault-reindex` is **debounced** (skips when both artifacts exist, the recorded note count matches, and no note is newer than `_index.yaml`; `-ForceRun` bypasses) and now emits TWO artifacts from ONE generator: `_index.yaml` (UTF-8 no BOM — unchanged machine source of truth) AND an OKF-style `index.md` per directory holding notes (no frontmatter; `# Section` headings; `* [Title](relative-url) - one-line description` bullets; `# Sections` links child-directory indexes for progressive disclosure, `# Notes` lists the directory's own notes with frontmatter `description:` preferred, root adds `# Recent Updates`), replacing the old wikilink-format root `index.md`; stale generated views are removed marker-guarded (hand-written `index.md` files are never touched) — the format the WS-B-11 vault lint (T1634) consumes and the WS-B-9 personal-vault rerun (T1632) executes. New T1171 companions `g-hk-vault-resolve.md`/`g-hk-vault-reindex.md`/`g-hk-vault-migrate.md`; `g-hk-vault-verify.md` + `raw-inbox-watcher.md` updated to their new registrations. All edits fanned out byte-identical (15× `g_hk_core.py`, 9× each vault hook + companion). New maintainer regression suite `test_vault_chain_wiring.py` (22 tests) pins fan-out byte-identity, chain + trigger-config registration (incl. watcher-before-reindex ordering), dual-artifact emission with agreeing note counts, OKF bullet/heading format, debounce skip→edit→regen, marker-guarded stale-view cleanup, the divergence gate both ways, and hook-mode exit codes.
- **Gemini hard-broken hook config fixed — `.agent/hooks.json` now invokes scripts that actually ship, under Gemini's native event casing (T1626, WS-A-3).** The 2026-07-03 workspace rebuild shipped a gemini repo whose `platforms/gemini/.agent/hooks.json` invoked `python .claude/hooks/g-hk-*.py` — a directory that does not exist in the gemini repo — under Claude-format event keys (`Stop`, `PreToolUse`) the gemini product never emits. All 11 registered `command`s and every `_hook_md` companion reference are re-pointed at `.agent/hooks/` (each script verified shipping in the overlay), and the event keys are translated to Gemini CLI's native casing via the inverse of `g_hk_core.PLATFORM_EVENT_MAP['gemini']` (`Stop`→`AfterAgent`, `PreToolUse`→`BeforeTool`; `SessionStart` is native to both). The stale `_doc` block — which prescribed Claude event names and claimed Claude Code reads the file — is rewritten to document gemini's 11 native events (per `g-skl-platform-gemini/PLATFORM_SPEC.md`), restate the T510 finding that gemini's REAL native surface is `.gemini/settings.json` (already correct; untouched), and record that the `BeforeTool` matchers retain the Claude/Cursor-era tool-name unions pending the WS-A-5 hook-parity lint disposition and that reconciling/removing the `.agent/` overlay stays tracked separately (T510 Status History). Smoke-fired all 11 registered hooks on a simulated gemini install (empty `{}` stdin payload): exit 0 each — guards answer `{"permission":"allow"}`, stop-chain hooks emit their normal continue payloads. New maintainer regression suite `test_gemini_hook_config.py` (19 tests) pins JSON parse, zero Claude dot-dir references, native-only event keys, and every-registered-script-ships for BOTH `.agent/hooks.json` and `.gemini/settings.json`, plus per-hook smoke-fire of the `.agent/hooks.json` chain; the fleet-shared dangling `_hook_md` companions (the same set dangles in the cursor reference overlay) are deliberately left to the WS-A-5 lint (T1628) for a fleet-wide disposition.
- **BUG-133 regression fixed properly: `g-hk-agent-complete` resolves its chat logger through the shared core/platform map, never a hardcoded platform filename (T1625, WS-A-2).** The stop-chain launcher used to reference `g-hk-cursor-chat-logger.py` by literal filename — the wrong file in `.claude` installs, silently no-opping the chat-log step. `g_hk_core.py` gains `PLATFORM_INSTALL_DIRS` (install dot-directory → `PLATFORM_EVENT_MAP` platform key, with `GALD3R_HOOK_PLATFORM` env override and goose/antigravity `.agents` disambiguation), `detect_platform()`, and `resolve_indirect_concerns()` (resolves a launcher's `INDIRECT_CONCERNS` scripts next to the install, `.py`-preferred — the same machine-readable map the WS-A-5 hook-parity lint consumes; `_locate()` refactored onto the shared `_resolve_script()` helper). `g-hk-agent-complete.py` now imports the core fail-soft, resolves the logger via that map, passes the **detected** platform as `--platform` (chat logs on Claude installs were previously mislabeled `cursor` in both filename slug and header), and emits a visible `WARNING: chat logger unresolved…` diag line when nothing ships instead of silently no-opping; flat legacy overlay layouts without a sibling core fall back to a generic `g-hk-*chat-logger.py` probe (no platform literals). Both files fanned out byte-identical across `gald3r_core` (15× core, 21× launcher). New maintainer regression suite `test_agent_complete_logger_resolution.py` (8 tests) pins no-filename-literals, core resolution, end-to-end correct-`--platform` invocation on simulated claude AND cursor installs, and the missing-logger WARNING — the WS-A-2 assertions the T1629 (WS-A-6) per-platform smoke harness will fold in.
- **Logging chain wired into the canonical hook core — chat log, session trace, CRASH record, and graph refresh now actually fire (T1624, WS-A-1).** The T424/T510/T512 overhaul stranded the shipped logging concerns (registered nowhere, fired never). `g_hk_core.py` `CONCERN_CHAIN` now runs `g-hk-pre-session-trace` on `session-start`, and `g-hk-post-session-trace` + `g-hk-crash-record` (explicit `--component-type hook --component-name stop-chain` declaration; still zero-overhead unless `GALD3R_CRASH_STATS` is set) + `g-hk-graph-update` (new 60s-per-indexer cap so a wedged muninn indexer can't stall a session) on `stop`, with `g-hk-post-session-trace --finalize` closing the trace marker on `session-end`; the same concerns are registered directly in the Claude `settings.json` (`SessionStart`/`Stop`) and Cursor `hooks.json` (`sessionStart`/`stop`) trigger configs (template + platform overlays). The chat logger stays launched by `g-hk-agent-complete` (transcript discovery lives there; direct registration would double-write every log) and that indirect wiring is now machine-readable via the new `g_hk_core.INDIRECT_CONCERNS` map for the WS-A-5 hook-parity lint. The gald3r-internal `pre_session`/`post_session` event names are **retired** (decision D-8): session traces ride the canonical events, and all hook code, trigger configs, `g-create-hook` docs, and PLATFORM_SPECs now say so. D-7 orphan dispositions recorded: `g-hk-setup-user` KEPT (one-time interactive identity CLI, engine-test-covered, never event-wired) and `g-hk-component-tag-check` KEPT (only g-rl-38 tagging enforcement; `gald3r validate` covers task/bug files, not component tags) — each with a written keep-justification in its companion `hook.md` (`g-hk-setup-user.md` + `g-hk-graph-update.md` companions newly added). Core + concern edits fanned out byte-identical to all 15 `g_hk_core.py` and 9 session-trace copies; end-to-end simulated fire (session-start → stop ×2 → session-end) produced the chat log, cumulative-elapsed lifecycle lines, CRASH activation records (payload session id now bridged to the engine recorder via `GALD3R_SESSION_ID`), and marker cleanup. New maintainer regression suite `test_logging_chain_wiring.py` (15 tests) pins the wiring, fan-out byte-identity, and retired-name absence until the WS-A-5 lint lands.
- **Ship pre-flight `[Unreleased]` audit hardened + proven consistent with publish (BUG-185).** `ShipSystem._audit_unreleased_nonempty` already read `gald3r_core/CHANGELOG.md` — the same file `PublishSystem._finalize_release_notes`/`_release_notes_content` promote and read — but nothing pinned that invariant. Added an explicit BUG-185 invariant docstring and two regression tests: one asserts the ship audit and publish derive the identical `core_root/CHANGELOG.md` path, the other proves the audit still refuses an empty `gald3r_core` `[Unreleased]` even when a fully-populated ROOT `CHANGELOG.md` is present (the exact drift scenario) — so misplaced root entries can never smuggle an empty release past the guard. Maintainer ship suite 40/40.

### Removed
- **PS1-KILL: deleted the 20 already-twinned `.ps1` stragglers in the `zed` platform overlay (BUG-203, epic T667).** The T1601 port closed the un-twinned `.ps1` tail; these 20 files under `gald3r_core/platforms/zed/.agents/skills/*/scripts/` were the last `.ps1` remaining anywhere in `gald3r_core`, each already carrying a byte-present, functionally-equivalent `.py` twin. Verified before deletion: every `.py` twin is real (non-stub) code, and the canonical `project_template/.claude/skills/` tree already ships `.py`-only for all 20 — the `zed` overlay was simply the last straggler the earlier ports missed (T1601 scoped to un-twinned files only). No executable wiring referenced these `.ps1`: Zed exposes no hooks/commands surface, and a repo-wide scan found zero callers — the remaining `.ps1` mentions are (a) provenance docstrings inside the `.py` ports ("Python port of X.ps1"), (b) SKILL.md prose that is byte-identical parity content across the canonical + every overlay (a separate, pre-existing repo-wide doc-debt, not zed-specific), and (c) `.gald3r_sys/skills/` test-fixture assertions about the *installed-runtime* tree, which this overlay-source deletion does not touch. `gald3r_core`'s tracked `.ps1` count is now **0** (plus one untouched third-party `.venv/Scripts/activate.ps1`).
- **Retired the 2 documented Windows user-entry `.ps1` launchers (T1599, epic T667).** `setup_gald3r_project.ps1` (root) and `.gald3r_sys/scripts/install_git_hooks.ps1` were the last 2 `.ps1` in `gald3r_core` kept deliberately as documented install entry points (T1598); both are now confirmed removed from the source tree (their `.py`/`.bat` twins were already the functional implementation per T676/T1586 — verified end-to-end: `setup_gald3r_project.py --target-path ... --platform ...` installs the full template + identity + attempts git-hooks install, and `install_git_hooks.py` / `--uninstall` correctly toggle `core.hooksPath`). Doc coordination completed so no reference to the retired `.ps1` remains: `gald3r_core/README.md` Option 2 now shows `setup_gald3r_project.bat -TargetPath ...` (Windows) and `python setup_gald3r_project.py --target-path ...` (macOS/Linux/any); `gald3r_core/project_template/WORKFLOW.md` (+ its `.gald3r_sys/install/project_root/` mirror) Session Start now runs `python setup_gald3r_project.py --platform auto`; `gald3r_core/PLATFORM_SUPPORT.html` points at `setup_gald3r_project.bat`/`python setup_gald3r_project.py`; the `.githooks/pre-commit` install comment (`gald3r_core/project_template/.gald3r_sys/install/project_root/.githooks/pre-commit`) now reads `scripts/install_git_hooks.py`. `scan_redundant_ps1(gald3r_core)` no longer reports either launcher (BUG-203 filed separately for 20 unrelated `.ps1` shipped by the `zed` platform overlay — pre-existing PS1-KILL straggler, out of this task's scope).
- **PS1-KILL: 16 unique un-twinned `.ps1` files ported to `.py` (T1601, epic T667).** Closes the final `gald3r_core` PS1-KILL tail. `g-hk-pcac-inbox-check.ps1` -> `.py`, propagated to all 7 platform overlays (antigravity, codex, cursor, gemini, goose, openhands, windsurf); stray `settings.local.json` permission-allowlist entries repointed. 5 Augment platform session hooks ported to `.cmd` shims (not `.ps1` — Augment's hook runner schema-requires a script-file extension and rejects a bare `python x.py` command; `.cmd` retires the `pwsh`/`ExecutionPolicy` dependency the old shims carried) invoking the existing canonical `g-hk-on-<event>.py` entrypoints; `settings.json` + `hooks/README.md` updated. 5 kiro-cli session hooks retired outright — `gald3r.json`'s `command` field now invokes `python .kiro/hooks/g-hk-on-<event>.py` directly (no shim needed at all, since kiro-cli's agent-JSON `command` accepts an arbitrary command string); `hooks-impl/` kept only for historical documentation. `provision_engine.ps1` + `provision_engine.sh` merged into one cross-platform `provision_engine.py` (stdlib-only; installs `uv` per-OS, then provisions/verifies the bundled engine) — bootstrap-ordering-safe since it's invoked by the already-Python `setup_gald3r_project.py`; 36 `g-skl-setup/SKILL.md` platform mirrors + the installer's `provision_engine()` updated. `update_plugin.ps1` retired in favor of the existing first-class `gald3r plugin update` engine CLI (`PluginSystem.update`, T663) — narrower scope than the old script (single-plugin, local-source only; no bulk remote-registry loop, CHANGELOG excerpt, or on-disk backup/rollback, matching how `INSTALL`/`REMOVE`/`LIST`/`NEW`/`CHECK_COMPAT` were already engine-only); `g-plugin-update.md` (both IDE trees) and `g-skl-plugins/SKILL.md` (3 mirrors) rewritten to the real CLI contract. `_install_helper.ps1` ported to an importable `_install_helper.py` module (same platform-capability-driven rules/skills install/remove functions) for the skill-pack installer architecture; skill-pack command docs + README updated from `install.ps1` to `install.py`. 2 `g-go-go` test fixtures (`test_ggo_outer_loop_t630`, `test_ggo_scheduled_reset_t635`) ported to pytest-runnable `.py` (3-way mirrored: `.claude`, `.cursor`, `platforms/zed`) — T630 passes cleanly against `ggo_outer_loop.py`; T635 exposes a real pre-existing gap in `g-hk-ggo-stop-detect.py` (see BUG-199) rather than being neutered to pass. `gald3r_core`'s `.ps1` count: 46 -> 20 (all 20 remaining already have confirmed `.py` twins in the `platforms/zed/` overlay — out of this task's un-twinned scope, follow-up spawned separately) + 1 third-party `.venv/Scripts/activate.ps1` (vendor file, untouched). New bugs filed for pre-existing gaps discovered during the port: BUG-199 (missing `scheduled_context_reset` re-invoke case), BUG-200 (stale plugin-ops doc), BUG-201 (stale test-manifest paths), BUG-202 (platform-overlay trees stuck on pre-PCAC->WPAC-rename content).
- **PS1-KILL: removed the last `.py`-first/`.ps1`-fallback runtime-resilience branches now that the `.ps1`-only-install EOL boundary has been declared (T1600, epic T667).** These branches (added by T676/T1598) let a legacy `.ps1`-only project keep working against a newer `.py`-shipping `gald3r_core` mid-migration; with the EOL boundary now declared (directive: replace all `.ps1` with Python), they are dead code in every current install (`gald3r_core` has shipped no `.ps1` twins for any of these siblings since T1598/T1601) and are removed, keeping the `.py` path only. `g-hk-session-start.py`'s `_run_script_pair`/`_run_sibling` (used for the `setup_gald3r_project` bootstrap call, the TASKS.md archive-gate check, and the WPAC inbox-check sibling) drop the `.ps1` branch and the `.ps1`-invocation helper is now reserved solely for running a user-authored HEARTBEAT watchdog script that happens to be `.ps1` (an arbitrary user script, not a gald3r-shipped twin — untouched). `g-hk-vault-migrate.py`'s `load_resolve_context()`/`run_reindex()` now import/invoke the `g-hk-vault-resolve.py`/`g-hk-vault-reindex.py` siblings directly instead of dot-sourcing a `.ps1` via PowerShell and parsing its JSON export. `gald3r_release.py`'s `_run_repo_semver()` (maintainer-only Track-B release tool) drops the `pwsh`-invoked `gald3r_semver.ps1` branch. `gald3r medic heal`'s `run_helper_script()`/`heal_c023()` drop the `.ps1`-via-pwsh branch for the `backfill_release_files` delegate. All four files' "prefer .py, fall back to .ps1" docstrings updated to `.py`-only; mechanically propagated byte-identical to all 110 tracked copies (`.claude`/`.cursor` mirrors + every `platforms/*` overlay). Engine suite 451/451, maintainer suite 220/220; `1_build_repos.py --what-if` dry-run still produces the full repo set.

---
## [2.4.0] - 2026-06-27

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

### Added
- **`@g-install-agent` / `@g-install-throne` IDE commands (T1617).** Discoverable command wrappers (shipped to every platform that has a `commands/` surface) that invoke the `gald3r install agent|throne` engine verb for the user — dry-run first, then real install, passing through `--release`, `--from-source`, and `--require-verification`. They do not reimplement install logic; they are the IDE-facing entry point for the consumer install path added in T1615.
- **`gald3r install agent|throne` now downloads the precompiled apps from public GitHub Releases (T1615).** The new default install method `github-release` fetches the per-OS binary/installer from `Gald3r-Labs/gald3r_agent` / `Gald3r-Labs/gald3r_throne` (latest, or `--release vX.Y.Z`), verifies integrity before installing (agent: SHA-256 `.sha256` sidecar; throne: minisign `.sig`, Throne updater key `F110B9BD6FF00BA2` -- missing/tampered signatures fail loud), and records the installed version in the install home. `--from-source` keeps the old `uv sync` (agent) / local Tauri-bundle (throne) developer path; `--dry-run` previews; network / missing-asset / 404 failures degrade to a clear message (never a crash or fake-success). Supersedes T571 (the install-verb block is removed here). macOS deferred ("coming soon").

### Changed

### Fixed
- **`gald3r install agent` no longer fails open on integrity (BUG-198).** Two gaps closed: (1) the published Agent `v0.1.0` release now carries `.sha256` sidecars so the verify step actually engages (a real SHA-256 match, not "unsigned-experimental"); future releases get sidecars automatically via the `agent-binary-build.yml` workflow. (2) A new fail-closed flag **`--require-verification`** makes a missing/mismatched checksum (agent `.sha256`) or signature (throne `.sig`) **abort** the install instead of proceeding unsigned — it also overrides `--allow-unsigned`. The default behaviour is unchanged (warn + proceed = experimental) for backward compatibility.
- **`ship` now stamps the source engine `pyproject.toml` version (T1605).** The version-cut
  step (`3_ship` → `Forge().ship` → `ShipSystem._bump_version`) writes the target version into
  `gald3r_core/project_template/.gald3r_sys/engine/pyproject.toml`'s `[project].version` line
  atomically with the `gald3r_core/VERSION` bump (new `ShipSystem._stamp_engine_pyproject`,
  mirroring `BuildSystem._stamp_engine_pyproject`'s targeted `count=1` TOML regex). The build's
  version-patterns never matched a TOML `version = "X.Y.Z"` line, so the source engine pyproject
  drifted every release and `5_release_repos.py`'s T572 pre-flight guard
  (`_assert_engine_version_synced`) blocked `5_release` until a hand-edit. A fresh `3_ship` →
  `5_release` now passes the guard with zero manual intervention. Dry-run writes nothing; a
  missing pyproject is a silent no-op. +6 tests (`TestEnginePyprojectStamp`). NOTE:
  `maintainer/uv.lock` also embeds the editable engine version; a deterministic re-lock needs the
  `uv` toolchain and is left as a follow-up — the T572 guard checks the pyproject, not the lock.

---
## [2.3.0] - 2026-06-25

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

> **Headline: the PS1-KILL release.** Almost all PowerShell has been removed from the gald3r
> framework — the hook, skill-script, task-pipeline, release, and vault surfaces are now Python,
> and ~1,065 redundant `.ps1` were pruned from the shipped source.

### Added
- **Build-time source-hygiene guard against shipping redundant `.ps1` (T1596 / BUG-191).** The
  maintainer build (`1_build_repos.py` → `Forge().build.run()`) now calls `scan_redundant_ps1()`
  to WARN (`REDUNDANT_PS1`) on any `.ps1` in `gald3r_core` that has a co-located `.py` twin (the
  C-NO-PS1 redundancy that previously shipped into every overlay), with an opt-in
  `--prune-redundant-ps1` to remove them from source. Report-only by default, honors `--what-if`,
  and is maintainer-source-only — it never touches a user project or the build-output workspace.
  +4 tests.

### Changed
- **PS1-KILL migration wave — the gald3r framework is now Python-first (epic T667).** Ported the
  PowerShell surface to Python across the framework: task-pipeline scripts (T670), hook families
  (T671–T674), release scripts (T675), vault/memory/learn scripts (T676), and the remaining skill
  scripts (T677). Replacements are `.py`-first with a `.ps1` runtime fallback retained for legacy
  `.ps1`-only installs (removal of those fallbacks tracked in T1600), and reconfigure stdout to
  UTF-8 at startup to kill the encoding footguns that motivated the epic.
- **Canonical bare-number task IDs in `TASKS.md`.** Intake now reads `T?`-prefixed inbox drafts but
  writes canonical bare-number IDs, removing the `T`-prefix drift that caused ID-collision edge
  cases.

### Removed
- **Pruned ~1,065 redundant `.ps1` from `gald3r_core` (T1597 + T1598, epic T667).** Acting on the
  T1596 guard finding (1067 `.ps1` carrying a `.py` twin): removed **948** genuinely dead twins
  (T1597), then **117** more whose callers were already `.py`-first runtime fallbacks (T1598),
  after repointing **195** agent-facing docs (SKILL/command files) from `X.ps1` to `python X.py`.
  The build guard now reports only **2** remaining redundant `.ps1` — both documented Windows
  user-entry launchers (`setup_gald3r_project.ps1`, `install_git_hooks.ps1`) intentionally kept
  pending a doc-coordinated retirement (T1599). The 24 genuinely un-ported `.ps1` (16 unique —
  augment/kiro-cli/pcac platform hooks + engine/install helpers + g-go test fixtures) are tracked
  in T1601.

### Fixed

---
## [2.2.0] - 2026-06-24

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

### Added
- **`DeploySystem` — the deploy pipeline step is now Python (T683, PS1-KILL epic T667).** Ported the last numbered PowerShell pipeline script, `custom_scripts/2_deploy_to_workspace.ps1`, to `maintainer/src/gald3r_forge/systems/deploy.py` (`Forge().deploy`) behind a thin `custom_scripts/2_deploy_to_workspace.py` wrapper. Faithful parity with the PS1: backs up + replaces the framework-owned folders (`.claude`/`.cursor`/`.gald3r_sys`, each moved to `<dir>_bk_<stamp>/` first), then upgrades `.gald3r/` by invoking the **target repo's own** engine (`uv run --project <repo>/.gald3r_sys/engine gald3r update --target <repo> --apply`, `python -m gald3r` fallback) so user task/bug/plan/vault data is preserved, never wiped. Same three modes — dry-run (default, write-nothing plan), `--apply`, and `--rollback YYYYMMDD_HHMMSS` — plus multi-target via `--repo` and/or `--workspace-manifest`, `--source` override, and `--skip-gald3r-upgrade`. Dry-run is a hard write-guard (mutating helpers assert non-dry). 28 new tests (`maintainer/tests/test_deploy.py`); maintainer suite 203/203 green. Verified a real `build → deploy --dry-run` cycle against the live repo.

### Changed
- **`@g-go-go` conductor now halts on coordinator failure instead of grinding the budget (circuit breakers).** A run hit a Claude monthly spend cap mid-run (2026-06-24): every subsequent `claude -p` coordinator failed instantly (`exit 1`, spend-limit message) but `ggo_outer_loop.py` kept spawning them, burning ~296 no-op iterations to `budget=0` — and the final state said only "budget exhausted," hiding the real cause. Two guards added: **(1) fatal-output detection** — the coordinator's streamed output is scanned for account-level sentinels (`FATAL_OUTPUT_SENTINELS`: monthly spend limit, credit balance too low, invalid api key, authentication error, unauthorized) and the run stops *immediately* with `authorized_hard_stop = "coordinator fatal signal: '<sentinel>'"` (retrying these always fails identically); **(2) a consecutive-failure circuit breaker** — `--max-consecutive-failures` (default 3) stops the run after N back-to-back non-zero coordinator exits. The coordinator's stdin write is now wrapped against `BrokenPipeError` so an instant-exit coordinator can't crash the conductor. Both paths record *why* in the marker so the stop reason is never hidden. Verified end-to-end (fatal sentinel stops at iter 0; breaker stops at the configured count) instead of running the full budget.
- **`@g-go-go` stateless conductor now streams live progress to the terminal/log.** `ggo_outer_loop.py` previously let the spawned `claude -p` coordinator's output buffer and inherited stdout, so a launch that redirects to `.gald3r/logs/ggo_outer_loop_stdout.log` only updated *once per finished iteration* — a run looked dead mid-task even while working hard. The coordinator subprocess is now spawned line-buffered (`Popen(..., bufsize=1, stderr=STDOUT)`) and its output is re-emitted line-by-line with `flush=True`, and every outer-loop event goes through a new timestamped `log()` helper (`[outer-loop <ts>] …`) including a per-iteration `iter advanced -> N / budget M (marker stamped …)` pulse. `Get-Content .gald3r/logs/ggo_outer_loop_stdout.log -Wait` now shows progress as it happens. (First slice of the queued live-status-indicator feature.)
- **Maintainer release-pipeline scripts renumbered by run order (T667/T683).** `custom_scripts/` scripts now carry numeric run-order prefixes so the sequence is self-documenting: `1_build_repos.py` → `2_deploy_to_workspace.py` → `3_ship_repos.py` → `4_push_repos.py` → `5_release_repos.py`. The `@g-gald3r-build/ship/publish/release` command docs, `paths.py`, `gald3r_templates/CLAUDE.md`, and the `parity-pipeline` subsystem registry were updated to the new paths; test scripts stay unnumbered. A rewritten `custom_scripts/README.md` documents the numbered pipeline, the ship-before-build version-cut nuance, and the ship-vs-publish "version number vs release docs" split.

### Removed
- **Deprecated PowerShell pipeline twins deleted (T667/T683).** `custom_scripts/build_repos.ps1`, `custom_scripts/push_repos.ps1`, and `custom_scripts/2_deploy_to_workspace.ps1` removed — their Python replacements (`1_build_repos.py`, `4_push_repos.py`, `2_deploy_to_workspace.py`) are at full parity (build `.py` is a superset adding `--workers`; push `.py` is 1:1 on all 10 flags; deploy `.py` mirrors all PS1 flags + modes), each delegating to `Forge().build` / `Forge().publish` / `Forge().deploy`. The only remaining `.ps1` in `custom_scripts/` is the unnumbered `test_full_scenario.ps1` (port tracked in T683).

### Fixed
- **Publish no longer ships the unfilled `NEXT_RELEASE` template as the GitHub release body (BUG-178).** `PublishSystem._release_notes_content` returned the archived `releases/RELEASE_v{version}.md` unconditionally, but the publish step archives `NEXT_RELEASE.md` even when nobody filled it in — so the empty promo skeleton (`_(One punchy line…)_`, "version number assigned at publish time") shipped as the release notes on 2.1.1 and 2.1.2. A new `_is_placeholder_notes()` guard detects the template sentinels and falls back to the (always-populated) CHANGELOG section. +1 publish test; maintainer publish suite 48/48. The live 2.1.1/2.1.2 GitHub releases were re-edited with proper notes from `RELEASE_v2.1.2.md`.

---
## [2.1.2] - 2026-06-23

### Added
- **`gald3r upgrade --deprecate-removed` opt-in flag (BUG-176).** Re-enables the legacy
  removed-framework cleanup (archiving framework files dropped by the target as
  `*_deprecated_<date>`). Safe ONLY with an explicit `--from-version`/`--from-dir` template
  baseline. Default is OFF.
- **Comprehensive pre-flight safety backup on `gald3r upgrade --apply` (BUG-176).** Before
  any change, `UpgradeSystem.backup_full()` zips every present framework tree (`.gald3r`,
  `.gald3r_sys`, `.claude`, `.cursor`, `.agent`, `.codex`, `.opencode`) to
  `<root>/<name>_<UTC timestamp>.zip` and ensures the archives are gitignored — so a user's
  custom code anywhere in those trees survives even a downstream wholesale-replace.

### Changed
- **`gald3r upgrade` no longer auto-deprecates by default (BUG-176, breaking-safe).** The
  migration plan now only ADDs new framework files and MERGEs format changes; it never
  archives a live file unless `--deprecate-removed` is explicitly passed. Every other file
  (user specs, tracking notes, coordination ledgers, loose top-level docs) is left untouched.

### Fixed
- **`gald3r --version` + `.gald3r_sys/VERSION` no longer report stale versions (BUG-175).**
  `gald3r/__init__.py` hardcoded `__version__ = "0.1.0"` (the build stamped `pyproject.toml`
  but never `__init__.py`), so `gald3r --version` printed `0.1.0` regardless of release; and
  no `version_patterns()` regex matched the plain `.gald3r_sys/VERSION` marker, so it stayed
  stale (observed `2.0.0` after the 2.1.1 deploy). Now `__version__` derives from installed
  package metadata (`importlib.metadata`, with a `.gald3r_sys/VERSION` → sentinel fallback for
  raw checkouts) — self-correcting, no stamping needed — and the build's
  `_stamp_gald3r_sys_version` advances `.gald3r_sys/VERSION` in every generated repo. +2 build
  tests; maintainer build suite 17/17; engine suite 476/476. Live proof: `gald3r --version`
  now reports the real version.
- **CRITICAL: `gald3r update` archived all user `.gald3r/` content as obsolete (BUG-176).**
  `UpgradeSystem.plan()` computed DEPRECATE as `live_files − target_template_files` guarded
  only by an incomplete user-data denylist. Since `gald3r update` runs with no
  `--from-version` (the `from` source defaults to the *live* project, not an old template
  baseline), every user-authored file looked obsolete — observed live during the 2.1.1
  deploy, which renamed ~4,250 files `*_deprecated_<date>` (incl. all `SPEC-*`,
  `IDEA_BOARD.md`, `workspace/`, `PLATFORM_*`, `linking/sent_orders/`). Without a backup this
  is catastrophic for a live user. Deprecation is now opt-in (see Changed/Added). +5 engine
  tests (no-deprecate default, opt-in path, `backup_full`); 24/24 upgrade + 476/476 full
  engine suite green. Live proof: the same operation now reports `DEPRECATE=0`.

---
## [2.1.1] - 2026-06-23

_Pending release notes accumulate here as tasks and bugs are completed. At publish time this
section is renamed to [X.Y.Z] - YYYY-MM-DD and a fresh [Unreleased] block is opened._

### Added
- **Plugin lifecycle ops in the engine (T663, epic T541).** `gald3r plugin install|remove|list|new|check-compat|update` CLI + `gald3r_plugin_*` MCP tools, backed by `gald3r.systems.plugins.PluginSystem` (owns the gald3r-plugin.yaml manifest schema, installed.yaml ledger, registry config, compat floor, D6 conflict-abort, `plugin_source:` provenance). Reimplements the designed-but-never-ported ops in Python (retires the PowerShell scripts per BUG-128/129/130). 21 tests; full engine suite 466 green. The single integration point for the T541 children (T664 editor / T665 marketplace backend / T666 UI).
- **Vault knowledge API tools (T609)** — `gald3r_vault_note_get` (note as structured JSON: frontmatter + body), `gald3r_vault_backlinks` (notes that `[[wikilink]]`-reference a note), and `gald3r_vault_context` (token-budgeted, newest-first vault context block — the `memory_context` pattern, vault-scoped). Engine `VaultSystem.note_get` / `backlinks` / `context` + the matching MCP tools. Offline/keyword (semantic search = T618). Completes the T609 vault API (search + ingest already shipped). 4 tests; canonical engine copy.
- **`gald3r vault location` CLI selector + layered resolution (T532).** Resolve/select the vault location (default user vault / workspace / project / create-new) with precedence session/project -> workspace -> default user home (T530); persists the choice to `.gald3r/.identity` (`vault_location`) via secret-stripping write_identity_file. New engine resolvers `resolve_vault_location_layered` / `resolve_vault_choice` / `persist_vault_location` (back-compat 2-layer resolver preserved). CLI `gald3r vault location [--select {default|workspace|project|create_new} [--path]]`. 23 tests; canonical + B-mirror parity. Throne selector UI is follow-up T650.
- **`@g-pt` workflow-profile CLI propagated to all IDE platform targets** (T417) — the
  `g-pt` command (`list`/`use`/`copy`/`edit`/`validate` for `.gald3r/config/workflow_profiles/*.yaml`)
  and its `gald3r project-type` skill script are now fanned out across the `gald3r_core/platforms/` source trees:
  `gald3r project-type` lands in every platform's `g-skl-project-types/scripts/` dir (31 targets, alongside the
  existing `gald3r project-type resolve`), and the `g-pt.md` command doc lands in every platform command/workflow
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
  hook-wiring system check (`gald3r selftest check_hook_wiring`) now reads BOTH surfaces and
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
- **Build hygiene: generated repos no longer ship Python build artifacts** (T507) — the build's copy primitive (`fs.copy_tree`) now always prunes `.venv`, `__pycache__`, and `.pytest_cache`, and the engine's dev-only pytest suite (`.gald3r_sys/engine/tests`) is excluded from every shipped `project_template` (runtime test fixtures under `g-skl-test` are preserved). A stray `.venv` had been adding ~52 MB of junk to each generated repo. Removed the duplicate `platforms/vibe` (it duplicated Mistral's `.vibe` config surface; Mistral retains it).

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
  event-first entrypoints `g-hk-on-<event>.py` delegate to `g_hk_core.dispatch(<event>)` — behavior
  is authored once and every platform's trigger layer calls the same core. Wired the first canonical
  events additively into **Cursor** (`postToolUse`, `beforeSubmitPrompt`) and **Claude**
  (`PostToolUse`, `UserPromptSubmit`); added the **Kiro IDE** `.kiro.hook` file-event trigger and the
  **kiro-cli** agent-JSON `hooks` field + STDIN `.ps1` shims as the third/fourth trigger models. New
  `.cursor/hooks/README.md` + `.claude/hooks/README.md` document the model. Existing per-concern hook
  wiring is retained intact; fan-out to the remaining hook-capable platforms is tracked as T510.
- **More platforms now route through the shared hook core** (T510, fan-out of T424) — seven more
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
  adapter that translates antigravity's `{decision}` I/O contract) are now wired too — **9/9
  hook-capable platforms**. Antigravity is authored to its launch-day docs and flagged PENDING
  live-install verification. Still pending (tracked in T510): antigravity live-verify, root live-repo
  tree propagation, and a forge rebuild.
- **Install gald3r_agent / gald3r_throne from the CLI** (T472, epic T470) — new `gald3r install agent|throne|all` detects the host OS (`windows`/`macos`/`linux`) and installs each product the right way: **agent** via `uv sync`; **throne** by locating the per-OS Tauri bundle (`npm run tauri:build` output — Windows NSIS/MSI, macOS .dmg/.app, Linux .deb/.AppImage/.rpm). `gald3r setup agent|throne|all` then initializes each product against the shared install home (vault, settings, log). `--dry-run` prints the full plan (artifact, target paths, PATH changes); `--json` emits it structured; `--products-root` / `GALD3R_PRODUCTS_ROOT` override the source root. Fail-loud (never a silent stub): a missing per-OS throne bundle raises a clear error with the exact build command and the paths searched. 27 unit tests.
- **Centralized install home + global `gald3r` CLI + USB-portable variant** (T471, epic T470) — new shared install home (`settings/`, `logs/`, `gald3r_vault/`, `VERSION`) resolved by precedence `override > portable > GALD3R_HOME > per-OS default` (Windows `%LOCALAPPDATA%\gald3r`, Linux `$XDG_DATA_HOME/gald3r`, macOS `~/Library/Application Support/gald3r`). USB-portable mode (`--portable` / `GALD3R_PORTABLE=1`) relocates the home to a removable medium with no outside writes. New `gald3r home [--portable] [--ensure] [--json]` subcommand + an idempotent, `--dry-run`-capable `install_global_cli` (Windows `gald3r.cmd` + user-PATH; POSIX `~/.local/bin` shim) so `gald3r --version` works from any directory. ADR-016. 26 unit tests.
- **Self-update: `gald3r version-check` + `gald3r upgrade`** (T473 agent + T475 templates, epic T470) — one shared engine serves both the agent and template-installed projects. `gald3r version-check` queries world_tree's version surface (`GET /api/v1/gald3r/version`) and reports current vs latest (offline-first: any unreachable/auth/timeout failure degrades to a clear message, never a crash or fabricated version). `gald3r upgrade` takes a timestamped gitignored backup of `.gald3r/`, migrates to the latest format (idempotent ADD/MERGE/DEPRECATE; user data — `tasks/**`, `bugs/**`, `TASKS.md`, `PLAN.md`, … — is never touched), and **rolls back from the backup on any failure**. `--dry-run` (default) previews; `--apply` performs; `--json` for both. 12 offline unit tests.
- **gald3r_throne: in-app version check + "update available" indicator** (T474, epic T470) — Throne now queries world_tree's version endpoint (`GET /api/v1/gald3r/version`) on connect and surfaces **current vs. latest** with an "update available" badge directly in the UI. Replaced the hardcoded `BUNDLED_LATEST_VERSION="1.2.0"` Rust constant with a live authenticated query via the existing `worldTreeFetch` client; project-relative version is read from `.gald3r/.identity`. Offline-first: unreachable / 401 / non-2xx world_tree → `reachable: false`, no throw, file-first status preserved. Includes a pre-apply preview modal (shows version delta before confirming). 11 Vitest tests.
- **gald3r_throne: in-app update APPLY in compiled Rust** (T481, epic T470) — Throne can now apply a `.gald3r/` update entirely from within the app, with no Python or engine dependency. Completes the T474 version-check half: `apply_create` writes real new-file content from the bundled template snapshot; `FileChange::Merge` performs a real frontmatter/key merge consistent with the engine's ADD/MERGE/DEPRECATE semantics. The full safety envelope is preserved: backup ZIP → integrity-verify → apply → registry-limited migrations → audit report → **byte-for-byte rollback on any failure**. User-data denylist (`tasks/**`, `bugs/**`, `TASKS.md`, `PLAN.md`, …) mirrors the Python engine — both implementations agree on what is never overwritten. 34 Rust `cargo test --lib project_update` tests. No process-spawn of Python. Offline-first preserved.
- **Local install folder auto-provisions the vault + inherits identity defaults** (T476, epic T470) — one shared `gald3r.provision` resolution used by both agent and throne (no fork): idempotently creates `gald3r_vault` at the configured `vault_location` (else the install home), and writes `.gald3r/.identity` by layering `install-home defaults -> user identity -> per-project overrides`. Any credential/token/password/secret/api_key-looking key is stripped before the identity is written (host-only secret state stays in the gitignored `.user_prefs.yaml`/`.env`). 26 unit tests.
- **Project scaffold against a target folder: `gald3r init` + `gald3r update`** (T477, epic T470) — `gald3r init` scaffolds a fresh gald3r project into a target folder (current dir by default, or `--target <folder>`) via the same canonical installer `@g-setup` uses, with new PROJECT.md param-seeding (`--name`, `--description`, `--vision`, `--tech-stack`); a user-edited section is never clobbered (idempotent), and an existing project routes to the update path instead of re-init. `gald3r update` routes a target folder through the T473 safe-update core (backup → migrate → rollback). `--dry-run`/`--json` for both. 23 unit tests.
- **CRASH activation tracking** (T433) — datetime invocation statistics for the five gald3r
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
- **Versioned `.gald3r/` snapshots for the upgrade engine** (T463) — each release cut now persists
  the canonical `.gald3r/` template as a stored, versioned snapshot
  (`gald3r_core/project_template/.gald3r_sys/snapshots/v<X.Y.Z>/.gald3r`, user data excluded) via
  `gald3r.systems.upgrade.capture_snapshot`, invoked by `@g-gald3r-publish`'s finalize step. The
  `gald3r upgrade` op gains `--from-version` / `--to-version` flags that resolve those stored
  snapshots automatically (`resolve_version_dir`), so a real vN→vN+1 migration can run against
  genuine historical sources instead of only synthetic fixtures.
- **Human-prose wishlist → task mining** (T453) — new `@g-wishlist-mine` command + `g-skl-wishlist-mine`
  skill productize the DELIVERABLES.md pattern: a non-technical user keeps a free-form, plain-language
  intent/wishlist document (no schema), and gald3r mines the READY, concrete wants into formal tasks.
  Mining is **READ-ONLY against the prose doc** (never rewritten/checklist-ified), dedups against
  existing `.gald3r/TASKS.md` entries, routes broad vision to a single epic, reports unsure items as
  backlog candidates (not over-created), and emits a created-tasks table + backlog-candidates list.
  Supports `--dry-run`, a configurable/default doc path (`.gald3r/DELIVERABLES.md`), and a WPAC
  controller cascade path via `@g-wpac-order`.
- **Turnkey hot-inbox staging zones** (T480) — fresh installs now ship pre-seeded
  `.gald3r/tasks/inbox/.gitkeep` and `.gald3r/bugs/inbox/.gitkeep` so the "drop a draft task/bug
  while g-go-go runs" zones are discoverable out of the box. The template `.gald3r/.gitignore` now
  declares them as gitignored staging zones (`tasks/inbox/*` + `!tasks/inbox/.gitkeep`, same for
  `bugs/inbox/`), matching the "gitignored staging zones" language in `g-go-go.md`: draft contents
  stay untracked (the `gald3r inbox` intake deletes them after absorbing), while the `.gitkeep`
  keeps the folder shipped.
- **All skill scripts ported to Python** (T1585) — every `.ps1` under `skills/*/scripts/`
  (48 scripts incl. the 1,765-line `gald3r_worktree.ps1`, decomposed into a `worktree_lib/`
  package) now has a `.py` sibling; SKILL.md/command invocations rewritten from
  `powershell/pwsh -File <script>.ps1` to `uv run python <script>.py` across all platform
  mirrors. PS1 files remain as transition fallbacks; ports prefer `.py` siblings for
  cross-script calls with `pwsh` fallback.
- **All platform hooks ported to Python** (T1584) — every `g-hk-*.ps1` hook (27 scripts)
  now has a `.py` sibling plus a shared `_hook_common.py` bootstrap; hook configs
  (`.claude/hooks.json`, `.cursor/hooks.json`, and all platform-overlay configs) now invoke
  `python <hook>.py` instead of `pwsh -File <hook>.ps1`. macOS/Linux installs get fully
  functional hooks without PowerShell. The `.ps1` files remain as transition fallbacks.
- **`setup_gald3r_project.py` cross-platform installer** (T1586) — Python port of the
  first-run setup with `--non-interactive` mode, `--dry-run`, UUID4 project_id generation,
  and new `setup_gald3r_project.sh` shim; `setup_gald3r_project.bat` now calls the Python
  version. `install_git_hooks.py` ports the git-hook installer (`core.hooksPath`,
  POSIX chmod +x).
- **`gald3r.utils` cross-platform utility module** (T1583) — new engine sub-package with
  `console` (colored output, NO_COLOR/FORCE_COLOR support), `fs` (`copy_tree` robocopy
  replacement, `clear_dir_except_git`, `replace_in_file_tree`, `ensure_dir`), `process`
  (`run_cmd`/`run_git` with dry-run and `RunResult`), and `paths` (`temp_file`,
  `gald3r_root`, `ecosystem_root`). Foundation for the PS1 → Python migration (T1581):
  ported scripts import from here instead of re-implementing PowerShell patterns.

### Changed
- **User scaffolding commands no longer reference maintainer-only commands** (BUG-137) — the
  shipped `@g-command-new` / `@g-rule-new` / `@g-skill-new` commands (48 files across 16 platform
  trees) dropped their `## Related` "Maintainer-only equivalent: `@g-gald3r-*-new`" bullet. These
  are end-user commands scoped to the user's own project; the maintainer `@g-gald3r-*` commands
  edit gald3r itself and have no place in a shipped user template (C-009 policy).

### Fixed
- **CRASH hook component metadata** (BUG-160, partial) — `g-hk-crash-record.md` was missing its
  `subsystem_memberships:` frontmatter (g-rl-38); added `[LOGGING_SYSTEM]` to match the hook's
  `.ps1` tag. The larger CRASH shipping gaps (engine `crash.py` absent from the shipped
  `project_template` engine, `.cursor` hook parity, `.py` port) are tracked in T511.
- **Stale `gald3r_rel_version` stamp in template `.gald3r/.gitignore`** (T480) — corrected the
  `# gald3r_rel_version: 3.0.0` header to `2.0.1` in both the canonical `project_template/.gald3r/.gitignore`
  and the `.gald3r_sys/template_verification/.gald3r/.gitignore` reference copy. (The forge does not
  re-stamp extensionless `.gitignore` files on build, so the canonical source carried the only stamp.)
- **Workspace manifest validator typo re-fixed in the canonical engine** (BUG-128) — the
  documented `pcac_relationship` → `wpac_relationship` fix had not landed in
  `project_template/.gald3r_sys/engine`; `validate_manifest()` and `status()` corrected.

---

## [2.0.1] - 2026-06-10

Patch release — copyright transfer, release pipeline org fix, and workspace engine bug fix.

### Changed
- **Copyright transferred to Gald3r Labs LLC** — all repository LICENSE files updated from
  `Warren R. Martel III` to `Gald3r Labs LLC` following company formation.
- **`push_repos.ps1` default org updated** — `GitHubOrg` default changed from `wrm3` to
  `Gald3r-Labs` to reflect the completed GitHub organization transfer.
- **Platform repos now get GitHub Releases by default** — previously required `-GitHubReleaseAll`
  flag; now all platform repos receive a tagged GitHub Release on every `push_repos.ps1` run.
  Use new `-SkipPlatformRelease` flag to opt out.

### Fixed
- **BUG-128**: `workspace.py status()` always returned `role: standalone` due to misspelled
  dict key `pcac_relationship` (should be `wpac_relationship`). WPAC topology was completely
  invisible — every project appeared standalone regardless of configured parent/child
  relationships. (`WORKSPACE_COORDINATION`)

---

## [2.0.0] - 2026-06-04

The **gald3r engine** release. gald3r gains a bundled, file-first Python core that backs every
system deterministically — while staying 100% markdown-on-disk. Existing installs keep working;
the engine is additive, and every slimmed component ships a no-engine fallback.

### Added
- **Bundled gald3r engine** (`.gald3r_sys/engine/`) — a pure, file-first state backend for every
  system: tasks, bugs, features, goals, prds, ideas, vocab, constraints, subsystems, vault,
  release, workspace, and inbox. **Mode-A**: deterministic, no LLM, no network, no Docker. One
  prerequisite — [`uv`](https://docs.astral.sh/uv/).
- **`gald3r` CLI** (and `python -m gald3r`) — drive every system from the shell: `gald3r task new`,
  `gald3r bug new`, `gald3r goal add`, `gald3r vault ingest`, `gald3r release new`,
  `gald3r workspace …`, `gald3r prompt get …`.
- **MCP server** (`gald3r mcp`) — ~20 Model Context Protocol tools exposing the same operations to
  any MCP-capable agent.
- **`gald3r doctor`** — read-only health check (structure, per-system index integrity, skill
  frontmatter, `.ps1` encoding) with an overall functionality score and a `--fail-below` CI gate.
- **Engine-absorbed operations** — five maintenance scripts reimplemented as pure engine verbs,
  each keeping its original `.ps1` as a no-engine (L0) fallback: `gald3r inbox` · `gald3r doctor` ·
  `gald3r platform status` · `gald3r tier show|set` · `gald3r sync --check|--apply` (alias
  `gald3r parity`).
- **Judgment / prompt layer** — 15 reasoning assets (Norse persona, role briefs, review rubrics,
  marketing voice) served by the engine (`gald3r prompt get role.code_reviewer`), so a brief is
  authored once and shared across platforms.

### Changed
- **Thinned component shims** — judgment skills and agents are slimmed to load their brief from the
  engine's prompt assets. Skills keep a full `SKILL.full.md` fallback; agents reference the shipped
  asset directly (no `.full.md` sidecar — it would register as a duplicate component).
- **Task status vocabulary** — `task_file.v1.schema.yaml` realigned to mirror the engine's enforced
  vocabulary (`pending → in-progress → awaiting-verification → completed …`). The YAML previously
  listed a never-implemented pipeline as "current" and the real vocabulary as "legacy."

### Fixed
- **Windows PowerShell 5.1 parse crash** — 1,055 shipped `.ps1` files were UTF-8 without a BOM, so
  `powershell.exe` mis-read multi-byte characters and failed to parse (including the installer
  itself). All BOM-protected (installer ASCII-cleaned); the build generators now emit safe `.ps1`
  and `gald3r doctor` flags any regression.
- **Duplicate component names** — removed the per-agent `*.full.md` sidecars and the deprecated
  `g-skl-medkit` (named `g-skl-medic`, colliding with the real skill). 106 skills + 13 agents now
  audit clean (no duplicate `name:`, no dangling shim references).
- **`doctor` / `bug sync` index mis-parse** — the id-scan matched the `## Next Bug ID:` counter line
  (and any title mentioning it), producing false phantom/orphan rows and a non-converging
  `bug sync`. Anchored to the counter heading.
- **Malformed component frontmatter** — added missing `name`/`description` to 5 skills and agents.

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
- **Restructured install model**: deliverable is now `project_template/` — copy its contents to
  your project root. Cursor + Claude Code are Tier 1; other platforms via `AGENTS.md` + `.gald3r/`.
- **Simplified installer**: `setup_gald3r_project.ps1` rewritten from 44KB → ~110 lines. Single
  purpose: copy `project_template/` to target, preserving existing `.gald3r/` user data.
- **Stripped maintainer-only rules**: `g-rl-25` (session-start), `g-rl-33` (enforcement-catchall),
  and `g-rl-36` (workspace-guard) removed from the shipped template — these are framework-build
  tools, not end-user config. Shipped set: 11 lightweight rules + `gald3r_personality`.
- **Updated README**: reflects actual structure and accurate component counts (110 skills,
  177 commands, 37 hooks, 12 rules); version badge, installer docs, and platform table.

### Fixed
- **Personality rule extension**: renamed `gald3r_personality.md` →
  `gald3r_personality.mdc` in `project_template/.cursor/rules/`. Cursor only loads
  `.mdc` files from the rules folder; the Norse personality was silently not loading.
- **License reference in README**: corrected from `[MIT]` to `[Fair Source License 1.1
  (FSL-1.1-Apache)]`. The actual LICENSE file was always FSL — only the README link was wrong.
- **BUG-099 safety fix**: All platform scaffold `gald3r_worktree.ps1` scripts and `development.yaml`
  files defaulted `TargetBranch`/`default_branch` to `dev` instead of `main` — a data-loss trap for
  new projects created from any platform template. Flipped 78 files (44 worktree scripts + 34
  development.yaml) to `main`. Affects all 34+ platform scaffolds.

---

## [1.9.0] - 2026-05-31 (Platforms/ Folder + Post-Push Verify + Plugin System Foundation)

### Added
- **Plugin system foundation** (T1557–T1559): `@g-plugin-install` lands — install a gald3r plugin
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
- **GitHub wiki launched** (T1550): 7 pages auto-generated from `.gald3r_sys/` — Home, Quickstart,
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
- **Branch model: feature-branches-only → `main` (USER-SAFETY, T1535)**. Retired the long-lived
  `dev`/`test` promotion branches (root cause of repeated history-loss incidents, BUG-099 class).
  `g-go`/`g-go-go` auto-merge default flipped `dev` → `main`; `gald3r_worktree.ps1`,
  `development.yaml`, and `g-skl-setup` realigned to `main`.

### Fixed
- **Eliminated the stale-`dev` auto-merge data-loss hazard (BUG-099, USER-SAFETY)**: gald3r no longer
  defaults swarm/autopilot auto-merge to a long-lived `dev` integration branch. Existing user repos
  are offered a safe, confirmation-gated migration — never an automatic branch delete.

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
- **Tier setup skill** (`g-skl-tier-setup`, `@g-tier-setup`): upgrade a project's gald3r installation tier (slim → full → adv) without losing existing state.
- **Codex CLI skill** (`g-skl-cli-codex`): dedicated reference skill for Codex terminal-first operation.
- **Copilot CLI skill** (`g-skl-cli-copilot`): dedicated reference skill for GitHub Copilot terminal-first operation.
- **Swarm commands** (`@g-go-swarm`, `@g-go-code-swarm`, `@g-go-review-swarm`): multi-agent coordinated execution across the backlog.
- **Vault process-inbox command** (`@g-vault-process-inbox`): process pending vault inbox items.
- **`.gald3r/releases/`** directory, **`.gald3r/release_profiles/`** directory, and **`.gald3r/RELEASES.md`** index: new release tracking structure.
- **`.gald3r/logs/`** directory: session log storage.
- **`ROADMAP.md`**: project roadmap file at repo root.
- **`raw-inbox-watcher.ps1`** hook: real-time PCAC inbox watcher.

### Changed

- `g-skl-reverse-spec` → `g-skl-recon-repo`: renamed and expanded. The recon namespace (`recon-*`) supersedes the ad-hoc harvest/ingest/reverse-spec naming.
- `g-skl-harvest-intake` → `g-skl-res-apply`: part of the three-step res-* workflow (res-review → res-deep → res-apply).
- `g-skl-ingest-docs` → `g-skl-recon-docs`: unified into recon namespace.
- `g-skl-ingest-url` → `g-skl-recon-url`: unified into recon namespace.
- `g-skl-ingest-youtube` → `g-skl-recon-yt`: unified into recon namespace.
- `g-skl-harvest` → subsumed by `g-skl-recon-repo` + `g-skl-res-review`.
- README: IDE parity updated from 5 → 6 IDEs (12 parity targets). Skills 49 → 58, Commands 78 → 89.
- `g-skl-medkit` version migration updated to include 1.2 → 1.4 path.

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

- **Feature pipeline** (`g-skl-features`, `FEATURES.md`, `.gald3r/features/`): structured staging layer between idea capture and task creation. Features move through `staging → specced → committed → shipped`. Only reach the TASKS.md backlog when explicitly promoted via `@g-feat-promote`. Prevents backlog pollution and keeps implementation intent explicit.
- **Reverse-spec skill** (`g-skl-reverse-spec`, `@g-reverse-spec`): deep 5-pass analysis of any external repository. Produces a structured harvest report in `research/harvests/{slug}/` with skeleton, module map, feature scan, deep dives, and synthesis passes. Human reviews and marks features `[✅] approved` before APPLY writes to `.gald3r/features/`.
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
- README: updated component counts (Skills: 39 → 47, Commands: 52 → 76, Skill Packs: 6 → 7), added Feature Pipeline section, updated directory tree to show `features/`, updated all skill and command references.

### Removed

- `g-claude-cli.md`, `g-cursor-cli.md`, `g-gemini-cli.md` commands (superseded by `g-cli-claude.md`, `g-cli-cursor.md`, `g-cli-gemini.md`)
- `g-go-verify.md` command (superseded by `g-go-review.md`)
- `g-skl-claude-cli`, `g-skl-cursor-cli`, `g-skl-gemini-cli`, `g-skl-opencode-cli` skill directories (superseded by `g-skl-cli-*` namespace)

---

## [1.1.0] - 2026-04-08

### Added

- **Task circuit breaker** (`[🚨]` Requires-User-Attention): tasks that fail verification 3 or more times are automatically escalated for human review. Automated agents skip them and they remain visible in the backlog until a human resets or cancels.
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

- `g-go-code` now requires a Status History entry before marking any item `[🔍]`. The b3 step is mandatory.
- `g-go-review` FAIL path now counts FAIL rows in Status History to determine whether to reset to `[📋]` or escalate to `[🚨]`.
- `g-go-code` skips `[🚨]` items entirely -- logs them in the Skipped section as Requires-User-Attention.
- Session start protocol (step 2) now surfaces re-work tasks when the last Status History entry is a FAIL.
- `g-skl-tasks` and `g-skl-bugs` templates include Status History section. Every status transition appends a row.

### Fixed

- Session hook (`g-hk-agent-complete.ps1`): `$input` pipeline variable does not capture external-process stdin in PowerShell. Fixed to use `[Console]::In.ReadToEnd()`. Status mapping corrected from `"success"` to `"completed"` per Cursor hook schema.
- `pending_reflection.json` was never written when the session hook ran in a non-interactive terminal. Fixed `[Console]::IsInputRedirected` guard to prevent blocking on `ReadToEnd()`.

---

## [1.0.0] - 2026-04-04

### Added

- **Task management system**: YAML frontmatter task specs with sequential IDs, priority, dependencies, and subsystem tracking. Master `TASKS.md` checklist with per-file status sync.
- **Two-phase adversarial code review** (`@g-go-code` / `@g-go-verify`): implementation and verification are separated into distinct agent sessions. The implementing agent marks `[🔍]`; a separate agent marks `[✅]`. Neither can do both.
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
- **TODO lifecycle enforcement**: stubs and TODOs must be annotated with `TODO[TASK-X→TASK-Y]` format and a follow-up task created before the implementing task can be marked complete.
- **Bug discovery gate**: pre-existing bugs encountered during implementation must have a BUG entry and code annotation before the task is marked `[🔍]`.
- **Git commit skill** (`g-skl-git-commit`): conventional commit format with task references and agent footers.
- **Project planning** (`g-skl-plan`, `g-skl-project`): PLAN.md (milestones and deliverables), PROJECT.md (mission, vision, goals), PRD files, and CONSTRAINTS.md.
- **Code review** (`g-skl-code-review`): structured review covering security, performance, maintainability, and architectural alignment. Severity-classified output with file/line references.
- **Harvest skill** (`g-skl-harvest`): analyze external repositories for adoptable patterns and improvements. Zero-change-without-approval output.

---

*gald3r is built with gald3r. The development history of this framework lives in the <gald3r_source> source repository.*