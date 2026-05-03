param(
    [string]$SourcePath = "",
    [string]$DestinationPath = "",
    [switch]$Force
)

. "$PSScriptRoot\g-hk-vault-resolve.ps1"

if (-not $SourcePath) {
    $SourcePath = $VaultLocalPath
}
if (-not $DestinationPath) {
    $DestinationPath = $VaultPath
}

if ($SourcePath -eq $DestinationPath) {
    Write-Host "Source and destination are the same. Nothing to migrate."
    exit 0
}

if (-not (Test-Path $SourcePath)) {
    Write-Host "Source path does not exist: $SourcePath"
    exit 1
}

if (-not (Test-Path $DestinationPath)) {
    New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
}

function Get-FileHashSafe {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $null
    }
    try {
        return (Get-FileHash -Path $Path -Algorithm SHA256).Hash
    } catch {
        return $null
    }
}

function Get-NoteDate {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return [datetime]::MinValue
    }

    try {
        $raw = Get-Content $Path -Raw -Encoding UTF8
        if ($raw -match '(?s)^---\r?\n(.+?)\r?\n---' -and $Matches[1] -match '(?m)^date:\s*(.+)$') {
            return [datetime]::Parse($Matches[1].Trim())
        }
    } catch {}

    return (Get-Item $Path).LastWriteTimeUtc
}

function Merge-LogFile {
    param(
        [string]$SourceLog,
        [string]$DestinationLog
    )

    $blocks = @()
    foreach ($path in @($DestinationLog, $SourceLog)) {
        if (Test-Path $path) {
            $raw = Get-Content $path -Raw -Encoding UTF8
            if ($raw) {
                $raw -split "(?=^## )" -im | ForEach-Object {
                    $block = $_.Trim()
                    if ($block) {
                        $blocks += $block
                    }
                }
            }
        }
    }

    $merged = $blocks | Select-Object -Unique
    if ($merged.Count -gt 0) {
        Set-Content -Path $DestinationLog -Value (($merged -join "`r`n`r`n") + "`r`n") -Encoding UTF8
    }
}

$copied = 0
$updated = 0
$skipped = 0
$conflicts = @()

$sourceFiles = Get-ChildItem -Path $SourcePath -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\.obsidian(\|\\)" }

foreach ($file in $sourceFiles) {
    $relativePath = $file.FullName.Substring($SourcePath.Length).TrimStart('\')
    $targetPath = Join-Path $DestinationPath $relativePath
    $targetDir = Split-Path $targetPath -Parent

    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    if ($file.Name -eq "log.md") {
        Merge-LogFile -SourceLog $file.FullName -DestinationLog $targetPath
        continue
    }

    $sourceHash = Get-FileHashSafe -Path $file.FullName
    $targetHash = Get-FileHashSafe -Path $targetPath

    if (-not $targetHash) {
        Copy-Item -Path $file.FullName -Destination $targetPath -Force
        $copied++
        continue
    }

    if ($sourceHash -eq $targetHash) {
        $skipped++
        continue
    }

    $sourceDate = Get-NoteDate -Path $file.FullName
    $targetDate = Get-NoteDate -Path $targetPath

    if ($Force -or $sourceDate -ge $targetDate) {
        Copy-Item -Path $file.FullName -Destination $targetPath -Force
        $updated++
    } else {
        $skipped++
        $conflicts += $relativePath
    }
}

& (Join-Path $PSScriptRoot "g-hk-vault-reindex.ps1") -VaultOverride $DestinationPath | Out-Null

Write-Host "Vault migration summary"
Write-Host "  source: $SourcePath"
Write-Host "  destination: $DestinationPath"
Write-Host "  copied: $copied"
Write-Host "  updated: $updated"
Write-Host "  skipped: $skipped"
if ($conflicts.Count -gt 0) {
    Write-Host "  conflicts kept at destination:"
    $conflicts | ForEach-Object { Write-Host "    - $_" }
}
