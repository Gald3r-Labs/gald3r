<#
.SYNOPSIS
    Auto-Triage L0 runner — assess risk, attempt fix if safe, log outcome.
    Phase 1 (cautious). Only fixes bounded, low-risk spec/schema defects.

.PARAMETER BugId
    e.g. "BUG-098"

.PARAMETER Kind
    Bug kind: spec_defect | policy_incongruity | design_gap | code

.PARAMETER Files
    Array of absolute paths to files the fix would touch.

.PARAMETER FixType
    schema_comment | manifest_annotation | command_annotation | rule_annotation | constraint_expire

.PARAMETER FixContent
    The text to add/append. For annotations, the exact comment string. For constraint_expire, "archived".

.PARAMETER TargetLine
    Optional: 1-based line number where the annotation should be inserted AFTER. If omitted, appends at end.

.PARAMETER ProjectRoot
    Absolute path to the gald3r_dev project root.

.PARAMETER DryRun
    If set, reports what would happen without writing anything.

.PARAMETER BugFilePath
    Absolute path to the bug's .md file (for updating triage_status frontmatter).
#>
param(
    [Parameter(Mandatory)][string]$BugId,
    [Parameter(Mandatory)][ValidateSet("spec_defect","policy_incongruity","design_gap","code")][string]$Kind,
    [Parameter(Mandatory)][string[]]$Files,
    [Parameter(Mandatory)][ValidateSet("schema_comment","manifest_annotation","command_annotation","rule_annotation","constraint_expire")][string]$FixType,
    [string]$FixContent = "",
    [int]$TargetLine = -1,
    [Parameter(Mandatory)][string]$ProjectRoot,
    [switch]$DryRun,
    [string]$BugFilePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path $MyInvocation.MyCommand.Path
$auditLog  = "$ProjectRoot\.gald3r\logs\triage_auto_$(Get-Date -Format 'yyyyMMdd').log"
$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

function Write-AuditLog {
    param([string]$Msg)
    $line = "$timestamp | $BugId | $Kind | fix=$FixType | $Msg"
    if ($DryRun) {
        Write-Host "[DRY-RUN] AUDIT: $line"
    } else {
        $logDir = Split-Path $auditLog
        if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
        Add-Content -Path $auditLog -Value $line
        Write-Host "AUDIT: $line"
    }
}

function Update-BugFrontmatter {
    param(
        [string]$BugFile,
        [string]$TriageStatus,
        [double]$RiskScore,
        [string]$TriageNote
    )
    if (-not (Test-Path $BugFile)) {
        Write-Host "WARNING: Bug file not found, skipping frontmatter update: $BugFile"
        return
    }

    $content = Get-Content $BugFile -Raw
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"

    # Add or update triage fields in frontmatter (between first --- pair)
    $fieldsToSet = @{
        "triage_status"    = $TriageStatus
        "triage_risk_score"= [string]$RiskScore
        "triage_attempted" = "'$ts'"
        "triage_notes"     = "'$TriageNote'"
        "kind"             = $Kind
    }

    foreach ($key in $fieldsToSet.Keys) {
        $val = $fieldsToSet[$key]
        if ($content -match "(?m)^$key:") {
            # Update existing field
            $content = $content -replace "(?m)^$key:.*$", "$key: $val"
        } else {
            # Insert after opening ---
            $content = $content -replace "(?m)^---\r?\n", "---`n$key`: $val`n"
        }
    }

    if ($DryRun) {
        Write-Host "[DRY-RUN] Would update frontmatter in: $BugFile"
        Write-Host "[DRY-RUN] triage_status=$TriageStatus risk=$RiskScore"
    } else {
        Set-Content $BugFile $content -NoNewline
        Write-Host "Updated frontmatter: $BugFile"
    }
}

# --- Step 1: Run risk assessment ---
Write-Host "[$BugId] Assessing risk for kind=$Kind fixType=$FixType files=[$($Files -join ', ')]"

$assessment = & "$scriptDir\calculate_risk.ps1" `
    -Kind $Kind `
    -Files $Files `
    -FixType $FixType `
    -ProjectRoot $ProjectRoot

Write-Host "[$BugId] Risk score: $($assessment.risk_score) | Eligible: $($assessment.eligible)"
Write-Host "[$BugId] Reason: $($assessment.reason)"

# --- Step 2: Gate check ---
if (-not $assessment.eligible) {
    $status = if ($assessment.risk_score -ge 99.0) { "blocked_by_risk" } else { "needs_attention" }

    Write-AuditLog "risk=$($assessment.risk_score) | $status | $($assessment.reason)"

    if ($BugFilePath -ne "") {
        Update-BugFrontmatter -BugFile $BugFilePath -TriageStatus $status `
            -RiskScore $assessment.risk_score -TriageNote $assessment.reason
    }

    Write-Host "[$BugId] Outcome: $status — no changes made"
    return [PSCustomObject]@{ outcome = $status; risk_score = $assessment.risk_score; changes = @() }
}

# --- Step 3: Validate fix content ---
if ($FixContent -eq "" -and $FixType -ne "constraint_expire") {
    Write-Host "[$BugId] ERROR: FixContent is required for fix_type=$FixType"
    Write-AuditLog "risk=$($assessment.risk_score) | error | FixContent empty, aborting"
    return [PSCustomObject]@{ outcome = "error"; risk_score = $assessment.risk_score; changes = @() }
}

# --- Step 4: Apply fix ---
$appliedChanges = @()

foreach ($file in $Files) {
    if (-not (Test-Path $file)) {
        Write-Host "[$BugId] WARNING: File not found, skipping: $file"
        continue
    }

    $fileContent = Get-Content $file -Raw
    $originalHash = (Get-FileHash $file -Algorithm SHA256).Hash

    switch ($FixType) {
        "schema_comment" {
            # Append a NOTE comment after a specific line or at end of file
            if ($TargetLine -gt 0) {
                $lines = $fileContent -split "`n"
                if ($TargetLine -le $lines.Count) {
                    $before = ($lines[0..($TargetLine-1)] -join "`n")
                    $after  = ($lines[$TargetLine..($lines.Count-1)] -join "`n")
                    $newContent = $before + "`n" + $FixContent + "`n" + $after
                } else {
                    $newContent = $fileContent.TrimEnd() + "`n" + $FixContent + "`n"
                }
            } else {
                $newContent = $fileContent.TrimEnd() + "`n" + $FixContent + "`n"
            }
        }
        "manifest_annotation" {
            # Same as schema_comment for Phase 1
            if ($TargetLine -gt 0) {
                $lines = $fileContent -split "`n"
                $before = ($lines[0..($TargetLine-1)] -join "`n")
                $after  = ($lines[$TargetLine..($lines.Count-1)] -join "`n")
                $newContent = $before + "`n" + $FixContent + "`n" + $after
            } else {
                $newContent = $fileContent.TrimEnd() + "`n" + $FixContent + "`n"
            }
        }
        "command_annotation" {
            # Append BUG[BUG-NNN] comment at specific line or end of file
            if ($TargetLine -gt 0) {
                $lines = $fileContent -split "`n"
                $before = ($lines[0..($TargetLine-1)] -join "`n")
                $after  = ($lines[$TargetLine..($lines.Count-1)] -join "`n")
                $newContent = $before + "`n" + $FixContent + "`n" + $after
            } else {
                $newContent = $fileContent.TrimEnd() + "`n" + $FixContent + "`n"
            }
        }
        "rule_annotation" {
            # Same pattern as command_annotation
            if ($TargetLine -gt 0) {
                $lines = $fileContent -split "`n"
                $before = ($lines[0..($TargetLine-1)] -join "`n")
                $after  = ($lines[$TargetLine..($lines.Count-1)] -join "`n")
                $newContent = $before + "`n" + $FixContent + "`n" + $after
            } else {
                $newContent = $fileContent.TrimEnd() + "`n" + $FixContent + "`n"
            }
        }
        "constraint_expire" {
            # Change status: active → archived for clearly expired constraints
            # Safety: only operates on status fields that have explicit expiry markers already met
            $newContent = $fileContent -replace "(?m)^(\s*status:\s*)active(\s*#.*expiry.*met)", '${1}archived${2}'
            if ($newContent -eq $fileContent) {
                Write-Host "[$BugId] WARNING: constraint_expire found no eligible 'status: active # expiry met' pattern in $file"
                continue
            }
        }
    }

    if ($DryRun) {
        Write-Host "[DRY-RUN] Would write to: $file"
        Write-Host "[DRY-RUN] Content preview (first 200 chars of change):"
        Write-Host $FixContent.Substring(0, [Math]::Min(200, $FixContent.Length))
    } else {
        Set-Content $file $newContent -NoNewline
        $newHash = (Get-FileHash $file -Algorithm SHA256).Hash

        if ($newHash -eq $originalHash) {
            Write-Host "[$BugId] WARNING: File hash unchanged after write — fix may be a no-op: $file"
        } else {
            Write-Host "[$BugId] Written: $file"
            $appliedChanges += $file
        }
    }
}

# --- Step 5: Log and update bug frontmatter ---
$outcome = if ($appliedChanges.Count -gt 0 -or $DryRun) { "auto_resolved" } else { "needs_attention" }
$noteStr  = "Applied $FixType to: $($Files -join ', ')"

Write-AuditLog "risk=$($assessment.risk_score) | $outcome | $noteStr"

if ($BugFilePath -ne "") {
    Update-BugFrontmatter -BugFile $BugFilePath -TriageStatus $outcome `
        -RiskScore $assessment.risk_score -TriageNote $noteStr
}

Write-Host "[$BugId] Outcome: $outcome | Changes: $($appliedChanges.Count) file(s)"

return [PSCustomObject]@{
    outcome     = $outcome
    risk_score  = $assessment.risk_score
    changes     = $appliedChanges
    dry_run     = $DryRun.IsPresent
}
