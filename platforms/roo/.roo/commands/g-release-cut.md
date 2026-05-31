---
name: g-release-cut
description: Accept a release proposal (or create one directly), cut a git tag locally, and commit the RELEASE_vX.Y.Z.md file. Does NOT push to remote.
subsystem_memberships: [RELEASE_AND_VERSIONING]
---

# @g-release-cut

Activate `g-skl-release` CUT operation.

## What this does

Accepts a release proposal from `releases/pending/`, cuts a local git tag, commits
the `RELEASE_v{version}.md` file, and promotes CHANGELOG `[Unreleased]` to the release version.

## Usage

```
@g-release-cut                                        # picks up the latest pending proposal
@g-release-cut --proposal releases/pending/RELEASE_PROPOSAL_v1.7.0.md
@g-release-cut --version 1.7.0 --bump minor          # no proposal file needed
```

## What happens

1. Reads proposal (or uses flags to determine version)
2. Writes `releases/RELEASE_v{version}.md` via `g-skl-release WRITE_RELEASE_FILE`
3. Updates `CHANGELOG.md`: promotes `[Unreleased]` → `[{version}] - {date}`
4. Runs `git tag v{version}` locally
5. Commits: `release: v{version}`
6. Prints push and graduation instructions — does NOT push automatically

## Does NOT push

Push is always explicit:
```
git push origin v{version}
# or graduate to _test:
scripts/graduate_to_test.ps1 -Version {version}
```

## See also

- `@g-release-propose` — generate a proposal before cutting
- `@g-release-publish` — graduate to _test or public tier
- `@g-ship` — alternative: full SemVer bump + tag in one step (g-skl-ship)
