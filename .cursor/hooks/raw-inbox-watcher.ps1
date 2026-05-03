# raw-inbox-watcher.ps1 - Vault Raw Inbox processor (Phase 2, manual trigger only)
#
# Scans {vault}/raw/ for dropped files, classifies each by extension/contents
# (rules-based, no LLM — that lives in Phase 3), and routes to the appropriate
# vault destination via the existing g-skl-ingest-* skills. On success files
# move to {vault}/raw/processed/YYYY-MM-DD/. On failure they move to
# {vault}/raw/failed/ alongside an error.md sibling explaining the reason.
#
# Phase 2 explicitly does NOT install a FileSystemWatcher service. It is
# invoked manually via @g-vault-process-inbox or directly:
#
#   pwsh .cursor/hooks/raw-inbox-watcher.ps1
#   pwsh .cursor/hooks/raw-inbox-watcher.ps1 -DryRun
#   pwsh .cursor/hooks/raw-inbox-watcher.ps1 -Verbose
#
# Re-running on an empty raw/ is a no-op.

[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$VaultPathOverride
)

$ErrorActionPreference = "Stop"

# ── Vault path resolution ────────────────────────────────────────────────────
if ($VaultPathOverride) {
    $VaultPath = $VaultPathOverride
} else {
    $resolveScript = Join-Path $PSScriptRoot "g-hk-vault-resolve.ps1"
    if (-not (Test-Path $resolveScript)) {
        Write-Error "raw-inbox-watcher: g-hk-vault-resolve.ps1 not found at $resolveScript"
        exit 1
    }
    . $resolveScript
}

if (-not (Test-Path $VaultPath)) {
    Write-Host "raw-inbox-watcher: vault path '$VaultPath' does not exist — nothing to do."
    exit 0
}

$rawDir       = Join-Path $VaultPath "raw"
$today        = (Get-Date -Format "yyyy-MM-dd")
$processedDir = Join-Path (Join-Path $rawDir "processed") $today
$failedDir    = Join-Path $rawDir "failed"

if (-not (Test-Path $rawDir)) {
    Write-Host "raw-inbox-watcher: $rawDir does not exist — nothing to do."
    exit 0
}

# ── Idempotent no-op on empty inbox ──────────────────────────────────────────
$candidates = @(
    Get-ChildItem -Path $rawDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne "README.md" }
)

if ($candidates.Count -eq 0) {
    Write-Host "raw-inbox-watcher: inbox empty — no work."
    exit 0
}

if (-not $DryRun) {
    if (-not (Test-Path $processedDir)) { New-Item -ItemType Directory -Path $processedDir -Force | Out-Null }
    if (-not (Test-Path $failedDir))    { New-Item -ItemType Directory -Path $failedDir    -Force | Out-Null }
}

# ── Helpers ───────────────────────────────────────────────────────────────────
function Find-IngestScript {
    param([string]$RelativePath)

    $current = Get-Location
    for ($i = 0; $i -lt 8; $i++) {
        $candidate = Join-Path $current $RelativePath
        if (Test-Path $candidate) { return $candidate }
        $parent = Split-Path $current -Parent
        if (-not $parent -or $parent -eq $current) { break }
        $current = $parent
    }
    return $null
}

