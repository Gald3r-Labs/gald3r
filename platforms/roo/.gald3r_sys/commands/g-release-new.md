---
subsystem_memberships: [RELEASE_AND_VERSIONING]
---
Create a new release. Activates **g-skl-release** → CREATE operation.

```
@g-release-new "Release Name"
@g-release-new "Release Name" --version 1.2.0
@g-release-new "Release Name" --target 2026-05-15
@g-release-new "Release Name" --cadence 21
```

Creates `.gald3r/releases/release{NNN}_{slug}.md` and appends a row to `RELEASES.md`.

- Next ID = highest in `RELEASES.md` + 1 (zero-padded to 3 digits)
- `target_date` defaults to (most-recent target_date + `cadence_days`); falls back to (today + cadence) for the first release
- `cadence_days` defaults to 14 (biweekly)
- Status starts at `planned`

**Before publishing a release:** run a STRIDE threat model check on any new API surfaces, authentication changes, or data-handling code included in this release. Reference: `@g-skl-code-review` security pass (OWASP Top 10 + STRIDE categories). Document findings in the release file under a `## Security Review` section; mark as `N/A` if the release contains no API/auth/data changes.
