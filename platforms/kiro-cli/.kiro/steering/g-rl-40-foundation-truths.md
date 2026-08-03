---
description: "Foundation truths — durable corrections for failures that recurred across sessions for 6 months. Read before acting; these override convenience."
globs:
alwaysApply: true
subsystem_memberships: [AGENT_ORCHESTRATION]
---

# Foundation Truths (g-rl-40)

These encode corrections the owner has had to repeat ~5 times across 6 months
because they lived only in per-session agent memory. They are now system rules.

## 1. READ THE SOURCE — the human is not your memory

Every component's origin implementation is on disk. Before asking the owner what
something does, or guessing, READ IT:

| What | Where |
|---|---|
| Engine origin (autopilot, daemon, DB design, valkyries) | `G:\gald3r_labs\gald3r_agent_dev` |
| Templates origin (skills, hooks, scripts, `.gald3r_sys` IP) | `G:\gald3r_labs\gald3r_templates_dev` |
| The clone gald3r_core was built from | `G:\gald3r_labs\gald3r_templates_workspace\gald3r` |
| This repo's installed copy of the IP | `.gald3r_sys/` (gitignored, readable) |

Asking the owner to explain code that exists in these locations is a violation,
not a clarification.

## 2. DB is the source of truth — files are a generated cache

**SQLite (`.gald3r/gald3r.db`) is authoritative for task and bug STATUS
TRANSITIONS.** Those writes go to the DB first; if the DB write fails the
operation refuses and the file is never touched. Everything else is still
file-first and is being converted tier by tier (T489). This section states what
is true TODAY, deliberately — it previously asserted blanket DB authority as
flat fact, which was false for most of the tree and is exactly what BUG-464 was
filed about. Do not restore the blanket wording ahead of the code.

**Authoritative in the DB now** (T489 Tier 1 + 1b, 2026-07-28):
- task status: claim / complete / fail / verify-pass / verify-fail
- bug status: resolve / wontfix
- task/bug creation, acceptance criteria (set + tick), task notes, bug
  severity/notes — DB row committed first, file written after (T499)
- artifact-record creation (`create_subsystem`/`create_feature`/`create_prd`)
  and the PRD status transition inside `revise_prd` (its `status` column only)
  — DB row committed first, file written after (Tier 3 — T501, 2026-07-28)
- `CONSTRAINTS.md` row append (`create_constraint`) — the ONE `documents`-table
  write this tier found with a real Python entry point; DB row committed
  first, file written after (Tier 2 — T500, 2026-07-28)

