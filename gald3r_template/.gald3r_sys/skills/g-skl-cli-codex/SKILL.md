---
name: g-skl-cli-codex
description: OpenAI Codex CLI (codex command) — approval modes, sandbox config, provider/model flags, session continuation, MCP tool integration, multi-agent coordination, and overnight/CI best practices.
---

# g-skl-cli-codex — OpenAI Codex CLI

> **Note**: This skill covers the **OpenAI Codex CLI** (`codex` binary from `@openai/codex` npm package).
> This is a different product from the old OpenAI Codex API model (deprecated 2023) and from OpenCode (`opencode` binary).
> See `g-skl-cli-opencode` for the OpenCode CLI.

Reference docs will live in: `{vault_location}/research/platforms/codex/` once populated via `@g-ingest-docs`.

## When to Use

- Running Codex agents headlessly in scripts or CI pipelines
- Overnight batch implementation tasks with full-auto mode
- Multi-agent workflows where Codex handles a focused subtask
- Configuring sandbox/network restrictions for safe autonomous runs
- Switching LLM providers (OpenAI, Azure, Gemini, Anthropic, Ollama, etc.)

## Installation

```bash
npm install -g @openai/codex
# or
npx @openai/codex
```

Requires Node.js 22+.

## Authentication

```bash
export OPENAI_API_KEY="sk-..."          # OpenAI (default provider)
export AZURE_OPENAI_API_KEY="..."       # Azure OpenAI
export GEMINI_API_KEY="..."             # Google Gemini
export ANTHROPIC_API_KEY="..."          # Anthropic via Codex
export OLLAMA_HOST="http://localhost:11434"  # Local Ollama
```

Codex reads the key for whichever `--provider` is selected.

## Approval Modes

| Mode | Flag | Behavior |
|------|------|----------|
| **Suggest** | `--approval-mode suggest` | Agent proposes changes, human approves each (default interactive) |
| **Auto-Edit** | `--approval-mode auto-edit` | File edits applied automatically; shell commands need approval |
| **Full Auto** | `--approval-mode full-auto` | All actions applied automatically; use with sandbox |

```bash
codex --approval-mode full-auto "implement the login feature per T095"
codex --approval-mode auto-edit "refactor the database layer"
codex --approval-mode suggest "add error handling to src/api/"   # default
```

**Safety rule**: Always use `full-auto` inside a sandbox or Docker container. Never on a live developer machine with production credentials.

## Model & Provider Flags

```bash
codex --model o4-mini "implement X"                          # OpenAI o4-mini (default)
codex --model o3 "design the architecture for feat-036"      # OpenAI o3
codex --model gemini-2.5-pro --provider gemini "review this" # Google Gemini
codex --model claude-sonnet-4-5 --provider anthropic "..."   # Anthropic
codex --model llama3 --provider ollama "..."                 # Local Ollama
```

Provider values: `openai` | `azure` | `gemini` | `anthropic` | `ollama` | `mistral` | `deepseek` | `xai` | `groq`

## Session Management

```bash
codex --continue                   # Continue most recent session
codex --resume {session-id}        # Resume specific session by ID
```

Session IDs are printed at session start. Use `--quiet` + JSON output to capture them in scripts.

## Quiet & Non-Interactive Mode

```bash
codex --quiet "implement T031 per the task spec"              # Suppress interactive UI
CODEX_QUIET_MODE=1 codex "run all acceptance criteria"        # Via env var
```

`--quiet` (or `CODEX_QUIET_MODE=1`) suppresses the full-screen TUI and writes structured output to stdout — suitable for CI pipelines and subprocess invocation.

## Config File

Codex reads `~/.codex/config.toml` (or path set via `CODEX_CONFIG` env var):

```toml
# ~/.codex/config.toml
model = "o4-mini"
provider = "openai"
approval_mode = "suggest"

[sandbox]
network = false          # Block network during execution
allowed_paths = ["/workspace"]

[memory]
project_doc = true       # Auto-load AGENTS.md / CODEX.md at session start
```

Per-project config can be placed at `.codex/config.toml` in the project root.

## Project Context Files

Codex auto-loads these files at session start (in priority order):

| File | Purpose |
|------|---------|
| `AGENTS.md` (project root) | Primary agent instructions |
| `.codex/CODEX.md` | Codex-specific project context |
| `~/.codex/CODEX.md` | User-level global instructions |

In gald3r projects, `AGENTS.md` at the root carries the full system instructions — no additional file needed.

## Sandbox / Network Restrictions

```bash
# Run with network blocked (safe for autonomous refactoring)
codex --approval-mode full-auto --no-network "refactor src/"

# Docker container pattern (recommended for full-auto CI)
docker run --rm -v $(pwd):/workspace \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  node:22 npx @openai/codex \
  --approval-mode full-auto --no-network \
  "implement task per AGENTS.md"
```

## MCP Tool Integration

```bash
# Enable MCP tools via project config
codex --mcp-server "gald3r:node scripts/gald3r-mcp.js" "use the gald3r MCP to check task status"
```

MCP servers can be defined in `.codex/config.toml`:

```toml
[[mcp_servers]]
name = "gald3r"
command = "node"
args = ["scripts/gald3r-mcp.js"]
```

## Multi-Agent Coordination

Codex can be invoked as a subprocess by other agents:

```bash
# Orchestrator spawns Codex for a focused subtask
codex --quiet --approval-mode full-auto \
  "implement task103 per .gald3r/tasks/task103_*.md" \
  2>&1 | tee .gald3r/logs/codex-task103.log
```

```python
# Python orchestration pattern
import subprocess
result = subprocess.run([
    "codex", "--quiet", "--approval-mode", "full-auto",
    "--model", "o4-mini",
    "implement task 103 per spec"
], capture_output=True, text=True, cwd="/path/to/project")
```

Coordinate sub-agents via `.gald3r/linking/INBOX.md` for PCAC messaging.
Each sub-agent should work on independent task files (`ai_safe: true`).

## Overnight / CI Best Practices

- Use `--approval-mode full-auto` + `--no-network` for autonomous overnight runs
- Set `CODEX_QUIET_MODE=1` for clean log output
- Use `--model o4-mini` for cost-efficient batch work; `o3` for complex reasoning tasks
- Rate limits: OpenAI has per-minute and daily token limits — space large batches with sleep between tasks
- Graceful shutdown: Codex handles SIGINT cleanly — send `Ctrl+C` or `kill -INT {pid}`
- Never mount production secrets into a sandbox container

```bash
# Recommended overnight CI pattern
export OPENAI_API_KEY=$OPENAI_API_KEY
export CODEX_QUIET_MODE=1

for task in task101 task102 task103; do
  codex --approval-mode full-auto --no-network \
    "implement $task per .gald3r/tasks/${task}_*.md"
  sleep 30  # rate limit breathing room
done
```

## Dangerous Flag Reference

| Flag | Effect | Safe when |
|------|--------|-----------|
| `--approval-mode full-auto` | No human approval required | Sandbox/Docker, no prod credentials |
| `--dangerously-auto-approve-everything` | Bypasses ALL gates | CI VM with ephemeral FS only |
| `--no-network` | Blocks network during execution | Always safe; recommended for full-auto |

## Vault Reference

Once `@g-ingest-docs` is run for `codex`, full docs will be at:
`{vault_location}/research/platforms/codex/`
