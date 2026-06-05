# g-hk-pre-tool-call-gald3r-guard.ps1
# @subsystems: PROJECT_IDENTITY_SETUP
# Pre-tool-call guard: refuse unsupervised Edit/Write to .gald3r/ paths.
#
# Enforces g-rl-33 ".gald3r/ Folder Gate (HARD RULE)":
#   "NEVER read or write any file inside .gald3r/ without an active gald3r agent."
#
# Hook contract (per Claude Code / Cursor PreToolUse spec):
#   stdin   : JSON { tool_name, tool_input: { file_path | path | notebook_path, ... } }
#   exit 0  : allow (no body)
#   exit 2  : deny  (body: { permission: "deny", user_message, agent_message })
#
# Bypass: $env:GALD3R_HOOK_BYPASS = '1'  (mirrors T600 §3.3 user override).
# Allow override (active gald3r command): $env:GALD3R_ACTIVE_AGENT = '<agent_id>'.
#
# Rule reference: .claude/rules/g-rl-33-enforcement_catchall.md

$ErrorActionPreference = "SilentlyContinue"

$raw = $input | Out-String
$tool = ""
$path = ""
try {
    $event = $raw | ConvertFrom-Json
    $tool  = "$($event.tool_name)"
    if ($event.tool_input) {
        foreach ($k in @("file_path", "path", "notebook_path", "target_file")) {
            if ($event.tool_input.PSObject.Properties[$k]) {
                $path = "$($event.tool_input.$k)"
                if ($path) { break }
            }
        }
    }
} catch {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Only inspect file-write tools.
$writeTools = @("Edit", "Write", "MultiEdit", "NotebookEdit", "Patch", "ApplyPatch", "str_replace_editor")
if ($writeTools -notcontains $tool) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

if (-not $path) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Normalize separators.
$norm = ($path -replace '\\', '/')

# Only enforce on .gald3r/ paths anywhere in the path.
if ($norm -notmatch '(^|/)\.gald3r/') {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Bypass switches.
if ($env:GALD3R_HOOK_BYPASS -eq '1') {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}
if ($env:GALD3R_ACTIVE_AGENT) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Refuse.
$msg = "Direct Edit/Write to .gald3r/ refused by g-hk-pre-tool-call-gald3r-guard. " +
       "Route the change through the appropriate gald3r agent (g-task-manager / g-qa-engineer / " +
       "g-planner / g-ideas-goals / etc.) or set GALD3R_ACTIVE_AGENT before the tool call. " +
       "See .claude/rules/g-rl-33-enforcement_catchall.md § '.gald3r/ Folder Gate (HARD RULE)'."

@{
    permission    = "deny"
    user_message  = $msg
    agent_message = $msg + " Target path: $path"
} | ConvertTo-Json -Compress
exit 2