**Still file-first** — the file is the source of truth; the DB mirrors it:
- `PROJECT.md`/`PLAN.md` (100% prose beyond `schema_version`/
  `gald3r_rel_version`, which are already modeled `documents` columns but
  nothing writes them today) and `SUBSYSTEMS.md`/`FEATURES.md` (their real
  "records" are a markdown TABLE in the body, not a frontmatter field on the
  singleton document — out of a per-row renderer's reach the same way
  `CONSTRAINTS.md`'s table would be, except `CONSTRAINTS.md` has the one
  write path that made flipping it possible; these two do not). A document
  renderer now exists (`artifact_render.render_document_text`, T500, proven
  byte-identical against all 8 real document rows in this repo's tree) but a
  renderer with no write path calling it changes nothing — see the honest
  inventory below.
- `.identity` (key=value lines, no YAML frontmatter at all — confirmed via
  `schema_migrate/engine.py`'s own migration writer, which explicitly skips
  it: "Files without YAML frontmatter ... cannot carry frontmatter schema
  metadata"). Nothing in this codebase writes `.identity` content outside
  first-time scaffold, so there is no write path to flip (T500).
- Two more `documents`-table write paths were IDENTIFIED but NOT converted —
  `schema_migrate/engine.py`'s `invoke_file_migration` (bumps
  `schema_version`/`gald3r_rel_version` frontmatter across 5 document kinds
  during a version migration) and `update_grouped_subsystems_index`
  (regenerates `SUBSYSTEMS.md`'s body index table). Both live in a
  977-line migration-critical module outside T500's file boundary —
  documented by omission, not silently skipped (T500 Agent Notes has the
  full rationale).
- everything else touching a subsystem/feature/PRD file: subsystem
  deprecate, feature promote/rename/archive/update, and any direct PRD field
  edit outside `revise_prd`. These are NOT "not yet flipped" in the Tier 1/2
  sense — they have no Python write function to flip at all; every one of
  them is a human/agent hand-editing the markdown file directly via a skill
  (`g-skl-subsystems`/`g-skl-features`/`g-skl-prds`), so there is no DB-first
  seam for them to go through short of adding that write function first (T501
  Agent Notes has the honest inventory). `supersedes`/`superseded_by` on a
  PRD (written by `revise_prd` itself) are the one exception on an otherwise
  DB-first path: they are not modeled `artifact_records` columns yet, so that
  half of the write stays file-first with a post-write re-sync.
When one of those converts, move it up in this list IN THE SAME CHANGE. Rule and
code must never be left disagreeing — that is this rule's own standing contract.

The `.gald3r/` markdown files remain the portable cache and stay canonical for
everything not listed as authoritative above. When world_tree (Postgres) is
connected, the local DB is the offline cache/sync buffer and API calls go to the
server.

- Query the DB for "open tasks, priority-sorted, dependencies cleared" — do NOT
  brute-read 69 task files to triage. (True regardless of which side is
  authoritative: the DB mirrors everything, so it is always the right thing to
  READ.)
- Update state through the DB API — do NOT hand-edit `TASKS.md`/`BUGS.md` or
  move task files when a DB verb exists.
- Markdown-file editing of state is the FALLBACK for platforms that cannot
  interface with the DB, never the preferred path.

## 3. "GATED" is a procedural flag, not a wall

A task marked GATED/DEFER means "needs the owner's word" — often a one-line
ratification. Check the actual gate text and the actual `dependencies:` status
before declaring anything blocked. Do not hand procedural flags back to the
owner as if they were technical blockers; ask the ratification question
directly, once, with the gate quoted.

## 4. `.gald3r_sys/` is compiled IP — absorb, don't deploy, don't retire blindly

`.gald3r_sys/` content is protected IP meant to be compiled INTO the `gald3r`
binary, never shipped as loose readable files. Component purposes (owner-
confirmed, do not re-derive): `schemas/`+`project_types/` = validation;
`snapshots/`+`migrate_schemas` = the version-upgrade system;
`template_verification/`+`aggregate_subsystems` = the g-medic/doctor repair
system (`aggregate_subsystems` itself was documented but never authored under
`.gald3r_sys/` -- BUG-196 implemented it natively as `gald3r subsystem aggregate`
instead of restoring it there); `_platform_capabilities.json` = platform-template
maintenance; `templates/` = critical. None of these are dead weight.

## 5. Valkyries (`gald3r valk`) are the coordination backbone

The Valkyrie connector replaces file-passing WPAC with live message sync
(agent↔user, agent↔agent) and syncs the local DB to world_tree. It was designed
to run FIRST so the owner can coordinate with a mid-swarm agent via the
hot-inbox (`gald3r inbox`) instead of interrupting. When planning multi-agent
work, bring the valkyrie loop up before long autonomous runs.

## 6. An active milestone steers task selection — check it before hand-picking work

`gald3r task ready` / `task next` / `autoclaim` (T275) machine-enforce this, but
an interactive session picking a task by hand (reading `TASKS.md`, browsing
`.gald3r/tasks/open/`, or just asking "what should I work on") must check the
same signal or it will silently pick lateral work while a mission-critical
milestone queue sits unclaimed:

1. Read `active_milestone:` from `.gald3r/config/AGENT_CONFIG.md`. Blank/absent
   means no milestone is active — proceed exactly as before (priority order).
2. When set, prefer any OPEN task whose `milestone:` frontmatter matches it over
   every other ready task, regardless of that other task's priority. Only fall
   back to lateral (non-milestone) work once every milestone-bound task is
   claimed, completed, or blocked.
3. `gald3r task ready --milestone <name>` / `task list --milestone <name>`
   inspects what a given milestone's queue looks like without changing the
   project's configured `active_milestone:`.

This is a steering signal, not a hard filter — never refuse lateral work
outright, and never invent a milestone value that isn't in `active_milestone:`
or the task's own `milestone:` field.

| Rationalization | Reality |
|---|---|
| "I'll just ask the owner what this does" | The source is on disk. Read it. |
| "GATED — moving on" | Read the gate. It's usually one question. |
| "I'll read the task files to find work" | `SELECT ... FROM tasks WHERE deps cleared ORDER BY priority`. |
| "This .gald3r_sys dir looks like dev junk" | It's the upgrade/medic/platform IP. Look up its purpose. |
| "I'll note this correction for next time" | Notes reset. Encode it in rules/DB/code. |
| "This task looks important, I'll grab it" | Check `active_milestone:` first — a milestone-bound task may be waiting. |
