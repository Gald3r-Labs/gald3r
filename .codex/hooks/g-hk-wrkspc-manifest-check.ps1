# g-hk-wrkspc-manifest-check.ps1
# Read-only Workspace-Control manifest preflight for g-wrkspc commands.
# Validates that the canonical manifest exists and can be parsed by PowerShell as basic YAML-like text.
# Deep schema validation belongs to g-skl-workspace VALIDATE.

param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$RequireManifest
)

$manifestPath = Join-Path $ProjectRoot ".gald3r\linking\workspace_manifest.yaml"

if (-not (Test-Path $manifestPath)) {
    if ($RequireManifest) {
        Write-Output "Workspace-Control: inactive (missing .gald3r/linking/workspace_manifest.yaml)"
        exit 2
    }
    Write-Output "Workspace-Control: inactive"
    exit 0
}

$content = Get-Content $manifestPath -Raw -ErrorAction SilentlyContinue
if ([string]::IsNullOrWhiteSpace($content)) {
    Write-Output "Workspace-Control: manifest is empty"
    exit 2
}

$required = @("schema:", "workspace:", "repositories:", "controlled_members:", "routing_policy:", "pcac_relationship:")
$missing = @()
foreach ($key in $required) {
    if ($content -notmatch "(?m)^$([regex]::Escape($key))") {
        $missing += $key
    }
}

if ($missing.Count -gt 0) {
    Write-Output ("Workspace-Control: manifest missing top-level key(s): " + ($missing -join ", "))
    exit 2
}

Write-Output "Workspace-Control: manifest preflight passed"
exit 0
