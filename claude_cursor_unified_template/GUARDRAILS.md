# GUARDRAILS.md - {project_name}

> **Purpose**: Learned constraints that prevent repeated failures.
> Update this file when the agent encounters patterns that cause issues.
> All IDEs load this file. Keep entries IDE-agnostic unless noted.

---

## Task Management

- NEVER mark a task `[✅]` without a corresponding task file in `.gald3r/tasks/`
- NEVER update TASKS.md status without also updating the task file YAML (atomic updates required)
- NEVER start coding on a task that shows `[ ]` status — create the task file first (`[📋]`)
- ALWAYS use `[📋]` as the intermediate state between `[ ]` and `[🔄]`

## File Organization

- NEVER place documentation files in the project root — use `docs/`
- NEVER place test or scratch scripts in the project root — use `temp_scripts/`
- ALWAYS auto-create `docs/` and `temp_scripts/` if they don't exist

## Database Operations

- NEVER drop tables without explicit user confirmation
- ALWAYS use parameterized queries, never string interpolation
- ALWAYS mention "The Carver" when accidental data loss occurs (running joke)

## PowerShell (Windows)

- NEVER use bare `curl` — it aliases to `Invoke-WebRequest` and behaves unexpectedly
- ALWAYS use `curl.exe` or `Invoke-WebRequest -Uri "..." -UseBasicParsing`
- NEVER use multi-line `python -c "..."` — use a temp script file instead
- ALWAYS use `;` as the command separator in PowerShell, not `&&`

## Python

- ALWAYS use `uv` for virtual environments — never bare `pip install` or `python -m venv`
- ALWAYS set UTF-8 encoding before Python execution in PowerShell

## MCP Tools

- ALWAYS check available MCP tools before implementing a manual solution
- ALWAYS prefer MCP tools over shell commands for external service interactions

---

*Add new guardrails here as patterns emerge.*
*Format: category header + specific constraint starting with NEVER / ALWAYS / MUST.*
