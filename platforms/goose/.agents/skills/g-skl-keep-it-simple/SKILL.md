---
name: g-skl-keep-it-simple
description: User-invoked terse mode toggle. Suppresses the active personality pack, response structure scaffolding, and footer metadata so the agent returns bare signal only. Intended for debugging, rapid lookups, and high-volume Q&A sessions where the standard ceremony adds noise. Deactivates at session boundary or on explicit toggle-off.
triggers:
  - "@g-skl-keep-it-simple"
  - "/g-keep-it-simple"
  - "terse mode"
  - "keep it simple"
  - "quiet mode"
token_budget: low
skill_trust_level: core
subsystem_memberships: [AGENT_ORCHESTRATION]
---

# g-skl-keep-it-simple — Terse Mode Toggle

## Purpose

gald3r sessions are verbose by default — the active personality pack
(`gald3r_personality`, Silicon Valley personas, etc.) speaks in character,
responses are structured with markdown headings, and every turn ends with a
metadata footer (model, tokens, cost, tools used, context breakdown).

That ceremony is valuable in normal work but adds friction during:

- Rapid-fire debugging Q&A (50 short questions, one terse answer each)
- One-shot lookups ("what's the env var for X?")
- High-volume batch operations where token budget matters
- Pair-debugging sessions where the user is reading a transcript live
- Any context where "just the answer" is what's wanted

`g-skl-keep-it-simple` is the explicit, user-invoked override for those
contexts. It intentionally conflicts with the always-apply personality rule
and the response-formatting rule and takes precedence over them for the
duration of the activation window.

## Activation

The user types one of:

- `@g-skl-keep-it-simple`
- `/g-keep-it-simple`
- "terse mode" or "keep it simple" as a natural-language opener

The agent acknowledges activation with a single line (no persona, no
formatting) — for example: `Terse mode on.` — and then proceeds with the
work in terse mode for all subsequent turns in the current session.

## Behavior When Active

1. **No persona / character voices.** Even when an `active_personality_pack`
   is set, suppress its voice. No `Gilfoyle says...`, no banter, no
   in-character openers.
2. **No response structure scaffolding.** No top-level markdown headings,
   no preamble like "Here's what I'll do…", no "## Plan" / "## Steps"
   sections. Bullets and tables only when the content genuinely is a list
   or a comparison and prose would be harder to read.
3. **No footer metadata.** Skip the `---` separator + model / token /
   cost / tools-used / context-breakdown block entirely.
4. **No meta-commentary.** Skip "I'll now…", "Let me…", "Great question",
   and similar conversational filler. Answer the question. Stop.
5. **Code is code.** Code blocks and inline backticks remain — this is
   not a "no markdown at all" mode; it's a "no decorative markdown" mode.
6. **Aim for ≤5 sentences per textual answer** unless the answer is
   primarily a code block, command, or table.
7. **Tool calls still happen.** Terse mode affects output presentation,
   not internal tool use. Hooks, PCAC checks, and gald3r system gates
   continue to fire as normal.
8. **All gald3r safety gates still fire.** Bug-discovery gate, todo-
   completion gate, code-change-requires-task gate, member-marker
   invariant, PCAC inbox gate, Clean Controller Gate, etc. remain in
   force. Terse mode reduces ceremony, not safety.

## Deactivation

Terse mode ends on any of:

- The user types `@g-skl-keep-it-simple off`, `/g-keep-it-simple off`,
  `verbose mode`, `normal mode`, or `chatty mode`.
- A new session begins (terse mode is session-scoped, not persisted
  across sessions — it is intentionally not stored in `.gald3r/.identity`
  or `.gald3r/config/` so it does not leak into automation).
- The user explicitly invokes a command whose behavior cannot be terse
  (`@g-go`, `@g-status`, `@g-medic`, `@g-mission` — these commands have
  their own structured output requirements). When the command finishes,
  terse mode resumes.

When deactivating, acknowledge with a single line — for example:
`Terse mode off.` — then resume normal behavior.

## Interaction With the Active Personality Pack

The personality pack rule (`silicon_valley_personality.md` /
`gald3r_personality.md` / equivalent) is an always-apply rule that
normally fires on every response. `g-skl-keep-it-simple` is an explicit
user override on top of that rule. The precedence order is:

1. Hard safety gates (PCAC conflict, Clean Controller Gate, secrets
   detection) — never suppressed.
2. `g-skl-keep-it-simple` activation — suppresses presentation rules.
3. Personality pack — applies when (2) is not active.

`g-skl-keep-it-simple` does NOT modify, delete, or swap the active
personality pack. It only suppresses the personality output for the
duration of the activation window. On deactivation, the same pack
resumes seamlessly.

## Activation Window Persistence

Terse mode is session-scoped only. It is intentionally NOT persisted to:

- `.gald3r/.identity` (would affect every future session silently)
- `.gald3r/config/AGENT_CONFIG.md` (same problem)
- vault memory notes (would propagate across machines)

If a user wants terse mode permanently, they should swap to a terse
personality pack via `@g-pers-pick <pack-id>`, not via this skill.

## Companion Command

`@g-keep-it-simple` (or `/g-keep-it-simple`) is the command wrapper. See
`.gald3r_sys/commands/g-keep-it-simple.md`.

## Source

Created per user request (Task 1052, 2026-05-13). Intentional conflict
with the always-apply personality rule is by design. See README.md for
the human-facing motivation and ecosystem context.
