# Hook: g-hk-pre-skill-timing

Example reference hook for the **`pre_skill`** lifecycle event (T1055). Demonstrates
per-skill timing/tracing without modifying any skill body.

## Fires On

The gald3r-internal **`pre_skill`** lifecycle event, immediately before a gald3r
skill body executes. `pre_skill` is a **gald3r-internal** lifecycle point, not a
native Cursor / Claude Code harness event — neither IDE exposes a skill-boundary
event. It is dispatched by the gald3r skill/command runner or fired manually, and
is therefore **not auto-wired** into `hooks.json` under a harness event name (the
`_doc.gald3r_lifecycle_events` block in `hooks.json` documents this distinction).
The payload arrives on stdin as JSON and SHOULD carry `skill_name`, `skill_path`,
and `timestamp`.

## What It Does

Parses the skill-event payload, then stages a per-skill start marker
(`.gald3r/logs/skill_timing_<skill>.json`) recording the start timestamp and an
epoch-ms stamp. The companion `g-hk-post-skill-timing` hook reads this marker to
compute elapsed time. Non-blocking by design.

## Side Effects

- Writes `.gald3r/logs/skill_timing_<skill>.json` (start marker, consumed by the
  post_skill hook).
- Appends a `pre_skill | skill=... | path=...` line to
  `.gald3r/logs/skill_lifecycle.log`.
- Always returns `{ continue = true }` and exits 0 — never blocks skill execution,
  never touches control-plane state (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1055 — Add plugin lifecycle hooks (pre/post skill/session) to the gald3r hooks
  system. This is the `pre_skill` reference example.
- Companion: `g-hk-post-skill-timing` (closes the timing record).
- Pattern: `commands/g-create-hook.md` (event list + scaffolding contract).
