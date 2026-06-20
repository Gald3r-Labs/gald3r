# Kiro IDE Agent Hooks (`.kiro.hook`)

Kiro IDE uses a **file/event Agent Hook** model that is fundamentally different
from the gald3r canonical agent-lifecycle event set (`session-start`,
`session-end`, `user-prompt-submit`, `tool-start`, `tool-end`, `stop`). It does
**not** delegate to the shared Python core (`g_hk_core.py`) — its hooks are
declarative JSON that ask the agent (or run a shell command) on file events.

## File format

One JSON file per hook with the **`.kiro.hook`** extension (NOT `.json`):

```json
{
  "enabled": true,
  "name": "Hook display name",
  "description": "What this hook does",
  "version": "1",
  "when": { "type": "fileEdited", "patterns": ["src/**/*.ts"] },
  "then": { "type": "askAgent", "prompt": "Natural-language instruction" }
}
```

- `when.type`: `fileEdited` (file events — requires `patterns` glob[]) or
  `userTriggered` (manual/on-demand). Other serialized event strings exposed in
  the Hook UI (File Create/Delete, Prompt Submit, Agent Stop, Pre/Post Tool Use,
  Pre/Post Task Execution) were not documented on the crawled pages — confirm the
  exact `when.type` string before authoring non-`fileEdited` hooks.
- `then.type`: `askAgent` (uses `prompt`) or `command` (shell `Run Command`,
  uses `command`).
- Caveat: `enabled` is currently not honored at runtime (hooks fire regardless)
  — Kiro issue kirodotdev/Kiro#9298.

## Shipped hooks

- `g-hk-kiro-file-change.kiro.hook` — `askAgent` on `.gald3r/**/*.md` edits,
  reminding the agent to keep `TASKS.md` / `BUGS.md` in sync.

## Canonical lifecycle hooks

For agent-lifecycle behavior (session start/end, tool guards, stop), use the
**Kiro CLI** surface — it has real lifecycle hooks in the agent JSON `hooks`
field that delegate to gald3r's shared canonical core. See
`platforms/kiro-cli/.kiro/hooks-impl/README.md`.

Authoritative schema: `skills/g-skl-platform-kiro/PLATFORM_SPEC.md` `## Hook System`.
