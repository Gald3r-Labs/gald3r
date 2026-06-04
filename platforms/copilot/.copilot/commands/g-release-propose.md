---
name: g-release-propose
description: Analyze completed tasks and propose the next semantic version bump + draft release notes. Creates releases/pending/RELEASE_PROPOSAL_vX.Y.Z.md for human review.
subsystem_memberships: [RELEASE_AND_VERSIONING]
---

# @g-release-propose

Activate `g-skl-release` PROPOSE operation.

## What this does

Reads the task backlog since the last release tag to determine the appropriate semantic
version bump (PATCH / MINOR / MAJOR), then drafts a release proposal file for review.

## Usage

```
@g-release-propose
@g-release-propose --from v1.6.0      # explicitly set the base version
@g-release-propose --bump minor       # override the auto-detected bump level
```

## Output

- Creates `releases/pending/RELEASE_PROPOSAL_v{next}.md`
- Prints: "Ready to cut v{next}? Edit the draft or run `@g-release-cut` to accept."

## Agents PROPOSE. Humans APPROVE.

The proposal is advisory. The human reviews the version and notes, edits if needed,
then runs `@g-release-cut` to accept. Delete the proposal file to reject entirely.

## See also

- `@g-release-cut` — accept a proposal and cut the release tag
- `@g-release-publish` — graduate accumulated releases to _test or public tier
- `g-skl-release` PROPOSE operation for full bump logic documentation
