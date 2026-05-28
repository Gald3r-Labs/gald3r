---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
# g-gald3r-optimize

**ROOT-ONLY — gald3r_dev maintainer tooling.** Not shipped to external templates (registered in
`custom_scripts/root_only_manifest.yaml` with `gald3r_sys_root_only: true`).

Audit the gald3r system corpus (`.gald3r_sys/skills/*/SKILL.md`, `rules/g-rl-*.md`, `agents/*.md`,
`commands/*.md`) for bloat and produce a ranked pruning report with specific suggested edits.
Activates **g-skl-gald3r-optimize**. Sibling of `@g-compress-memory` (T1053) — same
preserve-always, dry-run-first philosophy, applied to system/config files.

## Usage
```
@g-gald3r-optimize                                 # AUDIT (dry-run) skills + rules + agents + commands
@g-gald3r-optimize .gald3r_sys/skills              # AUDIT a directory
@g-gald3r-optimize --preview <file>                # PREVIEW per-file diff (no writes)
@g-gald3r-optimize --apply <single-file> --confirm # APPLY — one file, confirmed, never bulk
```

## Modes
1. **AUDIT** (default, no writes): runs `gald3r_optimize.ps1 -Mode AUDIT`, ranks files by bloat
   score, and lists the top suggested removals (file, line, reason, text).
2. **PREVIEW** (no writes): `-Mode PREVIEW` — shows the full proposed removal diff for the target.
3. **APPLY** (writes): `-Mode APPLY -Path <single file> -Confirm` — prunes only the auto-removable
   suggestions for that one file, after printing exactly what changes. Never bulk-applies; a
   directory `-Path` is refused.

## Always preserved
Code blocks, command syntax, acceptance criteria, hard rules / enforcement logic, YAML frontmatter,
and URLs are never flagged or removed.

Helper: `.gald3r_sys/skills/g-skl-gald3r-optimize/scripts/gald3r_optimize.ps1`
