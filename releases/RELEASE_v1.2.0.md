> **Released**: 2026-04-11
> **Previous release**: [v1.0.0](RELEASE_v1.0.0.md)

---

## Full Changelog

### Added
- **T087**: Renamed `g-go-verify` ? `g-go-review` across all 20 command targets and 163 reference files; "VERIFY" ? "REVIEW" in command content
- **T088**: Renamed `g-*-cli` ? `g-cli-*` commands (`g-cursor-cli`, `g-claude-cli`, `g-gemini-cli` ? `g-cli-cursor`, `g-cli-claude`, `g-cli-gemini`); renamed matching skill folders (`g-skl-cursor-cli` ? `g-skl-cli-cursor` etc.); 60 command files + 80 skill folders + 10 reference files updated across all targets
- **T084-1**: FEATURES system infrastructure ? `prds/` renamed to `features/`; `PRDS.md` ? `FEATURES.md` with lifecycle statuses (staging ? specced ? committed ? shipped); 35 existing PRD files migrated with smart status mapping; 345 cross-reference files updated
- **T051**: `g-skl-reverse-spec` skill ? 5-pass repo analysis (Skeleton ? Module Map ? Feature Scan ? Deep Dives ? Synthesis); ANALYZE/RESUME/APPLY/STATUS operations; APPLY writes to `.gald3r/features/` staging; reporter-over-editor principle enforced; `g-reverse-spec` command; deployed to all 20 IDE targets

### Changed
- **T209**: `g-go-code-swarm` and `g-go-swarm` now auto-downgrade to standard single-agent implementation when exactly one runnable item remains after Workspace-Control preflight, while preserving hard blockers for unknown workspace members, non-git-root targets, and unauthorized member writes.
- **T084-1**: `g-skl-plan` updated ? "CREATE PRD" ? "STAGE FEATURE" operation; new features default to `status: staging`; FEATURES.md template updated with lifecycle groups; propagated to all 19 IDE targets


---

---

## Migration Notes

No breaking changes unless noted above. Review any ### Breaking Changes section above if present.

---

*Generated from [CHANGELOG.md](../CHANGELOG.md) by scripts/backfill_release_files.ps1*