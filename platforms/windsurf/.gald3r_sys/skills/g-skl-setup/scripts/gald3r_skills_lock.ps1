<#
.SYNOPSIS
    Read/write/verify gald3r-skills-lock.json (T1043 / IDEA-HARVEST-136).

.DESCRIPTION
    Lock-file management for installed gald3r projects. Mirrors the caveman
    skills-lock.json pattern. Operations:

      WRITE   — scan installed platform skill copies, compute SHA-256 hashes,
                write gald3r-skills-lock.json.
      VERIFY  — recompute hashes against current files, classify each skill
                as unchanged | updated | tampered | missing.
      UPGRADE — recompute hashes; for each entry, compare against the
                canonical source under -SourceRoot. Classify each skill as
                unchanged | local-modified | upstream-changed | both-changed
                | new (in source, not in lock) | removed (in lock, missing in source).
      READ    — print the parsed lock JSON to stdout.

    Lock format (version 1):
      {
        "version": 1,
        "gald3r_version": "x.y.z",
        "installed_date": "ISO-8601",
        "skills": {
          "<slug>": {
            "source": "github:gald3r/gald3r",
            "path": ".cursor/skills/<slug>/SKILL.md",
            "sha256_hash": "...",
            "tier": "full|slim|adv|unknown",
            "installed_at": "ISO-8601"
          }
        }
      }

.PARAMETER Action
    WRITE | VERIFY | UPGRADE | READ.

.PARAMETER ProjectPath
    Installed project root. Default: current directory.

.PARAMETER SourceRoot
    Canonical gald3r source (for UPGRADE). Default: gald3r_dev parent of this script.

.PARAMETER LockFile
    Lock file relative path (default: gald3r-skills-lock.json at project root).

.PARAMETER Tier
    Tier tag for WRITE (full|slim|adv). Default: unknown.

.PARAMETER Json
    Emit machine-readable JSON instead of human report.

.EXAMPLE
    .\scripts\gald3r_skills_lock.ps1 -Action WRITE -ProjectPath . -Tier full

.EXAMPLE
    .\scripts\gald3r_skills_lock.ps1 -Action VERIFY -Json
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('WRITE', 'VERIFY', 'UPGRADE', 'READ')]
    [string]$Action,

    [string]$ProjectPath = (Get-Location).Path,
    [string]$SourceRoot  = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$LockFile    = 'gald3r-skills-lock.json',
    [ValidateSet('full', 'slim', 'adv', 'unknown')]
    [string]$Tier        = 'unknown',
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$LOCK_VERSION = 1

# Platform skill directories to scan (in install priority order)
$PLATFORM_DIRS = @('.cursor/skills', '.claude/skills', '.agent/skills', '.codex/skills', '.opencode/skills')

function Get-Gald3rVersion {
    param([string]$Root)
    $changelog = Join-Path $Root 'CHANGELOG.md'
    if (-not (Test-Path $changelog)) { return 'unknown' }
    $content = Get-Content $changelog -Raw
    $match = [regex]::Match($content, '(?m)^## \[(\d+\.\d+\.\d+[^\]]*)\]')
    if ($match.Success) { return $match.Groups[1].Value }
    return 'unreleased'
}

