---
description: Agents must update CHANGELOG.md and README.md when completing user-facing feature tasks
globs: ["**/*.md", "**/*.mdc", "**/*.ps1", "**/*.json"]
alwaysApply: true
---

# Rule: Update Documentation at Feature Boundary

When completing any task that **adds, removes, or changes user-facing behavior** — skills, commands,
hooks, agents, rules, conventions, or any element visible to end-users — the completing agent MUST:

## 1. Append to CHANGELOG.md

Add an entry under the `[Unreleased]` section using Keep a Changelog format:

```markdown
### Added
- Feature description with relevant command/file names

### Changed
- What changed and what it replaces

### Removed
- What was deprecated or removed
```

- Place the entry in the appropriate subsection (`Added`, `Changed`, `Removed`)
- Be specific: include command names, file paths, or skill names
- One entry per logical change (not one per file)

## 2. Update README.md (If Relevant Section Exists)

If the completed task changes something that has a section in `README.md`:
- Update the relevant section to reflect the new state
- Update counts in the "What's Included" table if agents/skills/commands count changed
- Update command names if they were renamed

## What Qualifies as "User-Facing"

**YES — must update docs:**
- New command, skill, agent, hook, or rule
- Renamed/deprecated command, skill, agent
- Changed behavior of an existing command
- New convention that agents must follow
- New configuration option

**NO — can skip:**
- Internal refactor with no behavior change
- Task file updates (TASKS.md, individual task specs)
- Bug fix with no interface change
- Code comments or inline documentation

## Where to Update

| Project type | CHANGELOG.md | README.md |
|-------------|--------------|-----------|
| gald3r_dev (this repo) | `CHANGELOG.md` at root | `README.md` at root (contributor view) |
| gald3r_template_full/ | `gald3r_template_full/CHANGELOG.md` | `gald3r_template_full/README.md` (end-user view) |
| Installed gald3r project | `CHANGELOG.md` at project root | `README.md` at project root |

## Timing

- Update docs **before** marking the task `[🔍]` (awaiting verification)
- Docs check is part of the `g-go` and `g-go-code` post-task checklist
