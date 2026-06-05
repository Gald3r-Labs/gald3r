---
subsystem_memberships: [TASK_MANAGEMENT]
---
# g-kamikaze

Alias for `@g-mission`. All-in autonomous loop until a verifiable condition is met: $ARGUMENTS

See `@g-mission` for full documentation.

## Usage

```
@g-kamikaze <condition>
@g-kamikaze <condition> --budget <N>
@g-kamikaze status
@g-kamikaze clear
@g-kamikaze <condition> --until-empty
@g-kamikaze --from-task T{id}
```

This command is identical to `@g-mission` in every way. The name evokes total commitment — burning all available turns toward the stated condition with no retreat.

> Note: `@g-kamikaze` does NOT reduce safety checks or skip verification gates. The name is flavor only. All gald3r safety invariants apply.

**Delegates to**: `@g-mission $ARGUMENTS`
