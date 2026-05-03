---
description: "Bug-discovery gate — bugs found during implementation are never silently ignored: current-task bugs fixed inline, pre-existing bugs logged with BUG[BUG-{id}] comment"
globs:
alwaysApply: true
---

# Bug-Discovery Gate (Zero-Ignore Policy)

When you encounter a bug during any coding or review session, the correct response depends on when the bug was introduced:

| Scenario | Correct Response |
|----------|-----------------|
| Bug introduced by **current task's code changes** | Fix it immediately (same task, same commit, no new ticket) |
| Bug is **pre-existing** (existed before this task started) | Create BUG entry + add `BUG[BUG-{id}]` comment; do NOT fix inline unless trivial |

**Silently ignoring a bug is never acceptable.**

---

## Step 1 — Determine Bug Origin

> Was the bug introduced by code changes in the *current task*?
> - Check: does the file modification list (or `git diff`) include the lines containing the bug?
> - **YES** → current-task bug
> - **NO** (or unsure) → treat as pre-existing (safer to over-log than under-log)

---

## Step 2A — Current-Task Bug

Fix it in place before marking `[🔍]`.

```
- No new BUG entry needed (it's part of this task's implementation)
- No BUG comment needed (it will be fixed before [🔍])
- If too complex to fix safely this session → treat as pre-existing (log it, move on)
```

---

## Step 2B — Pre-Existing Bug (Mandatory Steps)

1. **Create BUG entry** via `g-skl-bugs` REPORT operation → get `BUG-{id}`
2. **Add annotation** at the bug site (on the line directly above or same line):
   ```
   BUG[BUG-{id}]: {description} — see .gald3r/bugs/bug{id}_{slug}.md
   ```
3. **Do NOT fix inline** unless the fix is:
   - 1–3 lines
   - Zero risk of expanding scope
   - Confirmed by code inspection (not guessed)
   If it doesn't meet all three → log and move on
4. **Notify in session summary**: "Found pre-existing bug BUG-{id}: {title}"

---

## BUG Comment Format (by language)

```python
# BUG[BUG-03]: Off-by-one in page count — see .gald3r/bugs/bug003_page_count.md
total_pages = len(items) / page_size  # should use ceil division
```

```javascript
// BUG[BUG-07]: Race condition on concurrent writes — see .gald3r/bugs/bug007_write_race.md
await saveRecord(data);
```

```typescript
// BUG[BUG-09]: Missing null guard on user.profile — see .gald3r/bugs/bug009_null_profile.md
return user.profile.name;
```

```sql
-- BUG[BUG-12]: NULL guard missing — divide-by-zero possible — see .gald3r/bugs/bug012_null_divide.md
```

```powershell
# BUG[BUG-14]: Path assumes Windows drive letter — see .gald3r/bugs/bug014_path_assumption.md
```

The `BUG[BUG-{id}]` format intentionally mirrors `TODO[TASK-X→TASK-Y]` from `g-rl-34` for a uniform annotation system.

---

## Exemptions

Do NOT report as pre-existing bugs:
- Intentional placeholder values (test fixtures, examples with clearly fake data)
- Linter warnings already tracked as tech debt in BUGS.md
- Cosmetic issues (formatting, whitespace, naming) **unless** they cause incorrect behavior

---

## Integration with g-go-code / g-go-review

**During implementation (g-go-code b2 AC gate)**:
- Any pre-existing bug encountered must have a BUG entry + comment before `[🔍]`
- Bugs introduced by this task must be fixed inline before `[🔍]`

**During verification (g-go-review review step)**:
- Bug introduced by this task → flag as unmet criterion → task FAIL (back to `[📋]`)
- Pre-existing bug discovered → log BUG entry + comment; note in summary; does NOT fail this task
