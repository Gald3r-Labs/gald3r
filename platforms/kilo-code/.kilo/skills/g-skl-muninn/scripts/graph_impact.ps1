<#
.SYNOPSIS
    Cross-file impact analysis for gald3r projects (T1158).
    Returns a list of files that import, call, or reference the target file/symbol.

.DESCRIPTION
    Wraps the gald3r_muninn `graph_impact` MCP tool (replaces the deprecated
    gitnexus-based `.claude/skills/g-skl-muninn/scripts/gitnexus_impact.ps1`).

    Backend resolution order:
    1. **muninn (preferred)** — invoke the muninn plugin core directly via
       Python (`docker/gald3r/tools/plugins/muninn/plugin.py`). Uses the
       persistent SQLite graph store at `~/.gald3r/muninn.db` (override with
       `MUNINN_DB_PATH`). This is the same code path the MCP server uses for
       the `graph_impact` tool — calling it in-process avoids the network
       hop and works whether or not the example_app MCP server is
       currently running.
    2. **MCP HTTP (optional)** — pass `-Backend mcp` to force a JSON-RPC
       call against the running example_app MCP server (default
       `http://localhost:8090/mcp`, override with `-McpUrl`).
    3. **ripgrep fallback** — when neither muninn path is reachable (no
       index, plugin import failed, network error), fall back to the
       legacy ripgrep-based import-pattern scan. Same fallback shape as
       the deprecated gitnexus_impact.ps1 for behavioral parity.

.PARAMETER File
    Relative or absolute path to the target file to analyze.
    Examples:
        -File "docker/gald3r/tools/plugins/search.py"
        -File "src/lib/agentActivity/index.ts"

.PARAMETER Depth
    Search depth for transitive dependents (default: 2). Currently advisory
    for the muninn backend (v1 returns direct importers/callers); honored
    by the ripgrep fallback.

.PARAMETER Backend
    Force backend: "muninn" | "mcp" | "ripgrep" | "auto" (default: "auto").
    `auto` tries muninn (direct Python), then falls back to ripgrep.

.PARAMETER McpUrl
    MCP server URL when -Backend mcp is used.
    Defaults to "http://localhost:8090/mcp" (example_app).

.PARAMETER Json
    Output results as JSON instead of formatted text.

.EXAMPLE
    .\scripts\graph_impact.ps1 -File "docker/gald3r/tools/plugins/search.py"
    .\scripts\graph_impact.ps1 -File "src/lib/agentActivity/index.ts" -Json
    .\scripts\graph_impact.ps1 -File "..." -Backend mcp

.NOTES
    Replaces `.claude/skills/g-skl-muninn/scripts/gitnexus_impact.ps1` (deprecated). See task T1158 for
    the migration; see `.gald3r/subsystems/codebase-graph.md` for subsystem
    overview. The muninn plugin lives at
    `docker/gald3r/tools/plugins/muninn/plugin.py` and exposes the
    `graph_impact` MCP tool via the example_app server.

    Task: T1158 — gald3r_muninn g-go-code Step b0 integration.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$File,

    [int]$Depth = 2,

    [ValidateSet("muninn", "mcp", "ripgrep", "auto")]
    [string]$Backend = "auto",

    [string]$McpUrl = "http://localhost:8090/mcp",

    [switch]$Json
)

$ErrorActionPreference = "Continue"

# Resolve project root (walk up to find .gald3r/)
function Find-ProjectRoot {
    $dir = (Get-Location).Path
    while ($dir -ne (Split-Path $dir -Parent)) {
        if (Test-Path (Join-Path $dir ".gald3r")) { return $dir }
        $dir = Split-Path $dir -Parent
    }
    return (Get-Location).Path
}

