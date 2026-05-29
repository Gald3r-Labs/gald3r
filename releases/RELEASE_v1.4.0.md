> **Released**: 2026-04-14
> **Previous release**: [v1.2.1](RELEASE_v1.2.1.md)

---

## Full Changelog

### Added

- **GitHub Copilot support** (`.copilot/`): 6th IDE added to the parity set. Full command surface (89 commands) deployed to `.copilot/commands/`. gald3r now supports Cursor, Claude Code, Gemini, Codex, OpenCode, and GitHub Copilot.
- **Recon suite** (`g-skl-recon-repo`, `g-skl-recon-url`, `g-skl-recon-docs`, `g-skl-recon-yt`, `g-skl-recon-file`): unified research/reconnaissance skill family. Replaces the separate `g-skl-reverse-spec`, `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube`, and `g-skl-harvest` skills with a consistent `recon-*` namespace. Each produces a structured recon report for human review before any writes occur.
- **Research review/apply suite** (`g-skl-res-review`, `g-skl-res-deep`, `g-skl-res-apply`): three-step workflow - review a recon report, deep-dive on specific findings, then apply approved findings into `.gald3r/features/` staging. Replaces `g-skl-harvest-intake`.
- **Release management skill** (`g-skl-release`, `@g-release-new`, `@g-release-assign`, `@g-release-status`, `@g-release-accelerate`, `@g-release-publish`): full release lifecycle from planning to publishing. Manages `.gald3r/releases/` and `.gald3r/RELEASES.md`.
- **Platform skills** (`g-skl-platform-cursor`, `g-skl-platform-claude`, `g-skl-platform-gemini`, `g-skl-platform-codex`, `g-skl-platform-opencode`, `g-skl-platform-copilot`): per-IDE platform reference skills for understanding each IDE's agent model, permission system, and tool surface.
- **Medic skill** (`g-skl-medic`, `@g-medic`): targeted surgical repair for a specific `.gald3r/` file or subsystem, complementing `g-skl-medkit` (which does full-project health checks).
- **Tier setup skill** (`g-skl-tier-setup`, `@g-tier-setup`): upgrade a project's gald3r installation tier (slim -> full -> adv) without losing existing state.
- **Codex CLI skill** (`g-skl-cli-codex`): dedicated reference skill for Codex terminal-first operation.
- **Copilot CLI skill** (`g-skl-cli-copilot`): dedicated reference skill for GitHub Copilot terminal-first operation.
- **Swarm commands** (`@g-go-swarm`, `@g-go-code-swarm`, `@g-go-review-swarm`): multi-agent coordinated execution across the backlog.
- **Vault process-inbox command** (`@g-vault-process-inbox`): process pending vault inbox items.
- **`.gald3r/releases/`** directory, **`.gald3r/release_profiles/`** directory, and **`.gald3r/RELEASES.md`** index: new release tracking structure.
- **`.gald3r/logs/`** directory: session log storage.
- **`ROADMAP.md`**: project roadmap file at repo root.
- **`raw-inbox-watcher.ps1`** hook: real-time WPAC inbox watcher.

### Changed

- `g-skl-reverse-spec` -> `g-skl-recon-repo`: renamed and expanded. The recon namespace (`recon-*`) supersedes the ad-hoc harvest/ingest/reverse-spec naming.
- `g-skl-harvest-intake` -> `g-skl-res-apply`: part of the three-step res-* workflow (res-review -> res-deep -> res-apply).
- `g-skl-ingest-docs` -> `g-skl-recon-docs`: unified into recon namespace.
- `g-skl-ingest-url` -> `g-skl-recon-url`: unified into recon namespace.
- `g-skl-ingest-youtube` -> `g-skl-recon-yt`: unified into recon namespace.
- `g-skl-harvest` -> subsumed by `g-skl-recon-repo` + `g-skl-res-review`.
- README: IDE parity updated from 5 -> 6 IDEs (12 parity targets). Skills 49 -> 58, Commands 78 -> 89.
- `g-skl-medkit` version migration updated to include 1.2 -> 1.4 path.

### Removed

- `g-skl-harvest`, `g-skl-harvest-intake` skill directories (superseded by recon-* / res-* suites)
- `g-skl-ingest-docs`, `g-skl-ingest-url`, `g-skl-ingest-youtube` skill directories (superseded by recon-*)
- `g-skl-reverse-spec` skill directory (superseded by `g-skl-recon-repo`)
- Corresponding commands: `@g-harvest`, `@g-harvest-intake`, `@g-ingest-docs`, `@g-ingest-url`, `@g-ingest-youtube`, `@g-reverse-spec`

---

---

## Migration Notes

No breaking changes unless noted above. Review any ### Breaking Changes section above if present.

---

*Generated from [CHANGELOG.md](../CHANGELOG.md) by scripts/backfill_release_files.ps1*