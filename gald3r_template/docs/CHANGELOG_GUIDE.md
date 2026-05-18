# Changelog Maintenance Guide

This guide helps you write clean, readable changelog entries when using gald3r's
research and analysis workflow to bring external improvements into your project.

---

## Why This Matters

When gald3r analyzes external codebases or libraries and proposes improvements, the
agent uses specific internal terminology in task frontmatter and skill output. That
language is useful for the agent — but it sounds odd or alarming in a public CHANGELOG
that your team (or the world) might read.

This guide gives you the translation from agent language to clear, user-facing prose.

---

## When to Update Your CHANGELOG

Update `CHANGELOG.md` when you complete a task that:

- Adds a new capability or command
- Changes how an existing feature behaves
- Removes or renames something users interact with
- Fixes a bug that was affecting users

You do **not** need a CHANGELOG entry for:
- Internal task file updates
- Config file tweaks with no behavior change
- Adding or updating `.gald3r/` planning documents

---

## Language Translation Table

When writing CHANGELOG entries, translate agent terminology into plain English:

| Agent / internal term | Plain-language alternative |
|---|---|
| Research review / recon / reverse-spec analysis | External analysis / external codebase review |
| Researched feature / analyzed feature | Feature sourced from external analysis |
| Replacement-class feature | Feature that modifies an existing capability |
| Additive feature | New capability (no existing feature affected) |
| External analysis safety gate | Comparison check before adopting external features |
| Pre-implementation verification | Review step before coding begins |
| Autopilot anti-quitting rule | Agent reliability improvement |
| Cross-project coordination | Multi-project workflow |
| Workspace routing policy | (omit — internal agent configuration) |
| Task frontmatter / task spec | (omit — describe the user-visible outcome instead) |
| BUG-NNN | (describe the fix naturally, e.g. "Fixed: login redirect loop") |
| Agent skipped / blocked task | (omit from public CHANGELOG) |
| Parity sync | (omit unless you're shipping an open-source framework) |

---

## Entry Format

Put new entries under `## [Unreleased]` in one of the four standard sections.

```markdown
## [Unreleased]

### Added
- **Feature name** (`@command`): one sentence describing what it does for you.
  Optional second sentence if context helps.

### Changed
- **What changed** (`@command`): what it does now vs. what it did before.

### Fixed
- **What was broken**: what it was doing wrong and what it does now.

### Removed
- **What's gone**: what you can no longer do and what to use instead.
```

---

## Good vs. Bad Examples

### ✅ Good — describes user outcome

```markdown
### Added
- **External analysis safety gate** (`@g-res-apply`): before scheduling implementation
  work from any external codebase analysis, gald3r now compares the proposed approach
  against your existing implementation and pending work queue. Features that would
  replace something you already have require your explicit confirmation; purely additive
  features proceed automatically.
```

### ❌ Avoid — exposes agent internals

```markdown
### Added
- **T809 — g-skl-res-apply Step 2.5 Existing State Check**: Added harvested_from
  frontmatter field detection. replacement-class tasks now block on harvest_approved
  flag check. APPLY flow reads subsystem specs before writing tasks to TASKS.md.
```

---

## Keeping Version Numbers Current

gald3r uses [Semantic Versioning](https://semver.org/):

| Change type | Version bump |
|---|---|
| New commands, skills, or agents | Minor: `1.2.0 → 1.3.0` |
| Behavior changes or fixes | Patch: `1.3.0 → 1.3.1` |
| Breaking changes or architecture shifts | Major: `1.x.x → 2.0.0` |

When you're ready to publish a version, move entries from `[Unreleased]` to a
dated version header:

```markdown
## [1.3.0] - 2026-05-06
```

---

## Releasing to GitHub

Run `@g-release-publish` to generate a `ROADMAP.md` and structured release notes
from your `.gald3r/releases/` directory. This is separate from CHANGELOG — it
produces milestone-style summaries rather than a per-change log.

---

*Part of the gald3r documentation. See `AGENTS.md` for the full command reference.*
