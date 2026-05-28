List and check the subsystem registry. Activates **g-skl-subsystems**.

```
@g-subsystems                    # sync check (default)
@g-subsystems --status active    # show only active subsystems
@g-subsystems --status all       # show all (active/planned/deprecated)
```

## What it does

| Invocation | Operation |
|------------|-----------|
| `(no args)` | **SYNC CHECK** — audit all task files' `subsystems:` fields against SUBSYSTEMS.md; report missing entries; create stub specs for any without spec files |
| `--status active` | List active subsystems grouped by status |
| `--status all` | List all subsystems (active + planned + deprecated) with min_tier column |

## Related CRUD commands

| Command | Operation |
|---------|-----------|
| `@g-subsystem-add` | Create new subsystem spec + SUBSYSTEMS.md entry |
| `@g-subsystem-upd` | Update subsystem spec fields + Activity Log |
| `@g-subsystem-del` | Deprecate a subsystem |

Activate the **g-skl-subsystems** skill.
