# gald3r_doctor.ps1 - Environment health check for gald3r projects
# Validates: identity/config, task state, MCP/Docker, vault, platform parity
# Safe to run multiple times (read-only by default; -Fix scope is narrow)
#
# Usage:
#   .\scripts\gald3r_doctor.ps1                    # full health report
#   .\scripts\gald3r_doctor.ps1 -Fix               # apply safe auto-fixes
#   .\scripts\gald3r_doctor.ps1 -Category identity # run one category only
#   .\scripts\gald3r_doctor.ps1 -Quiet             # pass/fail counts only
#
# Fix scope (NARROW by design - the OpenClaw 5.5 lesson):
#   - Creates missing .gald3r/ subdirectories
#   - Writes a minimal .gald3r/.identity stub when the file is missing
#   - Does NOT touch routing, credentials, connection types, or TASKS.md

param(
    [switch]$Fix,
    [ValidateSet('identity', 'tasks', 'mcp', 'vault', 'platform', 'all')]
    [string]$Category = 'all',
    [switch]$Quiet,
    [string]$ProjectRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

if (-not $ProjectRoot) {
    $dir = (Get-Location).Path
    while ($dir -and $dir -ne [System.IO.Path]::GetPathRoot($dir)) {
        if (Test-Path (Join-Path $dir '.gald3r')) {
            $ProjectRoot = $dir
            break
        }
        $dir = Split-Path $dir -Parent
    }
}

if (-not $ProjectRoot -or -not (Test-Path (Join-Path $ProjectRoot '.gald3r'))) {
    Write-Host 'FATAL: Cannot locate .gald3r/ folder. Run from inside a gald3r project.' -ForegroundColor Red
    exit 2
}

$gald3rDir = Join-Path $ProjectRoot '.gald3r'
$script:results = [System.Collections.Generic.List[hashtable]]::new()

function Add-Result {
    param([string]$Status, [string]$Check, [string]$Detail, [string]$FixHint = '')
    $script:results.Add(@{ Status = $Status; Check = $Check; Detail = $Detail; FixHint = $FixHint })
}

function Pass { param([string]$c, [string]$d) Add-Result 'PASS' $c $d }
function Warn { param([string]$c, [string]$d, [string]$f = '') Add-Result 'WARN' $c $d $f }
function Fail { param([string]$c, [string]$d, [string]$f = '') Add-Result 'FAIL' $c $d $f }

# ---------------------------------------------------------------------------
# Category 1: Identity & Config
# ---------------------------------------------------------------------------

function Test-Identity {
    $identityPath = Join-Path $gald3rDir '.identity'

    if (-not (Test-Path $identityPath)) {
        if ($Fix) {
            $newId = [System.Guid]::NewGuid().ToString()
            $stub  = "project_id=stub-$newId`ngald3r_version=unknown`nvault_location={LOCAL}`n"
            Set-Content -Path $identityPath -Value $stub -NoNewline
            Pass 'identity/.identity exists' 'Created stub .identity via -Fix'
        } else {
            Fail 'identity/.identity exists' '.gald3r/.identity not found' 'Run @g-doctor -Fix to create a stub, then fill in project_id and vault_location'
        }
        return
    }

    $raw = Get-Content $identityPath -Raw
    $requiredFields = @('project_id', 'gald3r_version', 'vault_location')
    $missing = @()
    foreach ($field in $requiredFields) {
        if ($raw -notmatch "(?m)^${field}=.+") { $missing += $field }
    }

    if ($missing.Count -gt 0) {
        Fail 'identity/.identity fields' ('Missing required fields: ' + ($missing -join ', ')) 'Edit .gald3r/.identity and add the missing fields'
    } else {
        Pass 'identity/.identity fields' 'project_id, gald3r_version, vault_location all present'
    }

    # Core file presence
    $required = @('TASKS.md', 'PLAN.md', 'PROJECT.md', 'CONSTRAINTS.md', 'BUGS.md', 'SUBSYSTEMS.md')
    $missingFiles = @()
    foreach ($f in $required) {
        $p = Join-Path $gald3rDir $f
        if (-not (Test-Path $p)) { $missingFiles += $f }
    }
    if ($missingFiles.Count -gt 0) {
        Warn 'identity/.gald3r structure' ('Missing core files: ' + ($missingFiles -join ', ')) 'Run @g-setup to initialize missing files'
    } else {
        Pass 'identity/.gald3r structure' 'All core .gald3r/ files present'
    }

    # Subdirectories
    foreach ($sub in @('tasks', 'bugs', 'subsystems')) {
        $subPath = Join-Path $gald3rDir $sub
        if (-not (Test-Path $subPath)) {
            if ($Fix) {
                New-Item -ItemType Directory -Path $subPath -Force | Out-Null
                Pass "identity/$sub/" "Created missing $sub/ via -Fix"
            } else {
                Warn "identity/$sub/" ".gald3r/$sub/ directory missing" "Run @g-doctor -Fix or mkdir .gald3r\$sub"
            }
        } else {
            Pass "identity/$sub/" ".gald3r/$sub/ exists"
        }
    }
}

# ---------------------------------------------------------------------------
# Category 2: Task State
# ---------------------------------------------------------------------------

function Test-Tasks {
    $tasksMd  = Join-Path $gald3rDir 'TASKS.md'
    $tasksDir = Join-Path $gald3rDir 'tasks'

    if (-not (Test-Path $tasksMd)) {
        Warn 'tasks/TASKS.md' 'TASKS.md not found - skipping task sync check' 'Run @g-setup'
        return
    }

    $tasksContent = Get-Content $tasksMd -Raw
    $mdIds = [System.Collections.Generic.HashSet[string]]::new()

    # Table row format
    [regex]::Matches($tasksContent, '\|\s*\[[^\]]+\]\s*\|\s*\[(\d+)\]') | ForEach-Object {
        [void]$mdIds.Add(([int]($_.Groups[1].Value)).ToString())
    }
    # Bullet row format
    [regex]::Matches($tasksContent, '-\s*\[[^\]]+\]\s*\*{0,2}[Tt](?:ask)?\s*(\d+)') | ForEach-Object {
        [void]$mdIds.Add(([int]($_.Groups[1].Value)).ToString())
    }

    if (-not (Test-Path $tasksDir)) {
        Warn 'tasks/sync' 'tasks/ directory missing - cannot verify sync' 'Run @g-doctor -Fix'
        return
    }

    $fileIds = [System.Collections.Generic.HashSet[string]]::new()
    Get-ChildItem $tasksDir -Filter 'task*.md' -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.Name -match 'task(\d+)') { [void]$fileIds.Add(([int]$Matches[1]).ToString()) }
    }

    $phantoms = @($mdIds  | Where-Object { -not $fileIds.Contains($_) })
    $orphans  = @($fileIds | Where-Object { -not $mdIds.Contains($_) })

    if ($phantoms.Count -gt 0) {
        Warn 'tasks/phantom' ($phantoms.Count.ToString() + ' phantom task(s) in TASKS.md with no task file: ' + ($phantoms -join ', ')) 'Create missing task files or remove stale TASKS.md rows'
    } else {
        Pass 'tasks/phantom' 'No phantom tasks detected'
    }

    if ($orphans.Count -gt 0) {
        Warn 'tasks/orphan' ($orphans.Count.ToString() + ' orphan task file(s) not in TASKS.md: ' + ($orphans -join ', ')) 'Add missing rows to TASKS.md or archive stale files via @g-task-archive'
    } else {
        Pass 'tasks/orphan' 'No orphan task files detected'
    }

    Pass 'tasks/TASKS.md' ('TASKS.md present (' + $mdIds.Count.ToString() + ' task IDs parsed)')
}

