# g-constraint-check

Validate the current task or implementation against all active constraints in `.gald3r/CONSTRAINTS.md`.

## When to use

- During `g-go-code` AC gate (step b2) — before marking any item `[🔍]`
- Before claiming a task — confirm no constraint violations in the planned implementation
- When unsure if a proposed change conflicts with project rules

## Steps

1. Read `g-skl-constraints` skill
2. Run the **CHECK** operation

## Output

```
CONSTRAINT CHECK:
  C-001 [file-first vault]: ✅ PASS
  C-002 [obsidian-markdown]: ✅ PASS
  C-009 [10-target-propagation]: ⚠️ POSSIBLE — new skill; confirm all 10 targets created
  ...
```

- `✅ PASS` — no conflict
- `⚠️ POSSIBLE` — touches the area; needs explicit confirmation
- `🚫 VIOLATION` — blocks task completion

## Usage

```
@g-constraint-check
```