$ProjectRoot = Find-ProjectRoot
$AbsFile = if ([System.IO.Path]::IsPathRooted($File)) { $File } else { Join-Path $ProjectRoot $File }
$RelFile = if ($AbsFile.StartsWith($ProjectRoot)) { $AbsFile.Substring($ProjectRoot.Length).TrimStart('\', '/') } else { $File }

if (-not (Test-Path $AbsFile)) {
    $result = @{
        success = $false
        error = "File not found: $AbsFile"
        file = $RelFile
    }
    if ($Json) { $result | ConvertTo-Json -Depth 3 } else { Write-Error $result.error }
    exit 1
}

# --- BACKEND: muninn (direct Python in-process) ---
function Invoke-MuninnImpact {
    $pluginPath = Join-Path $ProjectRoot "docker\gald3r\tools\plugins\muninn\plugin.py"
    if (-not (Test-Path $pluginPath)) { return $null }

    $pyAvailable = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pyAvailable) { return $null }

    # Run plugin.graph_impact(file_path=...) in-process via a one-liner.
    # Output is the JSON dict from the tool (or the error envelope on failure).
    $escFile = $RelFile.Replace("\", "/").Replace("'", "''")
    $pyScript = @"
import asyncio, importlib.util, json, sys
from pathlib import Path
plugin_path = Path(r'$pluginPath')
spec = importlib.util.spec_from_file_location('muninn_plugin_core', plugin_path)
if spec is None or spec.loader is None:
    print(json.dumps({'error': 'internal_error', 'message': 'spec failed'}))
    sys.exit(0)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    result = asyncio.run(mod.graph_impact(file_path='$escFile'))
    print(json.dumps(result))
except Exception as exc:
    print(json.dumps({'error': 'internal_error', 'message': str(exc)}))
"@

    try {
        $output = $pyScript | python 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $output) { return $null }
        $parsed = $output | ConvertFrom-Json -ErrorAction Stop

        # Error envelope from the plugin -> treat as unavailable, fall back.
        if ($parsed.error) { return $null }

        # Successful, but no index? Surface so the caller knows to fall back.
        $warning = $null
        if ($parsed.warning) { $warning = $parsed.warning }

        $files = @()
        if ($parsed.files) {
            foreach ($f in $parsed.files) {
                if ($f.path) { $files += $f.path } else { $files += $f }
            }
        }

        return @{
            backend = "muninn"
            files = $files
            count = if ($parsed.count) { $parsed.count } else { $files.Count }
            depth = $Depth
            warning = $warning
        }
    } catch {
        return $null
    }
}

# --- BACKEND: MCP HTTP (example_app server) ---
function Invoke-McpImpact {
    try {
        $payload = @{
            jsonrpc = "2.0"
            id = 1
            method = "tools/call"
            params = @{
                name = "graph_impact"
                arguments = @{ file_path = $RelFile }
            }
        } | ConvertTo-Json -Depth 6 -Compress

        $resp = Invoke-WebRequest -Uri $McpUrl -Method POST -Body $payload `
            -ContentType "application/json" -UseBasicParsing -TimeoutSec 5
        if (-not $resp -or -not $resp.Content) { return $null }
        $body = $resp.Content | ConvertFrom-Json -ErrorAction Stop
        if ($body.error) { return $null }

        # FastMCP tools/call wraps tool output in result.content[].text
        $textPayload = $null
        if ($body.result -and $body.result.content) {
            foreach ($c in $body.result.content) {
                if ($c.text) { $textPayload = $c.text; break }
            }
        }
        if (-not $textPayload) { return $null }

        $parsed = $textPayload | ConvertFrom-Json -ErrorAction Stop
        if ($parsed.error) { return $null }

        $files = @()
        if ($parsed.files) {
            foreach ($f in $parsed.files) {
                if ($f.path) { $files += $f.path } else { $files += $f }
            }
        }
        return @{
            backend = "muninn-mcp"
            files = $files
            count = if ($parsed.count) { $parsed.count } else { $files.Count }
            depth = $Depth
            warning = $parsed.warning
        }
    } catch {
        return $null
    }
}

# --- BACKEND: ripgrep fallback ---
function Invoke-RipgrepImpact {
    $ext = [System.IO.Path]::GetExtension($AbsFile).ToLower()
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($AbsFile)

    $affectedFiles = [System.Collections.Generic.HashSet[string]]::new()

    if ($ext -in @('.py', '.pyi')) {
        $patterns = @(
            "import $baseName",
            "from $baseName import",
            "from .* import.*$baseName"
        )

        $relDir = [System.IO.Path]::GetDirectoryName($RelFile)
        $modulePath = $relDir.Replace('\', '.').Replace('/', '.').TrimStart('.')
        if ($modulePath) {
            $patterns += "from $modulePath import"
            $patterns += "from $modulePath\.$baseName"
        }

        $rgAvailable = Get-Command rg -ErrorAction SilentlyContinue
        if ($rgAvailable) {
            foreach ($pattern in $patterns) {
                $matches = & rg -l --type py "$pattern" $ProjectRoot 2>$null
                foreach ($m in $matches) {
                    if ($m -ne $AbsFile) {
                        $affectedFiles.Add($m.Replace($ProjectRoot, '').TrimStart('\', '/')) | Out-Null
                    }
                }
            }
        }
    } elseif ($ext -in @('.ts', '.tsx', '.js', '.mjs', '.mts')) {
        $patterns = @(
            "from ['""].*$baseName['""]",
            "import.*['""].*$baseName['""]",
            "require\(['""].*$baseName['""]"
        )

        $rgAvailable = Get-Command rg -ErrorAction SilentlyContinue
        if ($rgAvailable) {
            foreach ($pattern in $patterns) {
                $matches = & rg -l -e "$pattern" --type ts --type js $ProjectRoot 2>$null
                foreach ($m in $matches) {
                    if ($m -ne $AbsFile) {
                        $affectedFiles.Add($m.Replace($ProjectRoot, '').TrimStart('\', '/')) | Out-Null
                    }
                }
            }
        }
    } else {
        $rgAvailable = Get-Command rg -ErrorAction SilentlyContinue
        if ($rgAvailable) {
            $matches = & rg -l "$baseName" $ProjectRoot 2>$null
            foreach ($m in $matches) {
                if ($m -ne $AbsFile) {
                    $affectedFiles.Add($m.Replace($ProjectRoot, '').TrimStart('\', '/')) | Out-Null
                }
            }
        }
    }

    $fileList = $affectedFiles | Sort-Object | Where-Object {
        $_ -notmatch "\.(lock|log|md|yaml|yml|json)$" -and
        $_ -notmatch "node_modules" -and
        $_ -notmatch "\.gald3r"
    }

    return @{
        backend = "ripgrep-fallback"
        files = @($fileList)
        count = @($fileList).Count
        depth = $Depth
        note = "muninn graph unavailable / not indexed - using ripgrep import scan (limited precision)"
    }
}

# --- MAIN ---

$result = $null

switch ($Backend) {
    "muninn" {
        $result = Invoke-MuninnImpact
    }
    "mcp" {
        $result = Invoke-McpImpact
    }
    "ripgrep" {
        $result = Invoke-RipgrepImpact
    }
    "auto" {
        $result = Invoke-MuninnImpact
        if (-not $result) { $result = Invoke-RipgrepImpact }
    }
}

# Last-ditch: never let an empty path-through escape; fall back to ripgrep.
if (-not $result) { $result = Invoke-RipgrepImpact }

$finalResult = @{
    success = $true
    backend = $result.backend
    file = $RelFile
    affected_files = $result.files
    count = $result.count
    depth = $result.depth
}
if ($result.warning) { $finalResult.warning = $result.warning }
if ($result.note) { $finalResult.note = $result.note }

if ($Json) {
    $finalResult | ConvertTo-Json -Depth 4
} else {
    Write-Host ""
    Write-Host "Impact Analysis: $RelFile" -ForegroundColor Cyan
    Write-Host "Backend: $($finalResult.backend)" -ForegroundColor Gray

    $files = $finalResult.affected_files
    if ($files -and $files.Count -gt 0) {
        Write-Host "Affected files ($($files.Count)):" -ForegroundColor Yellow
        foreach ($f in $files) {
            Write-Host "  - $f"
        }
    } else {
        Write-Host "No files found that import/reference this target." -ForegroundColor Green
    }
    if ($finalResult.warning) {
        Write-Host ""
        Write-Host "Warning: $($finalResult.warning)" -ForegroundColor DarkYellow
    }
    if ($finalResult.note) {
        Write-Host ""
        Write-Host "Note: $($finalResult.note)" -ForegroundColor DarkGray
    }
    Write-Host ""
}
