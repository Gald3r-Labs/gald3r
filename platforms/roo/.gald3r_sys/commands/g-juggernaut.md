---
subsystem_memberships: [TASK_MANAGEMENT]
---
# g-juggernaut

Alias for `@g-mission`. Unstoppable autonomous loop until a verifiable condition is met: $ARGUMENTS

See `@g-mission` for full documentation.

## Usage

```
@g-juggernaut <condition>
@g-juggernaut <condition> --budget <N>
@g-juggernaut status
@g-juggernaut clear
@g-juggernaut <condition> --until-empty
@g-juggernaut --from-task T{id}
```

This command is identical to `@g-mission` in every way. The name evokes unstoppable forward momentum — once launched, it does not stop until the condition is provably satisfied or the turn budget is exhausted.

**Delegates to**: `@g-mission $ARGUMENTS`