function Get-FileSha256 {
    param([string]$Path)
    (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLower()
}

function Find-InstalledSkills {
    param([string]$Root)
    $found = @{}
    foreach ($dir in $PLATFORM_DIRS) {
        $base = Join-Path $Root $dir
        if (-not (Test-Path $base)) { continue }
        Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $skillFile = Join-Path $_.FullName 'SKILL.md'
            if (Test-Path $skillFile) {
                if (-not $found.ContainsKey($_.Name)) {
                    $rootResolved = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\','/')
                    $absResolved  = (Resolve-Path -LiteralPath $skillFile).Path
                    $relNorm = $absResolved.Substring($rootResolved.Length).TrimStart('\','/') -replace '\\','/'
                    $found[$_.Name] = @{
                        slug = $_.Name
                        abs  = $skillFile
                        rel  = $relNorm
                    }
                }
            }
        }
    }
    return $found
}

function Action-Write {
    param([string]$Root, [string]$LockPath, [string]$TierTag)

    $skills = Find-InstalledSkills -Root $Root
    if ($skills.Count -eq 0) {
        Write-Warning "No installed skills found under platform dirs: $($PLATFORM_DIRS -join ', ')"
    }

    $now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $lock = [ordered]@{
        version        = $LOCK_VERSION
        gald3r_version = Get-Gald3rVersion -Root $Root
        installed_date = $now
        tier           = $TierTag
        skills         = [ordered]@{}
    }

    foreach ($slug in ($skills.Keys | Sort-Object)) {
        $s = $skills[$slug]
        $lock.skills[$slug] = [ordered]@{
            source       = 'github:gald3r/gald3r'
            path         = $s.rel
            sha256_hash  = Get-FileSha256 -Path $s.abs
            tier         = $TierTag
            installed_at = $now
        }
    }

    $json = $lock | ConvertTo-Json -Depth 6
    Set-Content -LiteralPath $LockPath -Value $json -Encoding UTF8 -NoNewline
    Add-Content -LiteralPath $LockPath -Value "`n" -Encoding UTF8

    if ($Json) {
        @{ action = 'WRITE'; lock_path = $LockPath; skills_count = $skills.Count; gald3r_version = $lock.gald3r_version; tier = $TierTag } | ConvertTo-Json
    } else {
        Write-Host "Wrote $LockPath"
        Write-Host "  gald3r_version : $($lock.gald3r_version)"
        Write-Host "  tier           : $TierTag"
        Write-Host "  skills hashed  : $($skills.Count)"
    }
}

function Action-Verify {
    param([string]$Root, [string]$LockPath)

    if (-not (Test-Path $LockPath)) {
        throw "Lock file not found: $LockPath. Run -Action WRITE first."
    }
    $lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json

    $report = [ordered]@{
        unchanged = @()
        tampered  = @()
        missing   = @()
    }

    foreach ($prop in $lock.skills.PSObject.Properties) {
        $slug = $prop.Name
        $entry = $prop.Value
        $abs = Join-Path $Root $entry.path
        if (-not (Test-Path $abs)) {
            $report.missing += $slug
            continue
        }
        $cur = Get-FileSha256 -Path $abs
        if ($cur -eq $entry.sha256_hash) {
            $report.unchanged += $slug
        } else {
            $report.tampered += $slug
        }
    }

    if ($Json) {
        @{
            action     = 'VERIFY'
            lock_path  = $LockPath
            counts     = @{
                unchanged = $report.unchanged.Count
                tampered  = $report.tampered.Count
                missing   = $report.missing.Count
            }
            tampered   = $report.tampered
            missing    = $report.missing
        } | ConvertTo-Json -Depth 4
    } else {
        Write-Host "VERIFY against $LockPath"
        Write-Host "  unchanged : $($report.unchanged.Count)"
        Write-Host "  tampered  : $($report.tampered.Count)"
        Write-Host "  missing   : $($report.missing.Count)"
        if ($report.tampered.Count -gt 0) {
            Write-Host ""
            Write-Host "Tampered skills (local hash != lock hash):" -ForegroundColor Yellow
            $report.tampered | ForEach-Object { Write-Host "  - $_" }
        }
        if ($report.missing.Count -gt 0) {
            Write-Host ""
            Write-Host "Missing skills (in lock, not on disk):" -ForegroundColor Yellow
            $report.missing | ForEach-Object { Write-Host "  - $_" }
        }
    }

    if ($report.tampered.Count -gt 0 -or $report.missing.Count -gt 0) {
        exit 1
    }
}

function Action-Upgrade {
    param([string]$Root, [string]$Source, [string]$LockPath)

    if (-not (Test-Path $LockPath)) {
        throw "Lock file not found: $LockPath. Run -Action WRITE first."
    }
    $lock = Get-Content -LiteralPath $LockPath -Raw | ConvertFrom-Json

    $local  = Find-InstalledSkills -Root $Root
    $source = Find-InstalledSkills -Root $Source

    $report = [ordered]@{
        unchanged        = @()
        local_modified   = @()  # tampered locally; source matches lock
        upstream_changed = @()  # source moved on; local still matches lock
        both_changed     = @()  # local AND source both differ from lock (rare)
        new              = @()  # in source, not in lock
        removed          = @()  # in lock, no longer in source
    }

    $lockSlugs = @{}
    foreach ($prop in $lock.skills.PSObject.Properties) { $lockSlugs[$prop.Name] = $prop.Value }

    foreach ($slug in $lockSlugs.Keys) {
        $entry = $lockSlugs[$slug]
        $lockHash = $entry.sha256_hash
        $localCur  = if ($local.ContainsKey($slug))  { Get-FileSha256 -Path $local[$slug].abs }  else { $null }
        $sourceCur = if ($source.ContainsKey($slug)) { Get-FileSha256 -Path $source[$slug].abs } else { $null }

        if (-not $sourceCur) {
            $report.removed += $slug
        } elseif ($localCur -eq $lockHash -and $sourceCur -eq $lockHash) {
            $report.unchanged += $slug
        } elseif ($localCur -ne $lockHash -and $sourceCur -eq $lockHash) {
            $report.local_modified += $slug
        } elseif ($localCur -eq $lockHash -and $sourceCur -ne $lockHash) {
            $report.upstream_changed += $slug
        } else {
            $report.both_changed += $slug
        }
    }

    foreach ($slug in $source.Keys) {
        if (-not $lockSlugs.ContainsKey($slug)) {
            $report.new += $slug
        }
    }

    if ($Json) {
        @{
            action   = 'UPGRADE'
            lock_path = $LockPath
            source   = $Source
            counts   = @{
                unchanged        = $report.unchanged.Count
                local_modified   = $report.local_modified.Count
                upstream_changed = $report.upstream_changed.Count
                both_changed     = $report.both_changed.Count
                new              = $report.new.Count
                removed          = $report.removed.Count
            }
            local_modified   = $report.local_modified
            upstream_changed = $report.upstream_changed
            both_changed     = $report.both_changed
            new              = $report.new
            removed          = $report.removed
        } | ConvertTo-Json -Depth 4
    } else {
        Write-Host "UPGRADE classification (lock vs local vs $Source)"
        Write-Host "  unchanged        : $($report.unchanged.Count)"
        Write-Host "  local-modified   : $($report.local_modified.Count)"
        Write-Host "  upstream-changed : $($report.upstream_changed.Count)"
        Write-Host "  both-changed     : $($report.both_changed.Count)"
        Write-Host "  new (in source)  : $($report.new.Count)"
        Write-Host "  removed          : $($report.removed.Count)"
        foreach ($cat in @('local_modified','upstream_changed','both_changed','new','removed')) {
            $items = $report[$cat]
            if ($items.Count -gt 0) {
                Write-Host ""
                Write-Host ("{0}:" -f ($cat -replace '_','-')) -ForegroundColor Cyan
                $items | ForEach-Object { Write-Host "  - $_" }
            }
        }
    }
}

function Action-Read {
    param([string]$LockPath)
    if (-not (Test-Path $LockPath)) {
        throw "Lock file not found: $LockPath"
    }
    Get-Content -LiteralPath $LockPath -Raw
}

# --- Dispatch ----------------------------------------------------------------

$ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
$lockPath = Join-Path $ProjectPath $LockFile

Push-Location $ProjectPath
try {
    switch ($Action) {
        'WRITE'   { Action-Write   -Root $ProjectPath -LockPath $lockPath -TierTag $Tier }
        'VERIFY'  { Action-Verify  -Root $ProjectPath -LockPath $lockPath }
        'UPGRADE' { Action-Upgrade -Root $ProjectPath -Source $SourceRoot -LockPath $lockPath }
        'READ'    { Action-Read    -LockPath $lockPath }
    }
} finally {
    Pop-Location
}
