# Release v1.2.1

> **Released**: 2026-04-14
> **Previous release**: [v1.2.0](RELEASE_v1.2.0.md)

---

## Full Changelog

### Added

- **WPAC Spawn skill** (`g-skl-wpac-spawn`, `@g-wpac-spawn`): spawn a new gald3r project from the current one - creates the project folder in the ecosystem root, installs gald3r (matching current project's install style), seeds it with an optional description/features/code, runs subsystem discovery, and registers bidirectional WPAC topology links in both projects. Supports `--sibling`, `--child`, `--parent`, and `--dry-run`.
- **WPAC Send-To skill** (`g-skl-wpac-send-to`, `@g-wpac-send-to`): transfer files, features, specs, ideas, bugs, or code from the current project to any related project in the topology. Lighter-weight than `g-skl-wpac-move` - works with freshly spawned projects, writes an INBOX notification in the destination, and logs provenance in the source vault. Supports `--type features|code|ideas|bugs|docs|spec`, `--delete-source`, and `--dry-run`.
- Both skills deployed across all 5 IDE trees (`.cursor`, `.claude`, `.agent`, `.codex`, `.opencode`) with full parity.
---

---

## Migration Notes

No breaking changes unless noted above. Review any ### Breaking Changes section above if present.

---

*Generated from [CHANGELOG.md](../CHANGELOG.md) by scripts/backfill_release_files.ps1*