function Get-FileClassification {
    param([System.IO.FileInfo]$File)

    $ext = $File.Extension.ToLowerInvariant()

    switch ($ext) {
        ".md" {
            return [PSCustomObject]@{ Kind = "markdown"; Reason = "markdown article" }
        }
        ".txt" {
            try {
                $content = (Get-Content -Path $File.FullName -Raw -ErrorAction Stop).Trim()
            } catch {
                return [PSCustomObject]@{ Kind = "unreadable"; Reason = "could not read text body: $_" }
            }
            $lines = @($content -split "\r?\n" | Where-Object { $_.Trim() -ne "" })
            if ($lines.Count -eq 1 -and $lines[0] -match '^https?://') {
                $url = $lines[0].Trim()
                if ($url -match 'youtube\.com|youtu\.be') {
                    return [PSCustomObject]@{ Kind = "youtube_url"; Reason = "single YouTube URL"; Url = $url }
                }
                return [PSCustomObject]@{ Kind = "single_url"; Reason = "single URL"; Url = $url }
            }
            return [PSCustomObject]@{ Kind = "text_article"; Reason = "multi-line text article" }
        }
        ".pdf" {
            return [PSCustomObject]@{ Kind = "deferred_phase3"; Reason = "PDF requires Phase 3 (LLM + extractor)" }
        }
        ".png" {
            return [PSCustomObject]@{ Kind = "deferred_phase3"; Reason = "Image requires Phase 3 (vision classifier)" }
        }
        ".jpg" {
            return [PSCustomObject]@{ Kind = "deferred_phase3"; Reason = "Image requires Phase 3 (vision classifier)" }
        }
        ".jpeg" {
            return [PSCustomObject]@{ Kind = "deferred_phase3"; Reason = "Image requires Phase 3 (vision classifier)" }
        }
        default {
            return [PSCustomObject]@{ Kind = "unknown"; Reason = "no rule for extension '$ext'" }
        }
    }
}

function Move-ToProcessed {
    param([System.IO.FileInfo]$File)
    if ($DryRun) { return $true }
    try {
        $dest = Join-Path $processedDir $File.Name
        if (Test-Path $dest) {
            $stamp = (Get-Date -Format "HHmmss")
            $base = [System.IO.Path]::GetFileNameWithoutExtension($File.Name)
            $ext  = [System.IO.Path]::GetExtension($File.Name)
            $dest = Join-Path $processedDir "${base}_${stamp}${ext}"
        }
        Move-Item -Path $File.FullName -Destination $dest -Force
        return $true
    } catch {
        Write-Warning "raw-inbox-watcher: could not move $($File.Name) to processed/: $_"
        return $false
    }
}

function Move-ToFailed {
    param(
        [System.IO.FileInfo]$File,
        [string]$Reason
    )
    if ($DryRun) { return }
    try {
        $dest = Join-Path $failedDir $File.Name
        if (Test-Path $dest) {
            $stamp = (Get-Date -Format "yyyyMMdd_HHmmss")
            $base = [System.IO.Path]::GetFileNameWithoutExtension($File.Name)
            $ext  = [System.IO.Path]::GetExtension($File.Name)
            $dest = Join-Path $failedDir "${base}_${stamp}${ext}"
        }
        Move-Item -Path $File.FullName -Destination $dest -Force
        $errorMd = "$dest.error.md"
        $body = @"
# raw-inbox-watcher failure

- **File**: $($File.Name)
- **Date**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
- **Reason**: $Reason

This file was moved to ``raw/failed/`` because the Phase 2 watcher could not
route it. To retry, move the file back into ``vault/raw/`` and re-run
``@g-vault-process-inbox`` (or pwsh .cursor/hooks/raw-inbox-watcher.ps1).
"@
        Set-Content -Path $errorMd -Value $body -Encoding UTF8 -NoNewline
    } catch {
        Write-Warning "raw-inbox-watcher: could not move $($File.Name) to failed/: $_"
    }
}

function Add-VaultLogEntry {
    param(
        [int]$Processed,
        [int]$Failed,
        [int]$Deferred,
        [string[]]$Routed
    )
    $logPath = Join-Path $VaultPath "log.md"
    $stamp = (Get-Date -Format "yyyy-MM-dd HH:mm")
    $body = @"

## $stamp — raw-inbox-watcher run
- Inbox files seen: $($candidates.Count)
- Processed: $Processed
- Failed: $Failed
- Deferred to Phase 3: $Deferred
- Routes invoked: $($Routed -join ", ")
"@
    if ($DryRun) { return }
    try {
        if (-not (Test-Path $logPath)) {
            Set-Content -Path $logPath -Value "# Vault Activity Log`n" -Encoding UTF8
        }
        Add-Content -Path $logPath -Value $body -Encoding UTF8
    } catch {
        Write-Warning "raw-inbox-watcher: could not append to vault log.md: $_"
    }
}

