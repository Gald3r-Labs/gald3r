# Release Files — Schema Reference

This directory holds per-release `.md` files that define what ships in each version.

## File Naming

```
release{NNN}_{slug}.md
```

- `{NNN}` — zero-padded sequential ID (001, 002, ...)
- `{slug}` — lowercase, hyphenated short name (e.g., `spring-drop`, `vault-refactor`)

## YAML Frontmatter Schema

Every release file must include this frontmatter block:

```yaml
---
id: 001                         # Sequential release ID (integer)
name: 'v1.1 — Spring Drop'     # Human-readable release name
version: '1.1.0'               # SemVer version string
target_date: '2026-04-23'      # Planned ship date (YYYY-MM-DD)
status: planned                 # planned | in_progress | released | deferred
cadence_days: 14                # Days between releases (default: 14 = biweekly)
features: []                   # Free-text feature descriptions included in this release
tasks: []                      # Task IDs assigned to this release (e.g., [42, 55, 61])
notes: ''                      # Freeform notes (blockers, dependencies, announcements)
created_date: '2026-04-09'     # Date this release file was created
released_date: ''               # Actual ship date (filled on release)
---
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | yes | Sequential release ID |
| `name` | string | yes | Human-readable release name |
| `version` | string | yes | SemVer version (e.g., `1.2.0`) |
| `target_date` | date | yes | Planned ship date (`YYYY-MM-DD`) |
| `status` | enum | yes | `planned` / `in_progress` / `released` / `deferred` |
| `cadence_days` | integer | no | Override project default cadence (default: 14) |
| `features` | list | no | Feature descriptions or IDs included |
| `tasks` | list | no | Task IDs assigned to this release |
| `notes` | string | no | Freeform text |
| `created_date` | date | yes | File creation date |
| `released_date` | date | no | Actual release date (filled when shipped) |

## Status Lifecycle

```
planned → in_progress → released
                      → deferred (can reactivate to planned)
```

## Biweekly Cadence Rules

- Default cadence is **14 days** (biweekly)
- Next release target = most recent `target_date` + `cadence_days`
- Override per-release by setting `cadence_days` in the release file
- Project-wide default is configurable in `RELEASES.md`
- The `g-skl-release` skill (Task 052-2) handles cadence calculation — this data model stores raw dates only

## Body Content

After the frontmatter, the release file body can include:

```markdown
# Release {NNN}: {name}

## Included Features
- feat-XXX: {title}
- feat-YYY: {title}

## Included Tasks
- Task {id}: {title}

## Release Notes
{Freeform release notes for changelog/announcement}

## Blockers
- {Any known blockers}
```

## Relationship to Other Files

- `RELEASES.md` — master index of all releases (lives in `.gald3r/`)
- `release_profiles/` — tier definitions (slim/full/adv) that control what ships where
- `CHANGELOG.md` — public-facing change log (root); release notes feed into this
- `PLAN.md` — milestones reference releases when applicable
