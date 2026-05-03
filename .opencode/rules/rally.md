---
description: Rally task tracking — search, create, update, and comment on team tickets via the Rally REST API. Use when the user asks to log work, post updates to Rally, move tickets, add comments, or check the kanban board.
alwaysApply: false
---

# Rally — Task Tracking System

You are interacting with **Rally**, the OBS team's internal task tracking and kanban board. Use the Rally HTTP API to search, create, update, comment on, and manage work items.

## Configuration

- **Base URL:** `http://10.50.50.60:4001` (override with `$env:RALLY_URL` if set in the environment)
- **Auth:** none (internal network)
- **Content-Type:** `application/json` for all bodied requests

When running `curl`/PowerShell, prefer reading these from environment variables:

```powershell
$env:RALLY_URL  # base URL, e.g. http://10.50.50.60:4001
$env:RALLY_ME   # the current user's person_id (integer)
```

If `$env:RALLY_ME` is not set and the user references "me/my/I", **STOP and ask** "Which Rally person are you?" then look them up in `/api/people` and offer to set the env var.

## Two modes — pick the right one before you act

This rule covers two different kinds of Rally activity. Decide which one applies before doing anything else.

### Mode A — Per-project status updates (the **default** in any gald3r-managed project)

If the user says **"post a status"**, **"update Rally"**, **"log what we did"**, **"push the project status"**, or anything that refers to the *current project* as a whole — you are in this mode. Most asks in a gald3r project will be this mode.

In the Midgard ecosystem (and any other gald3r workspace) **each project owns ONE persistent Rally `note` item — its "tracker"**. Status updates are *comments* on that tracker, not new items. The tracker also has a tag of the form `proj:<project_name>` so per-task work items can cross-reference the project.

Each project's tracker is recorded in `.gald3r/.identity` as:

```
rally_item_id=<int>
rally_tag=proj:<slug>
```

#### Resolving "this project"

1. Walk up from the current working directory looking for `.gald3r/.identity`.
2. Read `project_name`, `rally_item_id`, `rally_tag` from it.
3. If `rally_item_id` is missing → the project is **not yet onboarded**. STOP and ask the user "This project isn't linked to Rally yet. Onboard it now (creates a tracker note + `proj:<slug>` tag)?" — only proceed with `Initialize-RallyProject` after explicit consent.

The PowerShell module does steps 1–2 for you:

```powershell
Get-RallyProjectContext              # returns ProjectName, RallyItemId, RallyTag, IsLinked
Get-RallyProjectItem                 # full Rally item detail for the tracker
Push-RallyProjectStatus -Body "..."  # comment on the tracker
Push-RallyProjectStatus -IncludeGald3rSummary -Body "End-of-session snapshot."
Push-RallyProjectStatus -Body "Blocked on auth schema." -Status blocked
Initialize-RallyProject              # one-time onboarding — creates tracker + tag
```

If the `Rally` module is not available, do the equivalent with raw API calls:

```bash
# Read .gald3r/.identity, then:
curl -X POST "$RALLY_URL/api/items/<rally_item_id>/comments" \
  -H 'Content-Type: application/json' \
  -d '{"person_id":<RALLY_ME>,"body":"Status update markdown..."}'
```

#### Rules for Mode A

- **Never create a new top-level Rally item for "project status."** Always comment on the tracker.
- **Never silently onboard.** If `rally_item_id` is missing, ask first.
- **Always include a gald3r context line** in the comment body when posting an automated/end-of-session status — at minimum the project name, date, and active/verify/blocked counts. `Push-RallyProjectStatus -IncludeGald3rSummary` builds this for you.
- **Keep status comments markdown-formatted** with headings or bullets — these become the audit trail readable from the Rally web UI.
- When pushing status from a gald3r `[🔍] → [✅]` transition or session end, add a short "What changed" section listing task IDs touched.
- The `proj:<slug>` tag should be applied to *any* per-task Rally items created for this project so they show up in tag-filtered queries.

#### Bulk operations across the Midgard ecosystem

If the user asks to "post status for all the gard projects" / "update Rally for every Midgard project" / similar, use the onboarding/sweep script:

