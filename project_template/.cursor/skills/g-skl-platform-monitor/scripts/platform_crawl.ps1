<#
.SYNOPSIS
    platform_crawl.ps1 — host-side crawl exporter (T646): the freshness-loop PRODUCER.

.DESCRIPTION
    Cross-OS .ps1 PARITY wrapper for the canonical platform_crawl.py. Per the
    g-skl-platform-monitor convention (cf. spec_refresh.ps1 / generate_status.ps1
    shelling out to their Python canonicals), this wrapper shells out to the Python
    canonical so the deterministic SQL/JSON export plumbing lives in ONE place and the
    two implementations can never drift. All parameters are forwarded verbatim.

    Writes the two JSON exports the T514/T515 freshness consumers read:
      -CrawlSnapshot  a platform_docs_search dump ({"results": [{content,title,url,...}]})
                      sourced from platform_ext.memory_captures (subject=platform_docs).
      -CrawlLedger    a platform_crawl_status dump ({"registry": [{platform,
                      last_crawled_at,pages_count,crawl_status}]}) sourced from
                      platform_ext.platform_docs_crawl_registry.
    Read-only over the crawl tables (alembic 0018); C-001 parity — no per-request
    backend tenant session. -Source sample (or -DryRun) produces a non-empty offline
    snapshot for the smoke test without a live DB.

.PARAMETER Source         'db' (live host-side read-only) or 'sample' (offline fixture).
.PARAMETER DbUrl          SQLAlchemy/psycopg connection URL for -Source db.
.PARAMETER Platform       Restrict both exports to one platform key (e.g. cursor).
.PARAMETER CrawlSnapshot  Output path for the platform_docs_search snapshot JSON.
.PARAMETER CrawlLedger    Output path for the platform_crawl_status ledger JSON.
.PARAMETER DryRun         Alias for -Source sample (offline fixture export, no DB).

.EXAMPLE
    .\platform_crawl.ps1 -Source sample -CrawlSnapshot snap.json -CrawlLedger ledger.json
    .\platform_crawl.ps1 -Source db -DbUrl $env:GALD3R_DATABASE_URL -CrawlSnapshot snap.json

.NOTES
    Task: T646 (host crawl exporter — freshness-loop producer). Canonical: platform_crawl.py.
#>
# @subsystems: PLATFORM_INTEGRATION

param(
    [ValidateSet("db", "sample")] [string]$Source,
    [string]$DbUrl,
    [string]$Platform,
    [string]$CrawlSnapshot,
    [string]$CrawlLedger,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$py = Join-Path $PSScriptRoot "platform_crawl.py"
if (-not (Test-Path $py)) {
    Write-Error "Canonical platform_crawl.py not found next to this wrapper: $py"
    exit 1
}

$argv = @()
if ($Source)        { $argv += @("--source", $Source) }
if ($DbUrl)         { $argv += @("--db-url", $DbUrl) }
if ($Platform)      { $argv += @("--platform", $Platform) }
if ($CrawlSnapshot) { $argv += @("--crawl-snapshot", $CrawlSnapshot) }
if ($CrawlLedger)   { $argv += @("--crawl-ledger", $CrawlLedger) }
if ($DryRun)        { $argv += "--dry-run" }

& python $py @argv
exit $LASTEXITCODE
