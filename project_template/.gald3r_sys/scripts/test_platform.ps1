# @subsystems: PLATFORM_INTEGRATION, UI_AND_OUTPUT
<#
.SYNOPSIS
    Platform Template Test Harness + HTML report card (T613) — PowerShell twin.

.DESCRIPTION
    Thin Windows delegator for test_platform.py. The entire 14-test plan, the
    scaffolding, the isolation selection, and the HTML report-card rendering live
    in the Python harness (one source of truth — g-rl-04 DRY); this wrapper only
    resolves an interpreter and forwards arguments.

    Interpreter resolution mirrors install_global_cli.ps1: prefer `uv run`
    against the bundled engine, fall back to `python`. All positional/named args
    after the script name are passed straight through to test_platform.py.

    Isolation order inside the Python harness: SmolVM -> Docker -> bare-local
    (bare-local prints a clear WARNING). A red report card is the CORRECT output
    for a stub/incomplete platform — the harness never fakes a pass.

.PARAMETER Platform
    Platform overlay name (e.g. claude, cursor, hermes). Optional with -List.

.PARAMETER Isolation
    auto | smolvm | docker | bare-local (default: auto).

.PARAMETER OutDir
    Extra output dir for the report card (in addition to the two canonical paths).

.PARAMETER List
    List known platform overlays and exit.

.PARAMETER Json
    Also print the report card as JSON.

.PARAMETER KeepScaffold
    Keep the temp scaffold on disk (debugging).

.EXAMPLE
    .\test_platform.ps1 claude

.EXAMPLE
    .\test_platform.ps1 hermes -Isolation bare-local

.EXAMPLE
    .\test_platform.ps1 -List
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $Platform = '',

    [ValidateSet('auto', 'smolvm', 'docker', 'bare-local')]
    [string] $Isolation = 'auto',

    [string] $OutDir = '',

    [switch] $List,

    [switch] $Json,

    [switch] $KeepScaffold
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $PSCommandPath
$Harness = Join-Path $ScriptDir 'test_platform.py'
if (-not (Test-Path $Harness)) {
    Write-Error "Harness not found: $Harness"
    exit 1
}

# Resolve the bundled engine dir (holds pyproject.toml) for `uv run --project`.
function Get-EngineDir {
    $candidates = @(
        (Join-Path (Split-Path -Parent $ScriptDir) 'engine'),
        (Join-Path (Get-Location).Path '.gald3r_sys\engine')
    )
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $c 'pyproject.toml')) { return $c }
    }
    return $null
}

# Build the forwarded argument list from the bound parameters.
$fwd = @()
if ($Platform)     { $fwd += $Platform }
if ($List)         { $fwd += '--list' }
if ($Isolation)    { $fwd += @('--isolation', $Isolation) }
if ($OutDir)       { $fwd += @('--out-dir', $OutDir) }
if ($Json)         { $fwd += '--json' }
if ($KeepScaffold) { $fwd += '--keep-scaffold' }

$engineDir = Get-EngineDir
$uv = Get-Command uv -ErrorAction SilentlyContinue

if ($uv -and $engineDir) {
    & uv run --project "$engineDir" python "$Harness" @fwd
    exit $LASTEXITCODE
}

# Fallback: plain python (engine/src is added to sys.path by the harness itself
# only for the gald3r CLI subprocess; the harness module is pure-stdlib).
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Error 'No uv project run and no python on PATH — cannot run the harness.'
    exit 1
}

& $py.Source "$Harness" @fwd
exit $LASTEXITCODE
