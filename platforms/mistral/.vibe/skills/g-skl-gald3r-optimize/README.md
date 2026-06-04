# g-skl-gald3r-optimize

Audit the gald3r **system corpus** (`.gald3r_sys/skills/*/SKILL.md`, `rules/g-rl-*.md`,
`agents/*.md`, `commands/*.md`) for bloat and produce a ranked pruning report with specific
suggested edits — while never touching code blocks, command syntax, acceptance criteria, hard
rules, frontmatter, or URLs. The framework-corpus counterpart of
[g-skl-compress-memory](../g-skl-compress-memory/) (T1053): same preserve-always, dry-run-first
philosophy, applied to system/config files instead of memory files.

**ROOT-ONLY:** gald3r_dev maintainer tooling. Registered in `custom_scripts/root_only_manifest.yaml`
with `gald3r_sys_root_only: true` — never propagated to external `gald3r_template_*` repos.

## Quick start

```bash
# AUDIT (read-only) — ranked bloat report + top suggested removals
pwsh -File scripts/gald3r_optimize.ps1 -Mode AUDIT -Path .gald3r_sys/skills
pwsh -File scripts/gald3r_optimize.ps1            # default: scans skills, rules, agents, commands

# PREVIEW (read-only) — per-file diff of proposed removals
pwsh -File scripts/gald3r_optimize.ps1 -Mode PREVIEW -Path .gald3r_sys/rules/g-rl-33-enforcement_catchall.md

# APPLY (writes) — ONE file at a time, requires -Confirm, never bulk
pwsh -File scripts/gald3r_optimize.ps1 -Mode APPLY -Path .gald3r_sys/skills/g-skl-foo/SKILL.md -Confirm
```

## Bloat signals (weighted)

| Signal | Trigger | Weight | Auto-removable |
|---|---|--:|---|
| `rationalization_table_overflow` | Rationalization/Reality table > 5 rows | 3 | yes (drop rows past first 3) |
| `skill_over_400_lines` | SKILL.md > 400 lines | 4 | no (manual — move to `reference/`) |
| `near_identical_enforcement` | rule file with > 3 near-identical enforcement lines | 3 | yes |
| `multiple_background_sections` | agent file with > 2 `## Background`/`## Context` | 2 | yes |
| `backref_filler` | "As mentioned above…" / "As noted in…" line | 1 each | yes |
| `duplicate_acceptance_criteria` | same criterion across two subsystem files | 2 | no (reported) |

Bloat score = weighted sum of detected signals; files are ranked highest-first.

## Always preserved

Fenced code blocks · command syntax (`@g-*`/`/g-*`) · acceptance criteria · hard rules
(`HARD RULE`/`MANDATORY`/`MUST NOT`/`NEVER`) · YAML frontmatter · URLs. A suggested removal is only
ever a redundant prose line.

## Safety

- AUDIT (read-only) is the default when `-Mode` is omitted.
- APPLY operates on a single file, requires `-Confirm`, and refuses a directory `-Path`.
- Flag-only signals (e.g. SKILL.md > 400 lines) are never auto-applied.

Command: `@g-gald3r-optimize`. Skill spec: `SKILL.md`. Source task: T1054.
