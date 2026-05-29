<#
.SYNOPSIS
    Auto-Triage L0 risk calculator for gald3r spec/policy defects.
    Returns a numeric risk score and eligibility verdict.

.DESCRIPTION
    Phase 1 (cautious). Computes risk_score = base_kind_score + file_sensitivity_bonus + scope_multiplier.
    Score <= threshold (default 2.0) = eligible for auto-fix.
    Score > threshold = needs_attention (human required).
    Infinity-class files = always blocked regardless of score.

.PARAMETER Kind
    Bug kind: spec_defect | policy_incongruity | design_gap | code

.PARAMETER Files
    Array of file paths that the proposed fix would touch.

.PARAMETER FixType
    The fix operation: schema_comment | manifest_annotation | command_annotation | rule_annotation | constraint_expire

.PARAMETER Threshold
    Override the risk threshold (default 2.0). Reads from AGENT_CONFIG.md if -ProjectRoot is provided.

.PARAMETER ProjectRoot
    Root of the gald3r project. Used to resolve AGENT_CONFIG.md threshold.

.OUTPUTS
    PSCustomObject with: risk_score, eligible, reason, blocked_paths
#>
param(
    [Parameter(Mandatory)][ValidateSet("spec_defect","policy_incongruity","design_gap","code")][string]$Kind,
    [Parameter(Mandatory)][string[]]$Files,
    [Parameter(Mandatory)][ValidateSet("schema_comment","manifest_annotation","command_annotation","rule_annotation","constraint_expire")][string]$FixType,
    [double]$Threshold = 2.0,
    [string]$ProjectRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Base kind scores ---
$baseScores = @{
    "spec_defect"         = 1.0
    "policy_incongruity"  = 2.0
    "design_gap"          = 99.0   # Always blocked — design decisions require humans
    "code"                = 99.0   # Always blocked — code bugs never auto-triaged
}

# --- Hard-block path patterns (infinity-class) ---
# Any file matching these patterns is an absolute block regardless of score.
# NOTE: linking/workspace_manifest.yaml is intentionally NOT blocked (it is schema/config,
# not PCAC coordination state). Only PCAC-specific linking files are blocked.
$blockPatterns = @(
    [regex]"\\TASKS\.md$",
    [regex]"[\\/]tasks[\\/]",
    [regex]"\\BUGS\.md$",
    [regex]"[\\/]bugs[\\/]",
    [regex]"\\CONSTRAINTS\.md$",
    [regex]"[\\/]features[\\/]",
    [regex]"[\\/]releases[\\/]",
    [regex]"[\\/]prds[\\/]",
    [regex]"[\\/]experiments[\\/]",
    # PCAC coordination state (not the manifest schema itself)
    [regex]"[\\/]linking[\\/]INBOX\.md$",
    [regex]"[\\/]linking[\\/]link_topology\.md$",
    [regex]"[\\/]linking[\\/]sent_orders[\\/]",
    [regex]"[\\/]linking[\\/]pending_orders[\\/]",
    [regex]"[\\/]linking[\\/]peers[\\/]"
)

# --- File sensitivity bonus ---
function Get-FileSensitivityBonus {
    param([string]$FilePath, [string]$FixTypeLocal)

    $name = Split-Path $FilePath -Leaf
    $pathLower = $FilePath.ToLower()

    # Check hard-block patterns first
    foreach ($pat in $blockPatterns) {
        if ($pat.IsMatch($FilePath)) {
            return 99.0   # Infinity-class
        }
    }

    # Source code files (member repo .ts, .tsx, .py, .js, .cs, etc.)
    if ($FilePath -match "\\gald3r_(throne|agent|valhalla|web|discord|world_tree)\\") {
        if ($FilePath -notmatch "\.md$|\.yaml$|\.yml$|\.json$") {
            return 99.0   # Infinity-class
        }
    }

    # Schema YAML comment (lowest risk)
    if ($FixTypeLocal -eq "schema_comment" -and ($name -match "\.yaml$|\.yml$")) { return 0.0 }

    # Manifest annotation or schema comment on workspace_manifest.yaml
    if ($name -eq "workspace_manifest.yaml") { return 0.5 }

    # Rule files
    if ($pathLower -match "[\\/]rules[\\/]" -and $name -match "\.mdc$|\.md$") { return 1.0 }

    # Command files
    if ($pathLower -match "[\\/]commands[\\/]" -and $name -match "\.md$") { return 1.0 }

    # AGENT_CONFIG
    if ($name -eq "AGENT_CONFIG.md") { return 1.0 }

    # SKILL.md files
    if ($name -eq "SKILL.md") { return 0.5 }

    # Generic YAML/schema files
    if ($name -match "\.yaml$|\.yml$") { return 0.5 }

    # Fallback — unknown file type, treat as moderate
    return 1.5
}

# --- Scope multiplier ---
function Get-ScopeMultiplier {
    param([int]$FileCount)
    if ($FileCount -eq 1) { return 1.0 }
    if ($FileCount -le 3) { return 1.5 }
    return 99.0   # > 3 files = infinity-class
}

# --- Try to read threshold from AGENT_CONFIG.md ---
if ($ProjectRoot -ne "" -and (Test-Path "$ProjectRoot\.gald3r\config\AGENT_CONFIG.md")) {
    $configContent = Get-Content "$ProjectRoot\.gald3r\config\AGENT_CONFIG.md" -Raw
    if ($configContent -match "auto_triage_risk_threshold:\s*([\d.]+)") {
        $configThreshold = [double]$matches[1]
        # Only use config value if -Threshold was not explicitly overridden (default 2.0)
        if ($Threshold -eq 2.0) {
            $Threshold = $configThreshold
        }
    }
}

# --- Compute score ---
$baseScore = $baseScores[$Kind]
$blockedPaths = @()
$maxFileSensitivity = 0.0

foreach ($f in $Files) {
    $bonus = Get-FileSensitivityBonus -FilePath $f -FixTypeLocal $FixType
    if ($bonus -ge 99.0) {
        $blockedPaths += $f
    }
    if ($bonus -gt $maxFileSensitivity) {
        $maxFileSensitivity = $bonus
    }
}

$scopeMultiplier = Get-ScopeMultiplier -FileCount $Files.Count

# If any hard-block, score is infinity
$rawScore = if ($blockedPaths.Count -gt 0 -or $maxFileSensitivity -ge 99.0 -or $scopeMultiplier -ge 99.0) {
    99.0
} else {
    ($baseScore + $maxFileSensitivity) * $scopeMultiplier
}

$riskScore = [Math]::Round($rawScore, 2)
$eligible = ($riskScore -le $Threshold) -and ($blockedPaths.Count -eq 0)

# --- Build reason string ---
$reason = if ($blockedPaths.Count -gt 0) {
    "BLOCKED: infinity-class files touched: $($blockedPaths -join ', ')"
} elseif ($riskScore -ge 99.0) {
    "BLOCKED: kind='$Kind' or scope exceeds Phase 1 limits"
} elseif ($eligible) {
    "ELIGIBLE: $Kind + $FixType on $($Files.Count) file(s) — score $riskScore <= threshold $Threshold"
} else {
    "NOT ELIGIBLE: score $riskScore exceeds threshold $Threshold — needs_attention"
}

[PSCustomObject]@{
    risk_score    = $riskScore
    eligible      = $eligible
    threshold     = $Threshold
    reason        = $reason
    blocked_paths = $blockedPaths
    kind          = $Kind
    fix_type      = $FixType
    file_count    = $Files.Count
}
