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

## [5.0.0-beta.12] - 2026-08-11

The eyes-and-teeth release: a stalled swarm can no longer hide, and
stopping one actually stops it.

- A worker that produces nothing gets caught: a per-worker liveness
  watchdog kills any bucket that goes silent, reports what it captured,
  and the loop MOVES ON to the next item instead of freezing forever
  behind one wedged process. The heartbeat now ticks through the entire
  dispatch window, so a quiet run always tells you it is alive.
- `gald3r autopilot stop --now` is genuinely immediate: it terminates
  the recorded process tree and finalizes the run marker itself -- no
  more killing by PID and hand-editing files to recover.
- Honest events: `bucket_planned` (intent) is now separate from
  `bucket_spawned` (worker confirmed running), so telemetry can never
  again claim five workers dispatched when none started.
- Claude-subscription users get autonomous implementers: `--provider
  claude` now genuinely drives the claude CLI instead of silently
  demanding an API key -- proven end-to-end with a real agent fixing a
  real bug before this release was cut.
- Every shipped @g-* command works as written: ten internal playbooks
  the commands reference are now retrievable, guarded by a test that
  walks every shipped command; and a mistyped subcommand errors with a
  did-you-mean across all 55 command groups instead of silently
  printing help.

## [5.0.0-beta.11] - 2026-08-11

The unblocked release: every kind of repo can loop now.

- The one-second bucket deaths are over. If your project gitignores its
  .gald3r/ folder -- the normal setup for application repos -- spawned
  workers used to land in a workspace with no task specs at all and die
  instantly. gald3r now detects that shape and points every worker at
  the real project state automatically, with a clear line in the log
  saying so.
- The @g-go command fallback works again: the instructions those
  commands fetch are no longer refused by the assistant-facing gate.
- Backup archives can no longer dirty your tree and block a run -- the
  ignore rule now heals itself at loop start, no reinstall needed.
- Memory upgrades: per-agent memory loadouts (give your reviewer and
  implementer different working memory), a skill-extraction pipeline
  that distills reusable skills from completed work (human-approved
  before anything ships), and session-local notes no longer leak into
  memory recall.

## [5.0.0-beta.10] - 2026-08-11

The delivered-orders release: spawned agents finally receive their instructions.

- The brief actually reaches the agent now. Headless CLI agents
  (cursor-agent, claude) were being launched without their
  instructions -- a real agent would run for minutes and change
  nothing. The prompt is now handed over the way those CLIs expect,
  so implementer and coordinator turns do the work they were asked to.
- Failures tell you why. Every loop-spawned worker's output is
  captured to a per-run log and the failing lines are quoted in the
  failure message -- no more bare "exited 1" with nothing to act on.
- What you asked for is what runs: the resolved provider and model
  travel explicitly with each spawned worker, and go / go-code /
  go-bug / go-review all accept --provider directly.
- Review runs on subscriptions too. The reviewer role can now drive
  cursor-agent, so verification passes work on a machine with no API
  keys -- and a verdict is only accepted from real recorded evidence,
  never from a clean exit code.
- Quality of life: crash telemetry and backup archives can no longer
  dirty your working tree or block a run, and the docs gained a cost
  guide for choosing how you loop (in-session pipelines vs spawned
  CLI sessions vs API-key providers).

## [5.0.0-beta.9] - 2026-08-11

The throughput release: your subscriptions now do the work.

