Deprecate a constraint. Activates **g-skl-constraints** → DEPRECATE operation.

```
@g-constraint-del C-NNN
@g-constraint-del C-NNN --reason "Superseded by C-NNN"
```

Marks constraint as `status: deprecated` in the Constraint Index and definition block. Does NOT remove the constraint definition (audit trail preserved). Appends to Change Log. Requires explicit user approval.
