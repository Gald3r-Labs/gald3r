---
subsystem_memberships: [WORKSPACE_COORDINATION]
---
Spawn a new gald3r project from this project with full setup and WPAC topology linking: $ARGUMENTS

## What This Command Does

Creates a new project in the same ecosystem root, installs gald3r (matching this project's
install style), seeds it with the provided description/features/code, runs gald3r-setup
subsystem discovery, and immediately registers the WPAC topology link in both projects.

Delegates to `g-skl-wpac-spawn`.

## Usage

```
@g-wpac-spawn <new_project_name> --sibling [options]
@g-wpac-spawn <new_project_name> --child [options]
@g-wpac-spawn <new_project_name> --parent [options]
```

**Options:**
- `--description "..."` — one-line mission for the new project
- `--features <path>` — features subfolder to transfer (e.g. `.gald3r/features/gald3r_backend`)
- `--code <path>` — code folder(s) to copy into the new project
- `--template slim|full|adv` — gald3r template tier (default: matches current)
- `--dry-run` — preview only, no changes

## Examples

```
# Create a sibling backend project seeded with backend features
@g-wpac-spawn gald3r_valhalla --sibling --description "Single-user Docker backend" --features .gald3r/features/gald3r_backend

# Create a child project for a payment subsystem with code
@g-wpac-spawn gald3r_payments --child --description "Payment processing" --code src/payments/

# Dry run to preview what would be created
@g-wpac-spawn gald3r_analytics --sibling --description "Analytics service" --dry-run
```

## What Happens

1. Validates ecosystem root and checks new project name doesn't conflict
2. Detects current project's gald3r install style (symlink vs copy)
3. Creates new project folder + git repo
4. Installs gald3r (rules, skills, templates) matching current project's style
5. Generates `.gald3r/.identity`, `PROJECT.md`, `PLAN.md`, `TASKS.md`, and all scaffolding
6. Transfers features/code (if specified) and builds FEATURES.md index
7. Runs subsystem discovery on transferred content
8. Initializes WPAC topology in both projects (bidirectional)
9. Creates initial git commit in new project
10. Asks about source cleanup (keeps originals until confirmed)

## Companion Commands

| Command | When to Use |
|---------|-------------|
| `@g-wpac-spawn` | Create a new project from this one |
| `@g-wpac-send-to` | Transfer content to an existing related project |
| `@g-wpac-adopt` | Link an existing project as a child (no spawn) |
| `@g-wpac-claim` | Link an existing project as a parent (no spawn) |
