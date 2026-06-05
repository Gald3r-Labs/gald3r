---
subsystem_memberships: [MEMORY_AND_KNOWLEDGE]
---
# g-skl-memory

> Human-facing companion to `SKILL.md`. The LLM agent reads `SKILL.md`; this
> page is for developers browsing the skill library on GitHub.

## What it does

Captures structured insights, session summaries, and cross-session semantic search via the **example_app** MCP backend.

Two modes:

- **Full mode** (adv tier) — requires the example_app Docker backend. Calls `memory_capture_insight`, `memory_capture_session`, `memory_search`, `memory_search_combined`. Semantic recall across sessions.
- **Degraded mode** (no backend) — automatically falls back to `g-skl-learn` for file-based capture into `.gald3r/learned-facts.md`. No semantic search, but session insights still persist.

## When to use

- Capturing important mid-session decisions
- Storing reusable how-to procedures the team should remember
- Searching what was decided in past sessions
- End-of-session summaries that should outlive the conversation
- "what did we decide", "remember this", "what was the conclusion"

## Trigger phrases

```
capture insight | remember this | store memory | search memory
what did we decide | cross-session memory | capture session | memory search
@g-memory
```

## Examples

### Capture a single insight

```
memory_capture_insight(
  category="architecture",
  topic="install pipeline",
  insight="bin/install.js writes gald3r-skills-lock.json after copying platform dirs"
)
```

### Capture a session summary at the end of work

```
memory_capture_session(
  summary="Implemented T1043, T1045, T1046 skills-lock-harvest tasks. "
          "T1042 deferred (ai_safe:false). T1044 pilot scope only.",
  topics=["skills-lock-harvest","skills-lock","installer","parity-sync"]
)
```

### Search past decisions

```
memory_search(query="why did we pick SHA-256 over BLAKE3 for lock hashes")
```

## Tier matrix

| Operation                  | adv (Docker) | full / slim (no Docker) |
|----------------------------|--------------|--------------------------|
| `memory_capture_insight`   | MCP backend  | falls back to `g-skl-learn` file capture |
| `memory_search`            | semantic     | not available — use `grep` over `learned-facts.md` |
| `memory_capture_session`   | MCP backend  | file fallback                            |

## See also

- `g-skl-learn` — the file-based fallback this skill degrades into
- `g-skl-vault` — vault notes (long-form knowledge cards), complementary surface
- `example_app` — the MCP backend that provides full-mode capability
