---
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
# @g-ship — Ship a Release

Ship the current [Unreleased] content as a versioned release.

## Usage

```
@g-ship major    — Breaking changes, reframe, new architecture
@g-ship minor    — New features, additive
@g-ship patch    — Bug fixes, small extensions
@g-ship status   — Show current version and [Unreleased] content
```

## What It Does

1. Shows the current `[Unreleased]` CHANGELOG section
2. Calculates the new version number (MAJOR.MINOR.PATCH)
3. Asks for a short theme/title for the release (optional)
4. Promotes `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`
5. Writes a new empty `[Unreleased]` at the top
6. Bumps the `VERSION` file
7. Updates the README version badge if present
8. Creates a focused commit: `release: vX.Y.Z`
9. Creates an annotated git tag: `vX.Y.Z`
10. Asks: Push to remote?
11. Asks: Create GitHub release?

## Semver Guide

| Type | When to use | Example |
|---|---|---|
| `major` | Users must change how they work after upgrading | New install structure, renamed commands |
| `minor` | New capabilities added, nothing existing breaks | New skill, new command, new subsystem |
| `patch` | Fixes and small improvements only | Bug fix, extended existing function, doc update |

## Activation

Follow `g-skl-ship` skill — BUMP operation.

## Related

- `@g-git-push` — prompts for ship if `[Unreleased]` is non-empty
- `g-skl-tasks` COMPLETE — adds entries to `[Unreleased]` automatically
- `g-skl-bugs` FIX — adds `### Fixed` entries to `[Unreleased]` automatically
