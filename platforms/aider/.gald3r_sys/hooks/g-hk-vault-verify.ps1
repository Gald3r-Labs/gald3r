# g-hk-vault-verify.ps1
# @subsystems: VAULT_AND_RESEARCH
# Vault existence / structure verification (T1456).
#
# Verifies that the configured vault directory exists and carries the expected
# research/ subdirectory layout, then emits a single status line:
#   Vault at {path}: OK | NOT FOUND | PARTIAL (missing: ...)
#
# Fail-soft by design: never throws, never blocks session start. When the vault
# is not configured (vault_location absent or {LOCAL}) it returns nothing.
#
# Two ways to use it:
#   1. Source it from another hook, then call Get-Gald3rVaultStatusBanner:
#        . "$PSScriptRoot\g-hk-vault-verify.ps1"
#        $line = Get-Gald3rVaultStatusBanner -ProjectRoot (Get-Location).Path
#   2. Run it directly: prints the status line (if any) to stdout and exits 0.

function Get-Gald3rVaultStatusBanner {
    param(
        [string]$ProjectRoot = (Get-Location).Path
    )

    try {
        # Expected research/ subdirs from the canonical vault layout (g-skl-vault SKILL.md).
        $researchSubdirs = @("articles", "github", "harvests", "papers", "platforms", "videos")

        $identityPath = Join-Path $ProjectRoot ".gald3r\.identity"
        if (-not (Test-Path $identityPath)) { return "" }

        # Read vault_location directly from .identity (the CONFIGURED value, not a
        # resolved/auto-created path) so we can detect a missing shared vault.
        $vaultLocation = ""
        foreach ($line in (Get-Content $identityPath -ErrorAction SilentlyContinue)) {
            if ($line -match "^\s*vault_location\s*=\s*(.+)$") {
                $vaultLocation = $Matches[1].Trim().Trim('"').Trim("'")
                break
            }
        }

        # Not configured, or local-only fallback: nothing to verify, stay silent.
        if (-not $vaultLocation -or $vaultLocation -eq "{LOCAL}") { return "" }

        # NOT FOUND: configured path does not exist on disk.
        if (-not (Test-Path $vaultLocation)) {
            return "- Vault at ``$vaultLocation``: NOT FOUND -- run ``@g-vault init`` to build the vault structure"
        }

        # Vault root exists. Check the research/ subdir layout.
        $researchRoot = Join-Path $vaultLocation "research"
        $missing = @()
        if (-not (Test-Path $researchRoot)) {
            $missing += "research/"
        } else {
            foreach ($sub in $researchSubdirs) {
                $subPath = Join-Path $researchRoot $sub
                if (-not (Test-Path $subPath)) { $missing += ("research/" + $sub + "/") }
            }
        }

        if ($missing.Count -gt 0) {
            $missingList = $missing -join ", "
            return "- Vault at ``$vaultLocation``: PARTIAL (missing: $missingList) -- run ``@g-vault init`` to create the missing folders"
        }

        return "- Vault at ``$vaultLocation``: OK"
    } catch {
        # Fail-soft: never surface an error, never block.
        return ""
    }
}

# Standalone execution: print the status line (if any) and exit 0.
# Guard against running the body when dot-sourced for the function only.
if ($MyInvocation.InvocationName -ne '.') {
    $banner = Get-Gald3rVaultStatusBanner -ProjectRoot (Get-Location).Path
    if ($banner) { Write-Output $banner }
    exit 0
}
