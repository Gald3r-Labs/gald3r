# @subsystems: LOGGING_SYSTEM
<#
.SYNOPSIS
    Shared gald3r hook system helpers (Task 600).

.DESCRIPTION
    Pure-function PowerShell helpers for the gald3r hook system extensions
    designed in `docs/20260506_000000_Cursor_T600_HOOK_SYSTEM_EXTENSIONS.md`.

    All helpers are side-effect-free except for INFO-level logging via
    Write-Verbose. They are safe to dot-source from other hook scripts.

    Functions:
      Test-HookToolMatch      — glob match tool names against patterns (B-3)
      Convert-HookArgSafe     — shell-safe arg substitution for ps/bash (B-6)
      Read-HookEventEnvelope  — parse the GALD3R_HOOK_EVENT JSON envelope

    Source-of-truth contract: see the design doc.

.NOTES
    Task: 600
    Subsystems: hook-system, ide-integration
#>

Set-StrictMode -Version Latest

# -----------------------------------------------------------------------------
# Test-HookToolMatch  (AC#2 / B-3)
# -----------------------------------------------------------------------------

<#
.SYNOPSIS
    Returns $true if the tool name matches at least one of the patterns.

.PARAMETER ToolName
    The tool identifier produced by the IDE (e.g., 'bash_run', 'file_read',
    'mcp__chrome-devtools__click'). Case-sensitive.

.PARAMETER Patterns
    String array of patterns. Supported syntax:
      'bash'           -- exact match
      'bash_*'         -- prefix match
      '*_run'          -- suffix match
      'mcp__*__execute'-- prefix + suffix (single '*' anywhere is fine)
      '*'              -- match every tool name

    '?' character classes, '**', and '/' segment anchors are NOT supported.

.PARAMETER MatchAllOnEmpty
    When -Patterns is empty/null, return $true (default behavior of
    "no filter == fire on every tool"). Set to $false to invert.

.EXAMPLE
    Test-HookToolMatch -ToolName 'bash_run' -Patterns @('bash_*')
    # True

.EXAMPLE
    Test-HookToolMatch -ToolName 'Bash' -Patterns @('bash_*')
    # False (case-sensitive AND no underscore)
#>
function Test-HookToolMatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$ToolName,

        [string[]]$Patterns,

        [bool]$MatchAllOnEmpty = $true
    )

    if ($null -eq $Patterns -or $Patterns.Count -eq 0) {
        return [bool]$MatchAllOnEmpty
    }

    foreach ($pattern in $Patterns) {
        if ([string]::IsNullOrEmpty($pattern)) { continue }

        # Exact match shortcut
        if ($pattern -ceq $ToolName) { return $true }

        # Build a literal-anchored regex from the pattern.
        # '*' is the only wildcard; everything else is escaped.
        # Use String.Split to preserve empty leading/trailing segments
        # (e.g., '*foo' splits to ['', 'foo']; 'foo*' splits to ['foo', '']).
        $regexParts = @()
        foreach ($segment in $pattern.Split('*')) {
            $regexParts += [regex]::Escape($segment)
        }
        $regex = '^' + ($regexParts -join '.*') + '$'

        if ($ToolName -cmatch $regex) { return $true }
    }

    return $false
}

# -----------------------------------------------------------------------------
# Convert-HookArgSafe  (AC#4 / B-6)
# -----------------------------------------------------------------------------

<#
.SYNOPSIS
    Returns a shell-safe single-quoted literal for the given value.

.DESCRIPTION
    Two modes:

    -Shell powershell  (default)
        Single-quoted. Embedded single quotes doubled. CR/LF replaced
        with placeholders so multi-line values cannot terminate the
        statement. PowerShell single-quote literals do not interpolate
        $variable, do not run $( ... ), and do not honor backticks for
        escapes.

    -Shell bash
        Single-quoted. Embedded single quotes replaced with the
        canonical '\'' end-quote / escaped-quote / re-open trick.
        Bash single-quote literals are perfectly literal.

