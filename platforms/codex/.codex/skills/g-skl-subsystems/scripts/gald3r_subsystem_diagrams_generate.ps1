<#
.SYNOPSIS
  Generate Mermaid architecture markdown under .gald3r/reports/architecture/

.DESCRIPTION
  Reads .gald3r/subsystems/*.md frontmatter and emits SYSTEM_ARCHITECTURE.md,
  SUBSYSTEM_TREE.md, DEPENDENCY_GRAPH.md. Hierarchy edges use parent_subsystem/domain/layer;
  dependency edges use dependencies: (separate graph). Safe to re-run; timestamps in header.

.PARAMETER ProjectRoot
  Repository root.
#>
[CmdletBinding()]
param([string]$ProjectRoot = (Get-Location).Path)

$ErrorActionPreference = 'Stop'
$subRoot = Join-Path (Join-Path $ProjectRoot '.gald3r') 'subsystems'
$outDir = Join-Path (Join-Path (Join-Path $ProjectRoot '.gald3r') 'reports') 'architecture'
if (-not (Test-Path $subRoot)) { throw "Missing $subRoot" }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

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
        }
    }
    return , $items.ToArray()
}

$nodes = [System.Collections.Generic.List[hashtable]]::new()
Get-ChildItem -Path $subRoot -Recurse -File -Filter '*.md' -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '^(SYSTEM_|SUBSYSTEM_TREE|DEPENDENCY_GRAPH)' } | ForEach-Object {
    $raw = Get-Content -LiteralPath $_.FullName -Raw -Encoding utf8
    $fm = Get-FrontmatterBlock $raw
    if (-not $fm) { return }
    $name = Get-YamlScalar $fm 'name'
    if (-not $name) { $name = $_.BaseName }
    $st = Get-YamlScalar $fm 'status'
    $domain = Get-YamlScalar $fm 'domain'
    if (-not $domain) { $domain = 'general' }
    $layer = Get-YamlScalar $fm 'layer'
    if (-not $layer) { $layer = 'unspecified' }
    $parent = Get-YamlScalar $fm 'parent_subsystem'
    $deps = @(Get-YamlStringList $fm 'dependencies')
    $nodes.Add(@{
            Name   = $name
            Status = $st
            Domain = $domain
            Layer  = $layer
            Parent = $parent
            Deps   = $deps
        })
}

$iso = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHHmmss') + 'Z'
$banner = @"
<!-- AUTO-GENERATED - do not hand-edit. Source: .gald3r_sys/skills/g-skl-subsystems/scripts/gald3r_subsystem_diagrams_generate.ps1 -->
<!-- Generated (UTC): $iso -->
<!-- Regenerate: pwsh -NoProfile -File .gald3r_sys/skills/g-skl-subsystems/scripts/gald3r_subsystem_diagrams_generate.ps1 -ProjectRoot (repo root) -->

"@

# --- SYSTEM_ARCHITECTURE overview ---
$arch = New-Object System.Text.StringBuilder
[void]$arch.AppendLine($banner)
[void]$arch.AppendLine('# System architecture overview')
[void]$arch.AppendLine('')
[void]$arch.AppendLine('Legend: **Domain** groups related subsystems. **Layer** is advisory (transport, policy, presentation, etc.). **Depends-on** edges are runtime/data coupling; **parent/child** is organizational containment from parent_subsystem metadata and nested spec paths.')
[void]$arch.AppendLine('')
$domains = $nodes | Group-Object { $_.Domain } | Sort-Object Name
foreach ($g in $domains) {
    [void]$arch.AppendLine("## Domain: $($g.Name)")
    foreach ($n in ($g.Group | Sort-Object Name)) {
        [void]$arch.AppendLine("- **$($n.Name)** - layer $($n.Layer) - status $($n.Status)")
    }
    [void]$arch.AppendLine('')
}
Set-Content -LiteralPath (Join-Path $outDir 'SYSTEM_ARCHITECTURE.md') -Value $arch.ToString() -Encoding utf8

# --- Tree (containment / hierarchy) ---
$tree = New-Object System.Text.StringBuilder
[void]$tree.AppendLine($banner)
[void]$tree.AppendLine('# Subsystem tree (hierarchy / grouping)')
[void]$tree.AppendLine('')
[void]$tree.AppendLine('```mermaid')
[void]$tree.AppendLine('flowchart TB')
foreach ($n in $nodes) {
    $id = ($n.Name -replace '[^a-zA-Z0-9_]', '_')
    $lbl = ('{0}<br/>{1} / {2}' -f $n.Name, $n.Domain, $n.Layer) -replace '"', "'"
    [void]$tree.AppendLine(('  {0}["{1}"]' -f $id, $lbl))
}
foreach ($n in $nodes) {
    if (-not $n.Parent) { continue }
    $cid = ($n.Name -replace '[^a-zA-Z0-9_]', '_')
    $parentNode = ($n.Parent -replace '[^a-zA-Z0-9_]', '_')
    [void]$tree.AppendLine("  $parentNode --> $cid")
}
[void]$tree.AppendLine('```')
[void]$tree.AppendLine('')
Set-Content -LiteralPath (Join-Path $outDir 'SUBSYSTEM_TREE.md') -Value $tree.ToString() -Encoding utf8

# --- Dependency graph ---
$dep = New-Object System.Text.StringBuilder
[void]$dep.AppendLine($banner)
[void]$dep.AppendLine('# Subsystem dependency graph (depends-on)')
[void]$dep.AppendLine('')
[void]$dep.AppendLine('```mermaid')
[void]$dep.AppendLine('flowchart LR')
foreach ($n in $nodes) {
    $id = ($n.Name -replace '[^a-zA-Z0-9_]', '_')
    $nm = ($n.Name -replace '"', "'")
    [void]$dep.AppendLine(('  {0}["{1}"]' -f $id, $nm))
}
foreach ($n in $nodes) {
    $tid = ($n.Name -replace '[^a-zA-Z0-9_]', '_')
    foreach ($d in $n.Deps) {
        if (-not $d) { continue }
        $did = ($d -replace '[^a-zA-Z0-9_]', '_')
        [void]$dep.AppendLine("  $did --> $tid")
    }
}
[void]$dep.AppendLine('```')
[void]$dep.AppendLine('')
Set-Content -LiteralPath (Join-Path $outDir 'DEPENDENCY_GRAPH.md') -Value $dep.ToString() -Encoding utf8

Write-Host "Wrote:"
Write-Host "  $(Join-Path $outDir 'SYSTEM_ARCHITECTURE.md')"
Write-Host "  $(Join-Path $outDir 'SUBSYSTEM_TREE.md')"
Write-Host "  $(Join-Path $outDir 'DEPENDENCY_GRAPH.md')"
