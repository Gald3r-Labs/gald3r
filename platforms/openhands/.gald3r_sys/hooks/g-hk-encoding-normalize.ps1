#Requires -Version 5.1
# @subsystems: PLATFORM_INTEGRATION
<#
.SYNOPSIS
    gald3r Encoding Normalizer -- T1428
    Strips spurious BOMs, fixes UTF-16, and normalizes CRLF to LF in text files
    written by the agent. Prevents PS5.1 mojibake, emoji corruption, and em-dash
    mangling (BUG-073 / BUG-094 class).

.DESCRIPTION
    Three invocation modes:
      1. stop / turn-end: called with no args -- normalizes all git-dirty text files
      2. explicit files:  called with -Files <path1> <path2> -- normalizes those files
      3. pre-commit:      called with -PreCommit -- normalizes all staged text files

    Encoding policy by file type (the critical T1428 distinction):
      - PowerShell source (.ps1 / .psm1 / .psd1): UTF-8 WITH BOM.
        Windows PowerShell 5.1 parses a BOM-less UTF-8 script as Windows-1252,
        which mangles any non-ASCII byte (em-dash, emoji, accented chars) and
        breaks parsing. The BOM is REQUIRED for PS5.1 correctness (BUG-073).
      - Everything else (.md, .yaml, .json, .ts, .py, task/bug files, ...):
        UTF-8 WITHOUT BOM. A BOM in markdown/JSON/source is the corruption.

    All processed files are normalized to LF line endings regardless of type.

    UTF-16 LE/BE inputs are always converted to the correct UTF-8 variant for
    the file's extension (BOM for PowerShell, no-BOM otherwise).

.PARAMETER Files
    Specific file paths to normalize.

.PARAMETER PreCommit
    Normalize all staged text files (pre-commit git hook mode); re-stages fixes.

.PARAMETER Scan
    Report-only. Detect and list files that WOULD be normalized; write nothing.
    Exit code 0 = clean, 1 = drift found (for CI / verification gates).

.PARAMETER Quiet
    Suppress per-file output. Errors are always shown.
#>

param(
    [string[]]$Files = @(),
    [switch]$PreCommit,
    [switch]$Scan,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

# Text file extensions to normalize (binary files are always skipped).
$TextExtensions = @(
    '.md', '.mdc', '.yaml', '.yml', '.json', '.ps1', '.psm1', '.psd1',
    '.ts', '.tsx', '.js', '.jsx', '.py', '.txt', '.sh', '.bash',
    '.html', '.htm', '.css', '.scss', '.sql', '.toml', '.ini', '.cfg',
    '.gitattributes', '.gitignore', '.env'
)

# PowerShell source -- requires UTF-8 WITH BOM for PS5.1 (BUG-073).
$PowerShellExtensions = @('.ps1', '.psm1', '.psd1')

# Encoders. UTF-8 no-BOM is the default for non-PowerShell text.
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$Utf8Bom   = [System.Text.UTF8Encoding]::new($true)

function Test-IsTextFile {
    param([string]$Path)
    $ext = [System.IO.Path]::GetExtension($Path).ToLower()
    if ($TextExtensions -contains $ext) { return $true }
    # Extensionless files inside .gald3r/ are task/bug/plan files -- treat as text.
    if ($ext -eq '' -and ($Path -replace '\\', '/') -match '/\.gald3r/') { return $true }
    return $false
}

function Test-IsPowerShellFile {
    param([string]$Path)
    $ext = [System.IO.Path]::GetExtension($Path).ToLower()
    return ($PowerShellExtensions -contains $ext)
}

function Get-BomEncoding {
    param([byte[]]$Bytes)
    if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
        return 'UTF8-BOM'
    }
    if ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFF -and $Bytes[1] -eq 0xFE) {
        return 'UTF16-LE'
    }
    if ($Bytes.Length -ge 2 -and $Bytes[0] -eq 0xFE -and $Bytes[1] -eq 0xFF) {
        return 'UTF16-BE'
    }
    return 'UTF8'
}

