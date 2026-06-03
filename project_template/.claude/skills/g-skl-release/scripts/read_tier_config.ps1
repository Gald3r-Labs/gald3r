# read_tier_config.ps1 - Parse tier graduation settings from AGENT_CONFIG + .identity
# @subsystems: RELEASE_AND_VERSIONING
<#
.SYNOPSIS
    Returns tier graduation configuration for the current or specified project root.

.OUTPUTS
    Hashtable with graduation_tier, dev_to_test_history, test_to_public_history,
    tier paths from .identity, and resolved public/test/dev paths.
#>
param(
    [string]$ProjectRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$config = @{
    graduation_tier          = "single"
    dev_to_test_history      = "squash-to-release-tag"
    test_to_public_history   = "scrub"
    tier                     = ""
    tier_profile             = ""
    tier_branch_model        = ""
    tier_dev_path            = ""
    tier_test_path           = ""
    tier_public_path         = ""
    tier_public_remote       = ""
}

$agentConfigPath = Join-Path $ProjectRoot ".gald3r\config\AGENT_CONFIG.md"
if (Test-Path $agentConfigPath) {
    $cfg = Get-Content $agentConfigPath -Raw
    if ($cfg -match '(?m)^-\s*graduation_tier:\s*(\S+)') { $config.graduation_tier = $Matches[1] }
    if ($cfg -match '(?m)^-\s*dev_to_test_history:\s*(\S+)') { $config.dev_to_test_history = $Matches[1] }
    if ($cfg -match '(?m)^-\s*test_to_public_history:\s*(\S+)') { $config.test_to_public_history = $Matches[1] }
    if ($cfg -match '(?m)graduation_tier:\s*(\S+)') { $config.graduation_tier = $Matches[1] }
    if ($cfg -match '(?m)dev_to_test_history:\s*(\S+)') { $config.dev_to_test_history = $Matches[1] }
    if ($cfg -match '(?m)test_to_public_history:\s*(\S+)') { $config.test_to_public_history = $Matches[1] }
}

$identityPath = Join-Path $ProjectRoot ".gald3r\.identity"
if (Test-Path $identityPath) {
    Get-Content $identityPath | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim()
            switch ($key) {
                "tier" { $config.tier = $val }
                "tier_profile" { $config.tier_profile = $val }
                "tier_branch_model" { $config.tier_branch_model = $val }
                "tier_dev_path" { $config.tier_dev_path = $val }
                "tier_test_path" { $config.tier_test_path = $val }
                "tier_public_path" { $config.tier_public_path = $val }
                "tier_public_remote" { $config.tier_public_remote = $val }
            }
        }
    }
}

if ($config.test_to_public_history -notin @("scrub", "carry")) {
    $config.test_to_public_history = "scrub"
}
if ($config.dev_to_test_history -notin @("carry", "squash-to-release-tag")) {
    $config.dev_to_test_history = "squash-to-release-tag"
}

return $config
