Update an existing subsystem spec. Activates **g-skl-subsystems** → UPDATE SUBSYSTEM operation.

```
@g-subsystem-upd subsystem-name
@g-subsystem-upd subsystem-name --field status --value active
@g-subsystem-upd subsystem-name --add-location "skill: g-skl-features"
@g-subsystem-upd subsystem-name --log "T084-2: g-skl-features skill added"
```

Updates spec file fields (status, dependencies, locations). Appends to Activity Log.
SUBSYSTEMS.md index row updated if status or name changes.
