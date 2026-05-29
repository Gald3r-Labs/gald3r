# Hook: g-hk-pre-tool-call

Shell output compression hook (T1106, IDEA-HARVEST-191). Compresses large
accumulated terminal output to cut context bloat in shell-heavy sessions.
Community pattern (0xNyk/awesome-hermes-agent) reports 60-90% token reduction.

## Fires On

The **`PreToolUse`** (Claude Code) / **`preToolUse`** (Cursor) event, before each
tool call. Wired in `.claude/hooks.json` (`PreToolUse`) and `.cursor/hooks.json`
(`preToolUse`) with matcher `Bash|Shell|Terminal|run_terminal_cmd` (shell-output
tools). Receives the upcoming tool-call JSON on stdin. Always non-blocking — it
NEVER denies a tool call; it only annotates with `additional_context`.

## What It Does

Inspects the event payload for a large stdout/stderr/output text block (probing
`output`, `stdout`, `stderr`, `tool_output`, `result`, `text` at top level and on
`tool_input` / `tool_response`). If a block exceeds N lines, it preserves the FULL
block to `.gald3r/logs/tool_output_<session_id>.log`, then returns a compressed
form as `additional_context`: a summary prefix
(`... [<total> lines compressed, last <N> shown -- run ID: <id>] ...`), any
error/warning "signal" lines lifted out of the truncated region, and the last N
lines. N is read from `.gald3r/config/AGENT_CONFIG.md` field
`pre_tool_call_compress_lines` (default 50; `0` = disabled).

## Side Effects

- Appends the full pre-compression output block to
  `.gald3r/logs/tool_output_<session_id>.log` (non-destructive preservation).
- Returns `{ "permission": "allow", "additional_context": "<compressed>" }` when
  it compresses; `{ "permission": "allow" }` (pure no-op) when disabled, on short
  output, on empty/unparseable stdin, or when no output field is present.
- Never blocks tool calls. Never touches `.gald3r/` control-plane state files
  (TASKS.md, BUGS.md, task/bug files).
- **Achievable-scope gap (documented):** a PowerShell `PreToolUse` hook cannot
  retroactively rewrite terminal output blocks already rendered in the agent's
  context window — only the harness splices `additional_context`. This hook
  compresses whatever output the harness supplies on the event payload (prior or
  preview output); where the harness exposes no output field, the hook is a safe
  no-op. Full lossless capture always lands in `.gald3r/logs/`.

## Related Tasks

- T1106 — Add pre_tool_call shell output compression hook (this hook).
- IDEA-HARVEST-191 — source pattern (awesome-hermes-agent).
- Related: IDEA-HARVEST-177 (/compress command), IDEA-HARVEST-166 (JSONL logging).
- Config: `.gald3r/config/AGENT_CONFIG.md` field `pre_tool_call_compress_lines`.