.PARAMETER Value
    The string to quote. $null becomes the empty string ''.

.PARAMETER Shell
    'powershell' (default) or 'bash'.

.EXAMPLE
    Convert-HookArgSafe -Value "it's"
    # 'it''s'

.EXAMPLE
    Convert-HookArgSafe -Value 'a$(whoami)b' -Shell bash
    # 'a$(whoami)b'

.EXAMPLE
    Convert-HookArgSafe -Value "; rm -rf /" -Shell powershell
    # '; rm -rf /'

.NOTES
    See §4 of the T600 design doc for the threat model and full vector
    table. CR/LF handling differs between the shells:
      powershell: replaced with literal <CR>/<LF> placeholders + Write-Verbose
      bash:       passed through (bash tolerates multi-line single-quoted argv)
#>
function Convert-HookArgSafe {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [AllowEmptyString()]
        [string]$Value,

        [ValidateSet('powershell', 'bash')]
        [string]$Shell = 'powershell'
    )

    if ($null -eq $Value) { $Value = '' }

    switch ($Shell) {
        'powershell' {
            $original = $Value
            # Replace CR/LF with visible placeholders. Multi-line values
            # break PowerShell's command parser when interpolated.
            $sanitized = $Value `
                -replace "`r", '<CR>' `
                -replace "`n", '<LF>'
            if ($sanitized -ne $original) {
                Write-Verbose "Convert-HookArgSafe: stripped CR/LF from value"
            }
            # Double up embedded single quotes for PowerShell single-quote literal.
            $escaped = $sanitized -replace "'", "''"
            return "'$escaped'"
        }

        'bash' {
            # 'foo'\''bar' is the canonical bash escape: close, escaped quote, reopen.
            $escaped = $Value -replace "'", "'\''"
            return "'$escaped'"
        }
    }
}

# -----------------------------------------------------------------------------
# Read-HookEventEnvelope  (companion to AC#1 / B-2)
# -----------------------------------------------------------------------------

<#
.SYNOPSIS
    Parse the gald3r hook event envelope from $env:GALD3R_HOOK_EVENT or a file.

.DESCRIPTION
    Hook scripts (command-type) receive the same JSON envelope that HTTP-type
    hooks receive in their POST body. The envelope is published via
    $env:GALD3R_HOOK_EVENT (preferred) or written to a temp file path passed
    via $env:GALD3R_HOOK_EVENT_FILE for environments where env-var size is
    constrained.

    Returns $null if neither is set.

.PARAMETER InlineJson
    Optional override; pass a JSON string directly (useful for tests).

.EXAMPLE
    $event = Read-HookEventEnvelope
    if ($event -and $event.tool.name -like 'bash_*') { ... }
#>
function Read-HookEventEnvelope {
    [CmdletBinding()]
    param(
        [string]$InlineJson
    )

    $json = $null

    if (-not [string]::IsNullOrEmpty($InlineJson)) {
        $json = $InlineJson
    } elseif (-not [string]::IsNullOrEmpty($env:GALD3R_HOOK_EVENT)) {
        $json = $env:GALD3R_HOOK_EVENT
    } elseif (-not [string]::IsNullOrEmpty($env:GALD3R_HOOK_EVENT_FILE) -and (Test-Path $env:GALD3R_HOOK_EVENT_FILE)) {
        $json = Get-Content -Path $env:GALD3R_HOOK_EVENT_FILE -Raw
    }

    if ([string]::IsNullOrEmpty($json)) { return $null }

    try {
        return $json | ConvertFrom-Json
    } catch {
        Write-Verbose "Read-HookEventEnvelope: failed to parse JSON: $($_.Exception.Message)"
        return $null
    }
}

