---
subsystem_memberships: [BUG_AND_QUALITY]
---
List and review auto-proposed skill drafts, then promote or discard: $ARGUMENTS

Reviews the skill drafts written by `@g-go-review --propose-skill` (T992) into
`.gald3r/proposed_skills/{task_id}_{slug}_draft.md`. **Human-gated** — drafts are never active
until promoted here.

## LIST (default, no args)

1. Scan `.gald3r/proposed_skills/*_draft.md`.
2. For each, show: `{task_id}` · proposed slug · one-line `description` · `proposed_date` · whether a
   same-named skill already exists in `.gald3r_sys/skills/`.
3. If the directory is empty/absent → report "No proposed skills." and exit.

## REVIEW `<task_id|slug>`

1. Display the full draft.
2. Cross-check: does an existing skill already cover this? (overlap warning — defer to
   `g-skl-curator` rubric if unsure).
3. Prompt the human for a decision: **promote**, **revise**, **discard**, or **defer**.

## PROMOTE `<task_id|slug>` (explicit, human-confirmed)

1. Route the draft through the skill authoring flow (`create-skill` / `writing-skills`) for final
   polish (proper `name`/`description`, trigger lines, output format, ≤500-line budget).
2. Write the polished SKILL.md to **`.gald3r_sys/skills/{slug}/SKILL.md`** (canonical source).
3. Run `custom_scripts/platform_parity_sync.ps1 -ApplyFromRoot -Sync` (or the bounded mirror sync)
   so `.cursor/`/`.claude/` receive it — **never** hand-copy a draft directly into a platform dir.
4. Move the draft to `.gald3r/proposed_skills/promoted/` (provenance) and mark the originating
   IDEA_BOARD `IDEA-AUTOSKILL-{task_id}` entry as promoted.

## DISCARD `<task_id|slug>`

Move the draft to `.gald3r/proposed_skills/discarded/` (kept for audit, not deleted) and mark the
IDEA_BOARD entry rejected with a one-line reason.

## Rules

- A `proposed_skills/` draft has `status: proposed` and is **inert** — it is not loaded as a skill
  and is not synced anywhere until PROMOTE runs.
- Promotion always goes through `.gald3r_sys/` (canonical) + parity sync, never a direct platform
  write (consistent with the canonical-source migration).
- This command only ever writes under `.gald3r/proposed_skills/` and (on PROMOTE) `.gald3r_sys/skills/`.
