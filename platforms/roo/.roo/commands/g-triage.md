---
subsystem_memberships: [BUG_AND_QUALITY]
---
# g-triage — External Backlog Intake

Parse unstructured external input (emails, Slack dumps, meeting notes, pasted URLs) and route each item to the correct gald3r destination.

> **Human-gated**: generates a triage table for review BEFORE any `.gald3r/` writes.

## Usage

```
@g-triage "paste your email/Slack/notes here"
@g-triage --file path/to/notes.txt
@g-triage https://github.com/org/repo/issues/42
@g-triage --clipboard     # read from clipboard contents
```

## What It Does

### Phase 1 — Parse & Classify (no writes)

1. Accept input as: inline text block, `--file` path, URL, or `--clipboard`
2. Split input into individual items:
   - Bullet list items (`-`, `*`, `•`, numbered)
   - Paragraph breaks (double newline = new item)
   - Quoted Slack/email threads (parse by sender line if detectable)
3. Classify each item into one of four categories:

| Category | Signals | Route |
|----------|---------|-------|
| `IDEA` | "would be nice", "what if", "consider", "we should eventually", feature requests | → `IDEA_BOARD.md` |
| `BUG` | "broken", "crash", "error", "doesn't work", "regression", "wrong output" | → `BUGS.md` stub |
| `TASK` | "please implement", "we need", "deadline", "by Friday", "action item", "assigned" | → task spec stub |
| `INFO` | status updates, FYIs, meeting recaps with no action | → no write (logged only) |

4. Assign a confidence score (`high` / `medium` / `low`) to each classification
5. For `IDEA` items: propose a one-line IDEA_BOARD summary
6. For `BUG` items: propose severity (`critical` / `high` / `medium` / `low`) based on language signals
7. For `TASK` items: extract title + any deadline signals

### Phase 2 — Triage Table Output (no writes yet)

Display a triage table:

```
## Triage Results — N items found

| # | Category | Confidence | Summary | Proposed Destination |
|---|----------|------------|---------|---------------------|
| 1 | IDEA     | high       | Dark mode toggle for dashboard | IDEA_BOARD — Medium priority |
| 2 | BUG      | high       | Login fails on Safari iOS 17 | BUGS.md — Severity: High |
| 3 | TASK     | medium     | Update pricing page before Monday | Task spec — Priority: High |
| 4 | INFO     | high       | Sprint review scheduled Thu 3pm | No write (info only) |

> **Review the table above. Edit routing if needed, then choose:**
> - `approve all` — write all non-INFO items as proposed
> - `approve N,M` — write only items N and M (e.g., `approve 1,3`)
> - `reclassify N as IDEA` — override classification for item N
> - `discard` — cancel all writes
```

### Phase 3 — Human Gate (HARD STOP)

**DO NOT write to `.gald3r/` until the user responds.** Wait for explicit approval.

Accepted responses:
- `approve all` → write all non-INFO items
- `approve 1,3` or `approve 2` → write only specified items
- `reclassify 2 as TASK` → change item 2's category, re-display table
- `discard` or `cancel` → abort with no writes

### Phase 4 — Writes (after approval)

For each approved item, route to the appropriate skill:

**IDEA items** → activate `g-skl-ideas` CAPTURE operation:
- Title: extracted summary
- Priority: derived from signals (urgent language → high, vague → low)
- Source: `triage` (+ original text excerpt as note)

**BUG items** → activate `g-skl-bugs` REPORT operation:
- Title: extracted summary
- Severity: derived classification
- Note: "Triaged from external input — confirm details before assigning"
- Source excerpt in bug file

**TASK items** → activate `g-skl-tasks` CREATE TASK operation:
- Title: extracted title
- Type: `feature` (default) or `bug_fix` if bug signals present
- Priority: derived from deadline signals
- Note: "Triaged from external input — [source excerpt]"

### Phase 5 — Summary

After writes complete, output:
```
## Triage Complete — N items written

✅ IDEA-NNN: Dark mode toggle for dashboard
✅ BUG-NNN: Login fails on Safari iOS 17 (Severity: High)
✅ Task NNN: Update pricing page (Priority: High)
ℹ️  1 INFO item logged (no write)
```

## Classification Heuristics

**Urgency signals** (elevate priority):
- "ASAP", "urgent", "by EOD", "critical", "blocking", "P0"
- Specific dates within 7 days
- Multiple exclamation points

**Bug signals**:
- Stack traces, error codes, HTTP status codes
- "expected X but got Y"
- "worked before", "regression", "broke after"

**Idea signals**:
- Conditional phrasing: "if we had...", "it would be great if..."
- Competitor comparisons: "like Notion does it"
- "Nice to have", "future", "backlog", "someday"

**Task signals**:
- Assignee names, "please", "can you", "we need"
- Hard deadlines with specific dates
- "action item", "follow up", "I'll need"

## Tips

- Paste a full email thread — the command extracts the actionable items
- Paste a Slack export — items are split by message
- For meeting notes, paste the raw transcript; INFO lines are skipped cleanly
- Use `--file` for long documents (PDFs converted to text, DOCX exports)
- The triage table is editable before approval — reclassify freely

## Related Commands

- `@g-idea-capture` — direct single-idea capture (no triage step)
- `@g-task-add` — direct task creation (no triage step)
- `@g-bug-add` — direct bug report (no triage step)
- `@g-propose` — full proposal generation from a single concept
