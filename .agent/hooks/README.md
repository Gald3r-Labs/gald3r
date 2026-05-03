# gald3r Hooks

Hooks extend Cursor IDE behavior at key lifecycle events.

## Active Hooks (hooks.json)

| Hook | Event | Does |
|------|-------|------|
| `session-start.ps1` | Session start | Injects "gald3r is active + check TASKS.md" into every session. Handles first-time user setup. Auto-heals `.gald3r/.project_id`. |
| `agent-complete.ps1` | Agent stop | Writes a local chat transcript to `.gald3r/logs/` and a session reminder for next session if 5+ turns occurred. |
| `validate-shell.ps1` | Before shell | Blocks dangerous commands (`rm -rf /`, `format c:`, etc). |
| `g-setup-user.ps1` | Called by session-start | Interactive first-time user identity setup. |

## Corporate / Security-Restricted Environments

Cursor hooks spawn PowerShell processes and can trigger endpoint security alerts
(SentinelOne, CrowdStrike, etc.) due to base64 payloads and child process creation.

**To disable all hooks:**

Replace `hooks.json` with an empty hooks object:

```json
{
  "version": 1,
  "hooks": {}
}
```

gald3r works without hooks — you just won't get the auto-injected context reminder
or the local chat transcripts in `.gald3r/logs/`. Add `@g-setup` or check
`.gald3r/TASKS.md` manually instead.

## What Was Removed (available in gald3r_dev)

The following hooks require the Docker MCP backend and are not included in gald3r lite:

- `cursor_adapter.py` / `claude_adapter.py` — MCP memory ingestion
- `heartbeat-scheduler.ps1` — Scheduled agent routines
- `vault-*.ps1` — Vault sync and search
- `sync-client.ps1` — WebSocket sync to MCP server
- `file-index-rebuild.ps1` — PostgreSQL file index
- `audit.ps1` — Tool call logging (also a SentinelOne trigger)

## Local Chat Logging In gald3r Slim

gald3r slim now keeps a local copy of chat history without Docker MCP.

- The `stop` hook calls the shared `.cursor/hooks/g-hk-cursor-chat-logger.py`
- If the platform provides a transcript path, that file is used directly
- Otherwise the logger falls back to the local Cursor transcript/state store
- It writes a human-readable transcript to `.gald3r/logs/*_agent_chat.log`
