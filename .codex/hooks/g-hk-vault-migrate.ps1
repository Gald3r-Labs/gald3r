param(
    [string]$SourcePath = "",
    [string]$DestinationPath = "",
    [switch]$Force
)

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
& (Join-Path $projectRoot ".cursor\hooks\g-hk-vault-migrate.ps1") @PSBoundParameters