# ---------------------------------------------------------------------------
# Category 3: MCP / Docker
# ---------------------------------------------------------------------------

function Test-Mcp {
    # Docker engine
    $dockerOk = $false
    try {
        $null = & docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerOk = $true
            Pass 'mcp/docker-engine' 'Docker engine is running'
        } else {
            Fail 'mcp/docker-engine' 'Docker info returned non-zero exit code' 'Start Docker Desktop or the Docker daemon'
        }
    } catch {
        Warn 'mcp/docker-engine' 'docker CLI not found or not in PATH' 'Install Docker Desktop: https://docs.docker.com/desktop/'
    }

    # gald3r container
    if ($dockerOk) {
        try {
            $containers = & docker ps --filter 'name=gald3r' --format '{{.Names}}' 2>&1
            if ($containers -and ($containers -match 'gald3r')) {
                Pass 'mcp/container' ('gald3r container running: ' + ($containers -join ', '))
            } else {
                Warn 'mcp/container' 'No running gald3r container found' 'Run: cd docker && docker compose up -d'
            }
        } catch {
            Warn 'mcp/container' 'Could not query Docker containers' 'Verify Docker is accessible'
        }
    }

    # HTTP health check
    $mcpUrl = 'http://localhost:8092/health'
    try {
        $response = Invoke-WebRequest -Uri $mcpUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Pass 'mcp/health-endpoint' ('MCP server responded OK at ' + $mcpUrl)
        } else {
            Warn 'mcp/health-endpoint' ('MCP server returned HTTP ' + $response.StatusCode) 'Check: docker logs gald3r_docker'
        }
    } catch [System.Net.WebException] {
        Warn 'mcp/health-endpoint' ('MCP server not reachable at ' + $mcpUrl) 'Run: cd docker && docker compose up -d'
    } catch {
        Warn 'mcp/health-endpoint' ('MCP server check failed: ' + $_.Exception.Message) 'Ensure gald3r Docker stack is running'
    }

    # Tool availability
    foreach ($tool in @('node', 'python', 'uv')) {
        try {
            $ver = & $tool --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Pass ('mcp/tool-' + $tool) ($tool + ' available: ' + ($ver | Select-Object -First 1))
            } else {
                Warn ('mcp/tool-' + $tool) ($tool + ' returned non-zero on --version') ('Install or repair ' + $tool)
            }
        } catch {
            Warn ('mcp/tool-' + $tool) ($tool + ' not found in PATH') ('Install ' + $tool + ': see project README')
        }
    }
}

