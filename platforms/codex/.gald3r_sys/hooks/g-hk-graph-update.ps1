# @subsystems: PROJECT_IDENTITY_SETUP
<#
.SYNOPSIS
    Post-commit hook: refresh the gald3r_muninn codebase graph index after
    each commit (T1158).

.DESCRIPTION
    Runs the muninn indexers (Python AST + TypeScript) over the changed
    files in the latest commit so `graph_impact`, `graph_callers`, etc.
    return current results for the next `g-go-code` Step b0 Impact Scan.

    Non-blocking by design: if the muninn plugin / Python / Node.js are
    not available, the hook logs the reason and exits 0 so the commit is
    never blocked.

.NOTES
    Install as a git post-commit hook:
        echo 'powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/g-hk-graph-update.ps1' > .git/hooks/post-commit

    Task: T1158 — gald3r_muninn integration into g-go-code Step b0.
#>

param(
    # T1159: regex matches any of the 5 IDE hook directories so the same
    # script body works when installed under .cursor/, .claude/, .agent/,
    # .codex/, or .opencode/.
    [string]$ProjectRoot = $PSScriptRoot -replace '[\\/]\.(cursor|claude|agent|codex|opencode)[\\/]hooks$', ''
)

if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path
}

# Resolve project root by walking up to .gald3r/ when needed.
if (-not (Test-Path (Join-Path $ProjectRoot ".gald3r"))) {
    $dir = (Get-Location).Path
    while ($dir -ne (Split-Path $dir -Parent)) {
        if (Test-Path (Join-Path $dir ".gald3r")) { $ProjectRoot = $dir; break }
        $dir = Split-Path $dir -Parent
    }
}

Set-Location $ProjectRoot

$pythonIndexer = Join-Path $ProjectRoot "docker\gald3r\tools\plugins\muninn\indexers\python_indexer.py"
$tsIndexer = Join-Path $ProjectRoot "docker\gald3r\tools\plugins\muninn\indexers\ts_indexer.js"

$logDir = Join-Path $ProjectRoot ".gald3r\logs"
$logFile = Join-Path $logDir "muninn_updates.log"
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

function Write-MuninnLog {
    param([string]$Line)
    if (Test-Path $logDir) {
        Add-Content -Path $logFile -Value "$timestamp | $Line" -ErrorAction SilentlyContinue
    }
}

# Skip silently if the muninn plugin is not present (e.g. on a non-gald3r-dev clone).
if (-not (Test-Path $pythonIndexer) -and -not (Test-Path $tsIndexer)) {
    Write-MuninnLog "muninn-update | skipped: no indexer files found"
    exit 0
}

# Python AST indexer
if (Test-Path $pythonIndexer) {
    $pyAvailable = Get-Command python -ErrorAction SilentlyContinue
    if ($pyAvailable) {
        try {
            $pyOut = & python $pythonIndexer --root $ProjectRoot --incremental 2>&1
            Write-MuninnLog "muninn-update | python-indexer | exit=$LASTEXITCODE | $($pyOut -join ' ')"
        } catch {
            Write-MuninnLog "muninn-update | python-indexer | exception=$($_.Exception.Message)"
        }
    } else {
        Write-MuninnLog "muninn-update | python-indexer | skipped: python not on PATH"
    }
}

# TypeScript / JavaScript indexer (Node.js)
if (Test-Path $tsIndexer) {
    $nodeAvailable = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeAvailable) {
        try {
            $nodeOut = & node $tsIndexer --root $ProjectRoot --incremental 2>&1
            Write-MuninnLog "muninn-update | ts-indexer | exit=$LASTEXITCODE | $($nodeOut -join ' ')"
        } catch {
            Write-MuninnLog "muninn-update | ts-indexer | exception=$($_.Exception.Message)"
        }
    } else {
        Write-MuninnLog "muninn-update | ts-indexer | skipped: node not on PATH"
    }
}

# Non-blocking: always exit 0 so git commit is not blocked.
exit 0
