---
name: g-skl-ideas
description: Own and manage IDEA_BOARD.md — capture ideas instantly, review the board, promote to tasks, and run proactive codebase scans for improvement opportunities.
token_budget: low
subsystem_memberships: [PROJECT_IDENTITY_SETUP, VAULT_AND_RESEARCH]
---
# g-ideas

**Files Owned**: `.gald3r/tracking/IDEA_BOARD.md`

**Activate for**: "make a note", "idea:", "remember this", "what if we", "someday", "for later", "eventually", review ideas, idea farm scan.

**Rule**: NEVER auto-promote to task. Capture now, user decides later.

**MCP acceleration (optional — guarded until T493 passes):** When a gald3r MCP server is configured, `capture_idea` can be routed through the MCP adapter (`adapter.capture_idea(content=..., category=..., source=...)`) instead of writing to `.gald3r/tracking/IDEA_BOARD.md` directly. File-first fallback is always required.

---

## Operation: CAPTURE (immediate — do not derail session)

**Trigger phrases**: "make a note", "idea:", "remember this", "what if we", "someday", "for later", "eventually"

1. **Preferred — use the CLI**: `gald3r idea add "<content>" --category <category> [--source <source>]` (this is exactly what `LocalFileAdapter.capture_idea()` runs). No id needs to be pre-computed: `.gald3r/tracking/IDEA_BOARD.md` is a flat markdown journal, and an idea's `idea_id` — the value later passed to `review`/`promote`/looked up via `list` — is simply its 1-based position among all entries in the file. It is derived automatically whenever the board is parsed; the agent never chooses or writes it.

2. **Classify** (free-form label — the CLI accepts any string; default is `general`):
   - `feature` — new capability
   - `monetization` — revenue/pricing
   - `ux` — user experience improvement
   - `technical` — architecture, performance, tooling
   - `architecture` — structural change
   - `business` — strategy, positioning