# ── Process each candidate ───────────────────────────────────────────────────
$processedCount = 0
$failedCount    = 0
$deferredCount  = 0
$routesUsed     = @()

foreach ($file in $candidates) {
    $cls = Get-FileClassification -File $file
    Write-Verbose "raw-inbox-watcher: $($file.Name) -> $($cls.Kind) ($($cls.Reason))"

    switch ($cls.Kind) {
        "markdown" {
            $articlesDir = Join-Path $VaultPath "research/articles"
            if (-not (Test-Path $articlesDir) -and -not $DryRun) {
                New-Item -ItemType Directory -Path $articlesDir -Force | Out-Null
            }
            $dest = Join-Path $articlesDir $file.Name
            if ($DryRun) {
                Write-Host "[dry-run] would route markdown $($file.Name) -> $dest"
            } else {
                try {
                    Copy-Item -Path $file.FullName -Destination $dest -Force
                    if (Move-ToProcessed -File $file) {
                        $processedCount++
                        $routesUsed += "markdown->articles"
                    } else {
                        $failedCount++
                    }
                } catch {
                    Move-ToFailed -File $file -Reason "Markdown copy failed: $_"
                    $failedCount++
                }
            }
        }

        "single_url" {
            $script = Find-IngestScript -RelativePath ".cursor/skills/g-skl-ingest-url/scripts/ingest_url.py"
            if (-not $script) {
                Move-ToFailed -File $file -Reason "ingest_url.py not found"
                $failedCount++
                continue
            }
            if ($DryRun) {
                Write-Host "[dry-run] would invoke g-skl-ingest-url for $($cls.Url)"
                continue
            }
            try {
                & python $script --url $cls.Url --vault-path $VaultPath 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    if (Move-ToProcessed -File $file) {
                        $processedCount++
                        $routesUsed += "url->ingest_url"
                    } else { $failedCount++ }
                } else {
                    Move-ToFailed -File $file -Reason "ingest_url.py exited with code $LASTEXITCODE"
                    $failedCount++
                }
            } catch {
                Move-ToFailed -File $file -Reason "ingest_url invocation failed: $_"
                $failedCount++
            }
        }

        "youtube_url" {
            $script = Find-IngestScript -RelativePath ".cursor/skills/g-skl-ingest-youtube/scripts/fetch_transcript.py"
            if (-not $script) {
                $script = Find-IngestScript -RelativePath "gald3r_template_full/.cursor/skills/g-skl-ingest-youtube/scripts/fetch_transcript.py"
            }
            if (-not $script) {
                Move-ToFailed -File $file -Reason "fetch_transcript.py not found in any IDE skill tree — invoke g-skl-ingest-youtube manually"
                $failedCount++
                continue
            }
            if ($DryRun) {
                Write-Host "[dry-run] would invoke g-skl-ingest-youtube for $($cls.Url)"
                continue
            }
            try {
                & python $script --url $cls.Url --vault-path $VaultPath 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    if (Move-ToProcessed -File $file) {
                        $processedCount++
                        $routesUsed += "url->ingest_youtube"
                    } else { $failedCount++ }
                } else {
                    Move-ToFailed -File $file -Reason "ingest_youtube.py exited with code $LASTEXITCODE"
                    $failedCount++
                }
            } catch {
                Move-ToFailed -File $file -Reason "ingest_youtube invocation failed: $_"
                $failedCount++
            }
        }

        "text_article" {
            $articlesDir = Join-Path $VaultPath "research/articles"
            if (-not (Test-Path $articlesDir) -and -not $DryRun) {
                New-Item -ItemType Directory -Path $articlesDir -Force | Out-Null
            }
            $base = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
            $slug = ($base -replace '[^a-zA-Z0-9]+', '-').ToLowerInvariant().Trim('-')
            if (-not $slug) { $slug = "raw-text-$(Get-Date -Format yyyyMMddHHmmss)" }
            $dest = Join-Path $articlesDir "$today`_$slug.md"
            if ($DryRun) {
                Write-Host "[dry-run] would wrap text $($file.Name) -> $dest"
                continue
            }
            try {
                $body = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
                $frontmatter = @"
---
date: $today
type: article
ingestion_type: raw_inbox_text
source: raw_inbox/$($file.Name)
title: "$base"
tags: [raw_inbox, text_article]
---

$body
"@
                Set-Content -Path $dest -Value $frontmatter -Encoding UTF8 -NoNewline
                if (Move-ToProcessed -File $file) {
                    $processedCount++
                    $routesUsed += "text->articles"
                } else { $failedCount++ }
            } catch {
                Move-ToFailed -File $file -Reason "Text wrap failed: $_"
                $failedCount++
            }
        }

        "deferred_phase3" {
            # Phase 3: attempt LLM/vision classification via raw_inbox_classifier.py
            $classifierScript = Find-IngestScript -RelativePath ".cursor/skills/g-skl-vault/scripts/raw_inbox_classifier.py"
            if (-not $classifierScript) {
                if ($DryRun) {
                    Write-Host "[dry-run] no classifier script found; would defer $($file.Name)"
                } else {
                    Move-ToFailed -File $file -Reason "Phase 3 classifier script not found ($($cls.Reason))"
                    $deferredCount++
                }
                continue
            }
            if ($DryRun) {
                Write-Host "[dry-run] would invoke Phase 3 classifier for $($file.Name)"
                continue
            }
            try {
                $classifierArgs = @("--file", $file.FullName, "--vault-path", $VaultPath)
                $output = & python $classifierScript @classifierArgs 2>&1
                Write-Verbose $($output -join "`n")
                if ($LASTEXITCODE -eq 0) {
                    if (Move-ToProcessed -File $file) {
                        $processedCount++
                        $routesUsed += "phase3->classified"
                    } else { $failedCount++ }
                } elseif ($LASTEXITCODE -eq 2) {
                    Write-Host "raw-inbox-watcher: LOW CONFIDENCE - $($file.Name) left in raw/ for human review"
                    Write-Host ($output -join "`n")
                    $deferredCount++
                } elseif ($LASTEXITCODE -eq 3) {
                    Move-ToFailed -File $file -Reason "Sensitive content detected by Phase 3 classifier"
                    $failedCount++
                } else {
                    Move-ToFailed -File $file -Reason "Phase 3 classifier exited with code $LASTEXITCODE"
                    $failedCount++
                }
            } catch {
                Move-ToFailed -File $file -Reason "Phase 3 classifier invocation failed: $_"
                $failedCount++
            }
        }

        "unreadable" {
            if ($DryRun) {
                Write-Host "[dry-run] would mark unreadable: $($file.Name)"
                continue
            }
            Move-ToFailed -File $file -Reason $cls.Reason
            $failedCount++
        }

        "unknown" {
            if ($DryRun) {
                Write-Host "[dry-run] unknown extension: $($file.Name) ($($cls.Reason))"
                continue
            }
            Move-ToFailed -File $file -Reason $cls.Reason
            $failedCount++
        }
    }
}

$routesUsed = @($routesUsed | Select-Object -Unique)
Add-VaultLogEntry -Processed $processedCount -Failed $failedCount -Deferred $deferredCount -Routed $routesUsed

$summary = "raw-inbox-watcher: seen=$($candidates.Count) processed=$processedCount failed=$failedCount deferred=$deferredCount"
if ($DryRun) { $summary += " (dry-run)" }
Write-Host $summary

# Exit codes: 0 = success or no work, 1 = unrecoverable error (caught above), 2 = some failures
if ($failedCount -gt 0 -or $deferredCount -gt 0) { exit 2 }
exit 0