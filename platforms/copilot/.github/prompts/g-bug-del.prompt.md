Close/archive a bug record. Activates **g-skl-bugs** → CLOSE BUG operation.

```
@g-bug-del BUG-NNN --reason "Won't fix — by design"
@g-bug-del BUG-NNN --resolved "Fixed in TASK-NNN"
```

Marks bug as `[❌] won't fix` or `[✅] resolved` in BUGS.md. Moves bug file to `bugs/archive/`.
Does NOT hard-delete — audit trail preserved.
