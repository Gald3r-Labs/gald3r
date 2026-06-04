Show release status. Activates **g-skl-release** → STATUS operation.

```
@g-release-status                  # summary of all active releases
@g-release-status 002              # detail for release 002
@g-release-status "Spring Drop"    # detail by name
```

**With a release id or name**: renders a per-release table (target_date, days until release, cadence, assigned tasks with task-file statuses, feature count, blocker count).

**Without args**: lists every release with `status ∈ {planned, in_progress}`, highlights overdue targets with `⚠️`.
