---
name: g-skl-wishlist-mine
description: Mine a free-form, human-prose intent/wishlist document into formal gald3r task specs — READ-ONLY against the prose doc, dedup against existing tasks, curation discipline (epics for vision, backlog-candidates for unsure). Productizes the DELIVERABLES.md mining pattern.
token_budget: medium
subsystem_memberships: [TASK_MANAGEMENT, MEMORY_AND_KNOWLEDGE]
skill_trust_level: core
---
# g-skl-wishlist-mine — prose wishlist → tasks (READ-ONLY mining)

A user keeps a free-form, human-prose **wishlist / intent document** in their own words — no schema,
no checklist, no required structure. This skill **reads** that document and **mines** concrete,
READY wants into formal task specs, with deduplication against already-tracked work and curation
discipline so the backlog does not flood with half-formed entries.

This is the productized form of the `DELIVERABLES.md` mining pattern: a non-technical user writes
plain-language intent; gald3r turns the READY parts into tracked tasks and reports the rest as
backlog candidates for the owner to prioritize.

**Activate for**: "mine my wishlist", "mine the deliverables doc", "turn my intent doc into tasks",
"what's ready to build from my notes", `@g-wishlist-mine`.

---

## ⛔ HARD RULE — THE PROSE DOC IS READ-ONLY

**The wishlist/intent document is human-owned. This skill MUST NEVER write to it.**

- NEVER rewrite, reformat, restructure, or checklist-ify the prose doc.
- NEVER append, delete, reorder, or "tidy up" its contents.
- NEVER annotate it with task IDs, checkboxes, status markers, or HTML comments.
- NEVER move or rename it.

Mining is a **one-way READ**: prose doc → proposed task specs. The only files this skill is
permitted to create/modify are gald3r task artifacts (via `g-skl-tasks`) and the run report it
emits to the chat. If you find yourself about to edit the prose doc for ANY reason — **stop.**
The owner edits that document; the agent only reads it. (See the DELIVERABLES.md memory note:
"living prose, not a checklist — never checklist-ify; mine tasks FROM it.")

| Rationalization | Reality |
|---|---|
| "I'll just add a checkbox so we can track what's mined" | That destroys the human's prose. Track mined items in the task system, not the doc. |
| "I'll reformat it to make mining easier next time" | The doc's format is the human's choice. Adapt your reading, not their writing. |
| "I'll append the new task IDs at the bottom for reference" | The task files reference the doc, not the reverse. Leave the doc untouched. |

---

## Operation: MINE (default)

### Step 1 — Designate / locate the prose doc

Resolve the document path in this order:
1. **Explicit path argument** — `@g-wishlist-mine <path>` (highest priority).
2. **Configured default** — read `.gald3r/.identity` (or `AGENT_CONFIG.md`) for a
   `wishlist_doc:` key if present.
3. **Convention default** — `.gald3r/DELIVERABLES.md` (the canonical big-picture prose doc),
   else `.gald3r/WISHLIST.md` if it exists.
4. If none found, ask the user: *"Where is your wishlist / intent document? (path)"* — do not guess.

Confirm the resolved path to the user before reading: `📖 Mining (read-only): {path}`.

### Step 2 — Read the prose doc (READ-ONLY)

Read the full document. Treat every line as immutable source. Build a mental model of the
human's intent. Do NOT open it in write mode.

### Step 3 — Extract candidate wants

Scan the prose for distinct *wants* — things the human wishes existed or wants done. For each,
classify its **readiness**:

| Readiness | Signal | Routing |
|---|---|---|
| **READY** | Concrete, scoped, single deliverable; you could write acceptance criteria today | → propose a TASK |
| **VISION** | Broad direction / theme / "someday the whole X should…" spanning many deliverables | → propose ONE epic (not N tasks) |
| **UNSURE** | Vague, ambiguous, missing scope, or needs an owner decision | → report as a BACKLOG CANDIDATE (do NOT create) |

Curation discipline (mirrors `g-skl-ideas` FARM): **do not over-create.** A paragraph of vision
becomes a single epic, never twelve speculative tasks. When in doubt about readiness, route to
backlog-candidate — under-creating is recoverable; flooding the backlog is not.

### Step 4 — DEDUP against existing tasks (MANDATORY)

Before proposing ANY task, deduplicate against work already tracked:
1. Read `.gald3r/TASKS.md` (the index) and scan task titles/summaries.
2. For near-matches, read the candidate task file(s) under `.gald3r/tasks/` to confirm.
3. Drop any candidate whose intent is already covered by an existing task (any status —
   pending, in-progress, awaiting-verification, or completed). A completed task means the want
   is already delivered; note it as "already done" in the report, do not recreate.
