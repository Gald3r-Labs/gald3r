## [1.8.0] - 2026-05-30 (Wiki Launch + GitHub Discussions + Test Harness + 35-Platform Sweep)

### Added
- **GitHub wiki launched** (T1550): 7 pages auto-generated from `.gald3r_sys/` — Home, Quickstart, Commands (179 `@g-*` commands indexed by category), Skills, Agents, Rules, Hooks. Sourced from canonical `.gald3r_sys/` and staged in `docs/wiki/`. Full argument/syntax expansion tracked in T1551.
- GitHub Discussions enabled as the community Q&A and announcement channel.
- Batch-11 platform specs consolidated into the canonical `project_template/.gald3r_sys/platforms/.<platform>/PLATFORM_SPEC.md` single-source-of-truth location (T1544): `.deepcode`, `.kilo`, `.hermes`, `.codebuddy`, `.astrbot`, `.amp`, `.void`, `.continue`, `.kimi`, `.trae`, `.qoder`, plus a `.vibe` stub spec that cross-links to `.mistral`. `platforms/` now holds 35 platform specs (23 original + 11 batch + `.vibe`).
- gald3r systems functional test harness `gald3r_system_test.ps1` (T1540): per-system PASS/PARTIAL/FAIL + overall "N% functional" score across 13 gald3r systems (Task, Bug, PLATFORM_SPEC, Parity, Hook Wiring, Git Hooks, Schema, Constraints, Subsystems, Skills, WPAC, Release, Encoding). Writes `.gald3r/reports/system_test_*.md`; `-FailBelow <N>` CI gate; `-Json`/`-NoReport`/`-Systems` flags. Added as the **FUNCTIONAL (L0)** operation in `g-skl-test`.
- Two-layer release system: `pre_release_audit.ps1`, `bump_identity_versions.ps1`, `release_gald3r_public.ps1`, `release_config.json` (T1528-T1530).
- Native tier graduation scripts in `g-skl-release/scripts/`: `graduate_to_public.ps1` (scrub + carry modes), `graduate_to_test.ps1`, `scrub_public_tree.ps1`, `read_tier_config.ps1`.
- Framework constraints C-041..C-043 (destructive git gate, content scrub, public main-only).

### Changed
- `scan_platform_docs.ps1` now discovers platforms by scanning `project_template/.gald3r_sys/platforms/` for any dir containing a `PLATFORM_SPEC.md` (no hardcoded 23-platform list; T1544 AC6). Discovery verified at 35 platforms under powershell.exe 5.1.
- `DISTRIBUTION_PLAYBOOK.md`, `BRANCH_TIER_POLICY.md`, `GIT_TIER_MODEL.md` — guarded public release path; `test_to_public_history: scrub|carry` in AGENT_CONFIG.
- **Branch model: feature-branches-only → `main` (USER-SAFETY, T1535)**. Retired the long-lived `dev`/`test` promotion branches that were the root cause of repeated history-loss incidents (BUG-099 class: stale `dev` auto-merge target). `g-rl-02-git_workflow` rewritten to feature-branches-only; `g-go`/`g-go-go` auto-merge default flipped `dev` → `main`; `gald3r_worktree.ps1` `-TargetBranch` default `dev` → `main`; `development.yaml` `default_branch` `dev` → `main`; `g-skl-setup` now checks for `main` instead of creating a `dev` branch.

### Fixed
- **Eliminated the stale-`dev` auto-merge data-loss hazard (BUG-099, USER-SAFETY)**: gald3r no longer defaults swarm/autopilot auto-merge to a long-lived `dev` integration branch. Existing user repos still on the old model are offered a safe, confirmation-gated migration (promote `dev` → `main`, then retire `dev`) — never an automatic branch delete.

---
