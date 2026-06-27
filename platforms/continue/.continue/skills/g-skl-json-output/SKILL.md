---
name: g-skl-json-output
description: Emit gald3r command output (status, review, backlog) as structured JSON for scripting, CI gates, dashboards, and agent-to-agent handoff. Operations SERIALIZE, SCHEMA, VALIDATE, EXPORT. Invoked by --json flag commands (T1381). Mirrors g-skl-html-output. Coordination state files stay markdown.
token_budget: low
subsystem_memberships: [UI_AND_OUTPUT]
---
# g-skl-json-output

Centralized JSON serialization for gald3r **human/machine-facing reports**. The
`--json` flag commands (`g-status`, `g-go-review`, `g-go-code` — T1381) route here.
Parallel to `g-skl-html-output` (T1316).

## When to Use
- A command was invoked with `--json` (or AGENT_CONFIG `output_format: json`).
- A CI gate, dashboard, or another agent needs to parse status/review/task data
  without screen-scraping markdown.

## Boundary (HARD)
JSON output is for **reports**, not coordination state. `TASKS.md`, `BUGS.md`,
`CONSTRAINTS.md`, task specs, and any `.gald3r/` control-plane file remain markdown
(they are the source of truth; JSON is a derived view).

## Envelope (all outputs)
```json
{
  "gald3r_version": "1.2.0",
  "generated_at": "2026-05-20T21:30:00Z",
  "command": "g-status",
  "schema": "status",
  "data": { }
}
```
- `gald3r_version` — from `.gald3r/.identity` (`gald3r_version=`), else `unknown`.
- `generated_at` — ISO-8601 UTC.
- `command` — the invoking command.
- `schema` — output type id (`status` | `review` | `backlog`).
- `data` — the payload (schema-specific).

## Operations

### SERIALIZE `<schema> <data>`
Wrap the command's collected data in the envelope. Emit valid JSON (2-space indent
by default; `--compact` for minified). Never JSONL unless the command naturally
streams multi-record output.

### SCHEMA `<schema>`
Emit the JSON Schema (draft-07) for an output type. Reference shapes:
- `status.data`: `{ project, project_type, counts:{open,in_progress,awaiting,completed,bugs}, top_tasks:[{id,title,priority,status}], constraints_active:int }`
- `review.data`: `{ verdict, findings:[{severity,title,detail,location}], files_reviewed:int, per_task:[{id,result,evidence}] }`
- `backlog.data`: `{ tasks:[{id,title,priority,status,type}], totals:{by_status:{},by_priority:{}} }`

### VALIDATE
Parse the produced string (must be valid JSON); confirm the envelope keys exist and
`data` conforms to the named schema. Abort EXPORT on failure.

### EXPORT
Save under `html_output_dir` (default `docs/`) using `g-rl-01` naming with a `.json`
extension: `YYYYMMDD_HHMMSS_<IDE>_<TOPIC>.json`. Return the path.

Helper: `.claude/skills/g-skl-json-output/scripts/json_output.py`
```powershell
uv run python .claude/skills/g-skl-json-output/scripts/json_output.py `
  -Command g-status -Schema status -DataJson $jsonString -OutDir docs -Topic STATUS
```

## Notes
- `--md`/`--json` override AGENT_CONFIG `output_format` per call; default `markdown`
  is unchanged.
- For swarm review (`g-go-review --json`), `data.per_task[]` wraps each PASS/FAIL
  record with evidence — ideal for a CI gate (`jq '.data.per_task[] | select(.result=="FAIL")'`).
