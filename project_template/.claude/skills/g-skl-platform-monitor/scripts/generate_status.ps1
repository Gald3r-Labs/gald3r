<#
.SYNOPSIS
    generate_status.ps1 — GAP B generator (T515): PLATFORM_STATUS.md from specs + ledger.

.DESCRIPTION
    Cross-OS .ps1 PARITY wrapper for the canonical generate_status.py. Per the
    g-skl-platform-monitor convention (cf. check_platform_status.ps1 shelling out to
    platform_registry.py), this wrapper shells out to the Python canonical so the
    deterministic spec-parse / cell-derivation / merge logic lives in ONE place and the
    two implementations can never drift. All parameters are forwarded verbatim.

    Regenerates PLATFORM_STATUS.md from each platform's PLATFORM_SPEC.md
    `## Capability Summary` (capability cells, derived the SAME way as
    --generate-matrix) + the crawl ledger (Last Doc Scan). SOURCE-OF-TRUTH = Option 2:
    the curated Status verdict + Notes columns are PRESERVED by merge; only the
    mechanical cells are regenerated. Dry-run is the default; -Apply rewrites the file.

.PARAMETER Apply         Rewrite PLATFORM_STATUS.md (default is dry-run).
.PARAMETER CrawlLedger   Optional crawl-ledger JSON snapshot (real Last Doc Scan date).
.PARAMETER NoTimestamp   Omit the generated timestamp line (byte-deterministic output).

.EXAMPLE
    .\generate_status.ps1
    .\generate_status.ps1 -Apply -CrawlLedger registry.json

.NOTES
    Task: T515 (GAP B — STATUS auto-generator). Canonical: generate_status.py.
#>
# @subsystems: PLATFORM_INTEGRATION

param(
    [switch]$Apply,
    [string]$CrawlLedger,
    [switch]$NoTimestamp
)

$ErrorActionPreference = "Stop"
$py = Join-Path $PSScriptRoot "generate_status.py"
if (-not (Test-Path $py)) {
    Write-Error "Canonical generate_status.py not found next to this wrapper: $py"
    exit 1
}

$argv = @()
if ($Apply)        { $argv += "--apply" }
if ($CrawlLedger)  { $argv += @("--crawl-ledger", $CrawlLedger) }
if ($NoTimestamp)  { $argv += "--no-timestamp" }

& python $py @argv
exit $LASTEXITCODE