```powershell
# One-time onboarding for every sibling project under g:\midgard_ecosystem\
.\powershell\Initialize-MidgardRally.ps1 -EcosystemRoot g:\midgard_ecosystem -WhatIf
.\powershell\Initialize-MidgardRally.ps1 -EcosystemRoot g:\midgard_ecosystem
```

Per-project status sweeps should iterate explicitly — do **not** invent your own loop without showing the user which projects you'll touch first.

### Mode B — Ad-hoc Rally work (the original API surface below)

If the user asks to operate on a *specific Rally item by ID*, search the board, manage Top 3, file a change ticket, attach a file, or do anything not tied to "this project's status" — use the standard endpoints documented below. This is the OBS-team-facing kanban workflow and is unchanged.

## Before you start

- **Always fetch people first** with `GET /api/people` before assigning items — never hardcode person IDs.
- **Always search first** with `GET /api/search?q=<term>` before creating a new item to avoid duplicates.
- **Always fetch tags** with `GET /api/tags` before tagging — reuse existing tags when possible.
- **Resolving "me"**: never guess. Use `$env:RALLY_ME` if set, otherwise ask the user their name and look them up.

## Valid enums

- **Status:** `icebox` → `backlog` → `todo` → `in-progress` → `blocked` → `review` → `done`
- **Priority:** `low`, `medium`, `high`, `critical`
- **Type:** `task`, `note`, `spec`, `change`
- **Change type:** `standard`, `normal`, `emergency`
- **Risk level:** `low`, `medium`, `high`
- **Change status flow:** `draft` → `approved` → `complete` or `cancelled`
- **Change category:** `infrastructure`, `application`, `code`, `process` (`infrastructure` REQUIRES at least one `ci_id`)
- **External link type:** `jira`, `wiki`, `docs`, `other`
- **Item link type:** `related`, `blocks`, `parent`

## Core operations

### Find a person's ID

```bash
curl -s "$RALLY_URL/api/people"
```

Returns active people with `id`, `name`, `team`, `avatar_color`.

### List the current user's work

```bash
curl -s "$RALLY_URL/api/items?assignee_id=$RALLY_ME"
curl -s "$RALLY_URL/api/items?assignee_id=$RALLY_ME&status=in-progress"
curl -s "$RALLY_URL/api/top3?person_id=$RALLY_ME"
```

### Search

```bash
curl -s "$RALLY_URL/api/search?q=SEARCH_TERM"
```

Minimum 2 chars. Returns up to 30 non-archived items with tags.

### Get a single item with full detail

```bash
curl -s "$RALLY_URL/api/items/ITEM_ID"
```

Returns the item plus `links`, `activity`, `comments`, `external_links`, `tags`, `subtasks`, `attachments`.

### Create an item

```bash
curl -X POST "$RALLY_URL/api/items" \
  -H 'Content-Type: application/json' \
  -d '{"type":"task","title":"...","body":"...","status":"backlog","priority":"medium","assignee_id":ID,"created_by_id":ID}'
```

### Update an item (status, priority, assignee, etc.)

```bash
curl -X PUT "$RALLY_URL/api/items/ITEM_ID" \
  -H 'Content-Type: application/json' \
  -d '{"status":"in-progress","assignee_id":ID,"person_id":ID}'
```

**Validation:** moving to `in-progress` or `blocked` REQUIRES `assignee_id`. Always pass `person_id` so the activity log attributes the change correctly.

### Add a comment (markdown supported)

```bash
curl -X POST "$RALLY_URL/api/items/ITEM_ID/comments" \
  -H 'Content-Type: application/json' \
  -d '{"person_id":ID,"body":"Comment text. **Markdown** works."}'
```

Activity is auto-logged via DB trigger. The commenter's `last_active_at` is updated.

### Add an external link (Jira ticket, PR, wiki, docs)

```bash
curl -X POST "$RALLY_URL/api/items/ITEM_ID/external-links" \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://...","label":"Description","link_type":"jira"}'
```

### Tag an item

```bash
curl -X POST "$RALLY_URL/api/items/ITEM_ID/tags" \
  -H 'Content-Type: application/json' \
  -d '{"tag_id":TAG_ID}'
```

Create a new tag only if no existing tag fits:

```bash
curl -X POST "$RALLY_URL/api/tags" \
  -H 'Content-Type: application/json' \
  -d '{"name":"tag-name","color":"#3b82f6"}'
```

### Subtasks

