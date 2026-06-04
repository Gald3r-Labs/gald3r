<#
.SYNOPSIS
  Wrap gald3r report data in the standard JSON envelope and export (T1381).
.DESCRIPTION
  SERIALIZE + VALIDATE + EXPORT for g-skl-json-output. Takes a JSON string of the
  schema-specific `data` payload, wraps it with version/timestamp/command/schema,
  validates, and writes a timestamped .json under the output dir (g-rl-01).
.EXAMPLE
  pwsh -File json_output.ps1 -Command g-status -Schema status -DataJson '{"counts":{}}' -OutDir docs -Topic STATUS
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$Command,
  [Parameter(Mandatory)][ValidateSet('status','review','backlog')][string]$Schema,
  [Parameter(Mandatory)][string]$DataJson,
  [string]$Topic,
  [string]$OutDir = 'docs',
  [string]$ProjectRoot,
  [string]$IDE = 'Claude',
  [switch]$Compact,
  [switch]$Stdout
)
$ErrorActionPreference = 'Stop'

if (-not $ProjectRoot) {
  $d = (Get-Location).Path
  while ($d -and -not (Test-Path (Join-Path $d '.gald3r'))) { $p = Split-Path $d -Parent; if ($p -eq $d) { break }; $d = $p }
  $ProjectRoot = $d
}

# gald3r_version from .identity
$ver = 'unknown'
$idf = Join-Path $ProjectRoot '.gald3r/.identity'
if (Test-Path $idf) {
  $m = Select-String -Path $idf -Pattern '^\s*gald3r_version=(.+)$' | Select-Object -First 1
  if ($m) { $ver = $m.Matches[0].Groups[1].Value.Trim() }
}

# VALIDATE: data payload must be valid JSON
try { $data = $DataJson | ConvertFrom-Json } catch { Write-Host "VALIDATE: FAIL — data is not valid JSON: $($_.Exception.Message)" -ForegroundColor Red; exit 1 }

$envelope = [ordered]@{
  gald3r_version = $ver
  generated_at   = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  command        = $Command
  schema         = $Schema
  data           = $data
}
$depth = 24
$json = if ($Compact) { ($envelope | ConvertTo-Json -Depth $depth -Compress) } else { ($envelope | ConvertTo-Json -Depth $depth) }

# VALIDATE: round-trip parse
try { $null = $json | ConvertFrom-Json } catch { Write-Host "VALIDATE: FAIL — envelope did not round-trip." -ForegroundColor Red; exit 1 }
Write-Host "VALIDATE: PASS (schema=$Schema, version=$ver)" -ForegroundColor Green

if ($Stdout) { $json; return }

if (-not $Topic) { $Topic = $Command -replace '[^A-Za-z0-9]+','_' }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outAbs = Join-Path $ProjectRoot $OutDir
if (-not (Test-Path $outAbs)) { New-Item -ItemType Directory -Path $outAbs -Force | Out-Null }
$outFile = Join-Path $outAbs ("{0}_{1}_{2}.json" -f $stamp, $IDE, $Topic.ToUpper())
$json | Set-Content -Path $outFile -Encoding UTF8
Write-Host "EXPORT: $outFile" -ForegroundColor Cyan
$outFile
