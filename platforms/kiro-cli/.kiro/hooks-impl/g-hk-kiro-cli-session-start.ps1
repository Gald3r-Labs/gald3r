# g-hk-kiro-cli-session-start.ps1 - kiro-cli `agentSpawn` -> canonical `session-start`
# @subsystems: PLATFORM_INTEGRATION
# Thin trigger shim ONLY: reads the kiro-cli STDIN-JSON payload and pipes it to
# the shared canonical event core. NO business logic lives here.
$ErrorActionPreference = 'SilentlyContinue'
$payload = $input | Out-String
$payload | python .kiro/hooks/g-hk-on-session-start.py
exit $LASTEXITCODE