# ---------------------------------------------------------------------------
# Category 4: Vault
# ---------------------------------------------------------------------------

function Test-Vault {
    $identityPath = Join-Path $gald3rDir '.identity'
    if (-not (Test-Path $identityPath)) {
        Warn 'vault/location' '.identity missing - cannot determine vault path' 'Run identity checks first'
        return
    }

    $raw = Get-Content $identityPath -Raw
    if ($raw -notmatch '(?m)^vault_location=(.+)') {
        Warn 'vault/location' 'vault_location not set in .identity' 'Add vault_location= to .gald3r/.identity'
        return
    }
    $vaultLocation = $Matches[1].Trim()

    if ($vaultLocation -eq '{LOCAL}') {
        Pass 'vault/location' 'vault_location={LOCAL} (local vault mode - no remote connectivity check)'
        $localVault = Join-Path $ProjectRoot 'vault'
        if (Test-Path $localVault) {
            $indexYaml = Join-Path $localVault '_index.yaml'
            if (Test-Path $indexYaml) {
                Pass 'vault/index' 'vault/_index.yaml present'
            } else {
                Warn 'vault/index' 'vault/_index.yaml missing' 'Run @g-vault-lint to regenerate the index'
            }
        } else {
            Warn 'vault/local-dir' ('vault/ directory not found at: ' + $localVault) 'Create the vault/ folder or set vault_location to a valid path'
        }
        return
    }

    # Non-local vault
    if (Test-Path $vaultLocation) {
        Pass 'vault/directory' ('Vault directory accessible: ' + $vaultLocation)
        $indexYaml = Join-Path $vaultLocation '_index.yaml'
        if (Test-Path $indexYaml) {
            Pass 'vault/index' '_index.yaml present in vault'
        } else {
            Warn 'vault/index' ('_index.yaml missing from vault at: ' + $vaultLocation) 'Run @g-vault-lint to regenerate'
        }
    } else {
        Fail 'vault/directory' ('Vault directory not found: ' + $vaultLocation) 'Update vault_location in .gald3r/.identity or create the directory'
    }

    # AC7: Remote connectivity check
    if ($vaultLocation -match '^https?://') {
        try {
            $r = Invoke-WebRequest -Uri $vaultLocation -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
            Pass 'vault/remote-api' ('Remote vault API reachable (HTTP ' + $r.StatusCode + ')')
        } catch {
            Fail 'vault/remote-api' ('Remote vault API unreachable: ' + $_.Exception.Message) 'Check network connectivity and vault_location URL'
        }
    }
}

# ---------------------------------------------------------------------------
# Category 5: Platform IDE Parity
# ---------------------------------------------------------------------------