- Autonomous implementers on subscription credentials: go-code and
  go-bug can now drive the same cursor-agent/claude CLI your
  subscription already pays for -- no API keys required. On a
  subscription-only machine, autopilot buckets actually implement and
  fix instead of failing in one second (the root cause behind every
  zero-throughput run since beta.3, found by beta.8's own diagnostics).
  A do-nothing agent can never fake a fix: evidence of real change is
  required before anything resolves.
- A doomed run refuses at startup with the remedy named -- before
  claiming work or creating worktrees -- and the circuit breaker names
  the shared cause when every failure is the same one.
- Review phase unstuck: awaiting-verification work dispatches again
  (the empty-queue miscount that let review items age forever is
  fixed).
- Harvest merges for real: diverged-but-clean bucket branches land via
  a proper merge commit; genuine conflicts surface exact copy-paste
  recovery commands. The first-merge-strands-the-rest era is over.
- Live run events can stream to world_tree subscribers (opt-in
  --publish-events; durable offline queue, never slows a run).
- Component activation telemetry is back (crash-stats records real
  usage again), config hot-reload is race-free on Windows, backup zips
  and telemetry logs can no longer block a run's preflight, and every
  shipped verb now has documentation enforced by CI.

Update: gald3r install update

## [5.0.0-beta.8] - 2026-08-10

The observability release: a swarm can never run dark again.

- Live event stream: every autopilot run now narrates itself the moment
  things happen -- claims, agent spawns, merges, harvests, breakers,
  costs -- as [AUTOPILOT][EVENT] lines in your session AND a durable
  per-run event ledger. New: gald3r autopilot events --follow tails a
  live run from any other terminal.
- Heartbeats and a stall watchdog: long iterations now beat every 15
  minutes with liveness diagnostics, and a frozen coordinator (the
  74-minute silent-stall class) is detected within minutes -- claims
  released, one retry, then a loud named halt. Never an hour of
  silence.
- autopilot status now tells the truth: it reads the same candidate
  board the loop itself uses (it previously read an unrelated legacy
  queue), and task show --json exposes claim ownership.
- Every Windows binary now has a face: Mjolnir-derived icons and real
  Gald3r Labs version metadata in Explorer, Task Manager, and
  Add/Remove Programs.
- Find your platform: 37 new docs pages -- one per supported platform
  -- at docs.gald3r.ai, matching the new Supported Platforms section in
  this README.
- Config hot-reload no longer races itself on Windows; a new CI gate
  guarantees every shipped verb has documentation.

Update: gald3r install update

## [5.0.0-beta.7] - 2026-08-10

The harvest release -- and Longship's debut: finished work always comes
home, and the Agentic Focus Terminal is now in the box.

- The harvest gate: work an autopilot agent completes in a worktree is now
  automatically committed and merged into your checkout -- at every
  iteration close and once more at run end. A merge that is not safe leaves
  the work preserved on its own branch, never destroyed, with a line naming
  why. Runs can no longer report "zero work" while finished code sits
  stranded.
- Longship ships in every install bundle: gald3r-longship, the terminal
  chat app, is now an eighth signed binary in the platform archives -- with
  a guided first-run: launch it with zero config and it walks you through
  picking a provider (a running Ollama or LM Studio is offered as the
  no-key instant path), then drops you straight into chat. No more fatal
  error before you even see the app.
- gald3r context now binds to the CALLING session's own transcript and
  never guesses -- previously, on a machine with several live sessions, it
  could silently measure a different session and report it as real. Cursor
  sessions get their own measurement source with the same honesty contract.
- Stale claims release themselves at run end; the worktree janitor no
  longer abandons a sweep at the first dirty worktree; long healthy
  iterations can no longer be killed by a stop-escalation ceiling shorter
  than the coordinator's own timeout; and every cost figure says
  "(estimated)" when it is one -- with real per-model pricing now wired
  into the loop.
- upgrade-project --dry-run is now truly read-only (it previously refreshed
  the overlay and wrote a backup), upgrades take an automatic pre-flight
  backup, search --path accepts a single file, and a mistyped task/bug
  subcommand tells you what it was and suggests the closest real one.

Update: gald3r install update

## [5.0.0-beta.6] - 2026-08-10

The autopilot integrity release: bugs are workable, work is unlosable,
parallelism is honest, and local AI works out of the box.

- New gald3r go-bug: autopilot can now FIX bugs, not just log them -- the
  full claim, agent turn, self-verify, resolve cycle, wired into
  deterministic dispatch. A bug backlog becomes reachable work and
  --min-severity finally gates something real. An empty bug queue no longer
  ends a run while tasks remain.
- Rescue commits: if a run dies mid-iteration (provider refusal, breaker,
  fatal signal), uncommitted run-authored work lands in a named wip(rescue)
  commit -- never lost to a cleanup, and never touching your own
  pre-existing uncommitted edits.
- Honest parallelism: implementer counts only count buckets that actually
  landed work; idle or failed buckets are loudly diagnosed; a dispatch that
  produces nothing counts as a capacity violation (consecutive AND
  cumulative breakers).
- Local AI out of the box: gald3r init-providers discovers a running Ollama
  server over HTTP (no CLI needed), the documented setup path just works,
  and the .gald3rsecret no-cloud tier correctly treats loopback AI as local
  (LAN endpoints require an explicit opt-in).
- New CI parity gates: advertised flags and documented environment
  variables are now mechanically verified against the binary on every
  change -- the lost-surface defect class is structurally dead.

Update: gald3r install update

## [5.0.0-beta.5] - 2026-08-09

Provider routing release: a rate-limited AI provider no longer stops your work.

- The autopilot coordinator is no longer hardcoded to the Claude CLI: a Cursor
  host defaults to cursor-agent, and the full routing surface works -- CLI
  flags (--provider/--model plus per-role --coordinator/--implementer/
  --reviewer -provider/-model), all six GALD3R_GGO_* environment variables,
  and AGENT_CONFIG keys, with a documented precedence order (flag beats env
  beats config beats host default).
- Hit a provider quota wall mid-run? The run no longer dies: the refusal
  costs no budget, gald3r falls back to a healthy configured provider (opt
  out with --no-provider-fallback), and if nothing is available it stops
  honestly with the provider's own quota-reset time, a distinct
  PROVIDER_UNAVAILABLE state, and exit code 4.
- cursor-agent runs now report token counts and honor the context-exhaustion
  safety stop.

Update: gald3r install update

## [5.0.0-beta.4] - 2026-08-09

- gald3r install update works again: downloads the per-platform archive,
  verifies it against SHA256SUMS.txt (fail-closed), extracts, and replaces the
  running binary safely. Sibling binaries you already have are refreshed too.
  (This fixes beta.3's known issue -- one last manual install gets you here.)
- Intel Macs no longer download the Apple Silicon build by mistake.
- Autopilot's deterministic dispatch now merges to your repo's actual branch
  (master/trunk/anything), not a hardcoded main.
- Engine CI is fully green on Linux again; one real SDK fix landed on the way
  (missing-executable errors now surface as the typed NOT_FOUND error on all
  platforms).

## [5.0.0-beta.3] - 2026-08-09

Autopilot economics release: the swarm now materializes.

- Deterministic implementer dispatch: when a coordinator ends an iteration with
  zero implementers despite runnable work, the outer loop provisions implementer
  runs itself (worktree-isolated; opt out with --no-deterministic-dispatch).
- Capacity circuit breaker: consecutive advertised-but-unmaterialized capacity
  halts the loop with exit code 3 instead of silently burning the budget
  (--capacity-violation-limit, --no-capacity-breaker).
- Review-phase iterations are skipped for free when nothing awaits verification.
- Iteration accounting diffs the git checkpoint: real commits are never reported
  as zero throughput again.
- gald3r run --approval-mode=ask: stream-json tool calls can require an
  approval_request/approval_response round trip on stdin (fail-closed on
  timeout or closed stdin).
- Known issue: 'gald3r install update' in fielded builds requests a retired
  asset name and fails (BUG-774, fix in the next beta) -- update by running
  the installer for your OS from the releases page instead.

## [5.0.0-beta.2] - 2026-08-09

- Release assets consolidated to one archive per platform with version-less
  names, so /releases/latest/download links never go stale.
- Signed installers: Windows .msi (Authenticode), macOS .pkg (Developer ID +
  notarized), Linux tarball with install.sh.

## [5.0.0-beta.1] - 2026-08-09

The Go rewrite. The engine is now a single fast native binary on every platform:
startup drops from 8-11s to ~120-190ms; no Python, no runtime to install.

- .gald3rsecret: keep sensitive files out of AI prompts, logs, and the cloud.
- .gald3rignore gains ! re-include negation.
- Restored/added verbs: search, validate, context, task next, task stale-claims.
- Auto-backup before schema migrations; safer upgrade path.

## [4.0.0-beta.3] - 2026-08-05

**The first three-platform signed release — and the storefront becomes a front door.**

### Added
- **Direct per-OS download table** on the README (installers and binaries, always resolving to
  the newest release) and a **`The gald3r system — who does what`** map: every user-visible
  capability of the product family and which piece owns it (`gald3r_core`, `gald3r_throne`,
  `world_tree`, the framework, `gald3r_longship`).
- **`PLATFORM_SUPPORT.md`** — the 38-platform support matrix as native Markdown, ported from
  the hand-verified canonical matrix with **the honest gaps marked** (what does not function
  today, and which of those are tracked follow-ups versus platform limitations). Replaces the
  old `PLATFORM_SUPPORT.html`, which rendered as unreadable raw HTML on GitHub.

### Changed
- **The repo is now a landing page, not an install dependency.** Everything that used to ship
  here as file trees — the per-platform overlays and the project template — is generated by the
  binary (`gald3r platform install <platform>`), always current with your binary version. The
  README was rewritten around that flow, with install paths for all three OSes.
- **The `.pkg` installer is now signed at the container level** (Developer ID Installer), so
  macOS no longer shows the unsigned-developer confirmation; the binary inside was already
  codesigned and notarized.

### Removed
- **14,702 legacy files**: `platforms/` and `project_template/` (provisioned by the binary
  now), the pre-4.0 clone-and-copy instructions and `setup_gald3r_project.*` scripts, old
  `releases/` notes, `ROADMAP.md`, `PLATFORM_SUPPORT.html`, and two generated matrix files
  whose canonical copies live in the engine repo.

## [4.0.0-beta.2] - 2026-08-03

### Added
- **Prominent Windows/macOS/Linux support statement** on the README and a direct link to the
  new docs site, [docs.gald3r.ai](https://docs.gald3r.ai).
- **`docs/IP_PURGE_PLAN.md`** — the options, exact commands, and consequences for a git-history
  scrub of the retired `project_template/.gald3r_sys` payload (BUG-639), left as an owner
  decision; the runbook has since moved to the engine repo's docs.

### Fixed
- **`PLATFORM_SUPPORT.html` pointed at 34 dead links.** Every platform card linked to a
  `github.com/Gald3r-Labs/gald3r_platform_<name>` repo — none of those repos exist (verified
  against the full `Gald3r-Labs` org roster). This repo is, and has been, a single monorepo:
  every platform's payload lives in `platforms/<name>/` right here. Cards now link to the real
  in-repo folders, cover all 38 shipped platforms (4 were missing: `mimo-code`, `pi`, `zcode`,
  `zed`), and the page's own copy no longer implies a "clone the repo you use" multi-repo model.
- **Corrected the platform count from 39 to 38 everywhere** (README badges/table/bullets,
  `CHANGELOG.md`, `PLATFORM_SUPPORT.html`) — `platforms/` has 38 real overlay directories; the
  prior count included `PLATFORM_REGISTRY.yaml` itself as if it were a platform.
- **`PLATFORM_CAPABILITY_MATRIX.md`** cited a `strategy/gen_platform_docs.py` generator, a
  `strategy/PLATFORM_DATA.json` source, and a `COMBINED_READINESS.md` companion — none exist in
  this repo. Removed those dangling references, corrected its own platform count (34 → 38),
  added the missing `mimo-code` row, and fixed two directory-name typos (`kilo_code` →
  `kilo-code`, `kiro_cli` → `kiro-cli`). The per-platform ✅/⚠️/❌ capability cells were not
  re-verified in this pass — see the file's own reconciliation note.

### Removed
- **`PLATFORM_COMBINED_READINESS.md`** — an orphaned doc (no incoming links from README or
  anywhere else) describing the same retired 34-platform, separate-repo-per-platform model as
  the dead `PLATFORM_SUPPORT.html` links above, sourced from a `strategy/PLATFORM_DATA.json`
  file that doesn't exist in this repo.

### Changed
- **`project_template/.gald3r_sys` removed from tracking** (328 files, ~45,000 lines) —
  compiled-into-binary IP that should never have shipped as loose source (BUG-639). `.gitignore`
  now guards against it coming back.
- **Every shipped reference to the retired `.gald3r_sys/schemas|scripts` tree** now points at the
  current native `gald3r` CLI surface instead (`gald3r schema-migrate`, `gald3r lint
  post-write`, etc.) across all 38 platform overlays and `project_template` (BUG-598) — an
  in-flight sweep that had been sitting uncommitted; reviewed file-by-file and confirmed every
  referenced verb actually exists before committing.
- **Corrected two stale component counts**: agents was miscounted as 15 (it was counting two
  non-agent index files alongside the real 13 `g-agnt-*` definitions); rules is 13, not 12, now
  that `g-rl-33-enforcement_catchall` is committed rather than sitting in the uncommitted sweep.

---

## [4.0.0-beta.1] - 2026-08-01

**gald3r becomes a matched pair: framework + compiled engine.**

### Added
- **A signed, compiled engine.** The deterministic core that runs task and bug lifecycle,
  validation, the local database, and multi-agent orchestration now ships as a single signed
  binary from [gald3r_core](https://github.com/Gald3r-Labs/gald3r_core/releases) — with a
  Windows MSI installer. No Python toolchain required.
- **38 supported AI coding platforms**, up from 34.
- **13 specialized agents** for review, verification, QA, and infrastructure work.

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