4. Borderline overlaps → report under backlog-candidates with a `dup?` flag and the suspected
   existing task ID, rather than silently creating a duplicate.

> Use the Think-in-Code pattern (g-rl-37): if dedup needs ≥3 reads, write one script that loads
> TASKS.md + the prose doc and prints title overlaps, instead of many sequential reads.

### Step 5 — Create the READY tasks + epics

For each surviving READY want (and each VISION epic), create a task via **`g-skl-tasks` CREATE**:
- Title = concise restatement of the want (the human's intent, not the prose verbatim).
- Description = the want + a one-line provenance pointer: `Mined from {doc path} (g-wishlist-mine)`.
- `type:` = `feature` (default) / `epic` for vision items.
- Let `g-skl-tasks` own ID allocation, file placement, and TASKS.md regeneration. This skill
  NEVER hand-edits TASKS.md or task files directly.
- **`--dry-run`**: when set, do NOT create anything — only populate the proposed-tasks table so
  the owner can review before committing.

### Step 6 — WPAC overhead-view routing (optional, AC6)

When this repo is a WPAC **controller** (`.gald3r/workspace/topology.md` present, or a
`workspace_manifest.yaml` declaring members), a mined want may target a member repo rather than
local. The controller mines ONE intent doc and cascades resulting tasks into member repos via the
existing order/direct-write mechanism:

- Tag a mined want with a target repo using the same convention as `g-skl-ideas` `target_repo:`
  (`local` | `<repo_id>` | `[repo_id, …]` | `workspace`). Default `local`.
- To cascade, hand the created task(s) to **`g-skl-wpac-order`** (the `@g-wpac-order` path), which
  writes the task file into `{member}/.gald3r/tasks/`, updates `{member}/.gald3r/TASKS.md`, and
  appends a `[BROADCAST]` entry to the member inbox — the same direct-write authority a controller
  already uses.
- **`--cascade` (T465)**: when the operator passes `--cascade` AND this repo is a WPAC controller,
  the created tasks are auto-dispatched to their `target_repo:` via `@g-wpac-order` at the end of the
  run. The cascade is **controller-tier-gated** — a non-controller never cascades (the gate refuses,
  mirroring `g-skl-wpac-order` "NOT ancestor → warn + abort"). Without `--cascade`, MINE only proposes
  targets and the operator runs `@g-wpac-order` to dispatch (or mines per member repo).
- **Server-triggered runs (T465)**: Throne / the CLI can trigger a mining run server-side via the
  world_tree route `POST /api/v1/planner/wishlist/mine` (`gald3r wishlist mine`, or the Throne
  `mineWishlist` bridge). The route is JWT-gated and tenant-safe, produces the same proposed-tasks /
  backlog-candidates split deterministically, and returns the agent-session dispatch that performs the
  JUDGMENT — it NEVER runs an LLM inline and NEVER writes the prose doc (`doc_modified: false`).

### Step 7 — Emit the report (exact output shape)

Mining ALWAYS ends with two sections — a created-tasks table and a backlog-candidates list:

```markdown
## 🪙 Wishlist Mining Report — {doc path}
Mode: {created | dry-run}   ·   {YYYY-MM-DD}

### Created Tasks
| Task ID | Title | Type | Target Repo | Source (doc anchor) |
|---------|-------|------|-------------|---------------------|
| T### | … | feature | local | "{short quote / heading}" |
| T### | … | epic | example_desktop | "{short quote / heading}" |

### Backlog Candidates (need owner priority)
- **{want}** — why deferred: {too vague / needs scope decision / owner-priority call}. {dup? → T###}
- **{want}** — …

### Skipped (already tracked)
- "{want}" → already covered by T### ({status})

### Summary
Created: N tasks (M epics) · Backlog candidates: K · Skipped as duplicate/done: J
Prose doc: READ-ONLY — not modified.
```

The final line **must** restate that the prose doc was not modified — it is the visible proof of
the READ-ONLY guarantee.

---

## Output Discipline (mirrors a disciplined mining run)

- READY → tasks. VISION → one epic each. UNSURE → backlog candidates (never auto-created).
- Dedup first; never recreate tracked or completed work.
- The prose doc is never written to.
- Non-technical author: the human writes plain language; they need zero gald3r-internal knowledge
  to author the doc. All structure (IDs, schema, status) lives on the gald3r side.

## Related

- Skill: `g-skl-tasks` (CREATE — owns task ID/file/index), `g-skl-ideas` (FARM curation discipline,
  `target_repo:` routing convention), `g-skl-wpac-order` (controller→member cascade).
- Command: `@g-wishlist-mine`
- Rules: `g-rl-37` (think-in-code for dedup), `g-rl-26` (CHANGELOG on user-facing add).
- Task: T453
