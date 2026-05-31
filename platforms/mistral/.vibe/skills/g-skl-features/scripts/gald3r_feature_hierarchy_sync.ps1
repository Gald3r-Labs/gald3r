<#
.SYNOPSIS
  Dry-run validation for feature hierarchy (flat + nested paths under .gald3r/features/).

.DESCRIPTION
  Scans all feature markdown files, parses YAML frontmatter for hierarchy fields, and reports:
  duplicate feat IDs, missing parents, stale children references, depth mismatches.
  Never mutates files. Exit 0 if clean, 1 if issues found (use -WarnOnly for exit 0).

.PARAMETER ProjectRoot
  Repository root containing .gald3r/features/

.PARAMETER WarnOnly
  Always exit 0 (CI advisory mode).

.PARAMETER Json
  Emit single-line JSON summary to stdout (still writes human report to stderr or default stream).
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$WarnOnly,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$featuresRoot = Join-Path (Join-Path $ProjectRoot '.gald3r') 'features'
if (-not (Test-Path $featuresRoot)) {
    Write-Host "SKIP: no .gald3r/features at $featuresRoot"
    if ($Json) { '{"status":"skip","issues":0}' }
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
                return , $items.ToArray()
            }
        }
        else {
            if ($line -match "^(\w+)\s*:") { break }
            if ($line -match "^\-\s+(.+)$") { $items.Add($Matches[1].Trim().Trim("'`"")) }
            elseif ($line -match "^\s{2,}\-\s+(.+)$") { $items.Add($Matches[1].Trim().Trim("'`"")) }
        }
    }
    return , $items.ToArray()
}

$byId = @{}
$records = @()
Get-ChildItem -Path $featuresRoot -Recurse -File -Filter '*.md' | ForEach-Object {
    $rel = $_.FullName.Substring($featuresRoot.Length).TrimStart('\', '/')
    if ($rel -notmatch '(?i)feat-\d+[_-]') { return }
    $raw = Get-Content -LiteralPath $_.FullName -Raw -Encoding utf8
    $fm = Get-FrontmatterBlock $raw
    if (-not $fm) { return }
    $id = Get-YamlScalar $fm 'id'
    if (-not $id) { return }
    $parent = Get-YamlScalar $fm 'parent_feature'
    $area = Get-YamlScalar $fm 'feature_area'
    $depthStr = Get-YamlScalar $fm 'depth'
    $depth = $null
    if ($depthStr -match '^\d+$') { $depth = [int]$depthStr }
    $children = @(Get-YamlStringList $fm 'children')
    $rec = [pscustomobject]@{
        Path     = $rel
        FullPath = $_.FullName
        Id       = $id
        Parent   = $parent
        Area     = $area
        Depth    = $depth
        Children = $children
    }
    $records += $rec
    if ($byId.ContainsKey($id)) {
        $byId[$id] = @($byId[$id]) + $rec
    }
    else {
        $byId[$id] = @($rec)
    }
}

$issues = [System.Collections.Generic.List[string]]::new()

foreach ($id in $byId.Keys) {
    $xs = $byId[$id]
    if ($xs.Count -gt 1) {
        $paths = ($xs | ForEach-Object { $_.Path }) -join '; '
        $issues.Add("DUPLICATE_ID $id → $paths")
    }
}

$idSet = [System.Collections.Generic.HashSet[string]]::new([string[]]$byId.Keys, [StringComparer]::OrdinalIgnoreCase)
foreach ($r in $records) {
    if ($r.Parent) {
        if (-not $idSet.Contains($r.Parent)) {
            $issues.Add("MISSING_PARENT $($r.Id) parent_feature=$($r.Parent) file=$($r.Path)")
        }
    }
    foreach ($ch in $r.Children) {
        if (-not $ch) { continue }
        if (-not $idSet.Contains($ch)) {
            $issues.Add("STALE_CHILD $($r.Id) children entry '$ch' missing feat file=$($r.Path)")
        }
    }
    if ($null -ne $r.Depth) {
        $segs = ($r.Path -split '[\\/]').Count - 1
        if ($r.Depth -ne $segs) {
            $issues.Add("DEPTH_MISMATCH $($r.Id) depth=$($r.Depth) path_segments=$segs file=$($r.Path)")
        }
    }
}

foreach ($r in $records) {
    foreach ($ch in $r.Children) {
        if (-not $ch) { continue }
        $childRecs = $byId[$ch]
        if (-not $childRecs) { continue }
        foreach ($cr in $childRecs) {
            if ($cr.Parent -and $r.Id -and $cr.Parent -ne $r.Id) {
                $issues.Add("CHILD_PARENT_MISMATCH parent $($r.Id) lists child $ch but $ch has parent_feature=$($cr.Parent)")
            }
        }
    }
}

$issueCount = $issues.Count
if (-not $Json) {
    Write-Host "=== gald3r_feature_hierarchy_sync (dry-run) ==="
    Write-Host "Features scanned: $($records.Count)"
    if ($issueCount -eq 0) { Write-Host "OK: no hierarchy issues detected." }
    else {
        Write-Host "ISSUES ($issueCount):"
        $issues | ForEach-Object { Write-Host "  - $_" }
    }
}

$exit = if ($issueCount -eq 0) { 0 } else { 1 }
if ($WarnOnly) { $exit = 0 }

if ($Json) {
    $payload = @{
        status = if ($issueCount -eq 0) { 'ok' } else { 'issues' }
        issues = $issueCount
        detail = $issues.ToArray()
    } | ConvertTo-Json -Compress -Depth 5
    Write-Output $payload
}

exit $exit