# -----------------------------------------------------------------------------
# Test vectors (smoke check — run this file directly to verify behavior)
# -----------------------------------------------------------------------------
#
# Test: Test-HookToolMatch
#   Test-HookToolMatch -ToolName 'bash_run' -Patterns @('bash_*')      -> $true
#   Test-HookToolMatch -ToolName 'bash'     -Patterns @('bash_*')      -> $false
#   Test-HookToolMatch -ToolName 'file_read' -Patterns @('bash_*','file_*') -> $true
#   Test-HookToolMatch -ToolName 'whatever' -Patterns @()              -> $true (default)
#   Test-HookToolMatch -ToolName 'whatever' -Patterns @() -MatchAllOnEmpty $false -> $false
#   Test-HookToolMatch -ToolName 'mcp__chrome-devtools__click' -Patterns @('mcp__*__click') -> $true
#
# Test: Convert-HookArgSafe
#   Convert-HookArgSafe -Value "it's" -Shell powershell   -> 'it''s'
#   Convert-HookArgSafe -Value "it's" -Shell bash         -> 'it'\''s'
#   Convert-HookArgSafe -Value '$(whoami)' -Shell powershell -> '$(whoami)'   (literal — no interp)
#   Convert-HookArgSafe -Value '; rm -rf /' -Shell bash   -> '; rm -rf /'    (literal — single quotes)
#

if ($MyInvocation.InvocationName -eq '.' -or $MyInvocation.InvocationName -eq '&' -or $MyInvocation.MyCommand.CommandType -eq 'ExternalScript') {
    if ($args -contains '-RunSelfTest') {
        $failed = 0
        function Assert-Eq {
            param([string]$Name, $Got, $Want)
            if ($Got -ceq $Want) {
                Write-Host "ok    $Name" -ForegroundColor Green
            } else {
                Write-Host "FAIL  $Name`n  got:  $Got`n  want: $Want" -ForegroundColor Red
                $script:failed++
            }
        }

        # Test-HookToolMatch
        Assert-Eq 'match prefix bash_*' (Test-HookToolMatch -ToolName 'bash_run' -Patterns @('bash_*')) $true
        Assert-Eq 'no match bash vs bash_*' (Test-HookToolMatch -ToolName 'bash' -Patterns @('bash_*')) $false
        Assert-Eq 'OR file_*' (Test-HookToolMatch -ToolName 'file_read' -Patterns @('bash_*','file_*')) $true
        Assert-Eq 'empty patterns -> true' (Test-HookToolMatch -ToolName 'whatever' -Patterns @()) $true
        Assert-Eq 'empty patterns + MatchAllOnEmpty=$false -> false' (Test-HookToolMatch -ToolName 'whatever' -Patterns @() -MatchAllOnEmpty $false) $false
        Assert-Eq 'mcp middle wildcard' (Test-HookToolMatch -ToolName 'mcp__chrome-devtools__click' -Patterns @('mcp__*__click')) $true
        Assert-Eq 'case sensitive' (Test-HookToolMatch -ToolName 'Bash_run' -Patterns @('bash_*')) $false
        Assert-Eq 'star matches all' (Test-HookToolMatch -ToolName 'anything' -Patterns @('*')) $true

        # Convert-HookArgSafe
        Assert-Eq 'ps simple' (Convert-HookArgSafe -Value 'hello' -Shell powershell) "'hello'"
        Assert-Eq 'ps single quote' (Convert-HookArgSafe -Value "it's" -Shell powershell) "'it''s'"
        Assert-Eq 'ps dollar paren literal' (Convert-HookArgSafe -Value '$(whoami)' -Shell powershell) "'`$(whoami)'".Replace('`','')
        Assert-Eq 'bash simple' (Convert-HookArgSafe -Value 'hello' -Shell bash) "'hello'"
        Assert-Eq 'bash single quote' (Convert-HookArgSafe -Value "it's" -Shell bash) "'it'\''s'"
        Assert-Eq 'bash semicolon' (Convert-HookArgSafe -Value '; rm -rf /' -Shell bash) "'; rm -rf /'"

        if ($failed -gt 0) {
            Write-Host "`n$failed test(s) failed" -ForegroundColor Red
            exit 1
        }
        Write-Host "`nAll tests passed." -ForegroundColor Green
        exit 0
    }
}
