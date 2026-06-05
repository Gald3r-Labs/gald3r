---
description:
globs:
alwaysApply: true
subsystem_memberships: [LOGGING_SYSTEM]
---
1. Include in the final line(s) on every response to the user:
   * Current timestamp with date, hour, and minutes (e.g., "2026-02-01 09:45 UTC")
   * List of tools used during the call
   * Context usage percentage (ALWAYS show, even if low)
   * Context breakdown showing:
     - Rules context: estimated % of context from .cursor/rules/
     - MCP context: estimated % from MCP tool descriptors/schemas
     - Conversation: % from actual conversation history
     - Skills/Other: % from skills, agents, and other sources

   Example format:
   ```
   ---
   2026-02-01 09:45 UTC
   Model: Claude Opus 4, Tokens: ~12,500 input / ~800 output, Est. Cost: ~$0.16
   Context: 45% used (Rules: ~15%, MCP: ~8%, Conversation: ~18%, Skills/Other: ~4%)
   Tools: Shell, Read, StrReplace
   ---
   ```

2. if any particular file in the code base exceeds 1500 lines of code...
 * begin asking the user if they would like to refactor the code to keep the file sizes smaller
 * become more insistant with every 100 lines added thereafter
 * become very insistant on refactoring once a file has hit 1700 lines

3. check your MCP tool lists, you seem to forget you have a lot of tools


4. When working with Python Project, please use the UV for virtual environment management

5. Your training data is 1-3 years old. For time-sensitive queries (versions, pricing, APIs, best practices), **research before answering** using WebSearch or WebFetch. Use today's date from system context, NOT training cutoff.

6. **Shell Context (Session Start) — OS + Shell Probe**. Before issuing ANY shell command, determine the host OS and target shell. This is a **session-start, one-shot probe** (a single env-var read or one `uname` call — not a multi-step diagnostic) intended to eliminate the bash-vs-PowerShell token-waste loop documented in BUG-031 / T1144.

   **Probe (pick the cheapest signal already available):**
   * `$env:OS` contains `"Windows"` **or** `$IsWindows -eq $true` (PowerShell 7+) → **PowerShell route**
   * `uname -s` returns `Linux` / `Darwin` **or** `$BASH_VERSION` is set → **bash/zsh route**
   * If the harness already tells you (e.g. system context says `Shell: PowerShell` or `Shell: Bash`), trust that — do not re-probe.

   **Never mix syntax inside a single tool call.** The interpreter is selected by the tool, not the snippet — `Bash(...)` will parse PowerShell syntax as bash and error. Concrete differences:

   | Concept | PowerShell | Bash / zsh |
   |---|---|---|
   | Array literal | `@("a","b","c")` | `("a" "b" "c")` or `arr=(a b c)` |
   | Statement separator | `;` (sequential); `&&` requires PS 7+ | `&&` (short-circuit), `;` (sequential) |
   | Env var read | `$env:VAR` | `$VAR` / `${VAR}` |
   | Path separator | `\` (forward `/` also accepted on Windows) | `/` |
   | File-exists test | `Test-Path $p` | `[ -f "$p" ]` / `[ -e "$p" ]` |
   | Pipeline filter | `Where-Object { ... }` | `grep` / `awk` / `xargs` |
   | Subshell / cmd substitution | `$(...)` (expression eval) | `$(...)` (command output) |

   **Default routing on Cursor/Claude Code on Windows**: assume PowerShell unless the terminal explicitly shows a bash/zsh prompt. When the harness exposes both a `Bash` and a `PowerShell` tool, route by **host OS**, not by tool-name preference.

   **Regression canonical example** — this is the exact construct that triggered T1144 (a PowerShell `@(...)` array piped through `Where-Object` to find a hook file, executed inside a `Bash` tool call):
   ```powershell
   $hook = @( ".cursor\hooks\g-hk-pcac-inbox-check.ps1", ".claude\hooks\g-hk-pcac-inbox-check.ps1" ) | Where-Object { Test-Path $_ } | Select-Object -First 1
   ```
   Bash rejects `@(` with `syntax error near unexpected token '('`. That error is a **tool-routing failure**, not a real PCAC conflict or hook-missing condition — re-route the same snippet through PowerShell and it succeeds. Do not enter an error-driven retry loop; switch tools.