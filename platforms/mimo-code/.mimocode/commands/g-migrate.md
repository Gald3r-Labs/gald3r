---
subsystem_memberships: [PROJECT_IDENTITY_SETUP]
---
Migrate skill/API interface callers: $ARGUMENTS

## Command: g-migrate

Scans the entire project for callers of a skill or API interface and proposes or applies
updates to match a new interface definition. Closes the "skill upgrade breaks callers"
problem. Pattern from Claude's `/migrate` operation.

## Usage

```
@g-migrate <skill-name> --from "<old-interface>" --to "<new-interface>"
@g-migrate <skill-name> --from "<old-interface>" --to "<new-interface>" --apply
@g-migrate --list-skills
```

## Arguments

| Flag | Description |
|------|-------------|
| `<skill-name>` | Name of the skill/command being migrated (e.g. `g-skl-tasks`) |
| `--from "<old>"` | Old interface string, function name, or invocation pattern to find |
| `--to "<new>"` | New interface string to replace it with |
| `--apply` | Write changes (default: dry-run only) |
| `--list-skills` | List all skill names found in .cursor/skills/ and .claude/skills/ |
| `--scope <path>` | Limit scan to a specific directory (default: entire project) |
| `--report-only` | Generate docs/ migration report without changing files |

## Protocol

### 1. Parse arguments from `$ARGUMENTS`

Extract: `skill_name`, `from_interface`, `to_interface`, flags (`--apply`, `--list-skills`, etc.)

If `--list-skills` is provided:
- List all directories under `.cursor/skills/` and `.claude/skills/`
- Show skill name + description from frontmatter
- Exit

### 2. Validate

- Confirm `<skill-name>` exists in `.cursor/skills/<skill-name>/` or `.claude/skills/<skill-name>/`
- Confirm `--from` value is non-empty
- Confirm `--to` value is non-empty
- If validation fails, print usage and exit with a clear error

### 3. Scan for callers

Search these paths for the `--from` pattern:

```
.cursor/commands/      .claude/commands/
.cursor/skills/        .claude/skills/
.agent/commands/       .agent/skills/
.codex/commands/       .codex/skills/
.opencode/commands/    .opencode/skills/
.copilot/commands/
src/                   scripts/
*.md (root level)      AGENTS.md  CLAUDE.md
```

Use ripgrep-style search (or built-in file scan) for exact string and common invocation patterns:
- `@<skill-name>`, `/<skill-name>`, `g-<skill-name>` invocations
- References like `` `<old-interface>` ``, `"<old-interface>"`, `{<old-interface>}`
- Imports or require statements

**Build a match list**: `[{ file, line, before, after }]`

### 4. Dry-run output (default)

```markdown
## g-migrate Dry-Run: <skill-name>

Migration: "<old-interface>" → "<new-interface>"
Callers found: N files, M occurrences

### Proposed Changes

#### <file-path>
  Line 42:  `<old-interface>` → `<new-interface>`
  Line 87:  `@g-<old-interface>` → `@g-<new-interface>`

#### <file-path>
  Line 12:  `<old-interface>` → `<new-interface>`

---
Run `@g-migrate <skill-name> --from "<old>" --to "<new>" --apply` to apply.
```

If `--report-only` is set, also write this report to `docs/<YYYYMMDD_HHMMSS>_Cursor_MIGRATE_<skill-name>.md`.

### 5. Apply mode (`--apply`)

For each matched file and occurrence:
1. Read the file
2. Replace the `--from` pattern with `--to` (exact string replacement, case-sensitive)
3. Write the file back
4. Log the change

After all replacements:
- Write migration report to `docs/<YYYYMMDD_HHMMSS>_Cursor_MIGRATE_<skill-name>.md`
- Show summary: "Applied N replacements across M files"

### 6. Migration report format

```markdown
# Migration Report: <skill-name>

**Date**: YYYY-MM-DD HH:MM UTC  
**From**: `<old-interface>`  
**To**: `<new-interface>`  
**Status**: Applied | Dry-run

## Summary

- Files changed: N
- Occurrences replaced: M

## Changes by File

### <file-path>
| Line | Before | After |
|------|--------|-------|
| 42 | `<before>` | `<after>` |

### <file-path>
...
```

### 7. Post-migrate checklist

After applying, surface:

```
✅ Migration applied.

Post-migration checklist:
- [ ] Review changed files for semantic correctness (the string was replaced, intent may need review)
- [ ] Run lint/typecheck: e.g. `npx tsc --noEmit` for TypeScript projects
- [ ] Commit: @g-git-commit (type: refactor, reference Task #{task_id})
- [ ] Update CHANGELOG.md if user-facing skill interface changed
```

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| `--from` pattern not found anywhere | Report "0 callers found — nothing to migrate" |
| Same file has multiple matches | Replace all occurrences in one pass |
| Binary files | Skip silently |
| `node_modules/`, `.git/`, `.venv/` | Always skip |
| Regex special chars in `--from` | Treat as literal string (no regex) |

## Examples

```
# Rename a deprecated skill command alias
@g-migrate g-skl-tasks --from "g-task-new" --to "g-task-add"

# Dry-run first, then apply
@g-migrate g-skl-bugs --from "g-bug-report" --to "g-bug-add"
@g-migrate g-skl-bugs --from "g-bug-report" --to "g-bug-add" --apply

# Migrate within a specific directory only
@g-migrate g-skl-pcac-order --from "g-broadcast" --to "g-pcac-order" --scope .cursor/commands/

# List all skills available for migration
@g-migrate --list-skills
```

## Parity

This command must exist in all 5 IDE platform command directories:
- `.cursor/commands/g-migrate.md`
- `.claude/commands/g-migrate.md`
- `.agent/commands/g-migrate.md`
- `.codex/commands/g-migrate.md`
- `.opencode/commands/g-migrate.md`
