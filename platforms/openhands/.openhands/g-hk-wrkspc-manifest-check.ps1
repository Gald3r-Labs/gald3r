# g-hk-wrkspc-manifest-check.ps1
# @subsystems: WORKSPACE_COORDINATION
# Read-only Workspace-Control manifest preflight for g-wrkspc commands.
# Validates that the canonical manifest exists and can be parsed by PowerShell as basic YAML-like text.
# Deep schema validation belongs to g-skl-workspace VALIDATE.

param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$RequireManifest,
    [switch]$ForceRun
)

# ── Idempotency guard ─────────────────────────────────────────────────────────
if (-not $ForceRun -and $env:GALD3R_HK_WRKSPC_MANIFEST_CHECK_APPLIED -eq "1") {
    Write-Output "[SKIP] g-hk-wrkspc-manifest-check already applied this session. Pass -ForceRun to override."
    exit 0
}
$env:GALD3R_HK_WRKSPC_MANIFEST_CHECK_APPLIED = "1"

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
