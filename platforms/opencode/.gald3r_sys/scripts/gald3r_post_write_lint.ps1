# @subsystems: BUG_AND_QUALITY
<#
.SYNOPSIS
    Post-write lint validation for gald3r g-go-code workflow (T919).

.DESCRIPTION
    Runs language-appropriate syntax checks after each file write in the
    g-go-code implementation loop. Catches malformed syntax at write time,
    not at test/CI time. Pattern from Hermes v0.13.0 PR #20191.

.PARAMETER FilePath
    Path to the file that was just written or modified.

.PARAMETER ProjectRoot
    Root of the project (defaults to current directory).

.EXAMPLE
    .\gald3r_post_write_lint.ps1 -FilePath "src/foo.py"

.EXAMPLE
    .\gald3r_post_write_lint.ps1 -FilePath "config.json"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $FilePath,

    [string] $ProjectRoot = (Get-Location).Path,

    [switch] $Json
)

$ErrorActionPreference = 'Stop'

function Write-Result {
    param([bool]$OK, [string]$Message, [string]$Detail = '')
    if ($Json) {
        $obj = @{ ok = $OK; message = $Message; detail = $Detail; file = $FilePath }
        Write-Output (ConvertTo-Json $obj -Compress)
    } else {
        $prefix = if ($OK) { '[LINT OK]' } else { '[LINT FAIL]' }
        $fg = if ($OK) { 'Green' } else { 'Red' }
        Write-Host "$prefix $Message" -ForegroundColor $fg
        if ($Detail -and -not $OK) { Write-Host "  $Detail" -ForegroundColor Yellow }
    }
}

# Resolve absolute path
$abs = if ([System.IO.Path]::IsPathRooted($FilePath)) {
    $FilePath
} else {
    [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($ProjectRoot, $FilePath))
}

if (-not (Test-Path $abs)) {
    Write-Result $false "File not found" $abs
    exit 1
}

$ext = [System.IO.Path]::GetExtension($abs).ToLower()

$ok = $true
$detail = ''

switch ($ext) {
    '.py' {
        $result = & python -m py_compile $abs 2>&1
        if ($LASTEXITCODE -ne 0) {
            $ok = $false
            $detail = $result -join '; '
        }
    }
    '.json' {
        $result = & python -c "import json, sys; json.load(open(sys.argv[1]))" $abs 2>&1
        if ($LASTEXITCODE -ne 0) {
            $ok = $false
            $detail = $result -join '; '
        }
    }
    { $_ -in '.yaml', '.yml' } {
        $result = & python -c "import yaml, sys; yaml.safe_load(open(sys.argv[1]).read())" $abs 2>&1
        if ($LASTEXITCODE -ne 0) {
            $ok = $false
            $detail = $result -join '; '
        }
    }
    '.toml' {
        $result = & python -c "import tomllib, sys; tomllib.load(open(sys.argv[1], 'rb'))" $abs 2>&1
        if ($LASTEXITCODE -ne 0) {
            $ok = $false
            $detail = $result -join '; '
        }
    }
    { $_ -in '.ts', '.tsx', '.js', '.jsx', '.mts', '.mjs' } {
        # Only run tsc when a tsconfig is present in the project
        $tsconfig = [System.IO.Path]::Combine($ProjectRoot, 'tsconfig.json')
        if (Test-Path $tsconfig) {
            $result = & npx tsc --noEmit --allowJs 2>&1
            if ($LASTEXITCODE -ne 0) {
                $ok = $false
                # Only surface errors from the target file to keep noise low
                $filtered = ($result | Where-Object { $_ -match [regex]::Escape([System.IO.Path]::GetFileName($abs)) })
                $detail = if ($filtered) { $filtered -join '; ' } else { ($result | Select-Object -First 5) -join '; ' }
            }
        } else {
            # No tsconfig — skip silently
            Write-Result $true "TypeScript/JS lint skipped (no tsconfig.json)" ''
            exit 0
        }
    }
    { $_ -in '.ps1', '.psm1', '.psd1' } {
        # Use Parser::ParseFile (not PSParser::Tokenize) so structural syntax
        # errors (e.g. unbalanced braces) actually surface (BUG-101 Gap 2).
        $parseErrors = $null
        $null = [System.Management.Automation.Language.Parser]::ParseFile($abs, [ref]$null, [ref]$parseErrors)
        if ($parseErrors -and $parseErrors.Count -gt 0) {
            $ok = $false
            $detail = ($parseErrors | ForEach-Object { "L$($_.Extent.StartLineNumber): $($_.Message)" }) -join '; '
        }
    }
    default {
        # Unsupported extension — pass silently
        Write-Result $true "Lint skipped (unsupported extension: $ext)" ''
        exit 0
    }
}

if ($ok) {
    Write-Result $true "Syntax OK ($ext)"
    exit 0
} else {
    Write-Result $false "Syntax error ($ext)" $detail
    exit 2
}
