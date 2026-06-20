---
subsystem_memberships: [AGENT_ORCHESTRATION]
---
# g-skl-keep-it-simple — Terse Mode

A user-invoked toggle that silences gald3r's response ceremony for a
session: no personality voice, no markdown decoration, no footer block.
The agent answers the question and stops.

## Why this exists

gald3r ships with rich response ceremony by default — personality packs,
structured markdown, end-of-turn metadata footers. That ceremony is great
for normal collaborative work but turns into noise in three concrete
scenarios:

- **Rapid Q&A**: 50 short questions in a row, each needing one
  one-sentence answer.
- **Live debugging**: the user is watching the transcript scroll in real
  time and just wants to see the *answer*, not the persona's reaction
  to the question.
- **Token-budget-sensitive work**: long batch operations where every
  hundred decorative tokens compounds.

For those, `@g-skl-keep-it-simple` is the explicit "turn off the
ceremony, just give me signal" toggle.

## How to use

```text
You: @g-skl-keep-it-simple
Agent: Terse mode on.

You: what's the env var for the openrouter base url?
Agent: OPENROUTER_BASE_URL

You: and the default?
Agent: https://openrouter.ai/api/v1

You: @g-skl-keep-it-simple off
Agent: Terse mode off.
```

## What it suppresses

- Personality pack output (Silicon Valley personas, Norse persona,
  any active pack)
- Top-level markdown headings, "## Plan" / "## Steps" scaffolding
- Conversational filler ("Great question", "Let me…")
- The `---` end-of-turn footer with model / tokens / cost / tools-used

## What it preserves

- Code blocks and inline `code`
- Tables and bullets when the data is genuinely tabular or a list
- All gald3r safety gates (PCAC, Clean Controller, bug-discovery, etc.)
- All hook execution

## What it does NOT do

- It does **not** swap the active personality pack — the pack stays
  the active pack; only its output is suppressed for the activation
  window.
- It does **not** persist across sessions — open a new chat and you
  are back to normal verbose mode.
- It does **not** reduce safety — every gald3r gate still fires.

## Deactivation

- `@g-skl-keep-it-simple off` (or `/g-keep-it-simple off`)
- `verbose mode` / `normal mode` / `chatty mode`
- Starting a new session

## Need it permanently?

Swap to a terse personality pack via `@g-pers-pick <pack-id>`. This
skill is meant for transient mode-switching, not durable preference.

## Source

Task 1052 (2026-05-13). IDEA-HARVEST follow-up to the verbosity
conversation that surfaced during the May 2026 personality-pack work.
The intentional conflict with the always-apply personality rule is the
whole point — explicit user override, scoped to one session.

## See also

- Skill: `.claude/skills/g-skl-keep-it-simple/SKILL.md`
- Command: `.claude/commands/g-keep-it-simple.md`
- Related: `@g-pers-pick`, `@g-pers-list`
