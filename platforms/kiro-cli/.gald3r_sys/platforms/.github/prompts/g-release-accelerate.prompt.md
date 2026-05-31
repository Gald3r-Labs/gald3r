Accelerate a release. Activates **g-skl-release** → ACCELERATE operation.

```
@g-release-accelerate 002 --days 7        # pull release 002 in by 7 days
@g-release-accelerate 002 --date 2026-05-01   # retarget to an explicit date
```

Computes `delta = new_date - original_target` and cascades the same delta to every `planned` release whose `target_date` is after the accelerated release's original target. Rewrites affected release files, updates `RELEASES.md` rows, and appends a `## Schedule Changes` entry to the accelerated release body.

Refuses to accelerate a release that is not in `status: planned`. Warns — but proceeds — when a cascade pushes any release target into the past.