3. **Manual fallback** (only if `gald3r idea add` truly cannot run) — append directly to `.gald3r/tracking/IDEA_BOARD.md`, matching the CLI's own output byte-for-byte:
   ```markdown
   ## {YYYY-MM-DD} — {category}

   {The idea in 1-3 sentences. Specific enough to reconstruct intent later.}

   _Source: {source}_
   ```
   - The `## {date} — {category}` heading (an em-dash `—`, not a hyphen) is the ONLY structural marker the parser recognizes. There is no `IDEA-NNN` id, no `## Active Ideas` heading, and no `**Status**` field anywhere in the real format.
   - The `_Source: ..._` line is optional — omit it entirely when there is no source to record. (`gald3r idea add`'s own default is `--source cli`, so CLI-captured entries carry a Source line unless `--source ""` is passed.)
   - If `.gald3r/tracking/IDEA_BOARD.md` does not exist yet, create it with the standard header first:
     ```markdown
     ---
     schema_version: "IDEA_BOARD-md-v1"
     type: idea_board
     title: "Idea Board"
     ---
     # Idea Board
     ```

4. **Confirm and continue**: `💡 Captured idea: {content, truncated}` — then resume current work immediately. There is no idea id to report at capture time; it only becomes meaningful the next time the board is listed.

---

## Operation: LIST

`gald3r idea list [--all] [--json]` parses the flat journal and prints one line per idea (promoted ideas hidden unless `--all`):
```
idea-1    technical      What if we cached the provider list?
idea-2    ux             Add dark mode toggle to settings  [promoted -> Task 1]
```
- `idea-N`'s `N` is the entry's 1-based file position — pass the bare number (`1`, `2`, ...) as `idea_id` to `review`/`promote`, not `idea-N`.
- A promoted idea shows a `[promoted -> Task N]` suffix; a reviewed idea shows `[reviewed]` or `[reviewed by X]`.
- `--json` emits every `IdeaRecord` field for scripting: `idea_id`, `category`, `content`, `source`, `created_date`, `promoted`, `promoted_task_id`, `reviewed`, `reviewer`, `review_notes`.

---

## Operation: REVIEW

`gald3r idea review <idea_id> [--reviewer NAME] [-n/--notes "..."]` annotates the entry in place — it never edits or deletes the original idea text:
```markdown
**Reviewed by {reviewer}**: {notes}
```
`reviewer` and `notes` are each independently optional (`**Reviewed**` alone, `**Reviewed**: {notes}` with no reviewer given, or `**Reviewed by {reviewer}**` with no notes). Reviewing the same idea a second time is refused (`already_reviewed`) — the first reviewer's notes are never overwritten.

---

## Operation: PROMOTE

`gald3r idea promote <idea_id> [--title ...] [-d/--description ...] [--type feature|bug_fix|refactor|docs|test|chore] [--priority critical|high|medium|low]`:

1. Creates a task through the same `create_task` path `gald3r task add` uses (single source of truth for task creation) — title/description default to the idea's own content when not given explicitly.
2. Annotates the `IDEA_BOARD.md` entry in place with:
   ```markdown
   **Promoted → Task {N}**
   ```
   The idea text is never deleted, only annotated — the record survives even if the board write fails after the task was already created (surfaced as an error, never silently swallowed).
3. Promoting the same idea a second time is refused (`already_promoted`) — no duplicate task is created.

There is no "shelve" operation and no status vocabulary (`raw` / `evaluating` / `accepted` / `shelved`) anywhere in the real format. `reviewed` and `promoted` are the only two annotations, and they are independent booleans — an idea may be reviewed, promoted, both, or neither.

---

## Operation: FARM (proactive scan)

Scan the codebase for improvement opportunities. Limit 10 new ideas per run. Skip duplicates.

**Pass 1 — Simplification**: files >500 lines, functions >50 lines, nesting >4 levels, repeated patterns
**Pass 2 — Dead code**: unused imports, unreferenced functions, commented-out blocks >10 lines
**Pass 3 — Duplication**: similar signatures, copy-pasted blocks, overlapping skill content
**Pass 4 — Best practices**: bare except/catch, missing type hints, missing tests, N+1 patterns
**Pass 5 — Knowledge gaps**: vault research not applied, IDEA_BOARD ideas now unblocked
**Pass 6 — Skill candidates (T1174)**: scan `.gald3r/reports/skill_candidates/` for stubs staged by `g-hk-agent-complete` and promote filled ones to IDEA_BOARD entries with category `skill_candidate`

**Output format** for each idea found — a normal flat-journal entry (see Operation: CAPTURE). Fold rationale/effort/impact/file pointer into the body text since the real format has no separate structured fields for them:
```markdown
## {YYYY-MM-DD} — {refactor|simplify|performance|security|feature|test|skill_candidate}

{Title}: {Rationale — why this improvement matters}. Files: `{path}` (lines N-M). Effort: {low|medium|high}. Impact: {low|medium|high}.

_Source: idea-farm_
```

**Deduplication**: before adding, check whether an existing entry already references the same file + category — a full-text scan of the body, since there is no structured `Files:`/`Category:` field to match against.

### Pass 6 — Skill Candidate Sweep (T1174)

When `.gald3r/reports/skill_candidates/` exists, perform a dedicated sub-pass:

1. **List stubs**: enumerate `.gald3r/reports/skill_candidates/*.md`
2. **Read frontmatter** `status:` from each:
   - `pending` (default after hook stages it) → stub is unfilled; skip and report count as `awaiting_input`
   - `discarded` → agent reviewed and decided no reusable pattern; move file to `.gald3r/reports/skill_candidates/discarded/`
   - `filled` or `ready` → eligible for promotion to IDEA_BOARD
3. **Promote filled stubs** to `IDEA_BOARD.md` as a single flat-journal entry per stub:
   ```markdown
   ## {YYYY-MM-DD} — skill_candidate

   Skill candidate — {name from stub}: {when_to_use} — {how_it_works} (3-5 lines from stub). Reusable pattern surfaced during task execution; promote via `@g-skill-create` if validated.

   _Source: skill_capture_hook ({stub filename})_
   ```
4. **Move promoted stub** to `.gald3r/reports/skill_candidates/promoted/{filename}` (preserve audit trail)
5. **Summary line**: `Skill candidates: N pending input, M promoted, K discarded`

**Stub format expected** (matches SKILL.md structure per AC5):
```yaml
---
status: pending | filled | ready | discarded
captured_at: YYYY-MM-DD HH:MM:SS
session_id: ...
task_id: ""
---

## name
<kebab-case skill name>

## when_to_use
<one sentence trigger>

## how_it_works
<3-5 lines of procedure>

## example
<minimal example>
```

**Dedup rule for skill candidates**: skip a stub whose `name:` already appears in any existing IDEA_BOARD entry with category `skill_candidate`. The stub still gets moved to `promoted/` to clear the queue.

---

## IDEA_BOARD.md Structure (real, flat-journal format)

```markdown
---
schema_version: "IDEA_BOARD-md-v1"
type: idea_board
title: "Idea Board"
---
# Idea Board

## {YYYY-MM-DD} — {category}

{content}

_Source: {source}_

**Reviewed [by {reviewer}]**[: {notes}]

**Promoted → Task {N}**
```

Entries are appended oldest-first and never reordered or moved between sections — there is no `## Active Ideas` / `## Promoted Ideas` / `## Shelved Ideas` split. `reviewed`/`promoted` are annotations recorded in place on the same entry, which always keeps its original position and content. An idea's `idea_id` is its 1-based position among ALL entries in the file (promoted or not), so an id seen from one `list` call keeps meaning the same entry even after promoted ideas are filtered out of a later un-`--all` listing.

## Idea Identity & Annotations

- **No status field.** There is no `raw` / `evaluating` / `accepted` / `shelved` vocabulary anywhere in the data model (`IdeaRecord`) or the parser. `reviewed: bool` and `promoted: bool` are the only two annotation flags, and they are independent of each other.
- **No `IDEA-NNN` ids.** `idea_id` is derived, not assigned — it is the entry's 1-based position in the file, recomputed fresh every time the board is parsed.
