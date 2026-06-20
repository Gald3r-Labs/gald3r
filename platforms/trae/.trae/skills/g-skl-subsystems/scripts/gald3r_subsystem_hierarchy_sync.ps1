<#
.SYNOPSIS
  Dry-run validation for subsystem hierarchy metadata under .gald3r/subsystems/**/*.md

.DESCRIPTION
  Recursively scans nested subsystem specs, validates parent_subsystem / children / locations:,
  cross-checks SUBSYSTEMS.md index paths against files on disk (drift either direction), and
  flags optional domain mismatch vs parent. Does not mutate files.

.PARAMETER ProjectRoot
  Repository root.

.PARAMETER WarnOnly
  Exit 0 even when issues found.

.PARAMETER Json
  Emit JSON summary.
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$WarnOnly,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$subRoot = Join-Path (Join-Path $ProjectRoot '.gald3r') 'subsystems'
if (-not (Test-Path $subRoot)) {
    if ($Json) { Write-Output '{"status":"skip","issues":0}' }
    exit 0
}

function Get-FrontmatterBlock([string]$content) {
    if ($content -notmatch '(?s)^---\r?\n(.+?)\r?\n---\r?\n') { return $null }
    return $Matches[1]
}

function Get-YamlScalar([string]$block, [string]$key) {
    $m = [regex]::Match($block, "(?m)^$key\s*:\s*(.+)\s*$")
    if (-not $m.Success) { return $null }
    $v = $m.Groups[1].Value.Trim()
    if ($v -match "^['\`"](.*)['\`"]$") { return $Matches[1] }
    return $v
}

function Get-YamlStringList([string]$block, [string]$key) {
    $lines = $block -split "`r?`n"
    $in = $false
    $items = [System.Collections.Generic.List[string]]::new()
    foreach ($line in $lines) {
        if ($line -match "^\s*$") { continue }
        if (-not $in) {
            if ($line -match "^$key\s*:\s*$") { $in = $true; continue }
            if ($line -match "^$key\s*:\s*\[\s*(.*?)\s*\]\s*$") {
                $inner = $Matches[1].Trim()
                if ($inner.Length -eq 0) { return @() }
                foreach ($p in ($inner -split ',')) { $items.Add($p.Trim().Trim("'`"")) }
                return $items.ToArray()
            }
        }
        else {
            if ($line -match "^(\w+)\s*:") { break }
            if ($line -match "^\-\s+(.+)$") { $items.Add($Matches[1].Trim().Trim("'`"")) }
            elseif ($line -match "^\s{2,}\-\s+(.+)$") { $items.Add($Matches[1].Trim().Trim("'`"")) }
        }
    }
    return $items.ToArray()
}

$gald3rDir = Join-Path $ProjectRoot '.gald3r'
function Get-RelFromGald3r([string]$fullPath) {
    if (-not $fullPath.StartsWith($gald3rDir, [StringComparison]::OrdinalIgnoreCase)) { return $null }
    $r = $fullPath.Substring($gald3rDir.Length).TrimStart([char[]]@('\', '/'))
    return ($r -replace '\\', '/')
}

# Paths listed in SUBSYSTEMS.md (subsystems/*.md), normalized with forward slashes
$indexPaths = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$subsystemsMd = Join-Path $gald3rDir 'SUBSYSTEMS.md'
if (Test-Path -LiteralPath $subsystemsMd) {
    $idxRaw = Get-Content -LiteralPath $subsystemsMd -Raw -Encoding utf8
    foreach ($m in [regex]::Matches($idxRaw, '(?i)`(subsystems/[^`]+\.md)`')) {
        $v = ($m.Groups[1].Value -replace '\\', '/')
        [void]$indexPaths.Add($v)
    }
    foreach ($m in [regex]::Matches($idxRaw, '(?i)\]\((subsystems/[^)]+\.md)\)')) {
        $v = ($m.Groups[1].Value -replace '\\', '/')
        [void]$indexPaths.Add($v)
    }
    foreach ($m in [regex]::Matches($idxRaw, '(?i)\|\s*`?(subsystems/[^`|]+\.md)`?\s*\|')) {
        $v = ($m.Groups[1].Value -replace '\\', '/')
        [void]$indexPaths.Add($v)
    }
}

$byName = @{}
$records = [System.Collections.Generic.List[object]]::new()
Get-ChildItem -Path $subRoot -Recurse -File -Filter '*.md' -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -notmatch '^(SYSTEM_|SUBSYSTEM_TREE|DEPENDENCY_GRAPH)'
} | ForEach-Object {
    $name = $_.BaseName
    $raw = Get-Content -LiteralPath $_.FullName -Raw -Encoding utf8
    $fm = Get-FrontmatterBlock $raw
    if (-not $fm) { return }
    $yamlName = Get-YamlScalar $fm 'name'
    if ($yamlName) { $name = $yamlName }
    $parent = Get-YamlScalar $fm 'parent_subsystem'
    $domain = Get-YamlScalar $fm 'domain'
    $layer = Get-YamlScalar $fm 'layer'
    $deps = @(Get-YamlStringList $fm 'dependencies')
    $children = @(Get-YamlStringList $fm 'children')
    $hasLocations = $fm -match '(?m)^locations:'
    $relGald3r = Get-RelFromGald3r $_.FullName
    $rec = [pscustomobject]@{
        File       = $_.Name
        RelPath    = $relGald3r
        Name       = $name
        Parent     = $parent
        Domain     = $domain
        Layer      = $layer
        Dependencies = $deps
        Children   = $children
        HasLocationsBlock = [bool]$hasLocations
    }
    $records.Add($rec)
    if ($byName.ContainsKey($name)) {
        $byName[$name] = @($byName[$name]) + $rec
    }
    else {
        $byName[$name] = @($rec)
    }
}

$records = @($records)

$issues = [System.Collections.Generic.List[string]]::new()
$nameSet = [System.Collections.Generic.HashSet[string]]::new([string[]]$byName.Keys, [StringComparer]::OrdinalIgnoreCase)

foreach ($n in $byName.Keys) {
    $xs = $byName[$n]
    if ($xs.Count -gt 1) {
        $issues.Add("DUPLICATE_SUBSYSTEM_NAME $n ($($xs.Count) specs)")
    }
}

foreach ($r in $records) {
    if ($r.Parent) {
        if (-not $nameSet.Contains($r.Parent)) {
            $issues.Add("MISSING_PARENT_SUBSYSTEM $($r.Name) parent_subsystem=$($r.Parent)")
        }
    }
    foreach ($ch in $r.Children) {
        if (-not $ch) { continue }
        if (-not $nameSet.Contains($ch)) {
            $issues.Add("STALE_CHILD $($r.Name) children='$ch'")
        }
    }
    # Intentionally do not validate dependencies: edges here — dependency graph is generated separately (Task 516);
    # YAML dependency list formats vary (quoted JSON-style arrays, inline lists) and are not hierarchy errors.
    if (-not $r.HasLocationsBlock) {
        $relNorm = if ($r.RelPath) { ($r.RelPath -replace '\\', '/') } else { '' }
        $isAdoptedStub = $r.File -match '(?i)^adopted_'
        if ($relNorm -and $indexPaths.Contains($relNorm) -and -not $isAdoptedStub) {
            $issues.Add("INCOMPLETE_LOCATIONS $($r.Name) ($relNorm) - add locations: mapping per subsystem spec policy")
        }
    }
    if ($r.Parent) {
        $pars = $byName[$r.Parent]
        if ($pars -and @($pars).Count -ge 1) {
            $p0 = @($pars)[0]
            if ($r.Domain -and $p0.Domain -and ($r.Domain -ne $p0.Domain)) {
                $issues.Add("DOMAIN_MISMATCH $($r.Name) domain=$($r.Domain) vs parent $($p0.Name) domain=$($p0.Domain)")
            }
        }
    }
}

foreach ($ip in $indexPaths) {
    $full = Join-Path $gald3rDir ($ip -replace '/', [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $full)) {
        $issues.Add("INDEX_BROKEN_LINK $ip listed in SUBSYSTEMS.md but file missing")
    }
}

$issueCount = $issues.Count
if (-not $Json) {
    Write-Host "=== gald3r_subsystem_hierarchy_sync (dry-run) ==="
    Write-Host "Specs scanned: $($records.Count)"
    if ($issueCount -eq 0) { Write-Host "OK: no blocking issues detected." }
    else {
        Write-Host "ISSUES ($($issues.Count)):"
        $issues | ForEach-Object { Write-Host "  - $_" }
    }
}

$hardCount = $issueCount
$exit = if ($hardCount -eq 0) { 0 } else { 1 }
if ($WarnOnly) { $exit = 0 }

if ($Json) {
    $diskSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($r in $records) { if ($r.RelPath) { [void]$diskSet.Add($r.RelPath) } }
    $notIndexed = @($diskSet | Where-Object { -not $indexPaths.Contains($_) })
    @{
        status           = if ($hardCount -eq 0) { 'ok' } else { 'issues' }
        issues           = $hardCount
        detail           = $issues.ToArray()
        specs_scanned    = $records.Count
        index_paths      = @($indexPaths)
        disk_not_indexed = $notIndexed
    } | ConvertTo-Json -Compress -Depth 6 | Write-Output
}

exit $exit
