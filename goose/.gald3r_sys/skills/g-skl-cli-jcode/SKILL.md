---
name: g-skl-cli-jcode
description: jcode CLI platform skill — Rust-based coding agent with 14ms startup (245x faster than Claude Code), local embeddings, multi-session, MIT licensed. Use for low-overhead local tasks, batch loops, and resource-constrained environments.
token_budget: low
subsystem_memberships: [PLATFORM_INTEGRATION]
---

# g-skl-cli-jcode — jcode Rust Coding Agent

Reference: [github.com/1jehuang/jcode](https://github.com/1jehuang/jcode) | 4,827 ⭐ | MIT | Rust

## What is jcode?

jcode is a Rust-native coding agent designed for minimal overhead and fast startup. It fills the "fast local runner" niche that Claude Code, Cursor, and Gemini CLI sacrifice for richer IDE integration.

**Performance profile** (vs Claude Code):

| Metric | jcode | Claude Code | Gemini CLI |
|--------|-------|-------------|------------|
| Startup time | **14ms** | 3.4s | ~2s |
| Startup ratio | **1×** (baseline) | 245× slower | ~140× slower |
| RAM per session | ~10 MB | ~24 MB | ~22 MB |
| Additional session RAM | **10.4 MB** | significantly higher | — |
| License | MIT | Proprietary | Proprietary |
| Network required | No (local models) | Yes (Anthropic API) | Yes (Google API) |
| Embeddings | Local (built-in) | Via API | Via API |

**jcode is the right choice when:**
- Startup time matters (tight loops, per-file batch processing)
- Running on resource-constrained hardware (< 512 MB available)
- Air-gapped or offline environments (local models only)
- High-volume tasks where API costs accumulate quickly
- Multi-session parallelism without per-session API overhead

---

## Installation

### Via Cargo (Rust toolchain required)

```bash
# Install from crates.io
cargo install jcode

# Verify
jcode --version
```

### Via Binary Download (no Rust required)

```bash
# Linux/macOS
curl -sSL https://github.com/1jehuang/jcode/releases/latest/download/jcode-$(uname -s | tr '[:upper:]' '[:lower:]')-x86_64.tar.gz | tar xz
sudo mv jcode /usr/local/bin/

# Windows (PowerShell)
$url = "https://github.com/1jehuang/jcode/releases/latest/download/jcode-windows-x86_64.zip"
Invoke-WebRequest -Uri $url -OutFile jcode.zip
Expand-Archive jcode.zip -DestinationPath .
Move-Item jcode.exe $env:USERPROFILE\bin\jcode.exe
```

### Verify Installation

```bash
jcode --version        # prints version + Rust toolchain info
jcode --help           # full flag reference
jcode --list-models    # shows available local models
```

---

## Configuration

jcode looks for config at `~/.jcode/config.toml`:

```toml
[model]
default = "qwen2.5-coder:7b"    # default local model
embedding = "nomic-embed-text"   # local embedding model
temperature = 0.1

[sessions]
dir = "~/.jcode/sessions"        # session history storage
max_sessions = 50

[project]
ignore_patterns = [".gald3r/", "node_modules/", ".git/"]
max_file_size_kb = 500           # skip files larger than this
```

---

## Key Flags and Usage Patterns

```bash
# Basic task
jcode "implement a retry function with exponential backoff"

# Specify model
jcode --model qwen2.5-coder:14b "refactor the authentication module"

# Point at a specific directory (not cwd)
jcode --project /path/to/repo "add docstrings to all public functions"

# Non-interactive (headless / scripting mode)
jcode --headless --output json "list all TODO comments in the codebase"

# Session management
jcode --session my-session "continue the API refactor"    # named session
jcode --resume                                             # resume last session
jcode --list-sessions                                      # see all sessions

# Limit scope (prevents drifting into unrelated files)
jcode --include "src/auth/**" "fix the token refresh logic"
jcode --exclude "tests/**" "add error handling to all service files"

# Embedding-based context (uses local embeddings)
jcode --embed-context "find code similar to the payment processor"
```

---

## Session Management

jcode persists sessions to `~/.jcode/sessions/`. Sessions are local — no API calls for session storage.

```bash
# List sessions
jcode --list-sessions
# → 2026-05-09 14:23  my-session     "implement retry logic"
# → 2026-05-09 11:05  auth-refactor  "refactor auth module"

# Resume a named session
jcode --session auth-refactor "continue with the token refresh"

# Export session as markdown (useful for handoffs to Claude/Cursor)
jcode --session auth-refactor --export > session-notes.md

# Delete old sessions
jcode --delete-session auth-refactor
```

---

## Model Setup (Local Models via Ollama)

jcode uses [Ollama](https://ollama.ai) as the local model backend:

```bash
# Install Ollama first
# Linux/macOS: curl -sSfL https://ollama.ai/install.sh | sh
# Windows: download from ollama.ai

# Pull a coding model
ollama pull qwen2.5-coder:7b       # fast, low RAM (~5 GB)
ollama pull qwen2.5-coder:14b      # higher quality (~9 GB)
ollama pull deepseek-coder-v2      # strong at reasoning

# jcode auto-detects running Ollama instances
jcode --list-models                # shows available Ollama models
```

For embedding (codebase search):
```bash
ollama pull nomic-embed-text       # fast local embeddings
```

---

## When to Use jcode vs Other Agents

| Scenario | Recommended Agent | Why |
|----------|------------------|-----|
| High-volume batch (100+ files) | **jcode** | 14ms startup, no API cost per run |
| Air-gapped / offline | **jcode** | Local models only |
| Quick one-shot edits | **jcode** | No startup penalty |
| Complex multi-file feature | Cursor / Claude Code | Better context, richer tooling |
| Code review with OWASP pass | **Cursor / g-go-review** | Richer analysis, task tracking |
| Internet research + coding | Cursor / Claude Code | Web access |
| Overnight batch loops | **jcode** (local) or Claude CLI | Depends on model quality needed |
| Gald3r task implementation | Cursor / Claude Code | Full `.gald3r/` integration |
| Pre-commit lint + fix | **jcode** | Fast, deterministic, per-file |

---

## Gald3r Integration

### Using jcode as a Task Executor

jcode can execute gald3r tasks when provided the task spec as context:

```bash
# Export task spec and feed to jcode
cat .gald3r/tasks/task123_my_task.md | jcode "implement this task: $(cat -)"

# Or pass the file directly
jcode --context .gald3r/tasks/task123_my_task.md "implement this task per the spec"
```

**Limitations**: jcode does NOT natively read or write `.gald3r/` files (TASKS.md, BUGS.md, etc.). It is a pure code executor. For gald3r coordination (status updates, task transitions), use Cursor or Claude Code.

### Pattern: jcode as the Coder, Cursor as the Coordinator

```
Coordinator (Cursor / @g-go):
  → Reads task spec
  → Exports task context to a temp file
  → Launches jcode --headless for implementation
  → Reads jcode output
  → Updates TASKS.md, commits, routes to review
```

This pattern uses jcode's speed for the heavy implementation work and Cursor for the coordination layer that requires `.gald3r/` integration.

### Batch Task Runner (PowerShell)

```powershell
# Run jcode on each pending task spec (example pattern)
Get-ChildItem .gald3r/tasks/task*_*.md | ForEach-Object {
    $taskContent = Get-Content $_.FullName -Raw
    jcode --headless --output json "implement this task: $taskContent" |
        Out-File "jcode-results/$($_.BaseName)-result.json"
}
```

### CI / Pre-Commit Hook Pattern

```bash
#!/bin/bash
# .git/hooks/pre-commit — jcode lint-and-fix pass
changed_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')
for f in $changed_files; do
    jcode --headless --include "$f" "fix any obvious bugs and style issues in this file"
done
```

---

## Caveats and Known Gaps

- **No built-in web access** — jcode is purely local; it cannot browse URLs or call APIs during a task
- **Context window varies by model** — quality is bounded by the local model choice (7B models miss subtle bugs)
- **No `.gald3r/` native support** — task status updates must be done outside jcode
- **Windows path handling** — use forward slashes or quoted backslash paths on Windows
- **Multi-repo tasks** — jcode scopes to `--project`; cross-repo work needs multiple invocations

---

## Vault Reference

Once `@g-recon-docs` is run for `jcode`, full docs will be at:
`{vault_location}/research/platforms/jcode/`

Source: `github.com/1jehuang/jcode` — ingested via IDEA-HARVEST-001.
