<#
.SYNOPSIS
    [DEPRECATED — T1158] Use `.gald3r_sys/skills/g-skl-muninn/scripts/graph_impact.ps1` instead.
    Cross-file impact analysis for gald3r projects (T921).
    Returns a list of files that import, call, or reference the target file/symbol.

.DESCRIPTION
    ⚠️ DEPRECATED (T1158): This script wrapped GitNexus, which has been
    replaced by the gald3r_muninn clean-room rewrite (parent epic T1147,
    plugin T1157). Use `.gald3r_sys/skills/g-skl-muninn/scripts/graph_impact.ps1` for all new work — it
    wraps the muninn `graph_impact` MCP tool and falls back to ripgrep
    automatically.

    This wrapper is kept temporarily so that any out-of-tree callers do
    not break mid-migration. It now forwards to `graph_impact.ps1` when
    that script is available and only falls through to the original
    GitNexus / ripgrep path when graph_impact.ps1 is missing.

    Attempts GitNexus impact analysis first (requires `gitnexus` to be indexed).
    Falls back to Python AST + ripgrep-based import graph analysis if GitNexus is
    unavailable or crashes (known issue: GitNexus tree-sitter crashes on Windows
    with certain Python file constructs; tracked as T921 evaluation finding).

.PARAMETER File
    Relative or absolute path to the target file or symbol to analyze.
    Examples:
        -File "docker/gald3r/tools/plugins/search.py"
        -File "src/lib/agentActivity/index.ts"

.PARAMETER Depth
    Search depth for transitive dependents (default: 2).
    Depth 1 = direct importers only.
    Depth 2 = importers of importers.

.PARAMETER Backend
    Force backend: "gitnexus" | "python" | "auto" (default: "auto")

.PARAMETER Json
    Output results as JSON instead of formatted text.

.EXAMPLE
    .\scripts\gitnexus_impact.ps1 -File "docker/gald3r/tools/plugins/search.py"
    .\scripts\gitnexus_impact.ps1 -File "src/lib/agentActivity/index.ts" -Json

.NOTES
    Installation:
        npm install -g gitnexus        # Primary backend (initialize with `gitnexus analyze .`)
        pip install tree-sitter        # Optional for Python backend
    
    GitNexus known issue (2026-05-08): Crashes on Windows with exit code -1073741819
    (tree-sitter access violation) on some Python files. Python fallback is used automatically.
    Monitor https://github.com/abhigyanpatwari/GitNexus for Windows fix.
    
    Task: T921 — GitNexus codebase semantic memory integration
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$File,
    
    [int]$Depth = 2,
    
    [ValidateSet("gitnexus", "python", "auto")]
    [string]$Backend = "auto",
    
    [switch]$Json
)

$ErrorActionPreference = "Continue"

# DEPRECATION NOTICE — T1158. Forward to .gald3r_sys/skills/g-skl-muninn/scripts/graph_impact.ps1 when
# available so existing callers keep working during the migration window.
$replacement = Join-Path $PSScriptRoot "graph_impact.ps1"
if (Test-Path $replacement) {
    Write-Warning "[DEPRECATED] .gald3r_sys/skills/g-skl-muninn/scripts/gitnexus_impact.ps1 is deprecated (T1158). Forwarding to .gald3r_sys/skills/g-skl-muninn/scripts/graph_impact.ps1."
    # Forward original parameters verbatim. Note: -Backend gitnexus is no
    # longer meaningful; the new script accepts 'muninn' | 'mcp' | 'ripgrep'
    # | 'auto'. Map the closest equivalent and let the new script decide.
    $newBackend = switch ($Backend) {
        "gitnexus" { "auto" }
        "python"   { "ripgrep" }
        default    { "auto" }
    }
    $fwdArgs = @{ File = $File; Depth = $Depth; Backend = $newBackend }
    if ($Json) { $fwdArgs.Json = $true }
    & $replacement @fwdArgs
    exit $LASTEXITCODE
}

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

# --- BACKEND: GitNexus ---
function Invoke-GitNexusImpact {
    $gnAvailable = Get-Command gitnexus -ErrorAction SilentlyContinue
    if (-not $gnAvailable) { return $null }
    
    # Check if indexed
    $statusOut = & gitnexus status 2>&1
    if ($statusOut -match "not indexed") { return $null }
    
    try {
        # Use timeout to avoid hanging if gitnexus crashes
        $job = Start-Job -ScriptBlock {
            param($root, $target, $depth)
            Set-Location $root
            & gitnexus impact $target --depth $depth --format json 2>&1
        } -ArgumentList $ProjectRoot, $RelFile, $Depth
        
        $done = Wait-Job $job -Timeout 30
        if (-not $done) {
            Stop-Job $job
            Remove-Job $job
            return $null  # Timed out — fall back
        }
        
        $output = Receive-Job $job
        Remove-Job $job
        
        if ($LASTEXITCODE -eq 0 -and $output) {
            return @{
                backend = "gitnexus"
                raw = $output -join "`n"
            }
        }
    } catch {}
    return $null
}

# --- BACKEND: Python AST + ripgrep fallback ---
function Invoke-PythonImpact {
    $ext = [System.IO.Path]::GetExtension($AbsFile).ToLower()
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($AbsFile)
    
    $affectedFiles = [System.Collections.Generic.HashSet[string]]::new()
    
    if ($ext -in @('.py', '.pyi')) {
        # Python: search for import/from patterns
        $patterns = @(
            "import $baseName",
            "from $baseName import",
            "from .* import.*$baseName"
        )
        
        # Get module path relative to src/project root
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
        # TypeScript/JavaScript: search for import patterns
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
        # Generic: filename-based reference search
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
        backend = "python-ripgrep"
        files = @($fileList)
        depth = $Depth
        note = "GitNexus unavailable/crashed - using ripgrep import scan (limited precision)"
    }
}

# --- MAIN ---

$gnResult = $null
if ($Backend -in @("gitnexus", "auto")) {
    $gnResult = Invoke-GitNexusImpact
}

$finalResult = if ($gnResult) {
    @{
        success = $true
        backend = "gitnexus"
        file = $RelFile
        impact_raw = $gnResult.raw
    }
} else {
    $pyResult = Invoke-PythonImpact
    @{
        success = $true
        backend = $pyResult.backend
        file = $RelFile
        affected_files = $pyResult.files
        count = $pyResult.files.Count
        depth = $Depth
        note = $pyResult.note
    }
}

if ($Json) {
    $finalResult | ConvertTo-Json -Depth 4
} else {
    Write-Host ""
    Write-Host "Impact Analysis: $RelFile" -ForegroundColor Cyan
    Write-Host "Backend: $($finalResult.backend)" -ForegroundColor Gray
    
    if ($finalResult.backend -eq "gitnexus") {
        Write-Host $finalResult.impact_raw
    } else {
        $files = $finalResult.affected_files
        if ($files -and $files.Count -gt 0) {
            Write-Host "Affected files ($($files.Count)):" -ForegroundColor Yellow
            foreach ($f in $files) {
                Write-Host "  - $f"
            }
        } else {
            Write-Host "No files found that import/reference this target." -ForegroundColor Green
        }
        if ($finalResult.note) {
            Write-Host ""
            Write-Host "Note: $($finalResult.note)" -ForegroundColor DarkGray
        }
    }
    Write-Host ""
}
