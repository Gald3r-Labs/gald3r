#!/usr/bin/env pwsh
# gald3r_validate.ps1 — Zero-dependency gald3r structure integrity check (T1012)
# Exit 0 = PASS, Exit 1 = FAIL (violations listed)
# Usage: powershell -File gald3r_validate.ps1 [--fix] [--json] [--project-root <path>] [--report]

param(
    [switch]$Fix,
    [switch]$Json,
    [switch]$Report,
    [string]$ProjectRoot = ""
)

$violations = @()
$warnings = @()

# Auto-discover project root
function Find-GaldRoot {
    param([string]$StartPath = (Get-Location).Path)
    $current = $StartPath
    for ($i = 0; $i -lt 8; $i++) {
        if (Test-Path (Join-Path $current ".gald3r")) { return $current }
        $parent = Split-Path $current -Parent
        if (-not $parent -or $parent -eq $current) { break }
        $current = $parent
    }
    return $null
}

if ($ProjectRoot -eq "") {
    $ProjectRoot = Find-GaldRoot
    if (-not $ProjectRoot) {
        Write-Host "gald3r validate: FAIL - .gald3r/ not found in current dir or any parent"
        exit 1
    }
}

$galdDir = Join-Path $ProjectRoot ".gald3r"
$tasksDir = Join-Path $galdDir "tasks"

# ── CHECK 1: .gald3r/ exists ──────────────────────────────────────────────────
if (-not (Test-Path $galdDir)) {
    $violations += "MISSING: .gald3r/ directory"
    if ($Fix) {
        New-Item -ItemType Directory -Path $galdDir -Force | Out-Null
        $violations[-1] += " [FIXED: created]"
    }
}

# ── CHECK 2: Required root files ─────────────────────────────────────────────
$requiredFiles = @("TASKS.md", "PROJECT.md", "CONSTRAINTS.md", "BUGS.md", "SUBSYSTEMS.md")
foreach ($file in $requiredFiles) {
    $path = Join-Path $galdDir $file
    if (-not (Test-Path $path)) {
        $violations += "MISSING: .gald3r/$file"
    }
}

# ── CHECK 3: tasks/ directory ────────────────────────────────────────────────
if (-not (Test-Path $tasksDir)) {
    $violations += "MISSING: .gald3r/tasks/ directory"
    if ($Fix) {
        foreach ($sub in @("open","in-progress","awaiting-verification","completed")) {
            New-Item -ItemType Directory -Path (Join-Path $tasksDir $sub) -Force | Out-Null
        }
        $violations[-1] += " [FIXED: created with subdirs]"
    }
}

# ── CHECK 4: Task file YAML frontmatter ──────────────────────────────────────
if (Test-Path $tasksDir) {
    Get-ChildItem $tasksDir -Recurse -Filter "*.md" | ForEach-Object {
        $content = Get-Content $_.FullName -Raw
        foreach ($field in @("id:", "title:", "status:", "type:")) {
            if ($content -notmatch "^$field" -and $content -notmatch "`n$field") {
                $violations += "MISSING_FIELD: $($_.Name) missing '$field'"
            }
        }
    }
}

# ── CHECK 5: Phantom detection (TASKS.md refs non-existent task files) ────────
$tasksIndexPath = Join-Path $galdDir "TASKS.md"
if (Test-Path $tasksIndexPath) {
    $tasksIndex = Get-Content $tasksIndexPath -Raw
    $refs = [regex]::Matches($tasksIndex, 'tasks/[^)]+\.md')
    foreach ($ref in $refs) {
        $refPath = Join-Path $galdDir $ref.Value
        if (-not (Test-Path $refPath)) {
            $violations += "PHANTOM: TASKS.md references missing file: $($ref.Value)"
        }
    }
}

# ── CHECK 6: Orphan detection (task files not in TASKS.md) ───────────────────
if ((Test-Path $tasksDir) -and (Test-Path $tasksIndexPath)) {
    $tasksIndex = Get-Content $tasksIndexPath -Raw
    Get-ChildItem $tasksDir -Recurse -Filter "task*.md" | ForEach-Object {
        $relPath = $_.FullName.Replace($galdDir + "\", "").Replace("\", "/")
        if ($tasksIndex -notmatch [regex]::Escape($_.BaseName)) {
            $warnings += "ORPHAN: $relPath not referenced in TASKS.md"
        }
    }
}

# ── CHECK 7: Subsystem spec files have locations: ────────────────────────────
$subsystemsDir = Join-Path $galdDir "subsystems"
if (Test-Path $subsystemsDir) {
    Get-ChildItem $subsystemsDir -Filter "*.md" | ForEach-Object {
        $content = Get-Content $_.FullName -Raw
        if ($content -notmatch "locations:") {
            $warnings += "INCOMPLETE: subsystems/$($_.Name) missing 'locations:' in frontmatter"
        }
    }
}

# ── REPORT ───────────────────────────────────────────────────────────────────
$totalViolations = $violations.Count
$totalWarnings = $warnings.Count

if ($Json) {
    $result = @{
        pass = ($totalViolations -eq 0)
        violations = $violations
        warnings = $warnings
        project_root = $ProjectRoot
    } | ConvertTo-Json -Depth 3
    Write-Output $result
} elseif ($Report) {
    if ($totalViolations -eq 0 -and $totalWarnings -eq 0) {
        Write-Host "gald3r validate: PASS" -ForegroundColor Green
        Write-Host "  Project root: $ProjectRoot"
        Write-Host "  All structural checks passed."
    } else {
        if ($totalViolations -gt 0) {
            Write-Host "gald3r validate: FAIL ($totalViolations violations, $totalWarnings warnings)" -ForegroundColor Red
        } else {
            Write-Host "gald3r validate: PASS with warnings ($totalWarnings warnings)" -ForegroundColor Yellow
        }
        Write-Host "  Project root: $ProjectRoot"
        foreach ($v in $violations) { Write-Host "  ❌ $v" -ForegroundColor Red }
        foreach ($w in $warnings) { Write-Host "  ⚠️  $w" -ForegroundColor Yellow }
    }
} else {
    # Default: simple output
    if ($totalViolations -eq 0) {
        Write-Host "gald3r validate: PASS"
    } else {
        Write-Host "gald3r validate: FAIL ($totalViolations violations)"
        foreach ($v in $violations) { Write-Host "  $v" }
    }
    if ($totalWarnings -gt 0 -and $Report) {
        foreach ($w in $warnings) { Write-Host "  WARN: $w" }
    }
}

if ($totalViolations -gt 0) { exit 1 } else { exit 0 }