```bash
# Add
curl -X POST "$RALLY_URL/api/items/ITEM_ID/subtasks" \
  -H 'Content-Type: application/json' -d '{"title":"Subtask description"}'

# Toggle complete
curl -X PUT "$RALLY_URL/api/subtasks/SUBTASK_ID" \
  -H 'Content-Type: application/json' -d '{"is_complete":true}'
```

### Attach a file

Allowed extensions: `.pdf, .png, .jpg, .jpeg, .gif, .doc, .docx, .xls, .xlsx, .ppt, .pptx, .txt, .csv, .md` — max 25 MB.

```bash
curl -X POST "$RALLY_URL/api/items/ITEM_ID/attachments" \
  -F "file=@/path/to/file.md" \
  -F "uploaded_by=PERSON_ID"
```

### Set today's Top 3

```bash
curl -X PUT "$RALLY_URL/api/top3" \
  -H 'Content-Type: application/json' \
  -d '{"person_id":ID,"items":[ID1,ID2,ID3]}'
```

Max 3 items. Replaces the person's Top 3 for the date.

## Change management (ITIL-lite, SOC2)

```bash
# Create — infrastructure changes REQUIRE ci_ids[]
curl -X POST "$RALLY_URL/api/changes" \
  -H 'Content-Type: application/json' \
  -d '{"title":"...","body":"...","priority":"medium","assignee_id":ID,"created_by_id":ID,"change_type":"normal","risk_level":"low","change_category":"infrastructure","ci_ids":[1,2],"systems_affected":"...","rollback_plan":"...","scheduled_date":"2026-04-15"}'

# Approve (cannot approve your own — separation of duties)
curl -X POST "$RALLY_URL/api/changes/ITEM_ID/approve" \
  -H 'Content-Type: application/json' -d '{"person_id":APPROVER_ID}'

# Complete
curl -X POST "$RALLY_URL/api/changes/ITEM_ID/complete" \
  -H 'Content-Type: application/json' \
  -d '{"person_id":ID,"outcome_notes":"Deployed successfully","rollback_needed":false}'

# Cancel
curl -X POST "$RALLY_URL/api/changes/ITEM_ID/cancel" \
  -H 'Content-Type: application/json' -d '{"person_id":ID,"reason":"No longer needed"}'
```

**Rules:**
- `normal` changes require a rollback plan and approval by someone other than the creator
- `standard` is pre-approved (auto-approved on creation)
- `emergency` is auto-approved but flagged for post-review
- `change_category=infrastructure` requires at least one linked CI

## Common workflows

### Log completed work
1. Search for duplicates first.
2. Create the item with `status: "done"` and a thorough markdown body.
3. If files/artifacts were produced, write a summary `.md` and attach it.
4. Add relevant tags.

### Create a new task
1. Search for duplicates first.
2. Look up the assignee's ID from `/api/people`.
3. Create with appropriate status and priority.
4. Add subtasks if work breaks into steps.

### Update existing work
1. Search for the item by keyword.
2. Confirm the right item with the user if multiple matches.
3. Update status / add a comment / attach a file as requested.
4. Always pass `person_id` on PUTs so activity is attributed.

## PowerShell shortcut

If the `Rally` PowerShell module is loaded (`Import-Module Rally`), prefer it over raw `curl`:

```powershell
Rally-MyItems
Rally-Search "login timeout"
Rally-Comment -Id 42 -Body "Pushed the fix."
Rally-Move -Id 42 -Status review
Rally-Top3 -ItemIds 42,87,103

# Per-project (Mode A) shortcuts:
Rally-Project                          # show this project's tracker linkage
Rally-Init                             # onboard this project to Rally
Rally-Status -Body "Auth refresh shipped." -IncludeGald3rSummary
```

See `powershell/Rally/Rally.psm1` for the full function list.

## Guidelines

- Use markdown in the `body` field for rich formatting.
- When creating items from a conversation, capture key decisions, context, and technical details — not just a title.
- Default to `status: "backlog"`, `priority: "medium"`, `type: "task"` unless the user specifies otherwise.
- An assignee is required for `in-progress` or `blocked` status.
- When logging completed work, use `status: "done"` and write a thorough body.
- After making changes, briefly tell the user what you posted (item ID + URL pattern: `http://10.50.50.60:4000` is the web UI).
