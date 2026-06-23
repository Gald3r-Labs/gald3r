<#
.SYNOPSIS
    spec_refresh.ps1 — GAP A consumer (T514): crawled docs -> PLATFORM_SPEC.md proposals.

.DESCRIPTION
    Cross-OS .ps1 PARITY wrapper for the canonical spec_refresh.py. Per the
    g-skl-platform-monitor convention (cf. check_platform_status.ps1 shelling out to
    platform_registry.py for YAML parsing), this wrapper shells out to the Python
    canonical so the deterministic diff/parse/registry-read plumbing lives in ONE
    place and the two implementations can never drift. All parameters are forwarded
    verbatim.

    Given the latest crawled-doc snapshot for one platform, it emits a REVIEWABLE
    PLATFORM_SPEC.md proposal (a *.proposed draft + a "what changed and why" summary)
    and stamps the proposed last_doc_scan from the crawl-ledger completion date.
    Dry-run is the default; -Apply lands ONLY the mechanical last_doc_scan stamp —
    capability cells are NEVER auto-flipped (they surface as [needs-review]).

.PARAMETER Platform        Platform name (e.g. cursor, claude, windsurf).
.PARAMETER CrawlSnapshot   Path to the crawled-doc snapshot JSON for the platform.
.PARAMETER CrawlLedger     Optional crawl-ledger JSON snapshot (real last_doc_scan date).
.PARAMETER OutDir          Write the *.proposed draft + summary here (review staging).
.PARAMETER Apply           Land the mechanical last_doc_scan stamp into the live spec.

.EXAMPLE
    .\spec_refresh.ps1 -Platform cursor -CrawlSnapshot cursor_docs.json
    .\spec_refresh.ps1 -Platform cursor -CrawlSnapshot cursor_docs.json -CrawlLedger registry.json -Apply

.NOTES
    Task: T514 (GAP A — spec-refresh consumer). Canonical: spec_refresh.py.
#>
# @subsystems: PLATFORM_INTEGRATION

param(
    [Parameter(Mandatory = $true)] [string]$Platform,
    [Parameter(Mandatory = $true)] [string]$CrawlSnapshot,
    [string]$CrawlLedger,
    [string]$OutDir,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$py = Join-Path $PSScriptRoot "spec_refresh.py"
if (-not (Test-Path $py)) {
    Write-Error "Canonical spec_refresh.py not found next to this wrapper: $py"
    exit 1
}

$argv = @("--platform", $Platform, "--crawl-snapshot", $CrawlSnapshot)
if ($CrawlLedger) { $argv += @("--crawl-ledger", $CrawlLedger) }
if ($OutDir)      { $argv += @("--out-dir", $OutDir) }
if ($Apply)       { $argv += "--apply" }

& python $py @argv
exit $LASTEXITCODE