# Returns $true when a change is needed; performs the write unless -Scan.
function Invoke-NormalizeFile {
    param([string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) { return $false }
    if (-not (Test-IsTextFile $Path)) { return $false }

    try {
        $bytes = [System.IO.File]::ReadAllBytes($Path)
        if ($bytes.Length -eq 0) { return $false }

        $encoding = Get-BomEncoding $bytes

        # Binary/invalid-content guard (T1447): a NUL byte (0x00) in a file the BOM sniff
        # treats as UTF-8/UTF-8-BOM (NOT UTF-16, which legitimately contains NULs) means the
        # file is really binary or invalid UTF-8 despite its text extension. Decoding it via
        # UTF8.GetString would silently replace bytes with U+FFFD (irreversible corruption).
        # Leave it byte-identical.
        if (($encoding -eq 'UTF8' -or $encoding -eq 'UTF8-BOM') -and ($bytes -contains 0x00)) {
            if ($Scan -and -not $Quiet) {
                Write-Host ("  skip-binary: {0} (NUL byte in non-UTF16 file)" -f `
                    [System.IO.Path]::GetFileName($Path)) -ForegroundColor DarkGray
            }
            return $false
        }

        $hasCrlf  = ($bytes -contains 0x0D)
        $isPs     = Test-IsPowerShellFile $Path

        # Desired final state:
        #   PowerShell  -> UTF8-BOM + LF
        #   other text  -> UTF8 no-BOM + LF
        $wantBom = $isPs

        $bomIsCorrect =
            ($wantBom  -and $encoding -eq 'UTF8-BOM') -or
            (-not $wantBom -and $encoding -eq 'UTF8')

        # Already clean? (correct BOM state AND LF-only)
        if ($bomIsCorrect -and -not $hasCrlf) { return $false }

        if ($Scan) {
            if (-not $Quiet) {
                $target = if ($wantBom) { 'UTF8-BOM' } else { 'UTF8-no-BOM' }
                $crlf   = if ($hasCrlf) { ' +CRLF' } else { '' }
                Write-Host ("  encoding-drift: {0} [{1}{2} -> {3}+LF]" -f `
                    [System.IO.Path]::GetFileName($Path), $encoding, $crlf, $target) -ForegroundColor Yellow
            }
            return $true
        }

        # Decode with the detected source encoding.
        $content = switch ($encoding) {
            'UTF8-BOM' { [System.Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length - 3) }
            'UTF16-LE' { [System.Text.Encoding]::Unicode.GetString($bytes, 2, $bytes.Length - 2) }
            'UTF16-BE' { [System.Text.Encoding]::BigEndianUnicode.GetString($bytes, 2, $bytes.Length - 2) }
            default    { [System.Text.Encoding]::UTF8.GetString($bytes) }
        }

        # Normalize line endings: CRLF -> LF, then any bare CR -> LF.
        $normalized = $content -replace "`r`n", "`n" -replace "`r", "`n"

        # Write back with the encoding correct for this file type.
        $writeEncoding = if ($wantBom) { $Utf8Bom } else { $Utf8NoBom }
        [System.IO.File]::WriteAllText($Path, $normalized, $writeEncoding)

        if (-not $Quiet) {
            $target = if ($wantBom) { 'UTF8-BOM' } else { 'UTF8-no-BOM' }
            $parts  = @()
            if (-not $bomIsCorrect) { $parts += "$encoding -> $target" }
            if ($hasCrlf)           { $parts += 'CRLF -> LF' }
            $reason = '[' + ($parts -join ', ') + ']'
            Write-Host ("  encoding-fix: {0} {1}" -f [System.IO.Path]::GetFileName($Path), $reason) -ForegroundColor Cyan
        }
        return $true
    }
    catch {
        Write-Warning ("  encoding-normalize: failed '{0}': {1}" -f $Path, $_)
        return $false
    }
}

# --- Resolve file list based on mode ---

if ($PreCommit) {
    $gitFiles = & git diff --cached --name-only --diff-filter=ACM 2>$null
    $Files = @($gitFiles | Where-Object { $_ -and $_.Trim() -ne '' })
}
elseif ($Files.Count -eq 0) {
    # stop / scan mode: all git-dirty (modified + added) text files.
    $gitStatus = & git status --porcelain 2>$null
    if ($gitStatus) {
        $Files = @($gitStatus | Where-Object { $_ -match '^[ MARC?][ MARC?] ' } |
            ForEach-Object { $_.Substring(3).Trim() } |
            Where-Object { $_ -ne '' })
    }
}

if ($Files.Count -eq 0) {
    if ($Scan -and -not $Quiet) { Write-Host "  encoding-scan: clean (no dirty files)" -ForegroundColor DarkGreen }
    exit 0
}

$touched = 0
foreach ($f in $Files) {
    $path = $f.Trim('"').Trim("'")
    if (-not [System.IO.Path]::IsPathRooted($path)) {
        $path = Join-Path (Get-Location) $path
    }
    if (Invoke-NormalizeFile $path) { $touched++ }
}

if ($Scan) {
    if ($touched -gt 0) {
        if (-not $Quiet) { Write-Host ("  encoding-scan: {0} file(s) need normalization" -f $touched) -ForegroundColor Yellow }
        exit 1
    }
    if (-not $Quiet) { Write-Host "  encoding-scan: clean" -ForegroundColor DarkGreen }
    exit 0
}

if ($touched -gt 0 -and -not $Quiet) {
    Write-Host ("  encoding-normalize: {0} file(s) normalized" -f $touched) -ForegroundColor DarkCyan
}

# In pre-commit mode, re-stage normalized files so the fix lands in the commit.
if ($PreCommit -and $touched -gt 0) {
    foreach ($f in $Files) {
        $path = $f.Trim('"').Trim("'")
        & git add -- $path 2>$null
    }
}

exit 0