function Test-Platform {
    $platforms = [ordered]@{
        '.cursor'   = '.cursor/'
        '.claude'   = '.claude/'
        '.agent'    = '.agent/'
        '.codex'    = '.codex/'
        '.opencode' = '.opencode/'
    }

    foreach ($kv in $platforms.GetEnumerator()) {
        $path = Join-Path $ProjectRoot $kv.Key
        if (Test-Path $path) {
            Pass ('platform/' + $kv.Key) ($kv.Value + ' directory present')
        } else {
            Warn ('platform/' + $kv.Key) ($kv.Value + ' not found') 'Run @g-setup or platform_parity_sync.ps1 -Sync to restore'
        }
    }

    # Primary surfaces: commands/ and skills/
    foreach ($primary in @('.cursor', '.claude')) {
        $cmdPath   = Join-Path (Join-Path $ProjectRoot $primary) 'commands'
        $skillPath = Join-Path (Join-Path $ProjectRoot $primary) 'skills'
        if (Test-Path $cmdPath) {
            $cmdCount = (Get-ChildItem $cmdPath -Filter '*.md').Count
            Pass ('platform/' + $primary + '/commands') ($primary + '/commands/ present (' + $cmdCount + ' files)')
        } else {
            Warn ('platform/' + $primary + '/commands') ($primary + '/commands/ missing') 'Run @g-setup'
        }
        if (Test-Path $skillPath) {
            Pass ('platform/' + $primary + '/skills') ($primary + '/skills/ present')
        } else {
            Warn ('platform/' + $primary + '/skills') ($primary + '/skills/ missing') 'Run @g-setup'
        }
    }

    # Copilot (Phase 1)
    $copilotPath = Join-Path $ProjectRoot '.copilot'
    if (Test-Path $copilotPath) {
        Pass 'platform/.copilot' '.copilot/ directory present (Phase 1 compatible)'
    } else {
        Warn 'platform/.copilot' '.copilot/ not found - GitHub Copilot support not installed' 'Run platform_parity_sync.ps1 -Sync'
    }
}

# ---------------------------------------------------------------------------
# Run selected categories
# ---------------------------------------------------------------------------

$categoriesToRun = switch ($Category) {
    'identity' { @('identity') }
    'tasks'    { @('tasks') }
    'mcp'      { @('mcp') }
    'vault'    { @('vault') }
    'platform' { @('platform') }
    default    { @('identity', 'tasks', 'mcp', 'vault', 'platform') }
}

foreach ($cat in $categoriesToRun) {
    switch ($cat) {
        'identity' { Test-Identity }
        'tasks'    { Test-Tasks }
        'mcp'      { Test-Mcp }
        'vault'    { Test-Vault }
        'platform' { Test-Platform }
    }
}

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

$passCount = @($script:results | Where-Object { $_.Status -eq 'PASS' }).Count
$warnCount = @($script:results | Where-Object { $_.Status -eq 'WARN' }).Count
$failCount = @($script:results | Where-Object { $_.Status -eq 'FAIL' }).Count

if (-not $Quiet) {
    Write-Host ''
    Write-Host 'gald3r doctor -- Environment Health Report' -ForegroundColor Cyan
    Write-Host ('=' * 50) -ForegroundColor Cyan
    Write-Host ''

    foreach ($r in $script:results) {
        switch ($r.Status) {
            'PASS' {
                Write-Host ('[PASS]  ' + $r.Check) -ForegroundColor Green
                Write-Host ('        ' + $r.Detail) -ForegroundColor Gray
            }
            'WARN' {
                Write-Host ('[WARN]  ' + $r.Check) -ForegroundColor Yellow
                Write-Host ('        ' + $r.Detail) -ForegroundColor Gray
                if ($r.FixHint) {
                    Write-Host ('        Fix: ' + $r.FixHint) -ForegroundColor DarkCyan
                }
            }
            'FAIL' {
                Write-Host ('[FAIL]  ' + $r.Check) -ForegroundColor Red
                Write-Host ('        ' + $r.Detail) -ForegroundColor Gray
                if ($r.FixHint) {
                    Write-Host ('        Fix: ' + $r.FixHint) -ForegroundColor DarkCyan
                }
            }
        }
    }

    Write-Host ''
    Write-Host ('=' * 50) -ForegroundColor Cyan
    $summaryPass = '[PASS] ' + $passCount
    $summaryWarn = '[WARN] ' + $warnCount
    $summaryFail = '[FAIL] ' + $failCount
    Write-Host 'Summary: ' -NoNewline
    Write-Host ($summaryPass + '  ') -NoNewline -ForegroundColor Green
    Write-Host ($summaryWarn + '  ') -NoNewline -ForegroundColor Yellow
    Write-Host $summaryFail -ForegroundColor Red

    if ($Fix) {
        Write-Host ''
        Write-Host 'NOTE: -Fix applied. Routing, credentials, and connection settings were NOT changed.' -ForegroundColor DarkCyan
    }

    Write-Host ''
}

if ($failCount -gt 0) { exit 1 } else { exit 0 }
