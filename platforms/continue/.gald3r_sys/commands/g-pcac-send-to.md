Send files, features, specs, ideas, or code to a related project in the ecosystem: $ARGUMENTS

## What This Command Does

Transfers content from this project to any related project (parent, sibling, or child),
writes an INBOX notification in the destination, logs provenance in the source vault,
and optionally deletes the source after confirmation.

Delegates to `g-skl-pcac-send-to`.

## Usage

```
@g-pcac-send-to --parent|--sibling|--child <project_name> [options]
```

**Options:**
- `--what <path>` — file or folder to send (relative to project root)
- `--type features|code|ideas|bugs|docs|spec` — content type (affects destination path)
- `--dest-path <path>` — override destination subdirectory
- `--message "..."` — message to include in INBOX notification
- `--delete-source` — delete source after confirmed copy
- `--dry-run` — preview only, no file operations

## Examples

```
# Send backend features to a sibling project
@g-pcac-send-to --sibling gald3r_valhalla --what .gald3r/features/gald3r_backend --type features

# Send a code folder to a child project
@g-pcac-send-to --child gald3r_payments --what src/payments/ --type code --message "Ready for extraction"

# Forward a feature to the parent template project
@g-pcac-send-to --parent gald3r_dev --what .gald3r/features/feat-012_auth.md --type features

# Dry run preview
@g-pcac-send-to --sibling gald3r_vault --what research/ --type docs --dry-run
```

## Content Type → Default Destination

| Type | Default destination in target project |
|------|--------------------------------------|
| `features` | `.gald3r/features/` |
| `code` | mirrors source structure |
| `ideas` | `.gald3r/IDEA_BOARD.md` (appended) |
| `bugs` | `.gald3r/bugs/` + BUGS.md index |
| `docs` | `docs/` |
| `spec` | `.gald3r/specifications_collection/` |

## What Happens

1. Resolves destination project path (from topology or ecosystem root)
2. Shows a preview of what will be sent
3. Copies files to destination
4. Updates FEATURES.md in destination (if type = features)
5. Appends INBOX notification in destination project
6. Logs provenance in source vault/log.md
7. Offers source deletion (with separate confirmation)

## Companion Commands

| Command | When to Use |
|---------|-------------|
| `@g-pcac-send-to` | Transfer content to an existing project |
| `@g-pcac-spawn` | Create a new project AND transfer content in one step |
| `@g-pcac-move` | Strict topology-gated migration with full pre-flight |
| `@g-pcac-notify` | FYI-only message, no files |
