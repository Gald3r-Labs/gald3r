# g-hk-kiro-cli-tool-end.ps1 - kiro-cli `postToolUse` -> canonical `tool-end`
# @subsystems: PLATFORM_INTEGRATION
# Thin trigger shim ONLY: reads the kiro-cli STDIN-JSON payload and pipes it to
# the shared canonical event core. NO business logic lives here.
$ErrorActionPreference = 'SilentlyContinue'
$payload = $input | Out-String
$payload | python .kiro/hooks/g-hk-on-tool-end.py
exit $LASTEXITCODE
