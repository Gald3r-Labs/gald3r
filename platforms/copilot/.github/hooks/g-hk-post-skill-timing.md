# Hook: g-hk-post-skill-timing

Example reference hook for the **`post_skill`** lifecycle event (T1055). Closes the
per-skill timing record opened by `g-hk-pre-skill-timing`.

## Fires On

The gald3r-internal **`post_skill`** lifecycle event, immediately after a gald3r
skill body finishes. Like `pre_skill`, `post_skill` is a **gald3r-internal**
lifecycle point (no native Cursor / Claude Code skill-boundary event exists),
dispatched by the gald3r skill/command runner or fired manually, and **not
auto-wired** into `hooks.json`. The payload arrives on stdin as JSON and SHOULD
carry `skill_name`, `skill_path`, and `timestamp`.

## What It Does

Reads the start marker staged by `g-hk-pre-skill-timing`
(`.gald3r/logs/skill_timing_<skill>.json`), computes elapsed milliseconds, removes
the marker, and appends a timing line. If no start marker is present it logs
`elapsed_ms=unknown`. Non-blocking by design.

## Side Effects

- Reads and then deletes `.gald3r/logs/skill_timing_<skill>.json`.
- Appends a `post_skill | skill=... | elapsed_ms=...` line to
  `.gald3r/logs/skill_lifecycle.log`.
- Always returns `{ continue = true }` and exits 0 — never blocks, never touches
  control-plane state (TASKS.md, BUGS.md, task/bug files).

## Related Tasks

- T1055 — Add plugin lifecycle hooks (pre/post skill/session). This is the
  `post_skill` reference example.
- Companion: `g-hk-pre-skill-timing` (opens the timing record).
- Pattern: `commands/g-create-hook.md` (event list + scaffolding contract).
