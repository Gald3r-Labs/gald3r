# scrub_public_tree.ps1 - Strip internal artifacts from an export tree before public ship
# @subsystems: RELEASE_AND_VERSIONING
<#
.SYNOPSIS
    Content-scrub gate for public graduation (Mode A and Mode B).

.DESCRIPTION
    Removes .gald3r/, .gald3r_sys/, internal docs, hooks, secrets; scrubs internal-only
    CHANGELOG lines; normalizes em-dash to ASCII double hyphen.

.PARAMETER TreePath
    Root directory of the export tree to scrub (modified in place).

.PARAMETER Quiet
    Suppress per-path log lines.
#>
param(
    [Parameter(Mandatory)]
    [string]$TreePath,

    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $TreePath)) {
    throw "TreePath not found: $TreePath"
}

function Write-ScrubLog {
    param([string]$Msg)
    if (-not $Quiet) { Write-Host "  [SCRUB] $Msg" -ForegroundColor DarkCyan }
}

$stripDirs = @(
    ".gald3r_sys",
    ".gald3r",
    "docs\internal",
    ".env",
    ".env.local",
    ".cursor\hooks",
    ".claude\hooks",
    ".agent",
    ".codex",
    ".opencode"
)

foreach ($rel in $stripDirs) {
    $p = Join-Path $TreePath $rel
    if (Test-Path $p) {
        Remove-Item $p -Recurse -Force
        Write-ScrubLog "Removed: $rel"
    }
}

$scriptsDir = Join-Path $TreePath "scripts"
if (Test-Path $scriptsDir) {
    Get-ChildItem $scriptsDir -Filter "backfill_*" -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem $scriptsDir -Filter "graduate_*" -ErrorAction SilentlyContinue | Remove-Item -Force
}

$customScripts = Join-Path $TreePath "custom_scripts"
if (Test-Path $customScripts) {
    Get-ChildItem $customScripts -Filter "graduate_*" -ErrorAction SilentlyContinue | Remove-Item -Force
}

$changelogPath = Join-Path $TreePath "CHANGELOG.md"
if (Test-Path $changelogPath) {
    $lines = Get-Content $changelogPath
    $internalPatterns = @(
        'license.{0,20}change',
        'history was reset',
        'repository history',
        'pivot',
        'internal only',
        'controller repo',
        'gald3r_dev',
        'do not publish'
    )
    $filtered = foreach ($line in $lines) {
        $drop = $false
        foreach ($pat in $internalPatterns) {
            if ($line -match $pat) { $drop = $true; break }
        }
        if (-not $drop) { $line }
    }
    $text = ($filtered -join "`n")
    $em = [char]0x2014
    $en = [char]0x2013
    $text = $text.Replace($em, "--").Replace($en, "-")
    Set-Content -Path $changelogPath -Value $text.TrimEnd() -Encoding UTF8
    Write-ScrubLog "Scrubbed CHANGELOG.md internal lines and encoding"
}

Get-ChildItem -Path $TreePath -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in @(".md", ".ps1", ".txt", ".json") } |
    ForEach-Object {
        $raw = [System.IO.File]::ReadAllText($_.FullName)
        $em = [char]0x2014
        if ($raw.Contains($em)) {
            $fixed = $raw.Replace($em, "--").Replace([char]0x2013, "-")
            [System.IO.File]::WriteAllText($_.FullName, $fixed, [System.Text.UTF8Encoding]::new($false))
        }
    }

return @{
    tree_path = $TreePath
    scrubbed  = $true
}
