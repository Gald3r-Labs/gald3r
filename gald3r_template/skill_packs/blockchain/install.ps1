<#
.SYNOPSIS
    Install the blockchain skill pack into a project.

.PARAMETER ProjectRoot
    Path to the project to install into. Defaults to current directory.

.PARAMETER List
    List files that would be installed without copying.

.EXAMPLE
    .\skill_packs\infrastructure\install.ps1
    .\skill_packs\infrastructure\install.ps1 -ProjectRoot "C:\my-project"
    .\skill_packs\infrastructure\install.ps1 -List
#>

param(
    [string]$ProjectRoot = ".",
    [switch]$List
)

$filesDir = Join-Path $PSScriptRoot "files"
$ProjectRoot = Resolve-Path $ProjectRoot

Write-Host ""
Write-Host "blockchain skill pack" -ForegroundColor Cyan
Write-Host "Target: $ProjectRoot"
if ($List) { Write-Host "Mode: LIST (no files copied)" -ForegroundColor Yellow }
Write-Host ""

$copied = 0
Get-ChildItem $filesDir -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($filesDir.Length + 1)
    $dest = Join-Path $ProjectRoot $rel
    if ($List) {
        Write-Host "  $rel"
    } else {
        $destDir = Split-Path $dest -Parent
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory $destDir -Force | Out-Null }
        Copy-Item $_.FullName $dest -Force
        Write-Host "  Installed: $rel" -ForegroundColor Green
        $copied++
    }
}

Write-Host ""
if ($List) {
    Write-Host "Files that would be installed: $((Get-ChildItem $filesDir -Recurse -File).Count)" -ForegroundColor Cyan
} else {
    Write-Host "Installed $copied file(s). Restart your IDE to load new skills." -ForegroundColor Green
}
