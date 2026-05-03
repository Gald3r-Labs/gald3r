---
name: g-skl-cli-gemini
description: Gemini CLI (gemini command) — authentication, checkpointing, config file, extensions/tools, memory patterns, and cross-use with other agents.
---

# g-skl-cli-gemini — Gemini CLI

Reference docs will live in: `{vault_location}/research/platforms/gemini/` once populated via `@g-ingest-docs`.

## When to Use

- Running Gemini agents from the terminal or scripts
- Long-context tasks (Gemini has a very large context window)
- Cross-agent workflows alongside Cursor/Claude agents
- Tasks requiring checkpointed state across runs

## Authentication

```bash
# Option 1: API key (recommended for scripts)
export GEMINI_API_KEY="your-key-here"
gemini "implement the feature"

# Option 2: Google account (browser-based auth, interactive only)
gemini auth login
```

For CI/overnight use, always use `GEMINI_API_KEY`. The Google account flow requires a browser.

## Config File

Gemini CLI reads `.gemini/settings.json` in the project root:

```json
{
  "model": "gemini-2.0-flash",
  "temperature": 0.1,
  "maxOutputTokens": 8192,
  "extensions": ["./my-tool.js"]
}
```

## Checkpointing

Gemini CLI saves state between runs — useful for long tasks that may be interrupted:

```bash
gemini --checkpoint-dir .gemini/checkpoints "refactor the whole API layer"
gemini --resume-checkpoint .gemini/checkpoints/latest "continue"
```

Checkpoints save the conversation state and tool call history. If a run is interrupted,
`--resume-checkpoint` picks up from the last safe state.

## Extensions / Tools

```bash
# Run with a custom tool
gemini --tool ./scripts/my-tool.js "use my-tool to process the data"
```

Extensions are JavaScript modules that expose functions Gemini can call.
Useful for integrating project-specific utilities.

## Memory and Context Persistence

Gemini does not persist memory automatically between sessions. Recommended patterns:

1. **Manual context injection**: `gemini "context: $(cat CLAUDE.md)" "now implement X"`
2. **Learned facts**: Write session summaries to `.gald3r/learned-facts.md` via `/g-learn`
3. **Session file**: Pass a context file at each run: `gemini --context SESSION.md "task"`

## Cross-Use with Cursor/Claude Agents

- Cursor agents can spawn Gemini for large-context analysis tasks
- Gemini can write results to standard gald3r task files for Cursor to pick up
- Coordinate via `.gald3r/linking/INBOX.md` for structured handoffs

## Vault Reference

Once `@g-ingest-docs` is run for `gemini`, full docs will be at:
`{vault_location}/research/platforms/gemini/`
