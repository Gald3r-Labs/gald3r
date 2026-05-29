# g-hk-pre-tool-call-prd-freeze.ps1
# @subsystems: RELEASE_AND_VERSIONING
# Pre-tool-call guard: refuse Edit/Write to a PRD file whose YAML status is
# `released` or `superseded` (C-019 / g-rl-33 § "PRD Freeze Gate").
#
# A frozen PRD is the audit-of-record. Only @g-prd-revise may touch it, which
# creates a successor PRD and updates the supersede chain atomically.
#
# Hook contract: same as g-hk-pre-tool-call-gald3r-guard (Claude Code / Cursor
# PreToolUse spec). exit 2 = deny, exit 0 = allow.
#
# Bypass: $env:GALD3R_HOOK_BYPASS = '1'.
# Revise flow: $env:GALD3R_PRD_REVISE_ACTIVE = '1' (set by @g-prd-revise).
#
# Rule reference: .claude/rules/g-rl-33-enforcement_catchall.md § "PRD Freeze Gate"
# Constraint: C-019

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

$writeTools = @("Edit", "Write", "MultiEdit", "NotebookEdit", "Patch", "ApplyPatch", "str_replace_editor")
if ($writeTools -notcontains $tool) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}
if (-not $path) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

$norm = ($path -replace '\\', '/')

# Only PRD spec files: .gald3r/prds/prdNNN_*.md (case-insensitive)
if ($norm -notmatch '(?i)(^|/)\.gald3r/prds/prd\d+_[^/]+\.md$') {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Resolve full path: if relative, prefix with cwd.
$full = $path
if (-not [System.IO.Path]::IsPathRooted($full)) {
    $full = Join-Path (Get-Location).Path $path
}
if (-not (Test-Path -LiteralPath $full)) {
    # New PRD creation is allowed; freeze applies only to existing released/superseded.
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Bypass switches.
if ($env:GALD3R_HOOK_BYPASS -eq '1') {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}
if ($env:GALD3R_PRD_REVISE_ACTIVE -eq '1') {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}

# Read YAML frontmatter (between first two `---` lines).
$content = Get-Content -LiteralPath $full -ErrorAction SilentlyContinue
if (-not $content) {
    @{ permission = "allow" } | ConvertTo-Json -Compress
    exit 0
}
$inFront = $false
$status = ""
foreach ($line in $content) {
    if ($line -match '^---\s*$') {
        if (-not $inFront) { $inFront = $true; continue }
        else { break }
    }
    if ($inFront -and $line -match '^\s*status:\s*([a-zA-Z_-]+)') {
        $status = $matches[1].ToLowerInvariant()
        break
    }
}

if ($status -eq 'released' -or $status -eq 'superseded') {
    $msg = "PRD freeze gate: refused Edit/Write to a $status PRD. " +
           "Released/superseded PRDs are the audit-of-record and are immutable. " +
           "Use @g-prd-revise to create a successor PRD instead (atomically updates the supersede chain). " +
           "See .claude/rules/g-rl-33-enforcement_catchall.md § 'PRD Freeze Gate (HARD RULE - C-019)'."
    @{
        permission    = "deny"
        user_message  = $msg
        agent_message = $msg + " Target: $path (status=$status)"
    } | ConvertTo-Json -Compress
    exit 2
}

@{ permission = "allow" } | ConvertTo-Json -Compress
exit 0
