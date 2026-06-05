<#
.SYNOPSIS
    Retrofit Obsidian/VAULT_OBSIDIAN_STANDARD YAML frontmatter onto vault notes
    that are missing it (T1334). Backup-first, dry-run by default, idempotent.

.DESCRIPTION
    Walks the vault for long-lived notes missing a leading `---` frontmatter block
    and prepends a conformant block. Targets:
      projects/*/memory.md      -> type: session
      projects/*/sessions/*.md  -> type: session
      projects/*/decisions/*.md -> type: decision (+ decision_status, decided_on)
      knowledge/*.md            -> type: knowledge_card

    Existing content is preserved byte-for-byte beneath the inserted block. Files
    that already have valid frontmatter are skipped (idempotent). Symlinked or
    read-only files are skipped with a warning.

    DRY-RUN by default — shows the planned per-file frontmatter. Pass -Apply to
    write; each modified file is backed up to {vault}/.backups/{timestamp}/<relpath>
    before the write.

.PARAMETER VaultLocation
    Vault root. Defaults to vault_location= in .gald3r/.identity (walk-up).

.PARAMETER File
    Single-file mode: retrofit just this one .md file.

.PARAMETER Apply
    Perform writes (with backup). Omit for dry-run.

.PARAMETER ProjectName
    Project name for source/topics. Defaults to .identity project_name or 'unknown'.

.EXAMPLE
    pwsh -File frontmatter_fix.ps1                 # dry-run, whole vault
    pwsh -File frontmatter_fix.ps1 -Apply
    pwsh -File frontmatter_fix.ps1 -File "<path>" -Apply
#>
[CmdletBinding()]
param(
    [string]$VaultLocation,
    [string]$File,
    [switch]$Apply,
    [string]$ProjectName
)

$ErrorActionPreference = 'Stop'

function Find-ProjectRoot {
    $dir = $PSScriptRoot
    for ($i = 0; $i -lt 12 -and $dir; $i++) {
        if (Test-Path (Join-Path $dir '.gald3r')) { return $dir }
        $p = Split-Path $dir -Parent; if ($p -eq $dir) { break }; $dir = $p
    }
    return (Get-Location).Path
}

function Get-IdentityValue {
    param([string]$Root, [string]$Key)
    $id = Join-Path $Root '.gald3r/.identity'
    if (Test-Path $id) {
        $line = Select-String -Path $id -Pattern "^\s*$Key\s*=\s*(.+)\s*$" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($line) { return $line.Matches[0].Groups[1].Value.Trim() }
    }
    return $null
}

$root = Find-ProjectRoot
if (-not $VaultLocation) { $VaultLocation = Get-IdentityValue -Root $root -Key 'vault_location' }
if (-not $ProjectName)   { $ProjectName   = Get-IdentityValue -Root $root -Key 'project_name' }
if (-not $ProjectName)   { $ProjectName   = 'unknown' }
if (-not $VaultLocation -or $VaultLocation -eq '{LOCAL}') {
    Write-Warning "No shared vault_location configured (value: '$VaultLocation'). Nothing to walk."
    exit 0
}
if (-not (Test-Path $VaultLocation)) {
    Write-Warning "Vault path '$VaultLocation' does not exist."
    exit 1
}

# Does the file already start with a YAML frontmatter fence?
function Test-HasFrontmatter {
    param([string]$Path)
    $first = Get-Content -LiteralPath $Path -TotalCount 1 -ErrorAction SilentlyContinue
    return ($first -ne $null -and $first.Trim() -eq '---')
}

function Get-NoteType {
    param([string]$RelPath)
    if ($RelPath -match '[\\/]decisions[\\/]') { return 'decision' }
    if ($RelPath -match '[\\/]sessions[\\/]')  { return 'session' }
    if ($RelPath -match '[\\/]knowledge[\\/]') { return 'knowledge_card' }
    if ($RelPath -match 'memory\.md$')         { return 'session' }
    return 'session'
}

function Get-Title {
    param([string]$Path)
    $h = Select-String -Path $Path -Pattern '^\#\s+(.+)$' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($h) { return $h.Matches[0].Groups[1].Value.Trim() }
    return [System.IO.Path]::GetFileNameWithoutExtension($Path)
}

function New-Frontmatter {
    param([string]$Path, [string]$RelPath)
    $type  = Get-NoteType -RelPath $RelPath
    $title = Get-Title -Path $Path
    $date  = (Get-Item -LiteralPath $Path).LastWriteTime.ToString('yyyy-MM-dd')
    $topics = @('memory', $type, $ProjectName) | Select-Object -Unique
    $topicsStr = '[' + (($topics) -join ', ') + ']'
    $lines = @('---')
    $lines += "date: $date"
    $lines += "type: $type"
    $lines += 'ingestion_type: agent'
    $lines += "source: gald3r-$ProjectName"
    $lines += "title: `"$($title -replace '"','\"')`""
    $lines += "topics: $topicsStr"
    if ($type -eq 'decision') {
        $lines += 'decision_status: active'
        $lines += "decided_on: $date"
    }
    $lines += '---'
    return ($lines -join "`n")
}

# Build the candidate list.
$candidates = @()
if ($File) {
    if (-not (Test-Path $File)) { Write-Warning "File not found: $File"; exit 1 }
    $candidates = @((Get-Item -LiteralPath $File))
} else {
    $globs = @(
        (Join-Path $VaultLocation 'projects'),
        (Join-Path $VaultLocation 'knowledge')
    )
    foreach ($g in $globs) {
        if (Test-Path $g) {
            $candidates += Get-ChildItem -Path $g -Recurse -Filter '*.md' -File -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.FullName -match 'memory\.md$' -or
                    $_.FullName -match '[\\/]sessions[\\/]' -or
                    $_.FullName -match '[\\/]decisions[\\/]' -or
                    $_.FullName -match '[\\/]knowledge[\\/]'
                }
        }
    }
}

$ts = (Get-Date).ToString('yyyyMMdd_HHmmss')
$backupRoot = Join-Path $VaultLocation ".backups/$ts"
$report = @()
$toFix = @()

foreach ($c in $candidates) {
    $rel = $c.FullName.Substring($VaultLocation.TrimEnd('\','/').Length).TrimStart('\','/')
    if (Test-HasFrontmatter -Path $c.FullName) {
        $report += [pscustomobject]@{ File = $rel; Status = 'ok (has frontmatter)' }
        continue
    }
    # skip read-only / reparse points (symlinks)
    if ($c.Attributes -band [IO.FileAttributes]::ReadOnly) { $report += [pscustomobject]@{ File = $rel; Status = 'SKIP read-only' }; continue }
    if ($c.Attributes -band [IO.FileAttributes]::ReparsePoint) { $report += [pscustomobject]@{ File = $rel; Status = 'SKIP symlink' }; continue }
    $toFix += $c
    $report += [pscustomobject]@{ File = $rel; Status = 'NEEDS frontmatter' }
}

Write-Host "=== Vault frontmatter scan: $VaultLocation ===" -ForegroundColor Cyan
$report | ForEach-Object { Write-Host ("  [{0}] {1}" -f $_.Status, $_.File) }
Write-Host ("Total: {0} scanned, {1} need frontmatter." -f $report.Count, $toFix.Count)

if ($toFix.Count -eq 0) { Write-Host "Nothing to retrofit. Idempotent no-op." -ForegroundColor Green; exit 0 }

if (-not $Apply) {
    Write-Host "`n--- DRY RUN (pass -Apply to write; backups go to $backupRoot) ---" -ForegroundColor Yellow
    foreach ($f in $toFix) {
        $rel = $f.FullName.Substring($VaultLocation.TrimEnd('\','/').Length).TrimStart('\','/')
        Write-Host "`n# would prepend to: $rel" -ForegroundColor Yellow
        Write-Host (New-Frontmatter -Path $f.FullName -RelPath $rel)
    }
    exit 0
}

# Apply: backup then prepend.
$enc = New-Object System.Text.UTF8Encoding($false)
foreach ($f in $toFix) {
    $rel = $f.FullName.Substring($VaultLocation.TrimEnd('\','/').Length).TrimStart('\','/')
    $backupPath = Join-Path $backupRoot $rel
    $backupDir = Split-Path $backupPath -Parent
    if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir -Force | Out-Null }
    Copy-Item -LiteralPath $f.FullName -Destination $backupPath -Force
    $fm = New-Frontmatter -Path $f.FullName -RelPath $rel
    $body = [System.IO.File]::ReadAllText($f.FullName)
    [System.IO.File]::WriteAllText($f.FullName, $fm + "`n`n" + $body, $enc)
    Write-Host "  retrofitted: $rel (backup: .backups/$ts/$rel)" -ForegroundColor Green
}
Write-Host ("`nDone. {0} file(s) retrofitted; backups in {1}" -f $toFix.Count, $backupRoot) -ForegroundColor Green
